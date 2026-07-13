#!/usr/bin/env python3
"""Starlette + uvicorn backend for the global runner — local-first control plane.

Imports the ``runner`` core directly (never shells out to a CLI), so the web app
and ``python run.py --flags`` share one behavior. Endpoints (07-frontend-runner.md
§6):

    GET  /api/skills                     list skills + file trees
    GET  /api/skills/{name}/file?path=   one skill file (text/bytes)
    GET  /api/prompts                    corpus prompts grouped by difficulty
    GET  /api/data                       available data/*.csv
    GET  /api/models                     model dropdown (label -> id)
    POST /api/plan                       dry-run a RunSpec -> planned dir tree
    POST /api/runs                       launch a run -> {run_id}
    GET  /api/runs                       history list (unified + legacy)
    GET  /api/runs/{id}                  run detail + file tree
    GET  /api/runs/{id}/file?path=       any file in a run dir (text/bytes)
    GET  /api/runs/{id}/events           SSE live event stream (buffered/replayable)
    /                                    the single-page app (web/static)

Concurrency: one run at a time (a non-blocking busy lock); each run's events are
buffered so a late/reconnecting browser replays cleanly. Each run executes in a
worker thread with its own event loop, so the sidecar-Chrome launch never blocks
uvicorn's loop.

Run it:  uvicorn web.server:app --port 8000   (or  python -m web.server)
"""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

import anyio
from dotenv import load_dotenv
from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from runner import discover, events, orchestrate, plan
from runner.engine import ROOT, _path_within
from runner.spec import RunSpec
from web import history

# Load .env at import so ANTHROPIC_API_KEY is present however the app is started
# (uvicorn web.server:app, python -m web.server, or the TestClient). Idempotent.
load_dotenv(ROOT / ".env")

STATIC_DIR = Path(__file__).parent / "static"

_TEXT_MEDIA = {
    "code": "text/x-python; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "markdown": "text/markdown; charset=utf-8",
    "data": "text/csv; charset=utf-8",
    "text": "text/plain; charset=utf-8",
}


# --------------------------------------------------------------------------- #
# run jobs — buffered events, one at a time, run in a worker thread
# --------------------------------------------------------------------------- #
class RunJob:
    """One launched run: a growing, replayable event buffer + done flag."""

    def __init__(self, run_id: str, spec: RunSpec) -> None:
        self.run_id = run_id
        self.spec = spec
        self.events: list[dict] = []
        self.done = False
        self._lock = threading.Lock()

    def emit(self, ev: dict) -> None:
        with self._lock:
            self.events.append(ev)
        if ev.get("type") in (events.RUN_FINISHED, events.RUN_ERROR):
            self.done = True

    def snapshot(self, since: int) -> tuple[list[dict], int]:
        with self._lock:
            return list(self.events[since:]), len(self.events)


class JobManager:
    """Launches runs (one at a time) in worker threads and keeps their buffers."""

    def __init__(self) -> None:
        self.jobs: dict[str, RunJob] = {}
        self._busy = threading.Lock()

    @property
    def busy(self) -> bool:
        return self._busy.locked()

    def launch(self, spec: RunSpec) -> str:
        spec.validate()
        if not self._busy.acquire(blocking=False):
            raise RuntimeError("a run is already in progress")
        try:
            run_dir = orchestrate.create_run_dir(spec)
        except Exception:
            self._busy.release()
            raise
        job = RunJob(run_dir.name, spec)
        self.jobs[run_dir.name] = job
        threading.Thread(
            target=self._drive, args=(job, spec, run_dir), daemon=True
        ).start()
        return run_dir.name

    def _drive(self, job: RunJob, spec: RunSpec, run_dir: Path) -> None:
        async def go() -> dict:
            return await orchestrate.run_spec(spec, run_dir, emit=job.emit)

        try:
            anyio.run(go)
        except Exception as e:  # run_spec catches its own; this is belt-and-braces
            job.emit(events.run_error(job.run_id, str(e)))
        finally:
            job.done = True
            self._busy.release()

    def get(self, run_id: str) -> RunJob | None:
        return self.jobs.get(run_id)


manager = JobManager()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _file_response(path: Path) -> Response:
    """Serve a file: images as-is (right content-type), text kinds as UTF-8 text."""
    kind = events.kind_for(path.name)
    if kind == "image":
        return FileResponse(path)
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return FileResponse(path)
    return PlainTextResponse(text, media_type=_TEXT_MEDIA.get(kind, _TEXT_MEDIA["text"]))


