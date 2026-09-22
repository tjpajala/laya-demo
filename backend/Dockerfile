# syntax=docker/dockerfile:1.7
#
# Two independent stages:
#   models  - fetches Laya + Qwen3.5-2B base + Open-Jev-2B weights. Depends
#             only on scripts/*, so editing app code never invalidates it and
#             never re-downloads multi-GB weights. See scripts/fetch_models.py.
#   backend - the actual FastAPI app; copies /models from the models stage.
#
# Both stages need network (pip installs, git clone, HF downloads) at BUILD
# time only. The running container sets HF_HUB_OFFLINE=1/TRANSFORMERS_OFFLINE=1
# and, per docker-compose.yml, sits on an `internal: true` network with no
# route out - it cannot reach the network even if something tried to.

FROM python:3.11-slim AS models
WORKDIR /build
RUN pip install --no-cache-dir "huggingface_hub>=0.24"
COPY scripts/fetch_models.py scripts/models_manifest.json ./
RUN --mount=type=cache,target=/root/.cache/huggingface,id=hf-dl-cache \
    python fetch_models.py --manifest models_manifest.json --dest /models

FROM python:3.11-slim AS backend
ENV HF_HOME=/models/hf_home \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    USE_TF=0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# Plain `pip install torch` resolves the default CUDA build, pulling in
# ~1.3GB of nvidia_* packages this CPU-only deployment never uses (and which
# make the build far more likely to hit a transient download timeout).
# Installing the CPU wheel first satisfies torch for everything below.
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-cache \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch>=2.8" \
    && pip install --no-cache-dir --default-timeout=120 -r requirements.txt

COPY --from=models /models /models
COPY app ./app

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
