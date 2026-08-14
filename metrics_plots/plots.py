#!/usr/bin/env python3
"""Plotnine plot-drawing helpers for ``metrics_plots``.

Adapted verbatim from the previous ``eval-results/_plots.py`` — same
palette, same layout, same theme — with two small generalizations for the
``--evaluate`` flag's variable repeat count and adaptive layout:

- The set of ``repeat_N`` variants is discovered from the metrics dict at
  render time rather than hard-coded to 3.
- The skill-series legend label reflects the actual attempt count
  ("with skill (N attempts)" where N is whatever was run).

Two chart shapes per skill:

  usage.png             grouped bar chart: bar height = mean total tokens
                         per prompt (skill vs. baseline), each bar's USD
                         cost printed at its tip.
  comparator_score.png  box plot of evaluation score across the skill's
                         repeats per prompt (box height IS the consistency
                         metric — no separate chart needed), with the
                         baseline score as a point, a mean-lift subtitle,
                         and a caption on how to read the box height.
                         Called "evaluation score" (not "comparator score")
                         since the score blends the deterministic
                         comparator with the LLM judge.
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

# Validated categorical pair (dataviz skill, fixed slot order): slot 1 blue
# for the skill series, slot 2 orange for baseline. Passes `validate_palette.js
# "#2a78d6,#eb6834" --mode light` on all 6 checks.
SKILL_COLOR = "#2a78d6"
SKILL_FILL = "#b7d3f6"
BASELINE_COLOR = "#eb6834"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
AXIS_LINE = "#c3c2b7"

BASELINE_LABEL = "baseline (no skill)"

# A fallback chain, not a single face — set once on the shared matplotlib
# rcParams (which plotnine renders through) rather than passed per-geom,
# since plotnine's per-geom `family` aesthetic wants one concrete name and
# rejects a list.
matplotlib.rcParams["font.family"] = ["Avenir Next", "Helvetica Neue", "Arial", "sans-serif"]


def _repeat_variants(metrics: dict) -> list[str]:
    """Every ``repeat_N`` key that shows up in this skill's metrics, sorted
    by N. Discovered from data so N=3 (the default) and N=5 (the
    ``--evaluate --repeat 5`` case) both work without editing this file."""
    keys: set[str] = set()
    for entry in metrics.get("prompts", {}).values():
        for v in (entry.get("variants") or {}).keys():
            if v.startswith("repeat_"):
                keys.add(v)
    return sorted(keys, key=lambda k: int(k.split("_", 1)[1]))


def _skill_label(repeats: list[str]) -> str:
    n = len(repeats)
    return f"with skill ({n} run{'s' if n != 1 else ''})"


def _adaptive_decimals(vals: list[float], min_decimals: int, max_decimals: int = 6) -> int:
    """Enough decimal places that adjacent TICKS stay visually distinct — a
    fixed ``.0f`` degenerates to identical-looking ticks (every tick reading
    "40K") whenever the axis's own range is small. Based on the smallest
    gap between actual tick values, not the axis's overall span."""
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
    """Shared look: system-sans typography, hairline recessive gridlines,
    no minor gridlines, generous margins so long titles/captions never
    clip against the saved PNG's edge."""
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
    """Swap in a no-op layer when ``df`` is empty rather than handing
    plotnine a zero-row frame — which raises a confusing
    "could not evaluate the mapping" PlotnineError at render time instead
    of just... not drawing that layer."""
    return layer if not df.empty else geom_blank()