async def _spec_from_body(request: Request) -> RunSpec:
    body = await request.json()
    return RunSpec.from_dict(body)


# --------------------------------------------------------------------------- #
# catalogs
# --------------------------------------------------------------------------- #
async def skills(_request: Request) -> JSONResponse:
    return JSONResponse({"skills": discover.list_skills()})


async def skill_file(request: Request) -> Response:
    label = request.path_params["name"]
    rel = request.query_params.get("path", "")
    base = discover.skill_dir(label)
    if base is None or not base.is_dir():
        return JSONResponse({"error": "unknown skill"}, status_code=404)
    target = (base / rel).resolve()
    if not rel or not _path_within(target, base.resolve()) or not target.is_file():
        return JSONResponse({"error": "file not found"}, status_code=404)
    return _file_response(target)


async def prompts(_request: Request) -> JSONResponse:
    return JSONResponse({"grouped": discover.prompts_grouped()})


async def data(_request: Request) -> JSONResponse:
    return JSONResponse({"data": discover.list_data()})


async def models(_request: Request) -> JSONResponse:
    return JSONResponse({"models": discover.list_models()})


# --------------------------------------------------------------------------- #
# plan + launch + history
# --------------------------------------------------------------------------- #
async def plan_ep(request: Request) -> JSONResponse:
    try:
        spec = await _spec_from_body(request)
        return JSONResponse(plan.build_plan(spec))
    except (KeyError, ValueError, TypeError) as e:
        return JSONResponse({"error": f"bad spec: {e}"}, status_code=400)


async def runs_ep(request: Request) -> JSONResponse:
    if request.method == "POST":
        try:
            spec = await _spec_from_body(request)
        except (KeyError, ValueError, TypeError) as e:
            return JSONResponse({"error": f"bad spec: {e}"}, status_code=400)
        try:
            run_id = manager.launch(spec)
        except ValueError as e:  # spec.validate() failed
            return JSONResponse({"error": str(e)}, status_code=400)
        except RuntimeError as e:  # busy
            return JSONResponse({"error": str(e)}, status_code=409)
        return JSONResponse({"run_id": run_id})
    return JSONResponse({"runs": history.list_runs(), "busy": manager.busy})


async def run_detail_ep(request: Request) -> JSONResponse:
    detail = history.run_detail(request.path_params["run_id"])
    if detail is None:
        return JSONResponse({"error": "unknown run"}, status_code=404)
    return JSONResponse(detail)


async def run_file_ep(request: Request) -> Response:
    rel = request.query_params.get("path", "")
    target = history.resolve_file(request.path_params["run_id"], rel)
    if target is None:
        return JSONResponse({"error": "file not found"}, status_code=404)
    return _file_response(target)


async def run_events(request: Request) -> Response:
    run_id = request.path_params["run_id"]
    job = manager.get(run_id)
    if job is None:
        return JSONResponse({"error": "unknown or expired run"}, status_code=404)

    async def gen():
        sent = 0
        while True:
            batch, total = job.snapshot(sent)
            for ev in batch:
                yield {"event": ev["type"], "data": json.dumps(ev)}
            sent = total
            if job.done:
                # flush anything appended between the snapshot and the done check
                tail, total2 = job.snapshot(sent)
                for ev in tail:
                    yield {"event": ev["type"], "data": json.dumps(ev)}
                break
            await asyncio.sleep(0.25)

    return EventSourceResponse(gen())


# --------------------------------------------------------------------------- #
# app
# --------------------------------------------------------------------------- #
routes = [
    Route("/api/skills", skills),
    Route("/api/skills/{name}/file", skill_file),
    Route("/api/prompts", prompts),
    Route("/api/data", data),
    Route("/api/models", models),
    Route("/api/plan", plan_ep, methods=["POST"]),
    Route("/api/runs/{run_id}/events", run_events),
    Route("/api/runs/{run_id}/file", run_file_ep),
    Route("/api/runs/{run_id}", run_detail_ep),
    Route("/api/runs", runs_ep, methods=["GET", "POST"]),
    Mount("/", app=StaticFiles(directory=str(STATIC_DIR), html=True)),
]

app = Starlette(routes=routes)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
