"""Loading and filtering the vendored public JevBench task set."""

from __future__ import annotations

from . import config
from .vendor.jevbench.tasks import Task, load_jsonl

SPLIT_ORDER = ["easy", "original", "hard"]
SPLIT_FILES = {"easy": "easy.jsonl", "original": "original.jsonl", "hard": "hard.jsonl"}


def available_splits() -> list[dict]:
    """Split name + task count, for the frontend's picker."""
    out = []
    for name in SPLIT_ORDER:
        tasks = load_jsonl(str(config.DATA_DIR / SPLIT_FILES[name]))
        out.append({"name": name, "n": len(tasks)})
    return out


def load_tasks(splits: list[str], limit: int | None) -> list[Task]:
    chosen = [s for s in SPLIT_ORDER if s in splits]
    unknown = set(splits) - set(SPLIT_ORDER)
    if unknown:
        raise ValueError(f"unknown split(s): {sorted(unknown)}")
    if not chosen:
        raise ValueError("at least one split must be selected")
    tasks: list[Task] = []
    for split in chosen:
        tasks.extend(load_jsonl(str(config.DATA_DIR / SPLIT_FILES[split])))
    if limit is not None:
        tasks = tasks[:limit]
    return tasks
