"""Tests for the deterministic SUMMARY.md writer in ``metrics_plots``."""

from __future__ import annotations

import json
from pathlib import Path


def _fake_metrics(scores_ws: list[float], scores_bl: list[float],
                  costs_ws: list[float], costs_bl: list[float]) -> dict:
    """Hand-build a metrics.json shape with as many with-skill (``repeat_1``,
    ``repeat_2``, ...) variants as the two score/cost lists demand — one
    variant per pair of matching entries — plus one ``baseline`` variant
    per prompt when the baseline lists are non-empty."""
    # Distribute across pseudo-prompts so each prompt has one repeat, keeping
    # the test's assertions simple. Real metrics.json has more per prompt;
    # compute_skill_stats doesn't care about the grouping.
    prompts: dict = {}
    for i, (pct, cost) in enumerate(zip(scores_ws, costs_ws)):
        prompts[f"p_ws_{i}"] = {
            "difficulty": "easy",
            "variants": {
                "repeat_1": {
                    "score": {"pct": pct},
                    "cost_tokens": {"cost_usd": cost, "input_tokens": 0,
                                    "output_tokens": 0, "cache_creation_tokens": 0},
                },
            },
        }
    for i, (pct, cost) in enumerate(zip(scores_bl, costs_bl)):
        prompts[f"p_bl_{i}"] = {
            "difficulty": "easy",
            "variants": {
                "baseline": {
                    "score": {"pct": pct},
                    "cost_tokens": {"cost_usd": cost, "input_tokens": 0,
                                    "output_tokens": 0, "cache_creation_tokens": 0},
                },
            },
        }
    return {"skill": "test", "prompts": prompts}


def test_compute_skill_stats_averages():
    from metrics_plots.summary import compute_skill_stats

    m = _fake_metrics([80, 90], [70, 60], [0.10, 0.20], [0.05, 0.07])
    s = compute_skill_stats(m)
    assert s["mean_score_with_skill"] == 85.0
    assert s["mean_score_baseline"] == 65.0
    assert s["mean_lift"] == 20.0
    assert abs(s["mean_cost_with_skill"] - 0.15) < 1e-9
    assert abs(s["mean_cost_baseline"] - 0.06) < 1e-9


def test_compute_skill_stats_handles_empty_variants():
    from metrics_plots.summary import compute_skill_stats

    s = compute_skill_stats({"skill": "test", "prompts": {}})
    assert s["mean_score_with_skill"] is None
    assert s["mean_score_baseline"] is None
    assert s["mean_lift"] is None
    assert s["mean_cost_with_skill"] is None
    assert s["mean_cost_baseline"] is None
    assert s["invocation_count"] == 0


def test_write_summary_produces_deterministic_output(tmp_path):
    from metrics_plots.summary import write_summary

    for skill, (ws, bl, cws, cbl) in {
        "creator": ([70, 80], [65, 70], [0.09, 0.10], [0.07, 0.08]),
        "house":   ([85, 90], [40, 50], [0.12, 0.14], [0.08, 0.09]),
        "prose":   ([88, 92], [30, 35], [0.15, 0.17], [0.07, 0.08]),
        "scripts": ([87, 89], [20, 25], [0.18, 0.19], [0.06, 0.07]),
    }.items():
        d = tmp_path / skill
        d.mkdir()
        (d / "metrics.json").write_text(json.dumps(_fake_metrics(ws, bl, cws, cbl)))

    first = write_summary(tmp_path).read_text()
    second = write_summary(tmp_path).read_text()
    assert first == second, "SUMMARY.md must be byte-identical on re-render"

    # Table shape: 4 skill rows in alphabetical order
    assert "| creator |" in first
    assert "| house |" in first
    assert "| prose |" in first
    assert "| scripts |" in first
    # creator row precedes scripts row
    assert first.index("| creator |") < first.index("| scripts |")

    # At-a-glance section: 4 bulleted lines
    at_a_glance = first.split("## At a glance")[1].split("## Leaders")[0]
    assert at_a_glance.count("\n- **") == 4

    # Leaders: prose leads on score (90.0%), scripts on lift (+65.5),
    # creator on cost ($0.0950).
    leaders = first.split("## Leaders")[1]
    assert "Highest average score:** `prose`" in leaders
    assert "Highest lift over baseline:** `scripts`" in leaders
    assert "Lowest cost per invocation:** `creator`" in leaders


def test_write_summary_handles_missing_metrics(tmp_path):
    """If no skill has a metrics.json, the writer produces a summary that
    reports the empty state without erroring."""
    from metrics_plots.summary import write_summary

    p = write_summary(tmp_path)
    text = p.read_text()
    assert "# Skill evaluation summary" in text
    assert "No scored variants" in text or "| ---" in text
