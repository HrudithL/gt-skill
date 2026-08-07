#!/usr/bin/env python3
"""Four plots for the `house` skill's full sweep, built from `../metrics.json`
(see `eval-results/_lib.py` for how that file was produced).

Run with the repo's venv active:

    python eval-results/house/plots/make_plots.py

Regenerates `cost.png`, `tokens.png`, `consistency.png`, `comparator_score.png`
next to this script and refreshes `../metrics.json` from the latest
`runs/sweep/*_house_6prompts` sweep first.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
EVAL_RESULTS = SKILL_DIR.parent
SKILL = "house"

sys.path.insert(0, str(EVAL_RESULTS))
import _lib as lib  # noqa: E402

PROMPT_IDS = [p for p, _ in lib.PROMPTS]
PROMPT_LABELS = {
    "gtcars_hp_price": "gtcars\nhp/price",
    "islands_sizes": "islands\nsizes",
    "airquality_monthly_summary": "airquality\nmonthly",
    "gtcars_top10_by_country": "gtcars\ntop10/country",
    "sp500_monthly_performance": "sp500\nmonthly",
    "towny_growth_trends": "towny\ngrowth",
}
REPEATS = ["repeat_1", "repeat_2", "repeat_3"]
REPEAT_COLOR = "#3B6FA0"
BASELINE_COLOR = "#B0413E"


def _load_metrics() -> dict:
    metrics_path = SKILL_DIR / "metrics.json"
    return lib.dump_metrics(SKILL, metrics_path, max_workers=6)


def plot_cost(metrics: dict, out_path: Path) -> None:
    """Grouped bar chart: mean skill cost vs. baseline cost, per prompt."""
    prompts = metrics["prompts"]
    x = np.arange(len(PROMPT_IDS))
    width = 0.35

    skill_means = []
    baseline_vals = []
    for pid in PROMPT_IDS:
        variants = prompts.get(pid, {}).get("variants", {})
        costs = [
            variants[r]["cost_tokens"]["cost_usd"]
            for r in REPEATS
            if variants.get(r) and variants[r]["cost_tokens"]
        ]
        skill_means.append(np.mean(costs) if costs else 0.0)
        b = variants.get("baseline")
        baseline_vals.append(b["cost_tokens"]["cost_usd"] if b and b["cost_tokens"] else 0.0)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width / 2, skill_means, width, label=f"{SKILL} skill (mean of 3 repeats)",
           color=REPEAT_COLOR)
    ax.bar(x + width / 2, baseline_vals, width, label="baseline (no skill)",
           color=BASELINE_COLOR)
    ax.set_xticks(x)
    ax.set_xticklabels([PROMPT_LABELS[p] for p in PROMPT_IDS], fontsize=9)
    ax.set_ylabel("Cost per invocation (USD)")
    ax.set_title(f"{SKILL} skill — cost per prompt vs. baseline")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_tokens(metrics: dict, out_path: Path) -> None:
    """Dot/strip plot: total tokens (input+output+cache) per invocation,
    one row per prompt, 3 skill repeats as dots + baseline as a diamond —
    a different chart family than the cost bar chart, and shows the
    per-prompt spread across repeats at a glance."""
    prompts = metrics["prompts"]
    fig, ax = plt.subplots(figsize=(9, 5.5))

    for i, pid in enumerate(PROMPT_IDS):
        variants = prompts.get(pid, {}).get("variants", {})
        for r in REPEATS:
            ct = variants.get(r, {}).get("cost_tokens") if variants.get(r) else None
            if not ct:
                continue
            total = ct["input_tokens"] + ct["output_tokens"] + ct["cache_creation_tokens"]
            ax.scatter(total, i, color=REPEAT_COLOR, s=70, zorder=3,
                       label="skill repeat" if i == 0 and r == "repeat_1" else None)
        b = variants.get("baseline", {}).get("cost_tokens") if variants.get("baseline") else None
        if b:
            total_b = b["input_tokens"] + b["output_tokens"] + b["cache_creation_tokens"]
            ax.scatter(total_b, i, color=BASELINE_COLOR, s=110, marker="D", zorder=3,
                       label="baseline" if i == 0 else None)

    ax.set_yticks(range(len(PROMPT_IDS)))
    ax.set_yticklabels([PROMPT_LABELS[p].replace("\n", " ") for p in PROMPT_IDS], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Total tokens (input + output + cache-creation)")
    ax.set_title(f"{SKILL} skill — token usage per invocation, by prompt")
    ax.legend(loc="upper right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_consistency(metrics: dict, out_path: Path) -> None:
    """Range ("dumbbell") plot: for each prompt, a line from the lowest to
    the highest comparator score among the 3 skill repeats, with the mean
    marked -- the line's length IS the consistency metric (how much the
    repeats' scores spread from each other), directly on the same score the
    `comparator_score.png` box plot shows, per the user's explicit
    definition: correctness = mean of the repeats, consistency = their
    spread. Baseline's own score is plotted alongside for reference, not
    folded into the spread (a single baseline run has no spread of its
    own)."""
    prompts = metrics["prompts"]
    means, los, his, baseline_vals = [], [], [], []
    for pid in PROMPT_IDS:
        variants = prompts.get(pid, {}).get("variants", {})
        pcts = [
            variants[r]["score"]["pct"]
            for r in REPEATS
            if variants.get(r) and variants[r]["score"] and variants[r]["score"]["pct"] is not None
        ]
        if pcts:
            means.append(np.mean(pcts))
            los.append(min(pcts))
            his.append(max(pcts))
        else:
            means.append(np.nan)
            los.append(np.nan)
            his.append(np.nan)
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        baseline_vals.append(b["pct"] if b and b["pct"] is not None else np.nan)

    y = np.arange(len(PROMPT_IDS))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for i in range(len(PROMPT_IDS)):
        if np.isnan(los[i]):
            continue
        ax.plot([los[i], his[i]], [y[i], y[i]], color=REPEAT_COLOR, lw=3, alpha=0.6,
                zorder=2, solid_capstyle="round")
    ax.scatter(means, y, color=REPEAT_COLOR, s=90, zorder=3,
               label="mean of 3 repeats (correctness)")
    ax.scatter(baseline_vals, y, color=BASELINE_COLOR, marker="X", s=110, zorder=3,
               label="baseline (no skill)")
    for i in range(len(PROMPT_IDS)):
        if np.isnan(los[i]):
            continue
        spread = his[i] - los[i]
        ax.text(his[i] + 1.5, y[i], f"spread={spread:.1f}pp", va="center", fontsize=8,
                color="#444444")

    ax.set_yticks(y)
    ax.set_yticklabels([PROMPT_LABELS[p].replace("\n", " ") for p in PROMPT_IDS], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Comparator total score (%)")
    ax.set_xlim(0, 100)
    ax.set_title(f"{SKILL} skill — consistency: min-mean-max score across 3 repeats")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_comparator_score(metrics: dict, out_path: Path) -> None:
    """Box plot of comparator total-score % across the 3 skill repeats per
    prompt, with the baseline score overlaid as a red X — shows both the
    skill's absolute quality and its margin over no-skill."""
    prompts = metrics["prompts"]
    box_data = []
    baseline_pts = []
    for pid in PROMPT_IDS:
        variants = prompts.get(pid, {}).get("variants", {})
        pcts = [
            variants[r]["score"]["pct"]
            for r in REPEATS
            if variants.get(r) and variants[r]["score"] and variants[r]["score"]["pct"] is not None
        ]
        box_data.append(pcts if pcts else [np.nan])
        b = variants.get("baseline", {}).get("score") if variants.get("baseline") else None
        baseline_pts.append(b["pct"] if b and b["pct"] is not None else np.nan)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    positions = np.arange(1, len(PROMPT_IDS) + 1)
    bp = ax.boxplot(box_data, positions=positions, widths=0.5, patch_artist=True,
                     showmeans=True)
    for patch in bp["boxes"]:
        patch.set_facecolor(REPEAT_COLOR)
        patch.set_alpha(0.5)
    ax.scatter(positions, baseline_pts, color=BASELINE_COLOR, marker="X", s=110,
               zorder=4, label="baseline (no skill)")
    ax.set_xticks(positions)
    ax.set_xticklabels([PROMPT_LABELS[p] for p in PROMPT_IDS], fontsize=9)
    ax.set_ylabel("Comparator total score (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"{SKILL} skill — comparator score: 3 repeats vs. baseline")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    metrics = _load_metrics()
    plot_cost(metrics, HERE / "cost.png")
    plot_tokens(metrics, HERE / "tokens.png")
    plot_consistency(metrics, HERE / "consistency.png")
    plot_comparator_score(metrics, HERE / "comparator_score.png")
    lib.curate_runs(metrics, SKILL_DIR / "samples")
    print(f"wrote 4 plots to {HERE} and curated runs under {SKILL_DIR / 'runs'}")


if __name__ == "__main__":
    main()
