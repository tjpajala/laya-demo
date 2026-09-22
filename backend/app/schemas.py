from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Model = Literal["laya", "open_jev"]


class RunRequest(BaseModel):
    model: Model
    datasets: list[str] = Field(min_length=1)
    limit: int | None = Field(default=None, gt=0, description="cap applied per dataset")
    force_rerun: bool = False


class RunStatusResponse(BaseModel):
    slug: str
    model: str
    dataset: str
    limit: int | None
    status: Literal["running", "done", "failed"]
    n_planned: int
    n_done: int
    error: str | None = None
    summary: dict[str, Any] | None = None


class RunBatchResponse(BaseModel):
    runs: list[RunStatusResponse]


class DatasetInfo(BaseModel):
    name: str
    label: str
    n: int


class DatasetsResponse(BaseModel):
    datasets: list[DatasetInfo]


class DatasetMetric(BaseModel):
    dataset: str
    slug: str
    ready: bool
    summary: dict[str, Any] | None = None


class ModelComparisonEntry(BaseModel):
    per_dataset: list[DatasetMetric]
    combined: dict[str, Any] | None = None  # pooled summarize() over all selected+ready datasets


class ComparisonResponse(BaseModel):
    laya: ModelComparisonEntry
    open_jev: ModelComparisonEntry
