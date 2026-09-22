"""Builds a ready-to-run adapter instance for a given model name."""

from __future__ import annotations

from . import config
from .adapters.open_jev_local import OpenJevLocalAdapter
from .adapters.open_jev_process import OpenJevServerManager
from .vendor.jevbench.adapters.laya_local import LayaLocalAdapter

_open_jev_server = OpenJevServerManager(
    checkpoint_path=str(config.OPEN_JEV_CHECKPOINT_DIR),
    host=config.OPEN_JEV_HOST,
    port=config.OPEN_JEV_PORT,
    device=config.OPEN_JEV_DEVICE,
)


def build_adapter(model: str):
    if model == "laya":
        adapter = LayaLocalAdapter(endpoint=config.LAYA_MODEL_ID)
        adapter.load()  # warm the model before the clock starts, like jevbench's own GPU entrants
        return adapter
    if model == "open_jev":
        _open_jev_server.ensure_running()
        adapter = OpenJevLocalAdapter(base_url=_open_jev_server.base_url)
        adapter.load()
        return adapter
    raise ValueError(f"unknown model {model!r}")
