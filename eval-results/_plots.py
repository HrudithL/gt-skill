#!/usr/bin/env python3
"""Shared plotnine plot-drawing helpers for eval-results/<skill>/plots/make_plots.py.

The 4 skills' `make_plots.py` scripts differ only in which skill's
`metrics.json` they read (see each script's own docstring) -- the actual
plot-drawing logic lives here once so a formatting fix applies to all 4
skills at once instead of drifting 4 separate ways.

Three plots per skill:
  usage.png             total tokens per prompt (skill mean vs. baseline),
                         with each bar's USD cost annotated directly on it --
                         replaces the old separate cost.png + tokens.png pair
                         so token volume and its dollar cost read as one story.
  consistency.png       min-mean-max comparator score across 3 repeats.
  comparator_score.png  comparator score distribution: repeats (box) vs.
                         baseline (point).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_boxplot,
    geom_col,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    labs,
    position_dodge,
    scale_color_manual,
    scale_fill_manual,
    scale_x_discrete,
    theme,
    theme_minimal,
    ylim,
)

REPEATS = ["repeat_1", "repeat_2", "repeat_3"]
REPEAT_COLOR = "#3B6FA0"
BASELINE_COLOR = "#B0413E"
SKILL_LABEL = "skill (mean of repeats)"
BASELINE_LABEL = "baseline (no skill)"
GROUP_COLORS = {SKILL_LABEL: REPEAT_COLOR, BASELINE_LABEL: BASELINE_COLOR}


def base_theme():
    """One consistent look for all 3 plots: no minor gridlines, no chart
    junk, generous margins so long titles/legends never clip against the
    saved PNG's edge."""
    return theme_minimal(base_size=11) + theme(
        plot_title=element_text(weight="bold", size=13, ha="left"),
        plot_margin=0.03,
        panel_grid_minor=element_blank(),
        legend_position="bottom",
        legend_title=element_blank(),
        legend_text=element_text(size=9),
        axis_title=element_text(size=10),
        figure_size=(9, 5.5),
    )


def _save(plot, out_path: Path) -> None:
    ggsave(
        plot,
        filename=str(out_path),
        dpi=150,
        verbose=False,
    )


def _prompt_order(prompt_labels: dict[str, str], prompt_ids: list[str]) -> list[str]:
    return [prompt_labels[p] for p in prompt_ids]


