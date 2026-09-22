# Vendored from jevbench

This directory is a trimmed vendor copy of the scoring core of
[fstandhartinger/jevbench](https://github.com/fstandhartinger/jevbench)
(MIT licensed, see `LICENSE`), pinned to commit
`f8ce71361165846101d02ebc83ad44e47ae44fc3` (the commit JevBench's own public
report also pins).

Included, unmodified:
- `tasks.py`, `budget.py`, `scoring.py`, `metrics.py`, `runner.py`,
  `summarize.py`, `__init__.py`
- `adapters/base.py`, `adapters/laya_local.py`

Intentionally **not** vendored: `cli.py` and every adapter other than
`laya_local` (e.g. `openai_compat`, `gradio_space`, `typesafe`, ...). Those
pull in extra third-party clients (OpenAI, Gradio, etc.) this project never
uses. Our backend drives `Runner` directly in-process instead of going
through `jevbench.cli`, and supplies its own adapter for Zefan-Cai's
Open-Jev at `backend/app/adapters/open_jev_local.py` (JevBench's own
`local_openjev` adapter targets a *different*, unrelated project also named
"Open-Jev" — see the top-level README for why).

Dataset files under `backend/app/data/jevbench/` (`easy.jsonl`,
`original.jsonl`, `hard.jsonl`, `manifest.json`) are the untouched public
JevBench v1.2 task set (231 tasks total) from the same commit.
