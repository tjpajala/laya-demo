"""On-disk result cache, keyed by a deterministic slug per (model, dataset,
limit). Each dataset is cached independently - selecting {easy, hard} then
later {healthcare, hard} only ever (re)runs healthcare, since hard's cache
entry doesn't depend on what else was selected alongside it.

A slug is `model__dataset__limit__hash`, so the same configuration always
maps to the same cache entry: re-POSTing an identical run reuses it, and
DELETE-ing it is what "remove for a rerun" means at the API layer.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import config

RESULTS_DIR = config.CACHE_DIR / "results"
SUMMARIES_DIR = config.CACHE_DIR / "summaries"
RAW_DIR = config.CACHE_DIR / "raw"
LEDGER_DIR = config.CACHE_DIR / "ledgers"

for _d in (RESULTS_DIR, SUMMARIES_DIR, RAW_DIR, LEDGER_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def make_slug(model: str, dataset: str, limit: int | None, dataset_hash: str) -> str:
    limit_part = f"limit{limit}" if limit else "all"
    return f"{model}__{dataset}__{limit_part}__{dataset_hash[:12]}"


def model_from_slug(slug: str) -> str:
    return slug.split("__", 1)[0]


def dataset_from_slug(slug: str) -> str:
    return slug.split("__")[1]


def results_path(slug: str) -> Path:
    return RESULTS_DIR / f"{slug}.jsonl"


def summary_path(slug: str) -> Path:
    return SUMMARIES_DIR / f"{slug}.json"


def raw_dir(slug: str) -> Path:
    return RAW_DIR / slug


def ledger_path(slug: str) -> Path:
    return LEDGER_DIR / f"{slug}.jsonl"


def is_cached(slug: str) -> bool:
    return summary_path(slug).exists() and results_path(slug).exists()


def progress(slug: str) -> int:
    """Completed task count for a run in progress, by counting streamed result lines."""
    path = results_path(slug)
    if not path.exists():
        return 0
    with path.open() as fh:
        return sum(1 for line in fh if line.strip())


def read_records(slug: str) -> list[dict]:
    """The cached per-task result records for a completed run.

    Used to recombine multiple datasets' results into a pooled summary on
    read (see main.py's /api/comparison), without re-running anything.
    """
    records = []
    with results_path(slug).open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def clear(slug: str) -> None:
    for path in (results_path(slug), summary_path(slug), ledger_path(slug)):
        path.unlink(missing_ok=True)
    raw = raw_dir(slug)
    if raw.exists():
        shutil.rmtree(raw)
