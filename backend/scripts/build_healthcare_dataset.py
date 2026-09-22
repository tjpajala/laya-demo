#!/usr/bin/env python3
"""Generates backend/app/data/healthcare/pubmedqa.jsonl from qiaojin/PubMedQA.

Run once, by hand, to (re)produce the committed dataset file - this is a
one-off content-generation step, not part of the Docker build or app
runtime (matching how backend/app/data/jevbench/*.jsonl are committed
static files, not fetched on demand).

Source: qiaojin/PubMedQA, config "pqa_labeled" (1000 expert-labeled
biomedical QA examples, MIT licensed). Fetched via the public
datasets-server REST API (stdlib only, no huggingface_hub/datasets
dependency needed for this one-off script).

Maps each row onto JevBench's Task schema as a `choice` question over
{yes, no, maybe}: `state` is the abstract (the evidence), `question.
instructions` folds in PubMedQA's own question. `long_answer` is
deliberately never included anywhere - it is PubMedQA's answer
explanation, and including it would leak the label into the state.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

DATASET = "qiaojin/PubMedQA"
CONFIG = "pqa_labeled"
N_ROWS = 100  # matches the scale of the existing easy/original/hard splits (48/72/111)
OUT_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "healthcare" / "pubmedqa.jsonl"

CRITERIA = {
    "yes": "The evidence clearly supports a yes answer to the question.",
    "no": "The evidence clearly supports a no answer to the question.",
    "maybe": "The evidence is inconclusive, mixed, or does not clearly support yes or no.",
}
LABELS = sorted(CRITERIA)  # ["maybe", "no", "yes"]


def fetch_rows(n: int) -> list[dict]:
    rows: list[dict] = []
    page = 100
    while len(rows) < n:
        url = (
            "https://datasets-server.huggingface.co/rows"
            f"?dataset={DATASET.replace('/', '%2F')}&config={CONFIG}&split=train"
            f"&offset={len(rows)}&length={min(page, n - len(rows))}"
        )
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = json.load(resp)
        batch = [r["row"] for r in body["rows"]]
        if not batch:
            break
        rows.extend(batch)
    return rows[:n]


def to_task(row: dict) -> dict:
    contexts = row["context"]["contexts"]
    labels = row["context"].get("labels") or []
    if labels and len(labels) == len(contexts):
        state = "\n\n".join(f"{lab}: {txt}" for lab, txt in zip(labels, contexts))
    else:
        state = "\n\n".join(contexts)

    expected = row["final_decision"].strip().lower()
    if expected not in LABELS:
        raise ValueError(f"unexpected final_decision {expected!r} for pubid {row['pubid']}")

    return {
        "id": f"pubmedqa-{row['pubid']}",
        "family": "medical_qa",
        "state": state,
        "question": {
            "type": "choice",
            "instructions": (
                "Based only on the research context above, what is the answer to this "
                f"question: {row['question']}"
            ),
            "criteria": CRITERIA,
        },
        "labels": LABELS,
        "expected": expected,
        "split": "public",
        "group": None,
        "provenance": {
            "source": f"{DATASET} ({CONFIG})",
            "source_id": str(row["pubid"]),
            "license": "MIT",
            "exclude_reason": None,
        },
    }


def main() -> None:
    rows = fetch_rows(N_ROWS)
    print(f"[build_healthcare_dataset] fetched {len(rows)} rows")
    tasks = [to_task(r) for r in rows]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for t in tasks:
            fh.write(json.dumps(t, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"[build_healthcare_dataset] wrote {len(tasks)} tasks -> {OUT_PATH}")


if __name__ == "__main__":
    main()
