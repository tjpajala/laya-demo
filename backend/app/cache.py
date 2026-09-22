"""On-disk result cache, keyed by a deterministic slug.

A run's slug is fully determined by (model, splits, limit, dataset hash), so
the same configuration always maps to the same cache entry: re-POSTing an
identical run reuses it, and DELETE-ing it is what "remove for a rerun"
means at the API layer.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import config

RESULTS_DIR = config.CACHE_DIR / "results"
SUMMARIES_DIR = config.CACHE_DIR / "summaries"
RAW_DIR = config.CACHE_DIR / "raw"
LEDGER_DIR = config.CACHE_DIR / "ledgers"

for _d in (RESULTS_DIR, SUMMARIES_DIR, RAW_DIR, LEDGER_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def make_slug(model: str, splits: list[str], limit: int | None, dataset_hash: str) -> str:
    split_part = "-".join(sorted(splits))
    limit_part = f"limit{limit}" if limit else "all"
    return f"{model}__{split_part}__{limit_part}__{dataset_hash[:12]}"


def model_from_slug(slug: str) -> str:
    return slug.split("__", 1)[0]


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


def clear(slug: str) -> None:
    for path in (results_path(slug), summary_path(slug), ledger_path(slug)):
        path.unlink(missing_ok=True)
    raw = raw_dir(slug)
    if raw.exists():
        shutil.rmtree(raw)
