# Laya vs Open-Jev on JevBench

Runs [`convaiinnovations/laya-typed-decisions`](https://huggingface.co/convaiinnovations/laya-typed-decisions)
and [Zefan-Cai/Open-Jev](https://github.com/Zefan-Cai/Open-Jev) (2B) on
[JevBench](https://github.com/fstandhartinger/jevbench)'s public 231-task
set, using JevBench's own (vendored, unmodified) scoring core so both models
are graded identically. A TS frontend launches and compares the two runs; a
Python backend does the actual inference and scoring. Everything runs in
Docker with no network access at runtime — model weights and packages are
fetched once at build time.

## Quick start

```bash
docker compose build   # needs network: downloads ~5-10GB of model weights, cached across rebuilds
docker compose up
```

Open http://localhost:5173. Pick dataset splits (`easy`/`original`/`hard`,
231 tasks total) and an optional task limit, then run each model. Once both
have a cached run for the same scope, a side-by-side comparison table
appears (accuracy, Brier, ECE, ordinal MAE, per-family accuracy, latency).

Runs are cached under a Docker volume, keyed by (model, splits, limit,
dataset hash) — rerunning the same configuration reuses the cached result
instantly. Use "Force rerun" or "Clear cache" in the UI (or `DELETE
/api/runs/{slug}`) to make it run again.

## Why two different codebases had to be glued together

JevBench (`fstandhartinger/jevbench`) already ships a full scoring harness
— dataset, adapters, Brier/ECE/argmax scoring — and even ships a ready-made
adapter for Laya (`laya_local`, vendored unmodified in
`backend/app/vendor/jevbench/`). It does *not* ship one for the Open-Jev
repo you get from the link above: JevBench's built-in `local_openjev`
adapter targets an unrelated, similarly-named project
(`com-kotobalabs/open-jev-deberta-v3-large`). Zefan-Cai/Open-Jev is a
separate, Qwen3.5-based project with its own HTTP server (`jev.server`) and
client (`jev.client.Client`). `backend/app/adapters/open_jev_local.py` is a
small adapter we wrote for it, built to the exact response shape confirmed
by reading Open-Jev's own source (`jev/api.py`'s `format_response`) —
mirroring how the vendored `laya_local` adapter already parses the same
"Jev shape" answers. See `backend/app/vendor/jevbench/VENDORED.md` for
exactly what was vendored and why.

**Caveat:** that adapter's response parsing was verified by reading
Open-Jev's source, not by running it end to end (that needs the actual
multi-GB model weights). If it needs a small fix once you run a real job,
`backend/app/adapters/open_jev_local.py` is the only place to look — the
JevBench scoring core itself is untouched upstream code.

## Architecture

```
backend/            FastAPI app, orchestrates everything
  app/vendor/jevbench/   unmodified vendor copy of JevBench's scoring core
  app/data/jevbench/     the public 231-task dataset (easy/original/hard)
  app/adapters/           new Open-Jev adapter + jev.server process manager
  app/jobs.py             background job runner + in-memory status
  app/cache.py             on-disk result cache, keyed by a deterministic slug
  scripts/fetch_models.py  build-time-only model downloader (see below)
frontend/            Vite + React + TS SPA, served by nginx in production
docker-compose.yml   orchestrates both services (see offline notes below)
```

Backend REST API: `GET /api/datasets`, `POST /api/runs`, `GET
/api/runs/{slug}`, `DELETE /api/runs/{slug}`, `GET /api/comparison`.

### Offline model weights without re-downloading on every build

`backend/Dockerfile` has a dedicated `models` build stage that depends only
on `scripts/fetch_models.py` + `scripts/models_manifest.json` — never on
app code — so editing the backend or frontend never invalidates it or
re-downloads anything. It also uses a BuildKit cache mount
(`--mount=type=cache,target=/root/.cache/huggingface`) as a second line of
defense, and `fetch_models.py` itself skips the network entirely once the
pinned revision is already on disk. The only thing that triggers a new
download is bumping a revision in `models_manifest.json`. Requires
BuildKit, which `docker compose build` uses by default on any reasonably
current Docker install.

At runtime, `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` make the
libraries fail fast instead of hanging if something isn't cached — this is
what actually enforces "no web access" for inference, not network
topology. (An earlier version of this compose file also marked the shared
network `internal: true` for defense in depth, but on Docker Desktop that
turned out to silently block the frontend's published host port too — so
it was dropped in favor of the env-var enforcement alone.)

### Why CPU / 2B-only / a subset by default

Open-Jev's trained checkpoints are only documented running on CUDA; this
setup targets CPU-only hosts, so it uses the smaller 2B checkpoint and
defaults the frontend's dataset picker to the 48-task `easy` split rather
than the full 231, since CPU inference on a 2B model is meaningfully
slower than the GPU numbers in either project's own published benchmarks.
All of this is just config: bump `models_manifest.json` to `Open-Jev-9B`
and `OPEN_JEV_DEVICE=cuda:0` (docker-compose environment) if you have a
GPU, or select more splits in the UI.

## Troubleshooting

**A build-time download fails or a pinned revision is stale.** Model
revisions are pinned in `backend/scripts/models_manifest.json`, the
Open-Jev package commit in `backend/requirements.txt`. Check the linked
repos for the current commit/revision and update the pin.

**A job fails with a network error at runtime despite offline env vars.**
Something is requesting a Hugging Face repo/revision not in
`models_manifest.json` — add it and rebuild.
