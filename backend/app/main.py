from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import cache, datasets
from .jobs import JobManager, JobState
from .schemas import (
    ComparisonResponse,
    DatasetMetric,
    DatasetsResponse,
    ModelComparisonEntry,
    RunBatchResponse,
    RunRequest,
    RunStatusResponse,
)
from .vendor.jevbench.summarize import summarize
from .vendor.jevbench.tasks import dataset_hash

app = FastAPI(title="Laya vs Open-Jev on JevBench")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

manager = JobManager()


def _job_to_response(job: JobState) -> RunStatusResponse:
    summary = None
    if job.status == "done":
        path = cache.summary_path(job.slug)
        if path.exists():
            summary = json.loads(path.read_text())
    return RunStatusResponse(
        slug=job.slug,
        model=job.model,
        dataset=job.dataset,
        limit=job.limit,
        status=job.status,
        n_planned=job.n_planned,
        n_done=manager.progress(job.slug) if job.status == "running" else job.n_planned,
        error=job.error,
        summary=summary,
    )


@app.get("/api/datasets", response_model=DatasetsResponse)
def get_datasets() -> DatasetsResponse:
    return DatasetsResponse(datasets=datasets.available_datasets())


@app.post("/api/runs", response_model=RunBatchResponse)
def start_runs(req: RunRequest) -> RunBatchResponse:
    runs = []
    for name in req.datasets:
        try:
            job = manager.start_or_get(req.model, name, req.limit, force_rerun=req.force_rerun)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        runs.append(_job_to_response(job))
    return RunBatchResponse(runs=runs)


@app.get("/api/runs/{slug}", response_model=RunStatusResponse)
def get_run(slug: str) -> RunStatusResponse:
    job = manager.status(slug)
    if job is not None:
        return _job_to_response(job)
    if cache.is_cached(slug):
        summary = json.loads(cache.summary_path(slug).read_text())
        return RunStatusResponse(
            slug=slug,
            model=cache.model_from_slug(slug),
            dataset=cache.dataset_from_slug(slug),
            limit=None,
            status="done",
            n_planned=summary["n_planned"],
            n_done=summary["n_attempted"],
            summary=summary,
        )
    raise HTTPException(404, "unknown run")


@app.delete("/api/runs/{slug}")
def delete_run(slug: str) -> dict:
    try:
        manager.clear(slug)
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e
    return {"cleared": True}


@app.get("/api/comparison", response_model=ComparisonResponse)
def get_comparison(
    datasets_param: str = Query(..., alias="datasets"), limit: int | None = None
) -> ComparisonResponse:
    names = [n for n in datasets_param.split(",") if n]
    if not names:
        raise HTTPException(400, "at least one dataset must be given")

    entries = {}
    for model in ("laya", "open_jev"):
        per_dataset: list[DatasetMetric] = []
        combined_tasks = []
        combined_records = []
        combined_charged = 0.0
        all_ready = True

        for name in names:
            try:
                tasks = datasets.load_dataset(name, limit)
            except ValueError as e:
                raise HTTPException(400, str(e)) from e
            dhash = dataset_hash(tasks)
            slug = cache.make_slug(model, name, limit, dhash)
            ready = cache.is_cached(slug)
            summary = json.loads(cache.summary_path(slug).read_text()) if ready else None
            per_dataset.append(DatasetMetric(dataset=name, slug=slug, ready=ready, summary=summary))
            if ready:
                combined_tasks.extend(tasks)
                combined_records.extend(cache.read_records(slug))
                combined_charged += summary.get("ledger_charged_usd") or 0.0
            else:
                all_ready = False

        combined = summarize(combined_tasks, combined_records, combined_charged) if all_ready else None
        entries[model] = ModelComparisonEntry(per_dataset=per_dataset, combined=combined)

    return ComparisonResponse(**entries)
