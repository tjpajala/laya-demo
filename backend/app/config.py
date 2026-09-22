"""Paths and settings, all overridable via environment variables."""

from __future__ import annotations

import os
from pathlib import Path

MODELS_DIR = Path(os.environ.get("MODELS_DIR", "/models"))
CACHE_DIR = Path(os.environ.get("APP_CACHE_DIR", "/app/cache"))
DATA_DIR = Path(__file__).parent / "data" / "jevbench"

LAYA_MODEL_ID = os.environ.get("LAYA_MODEL_ID", "convaiinnovations/laya-typed-decisions")

OPEN_JEV_CHECKPOINT_DIR = Path(
    os.environ.get(
        "OPEN_JEV_CHECKPOINT_DIR",
        str(MODELS_DIR / "open-jev-2b" / "package" / "checkpoint"),
    )
)
OPEN_JEV_HOST = os.environ.get("OPEN_JEV_HOST", "127.0.0.1")
OPEN_JEV_PORT = int(os.environ.get("OPEN_JEV_PORT", "8791"))
OPEN_JEV_DEVICE = os.environ.get("OPEN_JEV_DEVICE", "cpu")

LEDGER_CAP_USD = float(os.environ.get("LEDGER_CAP_USD", "1000000"))
