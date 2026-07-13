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
    item: dict = {
        "id": d.name,
        "layout": layout,
        "root": d.parent.name,  # "runs" | "test-runs"
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
        item.update(
            variant=rep.get("variant"),
            model=rep.get("model"),
            repeats=rep.get("repeat"),
            baseline=True,
            prompts=[rep.get("prompt", "")[:60]] if rep.get("prompt") else [],
            convergence=rep.get("overall_convergence"),
            status="done",
        )

    elif layout == "sweep":
        summ = _read_json(d / "summary.json") or {}
        cfg = summ.get("config") or {}
        agg = summ.get("aggregate") or {}
        names = []
        for r in summ.get("results", []):
            n = r.get("name")
            if n and n not in names:
                names.append(n)
        item.update(
            variant=cfg.get("variant"),
            model=cfg.get("model"),
            repeats=cfg.get("repeat"),
            prompts=names,
            pass_rate=agg.get("pass_rate"),
            cost_usd=agg.get("total_cost_usd"),
            status="done",
        )

    elif layout == "single":
        item.update(status=_single_status(d), repeats=1)

    return item


def list_runs() -> list[dict]:
    """Every past run across runs/ and test-runs/, newest first."""
    items: list[dict] = []
    for base in (RUNS_DIR, TESTRUNS_DIR):
        if not base.is_dir():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
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
    """Resolve a run id (dir name) to its dir under runs/ or test-runs/."""
    for base in (RUNS_DIR, TESTRUNS_DIR):
        cand = base / run_id
        if cand.is_dir():
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
    """Resolve ``rel`` to a real file inside the run dir, guarding traversal."""
    d = _find_run(run_id)
    if d is None:
        return None
    target = (d / rel).resolve()
    # Lexical containment against the run dir; symlinked data/.claude targets
    # inside the run dir are fine. Reject escapes.
    if not _path_within(target, d.resolve()):
        # A run-dir symlink (e.g. the data snapshot) may resolve outside the run
        # dir; allow it only when the *pre-resolution* path stays within.
        lexical = (d / rel)
        if not _path_within(lexical, d):
            return None
        target = lexical
    if not target.is_file():
        return None
    return target
