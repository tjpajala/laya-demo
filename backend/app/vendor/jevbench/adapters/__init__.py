"""Trimmed adapter registry: only the pieces this project vendors.

Upstream jevbench.adapters exports ~15 adapters; most need extra third-party
clients (openai, gradio_client, ...) this project never installs. We only
need the shared base helpers and the ready-made Laya adapter — Open-Jev's
adapter lives in app.adapters.open_jev_local instead, since it targets a
different codebase than upstream's own local_openjev adapter.
"""

from .base import DecisionResult, build_question, http_post_json
from .laya_local import LayaLocalAdapter

__all__ = ["DecisionResult", "build_question", "http_post_json", "LayaLocalAdapter"]
