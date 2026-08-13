#!/usr/bin/env python3
"""Shared plotnine plot-drawing helpers for eval-results/<skill>/plots/make_plots.py.

The 4 skills' `make_plots.py` scripts differ only in which skill's
`metrics.json` they read (see each script's own docstring) -- the actual
plot-drawing logic lives here once so a formatting fix applies to all 4
skills at once instead of drifting 4 separate ways.

Design follows the repo's `dataviz` skill method: fixed-order categorical
palette (skill = slot 1 blue, baseline = slot 2 orange -- validated with
`validate_palette.js`, both checks PASS on the light surface), ring-backed
markers, hairline recessive gridlines, and selective direct labels instead
of a label on every mark. Chart text never names the specific skill
(creator/house/prose/scripts) -- only "the skill" -- so a reader learns
what's being evaluated, not which skill produced it. Neither chart facets
by difficulty tier or splits the 6 prompts into separate panels -- all 6
render together in one view.

Two plots per skill:
  usage.png             grouped bar chart: bar height = mean total tokens
                         per prompt (skill vs. baseline), each bar's USD
                         cost printed at its tip -- one glance shows both
                         how many tokens an invocation used and what it
                         cost, without a second numeric axis to
                         cross-reference or a scatter plot's x/y mapping to
                         decode.
  comparator_score.png  box plot of evaluation score across 3 skill repeats
                         per prompt (the box's height already *is* the
                         consistency metric -- no separate chart needed for
                         it), with the baseline score as a point, a computed
                         mean-lift subtitle, and a caption on how to read
                         the box height. Called "evaluation score" in the
                         chart's own text (not "comparator score") since
                         the score blends the deterministic comparator with
                         the LLM judge, not the comparator alone.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_blank,
    geom_boxplot,
    geom_col,
    geom_point,
    geom_text,
    ggplot,
    ggsave,
    labs,
    position_dodge,
    scale_color_manual,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
    theme_minimal,
    ylim,
)

REPEATS = ["repeat_1", "repeat_2", "repeat_3"]

# Validated categorical pair (dataviz skill, fixed slot order): slot 1 blue
# for the skill series, slot 2 orange for baseline. `validate_palette.js
# "#2a78d6,#eb6834" --mode light` passes all 6 checks (worst adjacent CVD
# ~24.7, normal-vision ~33.6, both well clear of the ~8 / ~15 targets).
SKILL_COLOR = "#2a78d6"
SKILL_FILL = "#b7d3f6"  # light step of the same hue, for the box fill wash
BASELINE_COLOR = "#eb6834"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
AXIS_LINE = "#c3c2b7"

SKILL_LABEL = "with skill (3 attempts)"
BASELINE_LABEL = "baseline (no skill)"

# A fallback chain, not a single face -- set once on the shared matplotlib
# rcParams (which plotnine renders through) rather than passed per-geom,
# since plotnine's per-geom `family` aesthetic wants one concrete name and
# rejects a list. Matplotlib itself resolves a list fine at the rcParams
# level, picking the first installed face.
matplotlib.rcParams["font.family"] = ["Avenir Next", "Helvetica Neue", "Arial", "sans-serif"]


def _adaptive_decimals(vals: list[float], min_decimals: int, max_decimals: int = 6) -> int:
    """Enough decimal places that adjacent TICKS stay visually distinct --
    a fixed `.0f` degenerates to identical-looking ticks (e.g. every tick
    reading "40K") whenever the axis's own range is small. Based on the
    smallest gap between the actual computed tick values (not the axis's
    overall span), so a normal wide range still gets the same clean,
    minimal-decimals output as a fixed formatter would."""
    uniq = sorted({v for v in vals if v is not None})
    if len(uniq) < 2:
        return min_decimals
    gap = min(b - a for a, b in zip(uniq, uniq[1:]) if b > a)
    if gap <= 0:
        return min_decimals
    needed = int(np.ceil(-np.log10(gap)))
    return min(max_decimals, max(min_decimals, needed))


def _token_tick_labels(vals):
    decimals = _adaptive_decimals(vals, min_decimals=0, max_decimals=2)
    return [f"{v:.{decimals}f}K" for v in vals]


def base_theme():
    """Shared look: system-sans typography (set globally, see
    `matplotlib.rcParams["font.family"]` above), hairline recessive
    gridlines, no minor gridlines, generous margins so long titles/captions
    never clip against the saved PNG's edge."""
    return theme_minimal(base_size=11) + theme(
        plot_title=element_text(weight="bold", size=14, ha="left"),
        plot_subtitle=element_text(size=10.5, ha="left", color=INK_SECONDARY),
        plot_caption=element_text(size=8.5, ha="left", color=INK_MUTED, style="italic"),
        plot_margin=0.035,
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color=GRIDLINE, size=0.5),
        axis_line=element_line(color=AXIS_LINE, size=0.6),
        axis_ticks=element_line(color=AXIS_LINE, size=0.6),
        axis_text=element_text(color=INK_MUTED, size=9),
        axis_title=element_text(color=INK_SECONDARY, size=10),
        panel_border=element_blank(),
        legend_position="bottom",
        legend_title=element_blank(),
        legend_text=element_text(size=9),
        figure_size=(10, 5.5),
    )


