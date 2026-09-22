# Laya vs Open-Jev on JevBench

Runs two typed-decision models —
[Laya Typed-Decisions](https://huggingface.co/convaiinnovations/laya-typed-decisions)
and [Open-Jev 2B](https://github.com/Zefan-Cai/Open-Jev) — against
[JevBench](https://github.com/fstandhartinger/jevbench)'s scoring harness
plus a PubMedQA healthcare dataset, and compares the results side by side.
A Python backend runs the models and scores them; a TS frontend launches
jobs and shows the comparison. Everything runs in Docker.

## Quick start

```bash
docker compose build   # needs network: downloads ~5-10GB of model weights, cached across rebuilds
docker compose up
```

Open http://localhost:5173. Pick one or more datasets (JevBench
easy/original/hard, or PubMedQA healthcare) and an optional per-dataset
task limit, then run each model. Once both have results for the same
datasets, a comparison table appears (accuracy, Brier, ECE, ordinal MAE,
per-family and per-dataset breakdowns, latency).

Each (model, dataset, limit) combination is cached independently in a
Docker volume — rerunning the same configuration reuses the cached result
instantly, and adding a new dataset to an existing selection only runs
that dataset, not the ones already cached. Use "Force rerun" or "Clear
cache" in the UI to make something run again.

## Architecture

```
backend/    FastAPI app - orchestrates jobs, scoring, caching
frontend/   Vite + React + TS SPA, served by nginx in production
docker-compose.yml
```

Model weights are downloaded once at `docker compose build` time and
cached across rebuilds; the running containers have no network access -
`HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` make everything resolve from
the local cache baked into the image.

## Why CPU / 2B-only by default

Open-Jev's trained checkpoints are only documented running on CUDA; this
setup targets CPU-only hosts, so it uses the smaller 2B checkpoint. Bump
`models_manifest.json` to `Open-Jev-9B` and set `OPEN_JEV_DEVICE=cuda:0`
(docker-compose environment) if you have a GPU.

## Troubleshooting

**A build-time download fails or a pinned revision is stale.** Model
revisions are pinned in `backend/scripts/models_manifest.json`, the
Open-Jev package commit in `backend/requirements.txt`. Check the linked
repos for the current commit/revision and update the pin.

**A job fails with a network error at runtime despite offline env vars.**
Something is requesting a Hugging Face repo/revision not in
`models_manifest.json` — add it and rebuild.
