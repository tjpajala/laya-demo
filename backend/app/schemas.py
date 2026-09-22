from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Split = Literal["easy", "original", "hard"]
Model = Literal["laya", "open_jev"]


class RunRequest(BaseModel):
    model: Model
    splits: list[Split] = Field(min_length=1)
    limit: int | None = Field(default=None, gt=0)
    force_rerun: bool = False


class RunStatusResponse(BaseModel):
    slug: str
    model: str
    splits: list[str]
    limit: int | None
    status: Literal["running", "done", "failed"]
    n_planned: int
    n_done: int
    error: str | None = None
    summary: dict[str, Any] | None = None


class SplitInfo(BaseModel):
    name: str
    n: int


class DatasetsResponse(BaseModel):
    splits: list[SplitInfo]


class ComparisonEntry(BaseModel):
    slug: str
    ready: bool
    summary: dict[str, Any] | None = None


class ComparisonResponse(BaseModel):
    laya: ComparisonEntry
    open_jev: ComparisonEntry
