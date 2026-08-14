#!/usr/bin/env python3
"""Adaptive render loop over an eval-results tree.

Called from ``run.py --evaluate`` after all 4 skills have finished (and
directly by the demo tree's regeneration path). Reads the per-skill
``samples/`` tree, computes metrics via ``metrics_plots.lib``, picks a
layout, writes plots and ``metrics.json``.

Layout policy (from the human's spec):

- If every difficulty has ≤3 prompts in this skill's samples, use the
  condensed pair: ``usage.png`` + ``comparator_score.png``.
- If any difficulty has >3 prompts, split into a per-difficulty pair per
  present difficulty: ``usage_<difficulty>.png`` +
  ``comparator_score_<difficulty>.png``.

Anything else in ``<skill>/plots/`` is left alone — the previous condensed
plots aren't scrubbed on a split render (or vice versa) because a
subsequent condensed render would rewrite them anyway, and the alternative
(force-clean the plots dir every time) makes ``git status`` noisier than
it needs to be. ``run.py --evaluate`` clears the whole ``eval-results/``
tree before it starts, so this concern only surfaces on ad-hoc calls into
``render_skill`` against a hand-built tree.
"""

from __future__ import annotations

from pathlib import Path

from . import lib
from . import plots

# The four skills that get built out under an eval-results tree. Matches
# runner.spec.SKILL_LABELS (not imported to avoid a hard dep on that module
# just for a static string list).
SKILLS = ("creator", "house", "prose", "scripts")

# Known corpus-prompt display labels, curated for two-line balance in the
# grouped bar chart's x-axis. Unknown prompt ids get an auto-derived label
# ("word1 word2\nword3 word4" or similar) so a fresh prompt added under
# prompts/<d>/ still renders — the auto label is passable, just less
# tuned. Extend this dict as the corpus grows if the auto label ever reads
# awkwardly.
PROMPT_LABELS: dict[str, str] = {
    # easy tier (8 prompts)
    "airquality_hottest_days": "airquality\nhottest days",
    "countrypops_most_populous_2021": "countrypops\ntop 2021",
    "films_longest_runtimes": "films\nlongest",
    "gtcars_hp_price": "gtcars\nhp/price",
    "gtcars_most_efficient": "gtcars\nefficient",
    "islands_sizes": "islands\nsizes",
    "metro_busiest_stations": "metro\nbusiest",
    "pizzaplace_top_pizzas": "pizzaplace\ntop",
    # medium tier (8 prompts)
    "airquality_monthly_summary": "airquality\nmonthly",
    "airquality_wind_regime": "airquality\nwind",
    "countrypops_fastest_growing": "countrypops\ngrowth",
    "films_prolific_directors": "films\ndirectors",
    "gibraltar_weekly_summary": "gibraltar\nweekly",
    "gtcars_top10_by_country": "gtcars\ntop10/country",
    "pizzaplace_category_performance": "pizzaplace\ncategory",
    "towny_top10_by_population": "towny\ntop10",
    # hard tier (8 prompts)
    "countrypops_decade_growth": "countrypops\ndecade",
    "films_by_decade": "films\nby decade",
    "gtcars_country_matrix": "gtcars\ncountry matrix",
    "pizzaplace_daypart_by_category": "pizzaplace\ndaypart",
    "sp500_monthly_performance": "sp500\nmonthly",
    "sp500_yearly_summary": "sp500\nyearly",
    "towny_density_quintiles": "towny\ndensity",
    "towny_growth_trends": "towny\ngrowth",
}


def _label_for(prompt_id: str) -> str:
    if prompt_id in PROMPT_LABELS:
        return PROMPT_LABELS[prompt_id]
    parts = prompt_id.split("_")
    if len(parts) <= 1:
        return prompt_id
    # Split roughly in half — first N//2 words on top line, rest on bottom.
    mid = len(parts) // 2 or 1
    return " ".join(parts[:mid]) + "\n" + " ".join(parts[mid:])


def _group_prompts_by_difficulty(metrics: dict) -> dict[str, list[str]]:
    """Return ``{difficulty: [prompt_id, ...]}`` in the difficulty order
    easy → medium → hard."""
    out: dict[str, list[str]] = {"easy": [], "medium": [], "hard": []}
    for pid, entry in metrics.get("prompts", {}).items():
        d = entry.get("difficulty")
        if d in out:
            out[d].append(pid)
    for d in out:
        out[d].sort()
    return out


def _should_split(per_difficulty: dict[str, list[str]]) -> bool:
    """Threshold from the human's spec: if any difficulty has >3 prompts,
    split into per-difficulty plots."""
    return any(len(v) > 3 for v in per_difficulty.values())


def render_skill(root: Path, skill: str) -> dict:
    """Regenerate ``root/<skill>/metrics.json`` and ``root/<skill>/plots/``
    from ``root/<skill>/samples/``. Returns a small summary dict for the
    caller (used by ``--evaluate`` to log which plots were written)."""
    root = Path(root)
    skill_dir = root / skill
    plots_dir = skill_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    metrics = lib.collect_metrics(root, skill)
    lib.dump_metrics(root, skill, metrics)

    per_diff = _group_prompts_by_difficulty(metrics)
    split = _should_split(per_diff)

    written: dict[str, bool] = {}
    if split:
        for difficulty, prompt_ids in per_diff.items():
            if not prompt_ids:
                continue
            labels = {pid: _label_for(pid) for pid in prompt_ids}
            written[f"usage_{difficulty}.png"] = plots.plot_usage(
                metrics, prompt_ids, labels, plots_dir / f"usage_{difficulty}.png"
            )
            written[f"comparator_score_{difficulty}.png"] = plots.plot_comparator_score(
                metrics, prompt_ids, labels, plots_dir / f"comparator_score_{difficulty}.png"
            )
    else:
        prompt_ids = [pid for ids in per_diff.values() for pid in ids]
        labels = {pid: _label_for(pid) for pid in prompt_ids}
        if prompt_ids:
            written["usage.png"] = plots.plot_usage(
                metrics, prompt_ids, labels, plots_dir / "usage.png"
            )
            written["comparator_score.png"] = plots.plot_comparator_score(
                metrics, prompt_ids, labels, plots_dir / "comparator_score.png"
            )

    return {
        "skill": skill,
        "layout": "per_difficulty" if split else "condensed",
        "plots": written,
        "metrics_path": str(skill_dir / "metrics.json"),
    }


def render_all(root: Path) -> list[dict]:
    """Call ``render_skill`` for every known skill directory found under
    ``root``. Skills without a ``samples/`` subdirectory are skipped
    (that's normal when a partial ``--evaluate`` run failed one skill —
    the others still get their plots). After every skill is rendered,
    writes a deterministic ``<root>/SUMMARY.md`` ranking the skills."""
    root = Path(root)
    out: list[dict] = []
    for skill in SKILLS:
        if not (root / skill / "samples").is_dir():
            continue
        out.append(render_skill(root, skill))
    from . import summary
    summary.write_summary(root)
    return out
