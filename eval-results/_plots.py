#!/usr/bin/env python3
"""Shared plotnine plot-drawing helpers for eval-results/<skill>/plots/make_plots.py.

The 4 skills' `make_plots.py` scripts differ only in which skill's
`metrics.json` they read (see each script's own docstring) -- the actual
plot-drawing logic lives here once so a formatting fix applies to all 4
skills at once instead of drifting 4 separate ways.

Design follows the repo's `dataviz` skill method: fixed-order categorical
palette (skill = slot 1 blue, baseline = slot 2 orange -- validated with
`validate_palette.js`, both checks PASS on the light surface), a dumbbell
form for the before/after story, ring-backed markers, hairline recessive
gridlines, and selective direct labels instead of a label on every mark.
Chart text never names the specific skill (creator/house/prose/scripts) --
only "the skill" -- so a reader learns what's being evaluated, not which
skill produced it.

Two plots per skill:
  usage.png             tokens (x) vs. cost (y), one point per prompt per
                         variant, connected baseline -> skill so the "cost
                         of using the skill" reads as a single 2D vector
                         instead of a bar height + a disconnected label.
                         Faceted by difficulty tier.
  comparator_score.png  box plot of comparator score across 3 skill repeats
                         per prompt (the box's width already *is* the
                         consistency metric -- no separate chart needed for
                         it), with the baseline score as a point, a computed
                         mean-lift subtitle, and a caption on how to read the
                         box width. Faceted by difficulty tier.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_blank,
    geom_boxplot,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
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

DIFFICULTY_ORDER = ["easy", "medium", "hard"]
DIFFICULTY_LABELS = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}


def base_theme():
    """Shared look: system-sans typography (set globally, see
    `matplotlib.rcParams["font.family"]` above), hairline recessive
    gridlines, no minor gridlines, generous margins so long titles/captions
    never clip against the saved PNG's edge, understated facet strips."""
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
        strip_background=element_rect(fill="#f2f1ec", color="none"),
        strip_text=element_text(color=INK_SECONDARY, weight="bold", size=9.5),
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


def _prompt_rows(metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str]):
    """One row per (prompt, difficulty, short display label) that actually
    has data in this sweep, in prompt-list order."""
    prompts = metrics["prompts"]
    for pid in prompt_ids:
        entry = prompts.get(pid)
        if not entry:
            continue
        yield pid, entry.get("difficulty", "easy"), prompt_labels[pid].replace("\n", " ")


