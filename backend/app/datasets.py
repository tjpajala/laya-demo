"""Loading the available task datasets: JevBench's public splits plus
PubMedQA (healthcare). Each entry is an independent, individually
cacheable dataset - see cache.py and jobs.py for why that matters.
"""

from __future__ import annotations

from . import config
from .vendor.jevbench.tasks import Task, load_jsonl

DATASETS: dict[str, dict] = {
    "easy": {
        "path": config.DATA_DIR / "jevbench" / "easy.jsonl",
        "label": "JevBench - easy",
    },
    "original": {
        "path": config.DATA_DIR / "jevbench" / "original.jsonl",
        "label": "JevBench - original",
    },
    "hard": {
        "path": config.DATA_DIR / "jevbench" / "hard.jsonl",
        "label": "JevBench - hard",
    },
    "healthcare": {
        "path": config.DATA_DIR / "healthcare" / "pubmedqa.jsonl",
        "label": "PubMedQA - healthcare",
    },
}
DATASET_ORDER = ["easy", "original", "hard", "healthcare"]


def available_datasets() -> list[dict]:
    """Dataset name + label + task count, for the frontend's picker."""
    out = []
    for name in DATASET_ORDER:
        entry = DATASETS[name]
        n = len(load_jsonl(str(entry["path"])))
        out.append({"name": name, "label": entry["label"], "n": n})
    return out


def load_dataset(name: str, limit: int | None) -> list[Task]:
    if name not in DATASETS:
        raise ValueError(f"unknown dataset {name!r}; choose one of {DATASET_ORDER}")
    tasks = load_jsonl(str(DATASETS[name]["path"]))
    if limit is not None:
        tasks = tasks[:limit]
    return tasks