def _save(plot, out_path: Path) -> None:
    ggsave(plot, filename=str(out_path), dpi=150, verbose=False)


def _layer_or_blank(df: pd.DataFrame, layer):
    """Swap in a no-op layer when `df` (the data the layer would draw from)
    is empty, rather than handing plotnine a zero-row frame -- which raises
    a confusing "could not evaluate the mapping" PlotnineError at render
    time instead of just... not drawing that layer."""
    return layer if not df.empty else geom_blank()


def plot_usage(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], out_path: Path
) -> bool:
    """Grouped bar chart: bar height = mean total tokens per prompt (skill
    vs. baseline), each bar's USD cost printed at its tip. One glance shows
    both how many tokens an invocation used and what it cost -- no second
    numeric axis to cross-reference, no x/y scatter mapping to decode.

    Returns whether a chart was actually written (False if there was no
    data at all for this skill's sweep)."""
    prompts = metrics["prompts"]
    rows = []
    order = []
    for pid in prompt_ids:
        entry = prompts.get(pid)
        if not entry:
            continue
        label = prompt_labels[pid]
        order.append(label)
        variants = entry.get("variants", {})
        skill_ct = [
            variants[r]["cost_tokens"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("cost_tokens")
        ]
        if skill_ct:
            rows.append(
                {
                    "prompt": label,
                    "group": SKILL_LABEL,
                    "tokens_k": np.mean(
                        [c["input_tokens"] + c["output_tokens"] + c["cache_creation_tokens"] for c in skill_ct]
                    )
                    / 1000.0,
                    "cost": np.mean([c["cost_usd"] for c in skill_ct]),
                }
            )
        b = variants.get("baseline", {}).get("cost_tokens") if variants.get("baseline") else None
        if b:
            rows.append(
                {
                    "prompt": label,
                    "group": BASELINE_LABEL,
                    "tokens_k": (b["input_tokens"] + b["output_tokens"] + b["cache_creation_tokens"]) / 1000.0,
                    "cost": b["cost_usd"],
                }
            )

    if not rows:
        return False
    df = pd.DataFrame(rows)
    df["prompt"] = pd.Categorical(df["prompt"], categories=order, ordered=True)
    df["cost_label"] = df["cost"].map(lambda c: f"${c:.2f}")

    # Headroom above the tallest bar so the cost label printed above it
    # never gets clipped by the plot's top edge; floored so an all-zero
    # sweep (e.g. every invocation missing usage data) still gets a
    # renderable, non-degenerate axis instead of an empty range.
    upper = max(df["tokens_k"].max() * 1.22, 1.0)

    # preserve="single" keeps every bar at its full dodged width even when
    # one prompt is missing a group (e.g. a crashed baseline) -- without it,
    # a lone surviving bar re-centers and doubles in width, which reads as
    # a normal bar rather than a visibly missing one. (It still slides into
    # the missing group's slot, not its own -- only the fill color marks
    # which group it is -- but the width alone no longer disguises it.)
    dodge = position_dodge(width=0.75, preserve="single")

    plot = (
        ggplot(df, aes(x="prompt", y="tokens_k", fill="group"))
        + geom_col(position=dodge, width=0.68)
        + geom_text(
            aes(label="cost_label", group="group"),
            position=dodge,
            va="bottom",
            size=8,
            color=INK_SECONDARY,
        )
        + scale_fill_manual(values={SKILL_LABEL: SKILL_COLOR, BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_discrete(limits=order)
        + scale_y_continuous(labels=_token_tick_labels, limits=(0, upper))
        + labs(
            title="Token usage per prompt, with cost per invocation",
            subtitle="Bar height is the total tokens spent; the label above each bar is what "
            "that invocation cost.",
            x="",
            y="Total tokens (input + output + cache-creation)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True


def plot_comparator_score(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], out_path: Path
) -> bool:
    """Box plot of evaluation score across the 3 skill repeats per prompt
    (box HEIGHT already IS the consistency metric -- no separate chart
    needed), with the baseline score as a point. Called "evaluation score"
    in the chart's own text -- the score blends the deterministic
    comparator with the LLM judge, not the comparator alone, so "comparator
    score" alone would misname what's actually plotted. Subtitle states the
    computed mean lift over baseline; caption explains how to read the box
    height.

    Returns whether a chart was actually written."""
    box_rows = []
    point_rows = []
    lifts = []
    order = []
    for pid in prompt_ids:
        entry = metrics["prompts"].get(pid)
        if not entry:
            continue
        label = prompt_labels[pid]
        order.append(label)
        variants = entry.get("variants", {})
        pcts = [
            variants[r]["score"]["pct"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("score") and variants[r]["score"]["pct"] is not None
        ]
        for pct in pcts:
            box_rows.append({"prompt": label, "pct": pct})
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        baseline_pct = b["pct"] if b and b["pct"] is not None else None
        if baseline_pct is not None:
            point_rows.append({"prompt": label, "pct": baseline_pct, "group": BASELINE_LABEL})
        if pcts and baseline_pct is not None:
            lifts.append(float(np.mean(pcts)) - baseline_pct)

    if not box_rows:
        return False
    box_df = pd.DataFrame(box_rows)
    box_df["group"] = SKILL_LABEL
    box_df["prompt"] = pd.Categorical(box_df["prompt"], categories=order, ordered=True)
    point_df = pd.DataFrame(point_rows)
    if not point_df.empty:
        point_df["prompt"] = pd.Categorical(point_df["prompt"], categories=order, ordered=True)

    if lifts:
        mean_lift = float(np.mean(lifts))
        rounded = round(abs(mean_lift))
        prompt_word = "prompt" if len(prompt_ids) == 1 else "prompts"
        coverage = (
            f"across all {len(prompt_ids)} {prompt_word}"
            if len(lifts) == len(prompt_ids)
            else f"across the {len(lifts)} of {len(prompt_ids)} {prompt_word} with both a baseline and at "
            "least one scored attempt"
        )
        if rounded == 0:
            lift_line = f"The skill's mean score matches the unassisted baseline, on average {coverage}."
        else:
            direction = "above" if mean_lift >= 0 else "below"
            point_word = "point" if rounded == 1 else "points"
            lift_line = (
                f"The skill's mean score is {rounded:.0f} {point_word} {direction} the unassisted "
                f"baseline, on average {coverage}."
            )
    else:
        lift_line = "Evaluation score per prompt, with the skill vs. without."

    plot = (
        ggplot(box_df, aes(x="prompt", y="pct"))
        + geom_boxplot(aes(fill="group"), color=SKILL_COLOR, width=0.5, outlier_shape=None, alpha=0.85)
        # white halo behind the baseline point -- keeps it legible where it
        # sits on or near the box/whisker (a degenerate 3-way-tied box can
        # render as a thin line right where the baseline point lands).
        + _layer_or_blank(point_df, geom_point(point_df, aes(x="prompt", y="pct"), color="white", size=5.4))
        + _layer_or_blank(point_df, geom_point(point_df, aes(color="group"), size=3.6))
        + scale_fill_manual(values={SKILL_LABEL: SKILL_FILL})
        + scale_color_manual(values={BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_discrete(limits=order)
        + ylim(0, 100)
        + labs(
            title="Evaluation score: repeated attempts with the skill vs. without",
            subtitle=lift_line,
            caption="Box = spread of the skill's score across 3 attempts on the same prompt -- "
            "shorter is more consistent. Dot = a single unassisted baseline attempt.",
            x="",
            y="Evaluation score (%)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True