def plot_usage(
    metrics: dict,
    prompt_ids: list[str],
    prompt_labels: dict[str, str],
    out_path: Path,
) -> bool:
    """Grouped bar chart: bar height = mean USD cost per invocation, with
    the cost printed above each bar. No token axis — this plot is now
    cost-focused; :func:`plot_tokens_and_cost` shows both together.

    Returns whether a chart was actually written (False if there was no
    data at all)."""
    repeats = _repeat_variants(metrics)
    skill_label = _skill_label(repeats)
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
            for r in repeats
            if variants.get(r) and variants[r].get("cost_tokens")
        ]
        if skill_ct:
            rows.append({
                "prompt": label,
                "group": skill_label,
                "cost": float(np.mean([c["cost_usd"] for c in skill_ct])),
            })
        b = variants.get("baseline", {}).get("cost_tokens") if variants.get("baseline") else None
        if b:
            rows.append({
                "prompt": label,
                "group": BASELINE_LABEL,
                "cost": float(b["cost_usd"]),
            })

    if not rows:
        return False
    df = pd.DataFrame(rows)
    df["prompt"] = pd.Categorical(df["prompt"], categories=order, ordered=True)
    df["cost_label"] = df["cost"].map(lambda c: f"${c:.2f}")

    upper = max(df["cost"].max() * 1.22, 0.02)
    dodge = position_dodge(width=0.75, preserve="single")

    plot = (
        ggplot(df, aes(x="prompt", y="cost", fill="group"))
        + geom_col(position=dodge, width=0.68)
        + geom_text(
            aes(label="cost_label", group="group"),
            position=dodge,
            va="bottom",
            size=8,
            color=INK_SECONDARY,
        )
        + scale_fill_manual(values={skill_label: SKILL_COLOR, BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_discrete(limits=order)
        + scale_y_continuous(labels=lambda vs: [f"${v:.2f}" for v in vs], limits=(0, upper))
        + labs(
            title="Cost per invocation, per prompt",
            x="",
            y="Cost per invocation (USD)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True


def plot_tokens_and_cost(
    metrics: dict,
    prompt_ids: list[str],
    prompt_labels: dict[str, str],
    out_path: Path,
) -> bool:
    """Two-facet grouped bar chart on one canvas: top facet shows cost per
    invocation (with USD labels), bottom facet shows tokens per invocation
    (with K labels). Same prompts on the x-axis so cost + tokens line up
    vertically per prompt and per variant. Provided as an experimental
    combined view alongside :func:`plot_usage` (cost-only) — pick whichever
    reads more clearly.

    Returns whether a chart was actually written."""
    from plotnine import facet_wrap

    repeats = _repeat_variants(metrics)
    skill_label = _skill_label(repeats)
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
            for r in repeats
            if variants.get(r) and variants[r].get("cost_tokens")
        ]
        if skill_ct:
            mean_cost = float(np.mean([c["cost_usd"] for c in skill_ct]))
            mean_tokens_k = float(np.mean([
                c["input_tokens"] + c["output_tokens"] + c["cache_creation_tokens"]
                for c in skill_ct
            ]) / 1000.0)
            rows.append({"prompt": label, "group": skill_label,
                          "facet": "Cost per invocation (USD)", "value": mean_cost,
                          "value_label": f"${mean_cost:.2f}"})
            rows.append({"prompt": label, "group": skill_label,
                          "facet": "Tokens per invocation (thousands)", "value": mean_tokens_k,
                          "value_label": f"{mean_tokens_k:.0f}K"})
        b = variants.get("baseline", {}).get("cost_tokens") if variants.get("baseline") else None
        if b:
            b_tokens_k = (b["input_tokens"] + b["output_tokens"] + b["cache_creation_tokens"]) / 1000.0
            rows.append({"prompt": label, "group": BASELINE_LABEL,
                          "facet": "Cost per invocation (USD)", "value": float(b["cost_usd"]),
                          "value_label": f"${b['cost_usd']:.2f}"})
            rows.append({"prompt": label, "group": BASELINE_LABEL,
                          "facet": "Tokens per invocation (thousands)", "value": b_tokens_k,
                          "value_label": f"{b_tokens_k:.0f}K"})

    if not rows:
        return False
    df = pd.DataFrame(rows)
    df["prompt"] = pd.Categorical(df["prompt"], categories=order, ordered=True)
    # Fixed facet order (cost on top, tokens on bottom).
    facet_order = ["Cost per invocation (USD)", "Tokens per invocation (thousands)"]
    df["facet"] = pd.Categorical(df["facet"], categories=facet_order, ordered=True)

    dodge = position_dodge(width=0.75, preserve="single")
    plot = (
        ggplot(df, aes(x="prompt", y="value", fill="group"))
        + geom_col(position=dodge, width=0.68)
        + geom_text(aes(label="value_label", group="group"),
                    position=dodge, va="bottom", size=7.5, color=INK_SECONDARY)
        + facet_wrap("~ facet", nrow=2, scales="free_y")
        + scale_fill_manual(values={skill_label: SKILL_COLOR, BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_discrete(limits=order)
        + labs(title="Cost and tokens per invocation, per prompt", x="", y="")
        + base_theme()
        + theme(figure_size=(10, 7))
    )
    _save(plot, out_path)
    return True


def plot_comparator_score(
    metrics: dict,
    prompt_ids: list[str],
    prompt_labels: dict[str, str],
    out_path: Path,
) -> bool:
    """Box plot of accuracy across the skill's runs per prompt, with the
    baseline score as a point. No subtitle, no caption — the plot title and
    the legend already say what the chart shows.

    Returns whether a chart was actually written."""
    repeats = _repeat_variants(metrics)
    skill_label = _skill_label(repeats)
    box_rows = []
    point_rows = []
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
            for r in repeats
            if variants.get(r)
            and variants[r].get("score")
            and variants[r]["score"]["pct"] is not None
        ]
        for pct in pcts:
            box_rows.append({"prompt": label, "pct": pct})
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        baseline_pct = b["pct"] if b and b["pct"] is not None else None
        if baseline_pct is not None:
            point_rows.append({"prompt": label, "pct": baseline_pct, "group": BASELINE_LABEL})

    if not box_rows:
        return False
    box_df = pd.DataFrame(box_rows)
    box_df["group"] = skill_label
    box_df["prompt"] = pd.Categorical(box_df["prompt"], categories=order, ordered=True)
    point_df = pd.DataFrame(point_rows)
    if not point_df.empty:
        point_df["prompt"] = pd.Categorical(point_df["prompt"], categories=order, ordered=True)

    plot = (
        ggplot(box_df, aes(x="prompt", y="pct"))
        + geom_boxplot(aes(fill="group"), color=SKILL_COLOR, width=0.5, outlier_shape=None, alpha=0.85)
        + _layer_or_blank(point_df, geom_point(point_df, aes(x="prompt", y="pct"), color="white", size=5.4))
        + _layer_or_blank(point_df, geom_point(point_df, aes(color="group"), size=3.6))
        + scale_fill_manual(values={skill_label: SKILL_FILL})
        + scale_color_manual(values={BASELINE_LABEL: BASELINE_COLOR})
        + scale_x_discrete(limits=order)
        + ylim(0, 100)
        + labs(
            title="Accuracy: repeated runs with the skill vs. without",
            x="",
            y="Accuracy (%)",
        )
        + base_theme()
    )
    _save(plot, out_path)
    return True
