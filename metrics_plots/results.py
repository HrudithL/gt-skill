#!/usr/bin/env python3
"""Deterministic per-skill per-prompt run breakdown.

The overall ``SUMMARY.md`` gives one row per skill — mean accuracy, cost,
lift over baseline. This module produces the drill-down: one section per
skill, one table row per prompt, with every individual run's accuracy
displayed alongside the baseline and the per-prompt lift.

Byte-for-byte deterministic: same metrics.json input → same RESULTS.md
output. No timestamps, no re-scoring. Prompt order is fixed (easy →
medium → hard, alphabetical within a tier).

Wired into ``render_all`` and copied by ``publish`` so a real ``--evaluate``
run refreshes both ``SUMMARY.md`` and ``RESULTS.md`` in
``published-metrics/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .render import SKILLS


_DIFFICULTY_ORDER = ("easy", "medium", "hard")


def _fmt_pct(v: float | None) -> str:
    return "—" if v is None else f"{v:.1f}%"


def _fmt_lift(v: float | None) -> str:
    return "—" if v is None else f"{v:+.1f}"


def _repeat_variants(metrics: dict) -> list[str]:
    """Sorted ``repeat_N`` keys present anywhere in this metrics.json."""
    keys: set[str] = set()
    for entry in (metrics.get("prompts") or {}).values():
        for v in (entry.get("variants") or {}).keys():
            if v.startswith("repeat_"):
                keys.add(v)
    return sorted(keys, key=lambda k: int(k.split("_", 1)[1]))


def _ordered_prompts(metrics: dict) -> list[tuple[str, str]]:
    """Return ``[(prompt_id, difficulty), ...]`` in the fixed
    easy → medium → hard, alphabetical-within-tier order."""
    by_diff: dict[str, list[str]] = {d: [] for d in _DIFFICULTY_ORDER}
    for pid, entry in (metrics.get("prompts") or {}).items():
        d = entry.get("difficulty")
        if d in by_diff:
            by_diff[d].append(pid)
    out: list[tuple[str, str]] = []
    for d in _DIFFICULTY_ORDER:
        for pid in sorted(by_diff[d]):
            out.append((pid, d))
    return out


def _run_pct(entry: dict, variant: str) -> float | None:
    v = (entry.get("variants") or {}).get(variant) or {}
    s = v.get("score") or {}
    pct = s.get("pct")
    return float(pct) if pct is not None else None


def _load_metrics(root: Path, skill: str) -> dict[str, Any] | None:
    p = root / skill / "metrics.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _render_skill_section(skill: str, metrics: dict) -> list[str]:
    """One skill's ``## <skill>`` section: intro line + table."""
    repeats = _repeat_variants(metrics)
    if not repeats:
        return [f"## `{skill}`", "", "_No scored runs for this skill._", ""]

    prompts = _ordered_prompts(metrics)
    if not prompts:
        return [f"## `{skill}`", "", "_No prompts in this metrics tree._", ""]

    header_runs = " | ".join(f"Run {i + 1}" for i in range(len(repeats)))
    header_sep = " | ".join(":---:" for _ in repeats)

    lines: list[str] = []
    lines.append(f"## `{skill}`")
    lines.append("")
    lines.append(
        f"Per-prompt accuracy across {len(repeats)} skill run"
        f"{'s' if len(repeats) != 1 else ''} plus the unassisted baseline."
    )
    lines.append("")
    lines.append(f"| Prompt | Difficulty | {header_runs} | Mean | Baseline | Lift |")
    lines.append(f"| --- | --- | {header_sep} | ---: | ---: | ---: |")

    for pid, difficulty in prompts:
        entry = metrics["prompts"][pid]
        run_pcts = [_run_pct(entry, r) for r in repeats]
        run_cells = " | ".join(_fmt_pct(v) for v in run_pcts)

        valid_runs = [v for v in run_pcts if v is not None]
        mean_run = sum(valid_runs) / len(valid_runs) if valid_runs else None

        baseline_pct = _run_pct(entry, "baseline")
        lift = (
            mean_run - baseline_pct
            if (mean_run is not None and baseline_pct is not None)
            else None
        )
        lines.append(
            f"| `{pid}` | {difficulty} | {run_cells} | "
            f"{_fmt_pct(mean_run)} | {_fmt_pct(baseline_pct)} | {_fmt_lift(lift)} |"
        )
    lines.append("")
    return lines


def _render(per_skill: dict[str, dict[str, Any]]) -> str:
    """Assemble the full markdown from the per-skill metrics dicts."""
    lines: list[str] = []
    lines.append("# Per-prompt run results")
    lines.append("")
    lines.append(
        "_Regenerated deterministically by `metrics_plots.write_results()` from "
        "each skill's `metrics.json`. Do not edit by hand._"
    )
    lines.append("")
    lines.append(
        "This page drills down from the overall ranking in "
        "[`SUMMARY.md`](SUMMARY.md): every prompt, every individual skill run, "
        "the mean of those runs, the unassisted baseline, and the per-prompt "
        "lift over baseline. Runs that the harness could not score show as "
        "`—`."
    )
    lines.append("")

    if not per_skill:
        lines.append("_No scored skills found under the given root._")
        lines.append("")
        return "\n".join(lines)

    for skill in sorted(per_skill):
        lines.extend(_render_skill_section(skill, per_skill[skill]))
    return "\n".join(lines)


def write_results(root: Path) -> Path:
    """Write ``<root>/RESULTS.md`` from every ``<root>/<skill>/metrics.json``
    that exists. Returns the written path."""
    root = Path(root)
    per_skill: dict[str, dict[str, Any]] = {}
    for skill in SKILLS:
        m = _load_metrics(root, skill)
        if m is not None:
            per_skill[skill] = m
    text = _render(per_skill)
    out = root / "RESULTS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out
