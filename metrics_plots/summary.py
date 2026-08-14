#!/usr/bin/env python3
"""Deterministic per-skill ranking summary for an eval-results tree.

Reads every ``<root>/<skill>/metrics.json`` present, computes per-skill mean
scores (with-skill and baseline), mean lift, and mean cost per invocation,
and writes ``<root>/SUMMARY.md`` — a short markdown with one table, a
one-line-per-skill "at a glance" section, and a three-line "leaders"
callout naming the winner on each axis (highest score, highest lift over
baseline, lowest cost per invocation).

Byte-for-byte deterministic: same metrics.json → same SUMMARY.md. No
timestamps, no run IDs. Ties in the leader lookup break on skill name in
alphabetical order — which is stable across runs of the same data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .render import SKILLS


def _iter_variants(metrics: dict) -> list[tuple[str, str, dict]]:
    """Yield ``(prompt_id, variant, variant_dict)`` for every variant that
    actually has data in this skill's metrics."""
    out: list[tuple[str, str, dict]] = []
    for prompt_id, entry in (metrics.get("prompts") or {}).items():
        for variant, v in (entry.get("variants") or {}).items():
            if v:
                out.append((prompt_id, variant, v))
    return out


def _mean(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def compute_skill_stats(metrics: dict) -> dict[str, Any]:
    """Aggregate one skill's metrics into a small stats dict."""
    ws_scores: list[float] = []
    bl_scores: list[float] = []
    ws_costs: list[float] = []
    bl_costs: list[float] = []
    for _pid, variant, v in _iter_variants(metrics):
        score_pct = None
        if v.get("score") and v["score"].get("pct") is not None:
            score_pct = v["score"]["pct"]
        cost = None
        if v.get("cost_tokens") and v["cost_tokens"].get("cost_usd") is not None:
            cost = v["cost_tokens"]["cost_usd"]
        if variant.startswith("repeat_"):
            if score_pct is not None:
                ws_scores.append(score_pct)
            if cost is not None:
                ws_costs.append(cost)
        elif variant == "baseline":
            if score_pct is not None:
                bl_scores.append(score_pct)
            if cost is not None:
                bl_costs.append(cost)

    ws_mean = _mean(ws_scores)
    bl_mean = _mean(bl_scores)
    lift = ws_mean - bl_mean if (ws_mean is not None and bl_mean is not None) else None
    return {
        "mean_score_with_skill": ws_mean,
        "mean_score_baseline": bl_mean,
        "mean_lift": lift,
        "mean_cost_with_skill": _mean(ws_costs),
        "mean_cost_baseline": _mean(bl_costs),
        "invocation_count": len(ws_scores) + len(bl_scores),
    }


def _fmt_pct(v: float | None) -> str:
    return "—" if v is None else f"{v:.1f}%"


def _fmt_lift(v: float | None) -> str:
    return "—" if v is None else f"{v:+.1f}"


def _fmt_cost(v: float | None) -> str:
    return "—" if v is None else f"${v:.4f}"


def _pick_leader(
    per_skill: dict[str, dict], key: str, *, highest: bool
) -> tuple[str, float] | None:
    """Return the (skill, value) that leads on ``key``, or None if no skill
    has data for it. Ties break on skill name alphabetically (SKILLS order
    is already alphabetical), so the result is deterministic."""
    candidates = [
        (s, stats[key]) for s, stats in per_skill.items() if stats.get(key) is not None
    ]
    if not candidates:
        return None
    ordered = sorted(
        candidates,
        key=lambda x: (-x[1] if highest else x[1], x[0]),
    )
    return ordered[0]


def _collect(root: Path) -> dict[str, dict[str, Any]]:
    """Read each skill's metrics.json under ``root`` and compute its stats.
    Skills without a metrics.json are omitted from the summary — the
    SUMMARY.md then just doesn't have a row for them, which is fine when a
    partial ``--evaluate`` run failed one skill."""
    out: dict[str, dict[str, Any]] = {}
    for skill in SKILLS:
        p = root / skill / "metrics.json"
        if not p.is_file():
            continue
        try:
            metrics = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        out[skill] = compute_skill_stats(metrics)
    return out


def _render(per_skill: dict[str, dict[str, Any]]) -> str:
    """Assemble the markdown text. Kept as a pure function so the writer
    and the unit test can share the exact same formatting path."""
    lines: list[str] = []
    lines.append("# Skill evaluation summary")
    lines.append("")
    lines.append(
        "_Regenerated deterministically by `metrics_plots.write_summary()` "
        "from each skill's `metrics.json`. Do not edit by hand._"
    )
    lines.append("")
    lines.append("## Scores and costs")
    lines.append("")
    lines.append(
        "Averaged across every prompt and every invocation in this evaluation."
    )
    lines.append("")
    lines.append(
        "| Skill | Score (with skill) | Score (baseline) | Lift | "
        "Cost / invocation (with skill) | Cost / invocation (baseline) |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for skill in sorted(per_skill):
        s = per_skill[skill]
        lines.append(
            f"| {skill} | {_fmt_pct(s['mean_score_with_skill'])} | "
            f"{_fmt_pct(s['mean_score_baseline'])} | "
            f"{_fmt_lift(s['mean_lift'])} | "
            f"{_fmt_cost(s['mean_cost_with_skill'])} | "
            f"{_fmt_cost(s['mean_cost_baseline'])} |"
        )
    lines.append("")

    lines.append("## At a glance")
    lines.append("")
    for skill in sorted(per_skill):
        s = per_skill[skill]
        lines.append(
            f"- **{skill}** — scored {_fmt_pct(s['mean_score_with_skill'])} on "
            f"average ({_fmt_lift(s['mean_lift'])} vs. the unassisted baseline) "
            f"at {_fmt_cost(s['mean_cost_with_skill'])} per invocation."
        )
    lines.append("")

    lines.append("## Leaders")
    lines.append("")
    top_score = _pick_leader(per_skill, "mean_score_with_skill", highest=True)
    top_lift = _pick_leader(per_skill, "mean_lift", highest=True)
    lowest_cost = _pick_leader(per_skill, "mean_cost_with_skill", highest=False)
    if top_score:
        lines.append(
            f"- **Highest average score:** `{top_score[0]}` "
            f"({_fmt_pct(top_score[1])})."
        )
    if top_lift:
        lines.append(
            f"- **Highest lift over baseline:** `{top_lift[0]}` "
            f"({_fmt_lift(top_lift[1])})."
        )
    if lowest_cost:
        lines.append(
            f"- **Lowest cost per invocation:** `{lowest_cost[0]}` "
            f"({_fmt_cost(lowest_cost[1])})."
        )
    if not (top_score or top_lift or lowest_cost):
        lines.append("- _No scored variants — nothing to rank._")
    lines.append("")

    return "\n".join(lines)


def write_summary(root: Path) -> Path:
    """Write ``<root>/SUMMARY.md`` from every ``<root>/<skill>/metrics.json``
    that exists. Returns the written path."""
    root = Path(root)
    per_skill = _collect(root)
    text = _render(per_skill)
    out = root / "SUMMARY.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out
