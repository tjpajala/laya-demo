"""JevBench-compatible adapter for Zefan-Cai/Open-Jev (github.com/Zefan-Cai/Open-Jev).

Not to be confused with jevbench's own upstream `local_openjev` adapter,
which targets a *different*, unrelated project also named "Open-Jev"
(com-kotobalabs/open-jev-deberta-v3-large). This project's Open-Jev is
Qwen3.5-based, ships its own HTTP server (`jev.server`, started separately
by `OpenJevServerManager`) and a stdlib-only client (`jev.client.Client`).

Confirmed against Open-Jev's actual source (jev/client.py, jev/api.py,
jev/serving.py, read 2026-09-21): `Client().ask(state, questions)` returns
`{"answers": {qid: {...}}, ...}`, and per Open-Jev's own `format_response()`
every typed answer echoes the same "Jev shape" jevbench's laya_local adapter
already relies on: `{"type": "noul", "noul": p_yes}` or
`{"type": "choice"|"score", "probabilities": {label: p, ...}, ...}`. This
adapter mirrors laya_local.py's parsing for exactly that reason.
"""

from __future__ import annotations

import time

from ..vendor.jevbench.adapters.base import DecisionResult, build_question


class OpenJevLocalAdapter:
    name = "open_jev_local"
    cost_basis = "local_cpu_no_provider_tariff"

    def __init__(
        self,
        base_url: str,
        model: str = "open-jev",
        price_input_per_m=None,
        price_output_per_m=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.price_input_per_m = price_input_per_m
        self.price_output_per_m = price_output_per_m
        self._client = None

    def load(self):
        if self._client is None:
            from jev.client import Client

            self._client = Client(endpoint=f"{self.base_url}/v1/systemone")
        return self._client

    def build_request(self, task) -> dict:
        return {"state": task.state, "questions": {"decision": build_question(task)}}

    def run(self, task) -> DecisionResult:
        res = DecisionResult(adapter=self.name, ok=False, probs_source="native", model=self.model)
        body = self.build_request(task)
        res.request_body = body
        try:
            client = self.load()
        except Exception as e:  # noqa: BLE001 - a failed load is a failed attempt
            res.error = f"load failed: {type(e).__name__}: {str(e)[:250]}"
            return res
        t0 = time.perf_counter()
        try:
            out = client.ask(body["state"], body["questions"])
        except Exception as e:  # noqa: BLE001
            res.latency_s = time.perf_counter() - t0
            res.error = f"{type(e).__name__}: {str(e)[:300]}"
            return res
        res.latency_s = time.perf_counter() - t0
        res.raw = {
            "response": out,
            "runtime": {"device": "cpu", "probability_origin": "native-softmax"},
        }
        res.usage = dict((out or {}).get("usage") or {})
        res.model = (out or {}).get("model") or self.model
        ans = ((out or {}).get("answers") or {}).get("decision")
        try:
            if not isinstance(ans, dict) or ans.get("type") != task.question["type"]:
                raise ValueError("missing or mistyped answers.decision")
            if task.question["type"] == "noul":
                p = float(ans["noul"])
                if not (0.0 <= p <= 1.0):
                    raise ValueError(f"noul out of range: {p}")
                res.probs = {"yes": p, "no": 1.0 - p}
            else:
                probs = ans["probabilities"]
                if not isinstance(probs, dict):
                    raise ValueError("missing probabilities")
                res.probs = {str(k): float(v) for k, v in probs.items()}
        except (KeyError, TypeError, ValueError) as e:
            res.error = f"answer parse failed: {e}"
            return res
        res.ok = True
        return res

    def reserve_estimate(self, task) -> float:
        return 0.0