def plot_usage(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], skill: str, out_path: Path
) -> bool:
    """Grouped bar chart of total tokens per prompt (skill mean vs.
    baseline), each bar's USD cost printed just above it -- one chart
    instead of a separate cost bar chart and token scatter plot, so the
    reader sees token volume and what it actually cost in the same glance.

    Returns whether a chart was actually written (False if there was no
    data at all for this skill's sweep -- callers should surface that
    loudly rather than silently leaving a stale PNG in place)."""
    prompts = metrics["prompts"]
    rows = []
    for pid in prompt_ids:
        variants = prompts.get(pid, {}).get("variants", {})
        skill_tokens = [
            variants[r]["cost_tokens"]["input_tokens"]
            + variants[r]["cost_tokens"]["output_tokens"]
            + variants[r]["cost_tokens"]["cache_creation_tokens"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("cost_tokens")
        ]
        skill_costs = [
            variants[r]["cost_tokens"]["cost_usd"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("cost_tokens")
        ]
        if skill_tokens:
            rows.append(
                {
                    "prompt": prompt_labels[pid],
                    "group": SKILL_LABEL,
                    "tokens_k": np.mean(skill_tokens) / 1000.0,
                    "cost": np.mean(skill_costs),
                }
            )
        b = variants.get("baseline", {}).get("cost_tokens") if variants.get("baseline") else None
        if b:
            rows.append(
                {
                    "prompt": prompt_labels[pid],
                    "group": BASELINE_LABEL,
                    "tokens_k": (b["input_tokens"] + b["output_tokens"] + b["cache_creation_tokens"]) / 1000.0,
                    "cost": b["cost_usd"],
                }
            )

    if not rows:
        return False
    df = pd.DataFrame(rows)
    order = _prompt_order(prompt_labels, prompt_ids)
    df["prompt"] = pd.Categorical(df["prompt"], categories=order, ordered=True)
    df["cost_label"] = df["cost"].map(lambda c: f"${c:.2f}")

    # Headroom above the tallest bar so the cost label printed above it
    # never gets clipped by the plot's top edge; floored so an all-zero
    # sweep (e.g. every invocation missing usage data) still gets a
    # renderable, non-degenerate axis instead of ylim(0, 0).
    upper = max(df["tokens_k"].max() * 1.22, 1.0)

    # preserve="single" keeps every bar at its full dodged width and slot
    # even when one prompt is missing a group (e.g. a crashed baseline) --
    # without it, a lone surviving bar re-centers and doubles in width,
    # which reads as a normal bar rather than a visibly missing one.
    dodge = position_dodge(width=0.75, preserve="single")

    plot = (
        ggplot(df, aes(x="prompt", y="tokens_k", fill="group"))
        + geom_col(position=dodge, width=0.68)
        + geom_text(
            aes(label="cost_label", group="group"),
            position=dodge,
            va="bottom",
            size=8,
        )
        + scale_fill_manual(values=GROUP_COLORS)
        + scale_x_discrete(limits=order)
        + ylim(0, upper)
        + labs(
            title=f"{skill} skill — token usage per prompt (bar height), with cost per invocation (label)",
            x="",
            y="Total tokens, thousands (input + output + cache-creation)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True


def plot_consistency(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], skill: str, out_path: Path
) -> bool:
    """Range ("dumbbell") plot: for each prompt, a line from the lowest to
    the highest comparator score among the 3 skill repeats, with the mean
    marked -- the line's length IS the consistency metric. Baseline's own
    score is plotted alongside for reference, not folded into the spread (a
    single baseline run has no spread of its own).

    Returns whether a chart was actually written (see `plot_usage`)."""
    prompts = metrics["prompts"]
    rows = []
    segments = []
    for pid in prompt_ids:
        variants = prompts.get(pid, {}).get("variants", {})
        pcts = [
            variants[r]["score"]["pct"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("score") and variants[r]["score"]["pct"] is not None
        ]
        label = prompt_labels[pid]
        if pcts:
            rows.append({"prompt": label, "group": SKILL_LABEL, "pct": float(np.mean(pcts))})
            segments.append({"prompt": label, "lo": min(pcts), "hi": max(pcts)})
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        if b and b["pct"] is not None:
            rows.append({"prompt": label, "group": BASELINE_LABEL, "pct": float(b["pct"])})

    if not rows:
        return False
    df = pd.DataFrame(rows)
    seg_df = pd.DataFrame(segments)
    order = _prompt_order(prompt_labels, prompt_ids)
    df["prompt"] = pd.Categorical(df["prompt"], categories=order, ordered=True)
    if not seg_df.empty:
        seg_df["prompt"] = pd.Categorical(seg_df["prompt"], categories=order, ordered=True)

    plot = (
        ggplot(df, aes(x="prompt", y="pct"))
        + geom_segment(
            data=seg_df,
            mapping=aes(x="prompt", xend="prompt", y="lo", yend="hi"),
            color=REPEAT_COLOR,
            size=3,
            alpha=0.55,
            inherit_aes=False,
        )
        + geom_point(aes(color="group"), size=3.2)
        + scale_color_manual(values=GROUP_COLORS)
        + scale_x_discrete(limits=order)
        + ylim(0, 100)
        + labs(
            title=f"{skill} skill — consistency: min–mean–max comparator score across 3 repeats",
            x="",
            y="Comparator total score (%)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True


def plot_comparator_score(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], skill: str, out_path: Path
) -> bool:
    """Box plot of comparator total-score % across the 3 skill repeats per
    prompt, with the baseline score overlaid as a point -- one fill color for
    the box, one color for the baseline point, no mean marker or other
    chart junk on top of the box itself.

    Returns whether a chart was actually written (see `plot_usage`)."""
    prompts = metrics["prompts"]
    box_rows = []
    point_rows = []
    for pid in prompt_ids:
        variants = prompts.get(pid, {}).get("variants", {})
        label = prompt_labels[pid]
        for r in REPEATS:
            score = variants.get(r, {}).get("score") if variants.get(r) else None
            if score and score["pct"] is not None:
                box_rows.append({"prompt": label, "pct": score["pct"]})
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        if b and b["pct"] is not None:
            point_rows.append({"prompt": label, "pct": b["pct"], "group": BASELINE_LABEL})

    if not box_rows:
        return False
    order = _prompt_order(prompt_labels, prompt_ids)
    box_df = pd.DataFrame(box_rows)
    box_df["prompt"] = pd.Categorical(box_df["prompt"], categories=order, ordered=True)
    point_df = pd.DataFrame(point_rows)
    if not point_df.empty:
        point_df["prompt"] = pd.Categorical(point_df["prompt"], categories=order, ordered=True)

    plot = (
        ggplot(box_df, aes(x="prompt", y="pct"))
        + geom_boxplot(fill=REPEAT_COLOR, alpha=0.5, width=0.5, outlier_size=1.5)
        + geom_point(point_df, aes(color="group"), size=3.2)
        + scale_color_manual(values={BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_discrete(limits=order)
        + ylim(0, 100)
        + labs(
            title=f"{skill} skill — comparator score: 3 repeats (box) vs. baseline (point)",
            x="",
            y="Comparator total score (%)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True