def plot_usage(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], out_path: Path
) -> bool:
    """Connected scatter: x = total tokens, y = cost (USD), one point per
    prompt per variant, with a thin arrow from baseline -> skill so the
    "cost of using the skill" is a single 2D vector instead of a bar height
    with a text label bolted on. Faceted by difficulty tier so the reader
    sees how usage scales with how hard the prompt is -- real structure the
    old chart never showed.

    Returns whether a chart was actually written."""
    rows = []
    for pid, difficulty, label in _prompt_rows(metrics, prompt_ids, prompt_labels):
        variants = metrics["prompts"][pid].get("variants", {})
        skill_ct = [
            variants[r]["cost_tokens"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("cost_tokens")
        ]
        if skill_ct:
            rows.append(
                {
                    "prompt": label,
                    "difficulty": difficulty,
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
                    "difficulty": difficulty,
                    "group": BASELINE_LABEL,
                    "tokens_k": (b["input_tokens"] + b["output_tokens"] + b["cache_creation_tokens"]) / 1000.0,
                    "cost": b["cost_usd"],
                }
            )

    if not rows:
        return False
    df = pd.DataFrame(rows)
    df["difficulty"] = pd.Categorical(df["difficulty"], categories=DIFFICULTY_ORDER, ordered=True)
    df["difficulty_label"] = df["difficulty"].map(DIFFICULTY_LABELS)
    df["difficulty_label"] = pd.Categorical(
        df["difficulty_label"], categories=[DIFFICULTY_LABELS[d] for d in DIFFICULTY_ORDER], ordered=True
    )

    # Segments only where a prompt has both a skill point and a baseline
    # point to connect -- an incomplete pair just renders as a lone point.
    wide = df.pivot_table(
        index=["prompt", "difficulty_label"], columns="group", values=["tokens_k", "cost"], aggfunc="first"
    )
    seg_rows = []
    for (prompt, diff_label), r in wide.iterrows():
        if SKILL_LABEL in r["tokens_k"].index and BASELINE_LABEL in r["tokens_k"].index:
            x0, y0 = r["tokens_k"][BASELINE_LABEL], r["cost"][BASELINE_LABEL]
            x1, y1 = r["tokens_k"][SKILL_LABEL], r["cost"][SKILL_LABEL]
            if pd.notna(x0) and pd.notna(x1):
                seg_rows.append(
                    {"prompt": prompt, "difficulty_label": diff_label, "x0": x0, "y0": y0, "x1": x1, "y1": y1}
                )
    seg_df = pd.DataFrame(seg_rows)
    if not seg_df.empty:
        # pivot_table's MultiIndex drops the Categorical dtype on the way
        # out -- recast it, or the facet layout silently falls back to
        # alphabetical order (Easy, Hard, Medium) instead of the difficulty
        # progression, since this layer's data no longer carries an order
        # for plotnine's panel layout to inherit.
        seg_df["difficulty_label"] = pd.Categorical(
            seg_df["difficulty_label"], categories=[DIFFICULTY_LABELS[d] for d in DIFFICULTY_ORDER], ordered=True
        )
        # Label at each segment's own midpoint (always inside its panel's
        # data range by construction) rather than nudged out from the
        # skill point -- which, being the higher-token point, usually sits
        # near a panel's right edge and would push long prompt names past
        # it. The vertical offset is scaled to the whole FACET's y-range
        # (not just this one segment's span) and staggered by each
        # segment's rank within its facet, so two prompts whose points
        # happen to sit close together still get visibly separated labels
        # instead of stacking on top of each other.
        seg_df["label_x"] = (seg_df["x0"] + seg_df["x1"]) / 2
        seg_df["_top"] = seg_df[["y0", "y1"]].max(axis=1)
        facet_range = seg_df.groupby("difficulty_label", observed=True)["_top"].transform(
            lambda s: (s.max() - s.min()) if s.max() > s.min() else s.max() * 0.2
        )
        rank = seg_df.groupby("difficulty_label", observed=True)["_top"].rank(method="first") - 1
        seg_df["label_y"] = seg_df["_top"] + facet_range * (0.10 + rank * 0.16)
        seg_df = seg_df.drop(columns="_top")

    plot = (
        ggplot(df, aes(x="tokens_k", y="cost"))
        + _layer_or_blank(
            seg_df,
            geom_segment(
                data=seg_df,
                mapping=aes(x="x0", y="y0", xend="x1", yend="y1"),
                color=INK_MUTED,
                size=0.6,
                alpha=0.7,
                arrow=arrow(length=0.12, type="closed"),
                inherit_aes=False,
            ),
        )
        # white halo behind every point -- a surface "ring" so points stay
        # legible where the connecting arrow passes under them.
        + geom_point(color="white", size=5.4)
        + geom_point(aes(color="group"), size=3.6)
        + _layer_or_blank(
            seg_df,
            geom_text(
                data=seg_df,
                mapping=aes(x="label_x", y="label_y", label="prompt"),
                color=INK_SECONDARY,
                size=7.5,
                va="bottom",
                inherit_aes=False,
            ),
        )
        + scale_color_manual(values={SKILL_LABEL: SKILL_COLOR, BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_continuous(labels=lambda vals: [f"{v:.0f}K" for v in vals], expand=(0.15, 0))
        + scale_y_continuous(labels=lambda vals: [f"${v:.2f}" for v in vals], expand=(0.12, 0, 0.32, 0))
        + facet_wrap("~difficulty_label", nrow=1, scales="free")
        + labs(
            title="Token usage and cost, per prompt",
            subtitle="Each arrow runs from an unassisted baseline to using the skill -- "
            "position shows both tokens spent and dollars spent for the same invocation.",
            x="Total tokens (input + output + cache-creation)",
            y="Cost per invocation",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True


def plot_comparator_score(
    metrics: dict, prompt_ids: list[str], prompt_labels: dict[str, str], out_path: Path
) -> bool:
    """Box plot of comparator total-score % across the 3 skill repeats per
    prompt (box width already IS the consistency metric -- no separate
    chart needed), with the baseline score as a point. Faceted by difficulty
    tier; subtitle states the computed mean lift over baseline; caption
    explains how to read the box width.

    Returns whether a chart was actually written."""
    box_rows = []
    point_rows = []
    lifts = []
    for pid, difficulty, label in _prompt_rows(metrics, prompt_ids, prompt_labels):
        variants = metrics["prompts"][pid].get("variants", {})
        pcts = [
            variants[r]["score"]["pct"]
            for r in REPEATS
            if variants.get(r) and variants[r].get("score") and variants[r]["score"]["pct"] is not None
        ]
        for pct in pcts:
            box_rows.append({"prompt": label, "difficulty": difficulty, "pct": pct})
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        baseline_pct = b["pct"] if b and b["pct"] is not None else None
        if baseline_pct is not None:
            point_rows.append(
                {"prompt": label, "difficulty": difficulty, "pct": baseline_pct, "group": BASELINE_LABEL}
            )
        if pcts and baseline_pct is not None:
            lifts.append(float(np.mean(pcts)) - baseline_pct)

    if not box_rows:
        return False
    box_df = pd.DataFrame(box_rows)
    box_df["group"] = SKILL_LABEL
    box_df["difficulty"] = pd.Categorical(box_df["difficulty"], categories=DIFFICULTY_ORDER, ordered=True)
    box_df["difficulty_label"] = box_df["difficulty"].map(DIFFICULTY_LABELS)
    box_df["difficulty_label"] = pd.Categorical(
        box_df["difficulty_label"], categories=[DIFFICULTY_LABELS[d] for d in DIFFICULTY_ORDER], ordered=True
    )
    point_df = pd.DataFrame(point_rows)
    if not point_df.empty:
        point_df["difficulty"] = pd.Categorical(point_df["difficulty"], categories=DIFFICULTY_ORDER, ordered=True)
        point_df["difficulty_label"] = point_df["difficulty"].map(DIFFICULTY_LABELS)
        point_df["difficulty_label"] = pd.Categorical(
            point_df["difficulty_label"], categories=[DIFFICULTY_LABELS[d] for d in DIFFICULTY_ORDER], ordered=True
        )

    if lifts:
        mean_lift = float(np.mean(lifts))
        direction = "above" if mean_lift >= 0 else "below"
        lift_line = (
            f"Across {len(lifts)} prompts, the skill's mean score is {abs(mean_lift):.0f} points "
            f"{direction} the unassisted baseline, on average."
        )
    else:
        lift_line = "Comparator score per prompt, with the skill vs. without."

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
        + facet_wrap("~difficulty_label", nrow=1, scales="free_x")
        + ylim(0, 100)
        + labs(
            title="Comparator score: repeated attempts with the skill vs. without",
            subtitle=lift_line,
            caption="Box = spread of the skill's score across 3 attempts on the same prompt -- "
            "narrower is more consistent. Dot = a single unassisted baseline attempt.",
            x="",
            y="Comparator total score (%)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True
