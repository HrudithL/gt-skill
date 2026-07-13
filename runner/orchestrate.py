#!/usr/bin/env python3
"""The one run driver: RunSpec -> the unified run tree + convergence + summary.

This is what both ``python run.py --flags`` and ``POST /api/runs`` call, so the
file runner and the web app share one behavior. It folds the four old runners
into one flow (07-frontend-runner.md §4.1):

  - for each selected prompt, run ``repeats`` with-skill invocations (+ one
    baseline when enabled),
  - when ``repeats > 1``, compute that prompt's convergence report + contact
    sheet (old consistency_runner behavior),
  - across all prompts, compute the aggregate pass/fail + token/cost summary
    (old test_runner behavior).

It owns the sidecar Chrome for the whole run (one shared browser, exactly like
the old runners' ``main()``), threads the selected model id through
``GTSKILL_AGENT_MODEL``, and emits UI events (``runner.events``) as it goes.

Output layout (07-frontend-runner.md §4.2):

    runs/<ts>_<skill>_<slug-or-multi>/
      run.json                 # spec + resolved config + status + timings
      summary.json             # aggregate pass/fail + tokens/cost
      prompts/<name>/
        convergence.json       # only when repeats > 1
        contact_sheet.png      # only when repeats > 1
        baseline/              # only when baseline enabled
        repeat_1/ … repeat_N/
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from runner import convergence, events
from runner.engine import BASELINE_VARIANT, ROOT
from runner.engine import run as engine_run
from runner.plan import prompt_dir_name, run_dir_name
from runner.sidecar import sidecar_chrome
from runner.spec import MODELS, PromptRef, RunSpec

Emit = Callable[[dict], None]


def _noop(_event: dict) -> None:
    pass


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _resolve_data(data: str) -> Path:
    """Resolve a PromptRef data path (absolute, or repo-relative like data/x.csv)."""
    p = Path(data).expanduser()
    if p.is_absolute():
        return p
    return (ROOT / p).resolve()


def _config(spec: RunSpec) -> dict:
    """The resolved config block written into run.json / summary.json."""
    return {
        "skill": spec.skill,
        "variant": spec.variant(),
        "model": {"label": spec.model, "id": spec.model_id()},
        "repeats": spec.repeats,
        "baseline": spec.baseline_enabled(),
    }


def _metrics(run_dir: Path) -> dict:
    """Pass/fail + cost/tokens for one invocation dir (old test_runner logic)."""
    transcript_path = run_dir / "transcript.json"
    if not transcript_path.exists():
        return {"status": "fail", "error": "no transcript.json produced"}
    try:
        transcript = json.loads(transcript_path.read_text())
    except Exception as e:
        return {"status": "fail", "error": f"unreadable transcript: {e}"}

    result_msg = next((e for e in transcript if e.get("role") == "result"), None)
    if result_msg is None:
        return {"status": "fail", "error": "no result message in transcript"}

    has_png = (run_dir / "table.png").exists()
    has_py = (run_dir / "table.py").exists()
    return {
        "status": "pass" if (not result_msg.get("is_error") and has_png) else "fail",
        "is_error": result_msg.get("is_error", True),
        "has_table_png": has_png,
        "has_table_py": has_py,
        "num_turns": result_msg.get("num_turns"),
        "duration_ms": result_msg.get("duration_ms"),
        "total_cost_usd": result_msg.get("total_cost_usd"),
        "usage": result_msg.get("usage"),
    }


def _write_run_json(run_dir: Path, payload: dict) -> None:
    (run_dir / "run.json").write_text(json.dumps(payload, indent=2, default=str))


# --------------------------------------------------------------------------- #
# run-dir creation (the backend calls this first to learn the run_id)
# --------------------------------------------------------------------------- #
def create_run_dir(spec: RunSpec, *, ts: str | None = None, root: Path = ROOT) -> Path:
    """Create ``runs/<ts>_<skill>_<slug>/`` and write an initial run.json.

    Returns the run dir; its ``.name`` is the run_id. Split from ``run_spec`` so
    the web backend can return ``{run_id}`` immediately and stream events, then
    drive the run in the background.
    """
    spec.validate()
    ts = ts or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = root / "runs" / run_dir_name(spec, ts)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)
    _write_run_json(
        run_dir,
        {
            "run_id": run_dir.name,
            "spec": spec.to_dict(),
            "config": _config(spec),
            "status": "pending",
            "started_at": None,
            "finished_at": None,
            "wall_time_s": None,
            "error": None,
        },
    )
    return run_dir


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
async def run_spec(spec: RunSpec, run_dir: Path, *, emit: Emit = _noop) -> dict:
    """Drive ``spec`` to completion in ``run_dir``; return the summary dict.

    Owns the sidecar Chrome, threads the model id, writes every artifact, and
    emits ``run_started`` / ``stage`` / ``message`` / ``usage`` / ``file`` /
    ``run_finished`` (or ``run_error``) events. Individual invocation failures
    are caught and recorded (a failed run becomes a failing result + a missing
    contact-sheet panel) so the run always finishes and produces a summary.
    """
    spec.validate()
    variant = spec.variant()
    baseline = spec.baseline_enabled()
    prompts_dir = run_dir / "prompts"

    # Thread the selected model id to the agent (engine.run reads this env var),
    # matching the old runners' --model handling.
    os.environ["GTSKILL_AGENT_MODEL"] = spec.model_id()

    started = time.time()
    started_iso = datetime.now().isoformat(timespec="seconds")
    base_run_json = {
        "run_id": run_dir.name,
        "spec": spec.to_dict(),
        "config": _config(spec),
        "status": "running",
        "started_at": started_iso,
        "finished_at": None,
        "wall_time_s": None,
        "error": None,
    }
    _write_run_json(run_dir, base_run_json)

    emit(events.run_started(run_dir.name, spec.to_dict()))

    total = spec.invocation_count()
    idx = 0
    tally = {"input": 0, "output": 0, "cost": 0.0}
    results: list[dict] = []
    prompt_summaries: list[dict] = []

    def _make_cb(pname: str, var: str, rep: int | None, rdir: Path) -> Callable[[dict], None]:
        """Per-invocation observer: message + running usage + file-appeared events."""
        seen: dict[str, tuple[float, int]] = {}

        def cb(msg: dict) -> None:
            emit(events.message(pname, var, rep, msg))
            # Accumulate the run-wide token/cost tally at result messages (their
            # usage is the authoritative per-invocation total), then re-emit it.
            if msg.get("role") == "result":
                di, do, dc = events.message_usage(msg)
                tally["input"] += di
                tally["output"] += do
                tally["cost"] += dc
                emit(events.usage(tally["input"], tally["output"], round(tally["cost"], 6)))
            # Surface files as they appear/change in this invocation dir (the
            # intermediate table.png renders show up here as the model iterates).
            try:
                for entry in os.scandir(rdir):
                    if not entry.is_file():
                        continue
                    try:
                        st = entry.stat()
                    except OSError:
                        continue
                    sig = (st.st_mtime, st.st_size)
                    if seen.get(entry.name) != sig:
                        seen[entry.name] = sig
                        rel = f"{rdir.relative_to(run_dir).as_posix()}/{entry.name}"
                        emit(events.file(pname, var, rep, rel, events.kind_for(entry.name)))
            except OSError:
                pass

        return cb

    async def _one(rdir: Path, var: str, pname: str, rep: int | None, prompt_text: str, data_path: Path) -> dict:
        rdir.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        try:
            await engine_run(
                prompt_text, data_path, rdir, chrome.ws_url,
                skill_variant=var, on_message=_make_cb(pname, var, rep, rdir),
            )
            m = _metrics(rdir)
        except Exception as e:  # keep going; failed run -> failing result
            m = {"status": "fail", "error": str(e)}
        m["wall_time_s"] = round(time.time() - t0, 2)
        return m

    error: str | None = None
    try:
        with sidecar_chrome(run_dir) as chrome:
            for p in spec.prompts:
                pname = prompt_dir_name(p)
                pdir = prompts_dir / pname
                pdir.mkdir(parents=True, exist_ok=True)
                data_path = _resolve_data(p.data)

                baseline_dir: Path | None = None
                repeat_dirs: list[Path] = []

                if baseline:
                    idx += 1
                    baseline_dir = pdir / "baseline"
                    emit(events.stage(pname, BASELINE_VARIANT, None, idx, total))
                    m = await _one(baseline_dir, BASELINE_VARIANT, pname, None, p.prompt, data_path)
                    results.append({"name": pname, "kind": "baseline", "repeat": 0,
                                    "run_dir": str(baseline_dir.relative_to(run_dir)), **m})

                for r in range(1, spec.repeats + 1):
                    idx += 1
                    rdir = pdir / f"repeat_{r}"
                    repeat_dirs.append(rdir)
                    emit(events.stage(pname, variant, r, idx, total))
                    m = await _one(rdir, variant, pname, r, p.prompt, data_path)
                    results.append({"name": pname, "kind": "repeat", "repeat": r,
                                    "run_dir": str(rdir.relative_to(run_dir)), **m})

                # Per-prompt convergence report + contact sheet when repeats > 1.
                conv_overall = None
                if spec.repeats > 1:
                    conv_overall = _finalize_prompt(
                        pdir, p, spec, baseline_dir, repeat_dirs, emit, pname, variant
                    )
                prompt_summaries.append({"name": pname, "convergence_overall": conv_overall})
    except Exception as e:
        error = str(e)

    summary = _write_summary(run_dir, spec, results, prompt_summaries)

    finished = time.time()
    _write_run_json(
        run_dir,
        {
            **base_run_json,
            "status": "error" if error else "done",
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "wall_time_s": round(finished - started, 2),
            "error": error,
        },
    )

    if error:
        emit(events.run_error(run_dir.name, error))
    else:
        emit(events.run_finished(run_dir.name, summary))
    return summary


def _finalize_prompt(
    pdir: Path,
    pref: PromptRef,
    spec: RunSpec,
    baseline_dir: Path | None,
    repeat_dirs: list[Path],
    emit: Emit,
    pname: str,
    variant: str,
) -> float | None:
    """Write convergence.json + contact_sheet.png for one prompt (repeats > 1)."""
    panels: list[tuple[str, Path]] = []
    if baseline_dir is not None:
        panels.append(("baseline", baseline_dir / "table.png"))
    panels += [(f"repeat {i}", d / "table.png") for i, d in enumerate(repeat_dirs, 1)]
    sheet = pdir / "contact_sheet.png"
    convergence.build_contact_sheet(panels, sheet)
    emit(events.file(pname, variant, None, f"prompts/{pname}/contact_sheet.png", "image"))

    baseline_parsed = (
        {"run_dir": str(baseline_dir), **convergence.parse_table_dir(baseline_dir)}
        if baseline_dir is not None
        else {"run_dir": None, "status": "missing", "choices": None, "has_png": False}
    )
    with_skill = [
        {"repeat": i, "run_dir": str(d), **convergence.parse_table_dir(d)}
        for i, d in enumerate(repeat_dirs, 1)
    ]
    meta = {
        "prompt": pref.prompt,
        "data": pref.data,
        "variant": variant,
        "repeat": spec.repeats,
        "model": spec.model_id(),
    }
    report = convergence.build_report(meta, baseline_parsed, with_skill)
    (pdir / "convergence.json").write_text(json.dumps(report, indent=2, default=str))
    emit(events.file(pname, variant, None, f"prompts/{pname}/convergence.json", "json"))
    return report.get("overall_convergence")


def _write_summary(
    run_dir: Path, spec: RunSpec, results: list[dict], prompt_summaries: list[dict]
) -> dict:
    """Aggregate pass/fail + tokens/cost across all invocations; write summary.json."""
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") != "pass")
    total_cost = sum(r.get("total_cost_usd") or 0 for r in results)
    total_in = sum((r.get("usage") or {}).get("input_tokens", 0) for r in results)
    total_out = sum((r.get("usage") or {}).get("output_tokens", 0) for r in results)

    summary = {
        "run_id": run_dir.name,
        "config": _config(spec),
        "aggregate": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed / len(results) * 100:.1f}%" if results else "n/a",
            "total_cost_usd": round(total_cost, 4),
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
        },
        "prompts": prompt_summaries,
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary
