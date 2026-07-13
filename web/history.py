#!/usr/bin/env python3
"""Tolerant run-history reader — the new unified layout AND the legacy ones.

The History tab must keep every past run browsable, so this reader classifies a
run directory by which marker files it has and extracts what it can, never
crashing on an odd directory (07-frontend-runner.md §4.2 / §5.2):

- **unified**     ``runs/<ts>_<skill>_<slug>/``   — has ``run.json`` (+ summary.json,
  prompts/<name>/{baseline,repeat_N,convergence.json,contact_sheet.png})
- **consistency** ``test-runs/<ts>_<slug>/``       — has ``consistency_report.json``
  (+ baseline/, with_skill/repeat_N/, contact_sheet.png)
- **sweep**       ``test-runs/<ts>/``               — has ``summary.json`` (old test_runner)
- **single**      ``runs/<ts>/``                    — bare table.py/table.png/transcript.json

``runs/`` is gitignored, so history is local-only; nothing here assumes a run is
in git.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from runner.engine import ROOT, _path_within
from runner.plan import RUN_TYPES

RUNS_DIR = ROOT / "runs"
TESTRUNS_DIR = ROOT / "test-runs"

# Dir-name prefix timestamp, e.g. 20260712_033543.
_TS_RE = re.compile(r"^(\d{8}_\d{6})")
# Entries never shown in a run's file tree (noise / already-cleaned).
_TREE_SKIP = {"__pycache__", ".DS_Store", ".chrome-profile"}


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# transcript-derived metrics — the source of truth for cost/model/turns when a
# report/summary omits them (old consistency reports store no cost; single runs
# have no summary at all). Every layout can therefore show a standardized cost.
# --------------------------------------------------------------------------- #
def _result_entry(transcript: Path) -> dict:
    """The final ``result`` message of a transcript.json (cost/turns/duration)."""
    data = _read_json(transcript)
    if not isinstance(data, list):
        return {}
    for e in reversed(data):
        if isinstance(e, dict) and e.get("role") == "result":
            return e
    return {}


def _model_from_transcript(transcript: Path) -> str | None:
    """The model id from a transcript's system/init banner, if present."""
    data = _read_json(transcript)
    if not isinstance(data, list):
        return None
    for e in data:
        if isinstance(e, dict) and e.get("role") == "system" and e.get("subtype") == "init":
            return (e.get("data") or {}).get("model")
    return None


def _sum_cost(transcripts: list[Path]) -> float | None:
    """Total cost across a set of transcripts, or None if none report a cost."""
    costs = [_result_entry(t).get("total_cost_usd") for t in transcripts]
    costs = [c for c in costs if isinstance(c, (int, float))]
    return round(sum(costs), 4) if costs else None


def _rel(base: Path, target) -> str | None:
    """``target`` as a POSIX path relative to the run dir, or None if outside it."""
    try:
        return (Path(target).resolve().relative_to(base.resolve())).as_posix()
    except (ValueError, OSError):
        return None


def _iteration(base: Path, idir: Path, label: str, extra: dict | None = None) -> dict:
    """One invocation (baseline / repeat_N / sweep test): its dir + standardized
    per-invocation metrics pulled from its transcript, so the UI can list and
    drill into each without hunting through the file tree."""
    res = _result_entry(idir / "transcript.json")
    it: dict = {
        "label": label,
        "dir": _rel(base, idir),
        "cost_usd": res.get("total_cost_usd"),
        "num_turns": res.get("num_turns"),
        "duration_ms": res.get("duration_ms"),
        "status": ("error" if res.get("is_error") else ("ok" if res else None)),
        "has_png": (idir / "table.png").is_file(),
        "has_py": (idir / "table.py").is_file(),
        "has_transcript": (idir / "transcript.json").is_file(),
    }
    if extra:
        it.update({k: v for k, v in extra.items() if v is not None})
    return it


def _timestamp(name: str, fallback: Path) -> str:
    m = _TS_RE.match(name)
    if m:
        return m.group(1)
    try:
        return str(int(fallback.stat().st_mtime))
    except OSError:
        return "0"


# --------------------------------------------------------------------------- #
# classification + per-layout summary
# --------------------------------------------------------------------------- #
def _classify(d: Path) -> str:
    if (d / "run.json").is_file():
        return "unified"
    if (d / "consistency_report.json").is_file():
        return "consistency"
    if (d / "summary.json").is_file():
        return "sweep"
    if (d / "table.py").is_file() or (d / "transcript.json").is_file():
        return "single"
    return "unknown"


def _single_status(d: Path) -> str:
    """pass/fail for a bare single-run dir (old run.py output has no summary)."""
    tp = d / "transcript.json"
    if not tp.exists():
        return "unknown"
    data = _read_json(tp)
    if not isinstance(data, list):
        return "unknown"
    result = next((e for e in data if isinstance(e, dict) and e.get("role") == "result"), None)
    if result is None:
        return "unknown"
    ok = (not result.get("is_error")) and (d / "table.png").exists()
    return "pass" if ok else "fail"


def _summarize(d: Path, layout: str) -> dict:
    """A compact history-list item for one run dir (best-effort per layout)."""
    # Top-level root (runs vs test-runs) regardless of nesting depth, plus the
    # run type from the parent dir when it's a unified runs/<type>/ run.
    if RUNS_DIR == d.parent or RUNS_DIR in d.parents:
        root_name = "runs"
    elif TESTRUNS_DIR == d.parent or TESTRUNS_DIR in d.parents:
        root_name = "test-runs"
    else:
        root_name = d.parent.name
    run_type_val = d.parent.name if d.parent.name in RUN_TYPES else None
    item: dict = {
        "id": d.name,
        "layout": layout,
        "root": root_name,
        "type": run_type_val,
        "timestamp": _timestamp(d.name, d),
        "skill": None,
        "variant": None,
        "model": None,
        "prompts": [],
        "repeats": None,
        "baseline": None,
        "status": None,
        "pass_rate": None,
        "cost_usd": None,
        "convergence": None,
    }

    if layout == "unified":
        run = _read_json(d / "run.json") or {}
        summ = _read_json(d / "summary.json") or {}
        cfg = run.get("config") or summ.get("config") or {}
        model = cfg.get("model") or {}
        item.update(
            skill=cfg.get("skill"),
            variant=cfg.get("variant"),
            model=model.get("label") if isinstance(model, dict) else model,
            repeats=cfg.get("repeats"),
            baseline=cfg.get("baseline"),
            status=run.get("status"),
            prompts=[p.get("name") for p in (summ.get("prompts") or [])]
            or [p.get("name") for p in (run.get("spec", {}).get("prompts") or [])],
        )
        agg = summ.get("aggregate") or {}
        item["pass_rate"] = agg.get("pass_rate")
        item["cost_usd"] = agg.get("total_cost_usd")
        convs = [p.get("convergence_overall") for p in (summ.get("prompts") or [])
                 if p.get("convergence_overall") is not None]
        item["convergence"] = round(sum(convs) / len(convs), 3) if convs else None

    elif layout == "consistency":
        rep = _read_json(d / "consistency_report.json") or {}
        # Cost/model aren't stored in the report — derive them from the per-repeat
        # (+ baseline) transcripts so every convergence run shows a real cost.
        tps = sorted((d / "with_skill").glob("repeat_*/transcript.json"))
        if (d / "baseline" / "transcript.json").is_file():
            tps.append(d / "baseline" / "transcript.json")
        model = rep.get("model") or (_model_from_transcript(tps[0]) if tps else None)
        item.update(
            skill=rep.get("skill"),
            variant=rep.get("variant"),
            model=model,
            repeats=rep.get("repeat"),
            baseline=True,
            prompts=[rep.get("prompt", "")[:60]] if rep.get("prompt") else [],
            convergence=rep.get("overall_convergence"),
            cost_usd=_sum_cost(tps),
            status="done",
        )

    elif layout == "sweep":
        summ = _read_json(d / "summary.json") or {}
        cfg = summ.get("config") or {}
        agg = summ.get("aggregate") or {}
        names = []
        first_dir = None
        for r in summ.get("results", []):
            n = r.get("name")
            if n and n not in names:
                names.append(n)
            if first_dir is None and r.get("run_dir"):
                first_dir = Path(r["run_dir"])
        # Old sweeps store model=None in config — recover it from a result transcript.
        model = cfg.get("model")
        if not model and first_dir is not None:
            model = _model_from_transcript(first_dir / "transcript.json")
        item.update(
            variant=cfg.get("variant"),
            model=model,
            repeats=cfg.get("repeat"),
            prompts=names,
            pass_rate=agg.get("pass_rate"),
            cost_usd=agg.get("total_cost_usd"),
            status="done",
        )

    elif layout == "single":
        res = _result_entry(d / "transcript.json")
        item.update(
            status=_single_status(d),
            repeats=1,
            model=_model_from_transcript(d / "transcript.json"),
            cost_usd=res.get("total_cost_usd"),
        )

    return item


def _run_dirs() -> list[Path]:
    """Every run directory across the unified runs/<type>/ layout and legacy dirs.

    - ``runs/<type>/<run>``  — the unified layout (type: single|convergence|sweep)
    - ``runs/<run>``         — legacy flat single runs (before the type split)
    - ``test-runs/<run>``    — legacy consistency / sweep from the retired runners

    So all current runs live under one ``runs/`` root organized by type, while
    every past run (wherever it was written) stays browsable.
    """
    dirs: list[Path] = []
    if RUNS_DIR.is_dir():
        for child in RUNS_DIR.iterdir():
            if not child.is_dir():
                continue
            if child.name in RUN_TYPES:  # a type container: descend one level
                dirs += [d for d in child.iterdir() if d.is_dir()]
            else:  # a legacy flat run dir written before the type split
                dirs.append(child)
    if TESTRUNS_DIR.is_dir():
        dirs += [d for d in TESTRUNS_DIR.iterdir() if d.is_dir()]
    return dirs


def list_runs() -> list[dict]:
    """Every past run (unified runs/<type>/ + legacy runs/ + test-runs/), newest first."""
    items: list[dict] = []
    for d in _run_dirs():
        layout = _classify(d)
        if layout == "unknown":
            continue
        items.append(_summarize(d, layout))
    items.sort(key=lambda it: it["timestamp"], reverse=True)
    return items


# --------------------------------------------------------------------------- #
# detail + file access
# --------------------------------------------------------------------------- #
def _find_run(run_id: str) -> Path | None:
    """Resolve a run id (dir name) to its dir under runs/ or test-runs/.

    A run id is a plain child directory name; reject anything with a path
    separator or a dot-segment (e.g. an encoded ``..``) so it cannot escape
    runs/ / test-runs/ and expose arbitrary repo files. The parent check pins
    the match to a direct child.
    """
    if not run_id or run_id in (".", "..") or "/" in run_id or "\\" in run_id or "\x00" in run_id:
        return None
    # Search the unified type subdirs first, then the legacy flat runs/ and
    # test-runs/. A run id is a timestamped leaf, unique across these, so the
    # first direct-child match is the run.
    bases = [RUNS_DIR / t for t in RUN_TYPES] + [RUNS_DIR, TESTRUNS_DIR]
    for base in bases:
        if base == RUNS_DIR and run_id in RUN_TYPES:
            continue  # a type container, not a run
        cand = base / run_id
        if cand.is_dir() and cand.resolve().parent == base.resolve():
            return cand
    return None


def _run_tree(root: Path, rel: Path | None = None) -> list[dict]:
    """Nested listing of a run dir. Symlinks (data snapshot, .claude link,
    helper links) show as leaves and are not followed, so the mounted skill
    under .claude-<variant>/ is browsable without cycles. Noise is skipped."""
    base = root if rel is None else root / rel
    out: list[dict] = []
    try:
        children = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return out
    for child in children:
        if child.name in _TREE_SKIP:
            continue
        child_rel = child.name if rel is None else f"{rel.as_posix()}/{child.name}"
        if child.is_symlink():
            out.append({"name": child.name, "type": "link", "path": child_rel})
        elif child.is_dir():
            out.append({"name": child.name, "type": "dir", "path": child_rel,
                        "children": _run_tree(root, Path(child_rel))})
        else:
            out.append({"name": child.name, "type": "file", "path": child_rel})
    return out


def _iterations(d: Path, layout: str) -> list[dict]:
    """Normalized, grouped invocations for the detail view's iteration selector.

    Returns ``[{prompt, items:[iteration,...]}]`` so the UI can offer a dropdown
    of the specific test / repeat to inspect (sweep tests, convergence repeats,
    the baseline control) instead of forcing the user to hunt in the file tree.
    """
    groups: list[dict] = []

    if layout == "unified":
        pdir = d / "prompts"
        if pdir.is_dir():
            for pd in sorted(p for p in pdir.iterdir() if p.is_dir()):
                items = []
                if (pd / "baseline").is_dir():
                    items.append(_iteration(d, pd / "baseline", "baseline"))
                for rp in sorted(pd.glob("repeat_*")):
                    items.append(_iteration(d, rp, rp.name.replace("repeat_", "repeat ")))
                groups.append({"prompt": pd.name, "items": items})

    elif layout == "consistency":
        rep = _read_json(d / "consistency_report.json") or {}
        choices_by_repeat = {w.get("repeat"): w.get("choices") for w in (rep.get("with_skill") or [])}
        items = []
        if (d / "baseline").is_dir():
            items.append(_iteration(d, d / "baseline", "baseline",
                                    {"choices": (rep.get("baseline") or {}).get("choices")}))
        ws = d / "with_skill"
        if ws.is_dir():
            for rp in sorted(ws.glob("repeat_*")):
                n = int(rp.name.split("_")[-1]) if rp.name.split("_")[-1].isdigit() else None
                items.append(_iteration(d, rp, rp.name.replace("repeat_", "repeat "),
                                        {"choices": choices_by_repeat.get(n)}))
        groups.append({"prompt": (rep.get("prompt") or "")[:80] or None, "items": items})

    elif layout == "sweep":
        summ = _read_json(d / "summary.json") or {}
        items = []
        for r in summ.get("results", []):
            rd = r.get("run_dir")
            idir = Path(rd) if rd else (d / (r.get("name") or ""))
            if not idir.is_dir():
                continue
            items.append(_iteration(d, idir, r.get("name") or idir.name, {
                "status": r.get("status"),
                "cost_usd": r.get("total_cost_usd"),
                "num_turns": r.get("num_turns"),
                "duration_ms": r.get("duration_ms"),
                "difficulty": r.get("difficulty"),
            }))
        groups.append({"prompt": None, "items": items})

    elif layout == "single":
        groups.append({"prompt": None, "items": [_iteration(d, d, "run")]})

    return [g for g in groups if g["items"]]


def run_detail(run_id: str) -> dict | None:
    """Full detail for one run: summary + parsed metadata + file tree."""
    d = _find_run(run_id)
    if d is None:
        return None
    layout = _classify(d)
    detail = {
        "id": run_id,
        "layout": layout,
        "summary": _summarize(d, layout),
        "run": _read_json(d / "run.json"),
        "summary_json": _read_json(d / "summary.json"),
        "consistency_report": _read_json(d / "consistency_report.json"),
        "tree": _run_tree(d),
        "iterations": _iterations(d, layout),
        # per-prompt convergence reports (unified layout: prompts/<n>/convergence.json)
        "convergence": {},
    }
    prompts_dir = d / "prompts"
    if prompts_dir.is_dir():
        for pd in sorted(prompts_dir.iterdir()):
            conv = _read_json(pd / "convergence.json")
            if conv is not None:
                detail["convergence"][pd.name] = conv
    return detail


def resolve_file(run_id: str, rel: str) -> Path | None:
    """Resolve ``rel`` to a real file inside the run dir, guarding traversal.

    Requires the fully *resolved* target to stay inside the run dir. A run dir
    holds untrusted content — the agent can create arbitrary symlinks in its
    working directory, and the data snapshot is itself a symlink out to
    ``data/`` — so a symlink whose target escapes the run dir is rejected rather
    than followed (those show as non-clickable ``link`` leaves in the tree).
    """
    d = _find_run(run_id)
    if d is None or not rel:
        return None
    target = (d / rel).resolve()
    if not _path_within(target, d.resolve()) or not target.is_file():
        return None
    return target
