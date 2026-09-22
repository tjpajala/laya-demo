"""In-memory job orchestration over the on-disk cache.

Jobs run on a background thread per (model, dataset, limit) combination.
The slug is deterministic, so re-requesting an identical configuration
either attaches to the job already running or returns the cached result
instantly; nothing is re-run unless the cache was explicitly cleared
first. Each dataset is its own job - requesting multiple datasets at once
is the API layer's job (main.py), by calling start_or_get once per dataset.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field

from . import cache, datasets
from .runners import build_adapter
from .vendor.jevbench.budget import Ledger
from .vendor.jevbench.runner import Runner
from .vendor.jevbench.summarize import summarize
from .vendor.jevbench.tasks import dataset_hash


@dataclass
class JobState:
    slug: str
    model: str
    dataset: str
    limit: int | None
    n_planned: int
    status: str = "running"  # running | done | failed
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None


class JobManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, JobState] = {}

    def status(self, slug: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(slug)

    def start_or_get(
        self, model: str, dataset: str, limit: int | None, force_rerun: bool = False
    ) -> JobState:
        tasks = datasets.load_dataset(dataset, limit)
        dhash = dataset_hash(tasks)
        slug = cache.make_slug(model, dataset, limit, dhash)

        with self._lock:
            existing = self._jobs.get(slug)
            if existing is not None and existing.status == "running":
                return existing
            if force_rerun:
                cache.clear(slug)
            elif cache.is_cached(slug):
                job = JobState(
                    slug=slug, model=model, dataset=dataset, limit=limit,
                    n_planned=len(tasks), status="done", finished_at=time.time(),
                )
                self._jobs[slug] = job
                return job
            else:
                cache.clear(slug)  # drop any stale/partial results from an earlier crash
            job = JobState(slug=slug, model=model, dataset=dataset, limit=limit, n_planned=len(tasks))
            self._jobs[slug] = job

        threading.Thread(target=self._run, args=(job, tasks), daemon=True).start()
        return job

    def _run(self, job: JobState, tasks) -> None:
        try:
            adapter = build_adapter(job.model)
            ledger = Ledger(str(cache.ledger_path(job.slug)), cap_usd=1_000_000)
            runner = Runner(adapter, ledger, raw_dir=str(cache.raw_dir(job.slug)))
            records = runner.run_all(tasks, results_path=str(cache.results_path(job.slug)))
            summary = summarize(tasks, records, ledger.charged)
            cache.summary_path(job.slug).write_text(json.dumps(summary, indent=2, sort_keys=True))
            with self._lock:
                job.status = "done"
                job.finished_at = time.time()
        except Exception as e:  # noqa: BLE001 - surfaced to the API as a failed job, not a crash
            with self._lock:
                job.status = "failed"
                job.error = f"{type(e).__name__}: {e}"
                job.finished_at = time.time()

    @staticmethod
    def progress(slug: str) -> int:
        return cache.progress(slug)

    def clear(self, slug: str) -> None:
        with self._lock:
            existing = self._jobs.get(slug)
            if existing is not None and existing.status == "running":
                raise RuntimeError("job is running; wait for it to finish before clearing")
            self._jobs.pop(slug, None)
        cache.clear(slug)
