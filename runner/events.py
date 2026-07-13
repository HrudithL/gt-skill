#!/usr/bin/env python3
"""UI event shapes emitted while a run streams (07-frontend-runner.md §6/§7).

`runner.orchestrate` calls an ``emit(event: dict)`` callback as a run
progresses; the web backend serializes those dicts onto the SSE stream and the
CLI logs them. Keeping the shapes here means the transcript renderer (frontend)
and the emitter (orchestrate) share one definition of the wire format.

Event ``type`` values and their payloads:

- ``run_started``  ``{run_id, spec}``
- ``stage``        ``{prompt, variant, repeat, index, total}``
- ``message``      ``{prompt, variant, repeat, msg}`` — one mapped transcript
  message (the readable dict from ``engine.message_to_dict``: assistant text /
  thinking / tool_use / tool_result / system / result)
- ``file``         ``{prompt, variant, repeat, path, kind}`` — a file appeared /
  changed in the run dir
- ``usage``        ``{input, output, cost_usd}`` — running cumulative tally
- ``run_finished`` ``{run_id, summary}``  /  ``run_error`` ``{run_id, error}``
"""

from __future__ import annotations

RUN_STARTED = "run_started"
STAGE = "stage"
MESSAGE = "message"
FILE = "file"
USAGE = "usage"
RUN_FINISHED = "run_finished"
RUN_ERROR = "run_error"


def event(type_: str, **data) -> dict:
    """Build one event dict ``{type, **data}``."""
    return {"type": type_, **data}


def run_started(run_id: str, spec: dict) -> dict:
    return event(RUN_STARTED, run_id=run_id, spec=spec)


def stage(prompt: str, variant: str, repeat: int | None, index: int, total: int) -> dict:
    return event(STAGE, prompt=prompt, variant=variant, repeat=repeat, index=index, total=total)


def message(prompt: str, variant: str, repeat: int | None, msg: dict) -> dict:
    return event(MESSAGE, prompt=prompt, variant=variant, repeat=repeat, msg=msg)


def file(prompt: str, variant: str, repeat: int | None, path: str, kind: str) -> dict:
    return event(FILE, prompt=prompt, variant=variant, repeat=repeat, path=path, kind=kind)


def usage(input_tokens: int, output_tokens: int, cost_usd: float) -> dict:
    return event(USAGE, input=input_tokens, output=output_tokens, cost_usd=cost_usd)


def run_finished(run_id: str, summary: dict) -> dict:
    return event(RUN_FINISHED, run_id=run_id, summary=summary)


def run_error(run_id: str, error: str) -> dict:
    return event(RUN_ERROR, run_id=run_id, error=error)


# --------------------------------------------------------------------------- #
# helpers for the running usage tally
# --------------------------------------------------------------------------- #
def message_usage(msg: dict) -> tuple[int, int, float]:
    """(input_tokens, output_tokens, cost_usd) contributed by one mapped message.

    Assistant messages carry a per-message ``usage`` dict; the final ``result``
    message carries ``total_cost_usd`` and cumulative ``usage``. Orchestrate uses
    the result's totals as authoritative and the assistant deltas for a live
    token counter between results. Missing fields read as 0.
    """
    role = msg.get("role")
    if role not in ("assistant", "result"):
        return 0, 0, 0.0
    u = msg.get("usage") or {}
    inp = int(u.get("input_tokens") or 0)
    out = int(u.get("output_tokens") or 0)
    cost = float(msg.get("total_cost_usd") or 0.0) if role == "result" else 0.0
    return inp, out, cost


def kind_for(path: str) -> str:
    """Classify a run-dir file path for the file-tree viewer (image/code/data/...)."""
    lower = path.lower()
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return "image"
    if lower.endswith((".py",)):
        return "code"
    if lower.endswith((".json",)):
        return "json"
    if lower.endswith((".md",)):
        return "markdown"
    if lower.endswith((".csv",)):
        return "data"
    return "text"
