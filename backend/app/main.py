from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import cache, datasets
from .jobs import JobManager, JobState
from .schemas import (
    ComparisonEntry,
    ComparisonResponse,
    DatasetsResponse,
    RunRequest,
    RunStatusResponse,
)
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
        splits=job.splits,
        limit=job.limit,
        status=job.status,
        n_planned=job.n_planned,
        n_done=manager.progress(job.slug) if job.status == "running" else job.n_planned,
        error=job.error,
        summary=summary,
    )


@app.get("/api/datasets", response_model=DatasetsResponse)
def get_datasets() -> DatasetsResponse:
    return DatasetsResponse(splits=datasets.available_splits())


@app.post("/api/runs", response_model=RunStatusResponse)
def start_run(req: RunRequest) -> RunStatusResponse:
    try:
        job = manager.start_or_get(req.model, req.splits, req.limit, force_rerun=req.force_rerun)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return _job_to_response(job)


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
            splits=[],
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
def get_comparison(splits: str, limit: int | None = None) -> ComparisonResponse:
    split_list = [s for s in splits.split(",") if s]
    try:
        tasks = datasets.load_tasks(split_list, limit)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    dhash = dataset_hash(tasks)

    entries = {}
    for model in ("laya", "open_jev"):
        slug = cache.make_slug(model, split_list, limit, dhash)
        ready = cache.is_cached(slug)
        summary = json.loads(cache.summary_path(slug).read_text()) if ready else None
        entries[model] = ComparisonEntry(slug=slug, ready=ready, summary=summary)
    return ComparisonResponse(**entries)
