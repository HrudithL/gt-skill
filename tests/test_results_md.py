"""Tests for ``metrics_plots.write_results`` — the per-prompt per-run drill-down
markdown writer.
"""

from __future__ import annotations

import json
from pathlib import Path


def _fake_metrics(prompt_scores: dict, difficulty_map: dict) -> dict:
    """Build a metrics.json shape given ``{prompt_id: {variant: pct_or_none}}``
    plus a ``{prompt_id: difficulty}`` map. Costs are zeroed out (write_results
    only reads scores)."""
    prompts: dict = {}
    for pid, variants in prompt_scores.items():
        prompts[pid] = {
            "difficulty": difficulty_map[pid],
            "variants": {
                v: (
                    {
                        "score": {"pct": pct},
                        "cost_tokens": {"cost_usd": 0.0, "input_tokens": 0,
                                        "output_tokens": 0, "cache_creation_tokens": 0},
                    }
                    if pct is not None
                    else {"score": None, "cost_tokens": None}
                )
                for v, pct in variants.items()
            },
        }
    return {"skill": "test", "prompts": prompts}


def test_write_results_deterministic_and_sorted(tmp_path):
    from metrics_plots.results import write_results

    diffs = {"a_easy": "easy", "b_easy": "easy", "c_medium": "medium", "d_hard": "hard"}
    scores = {
        "a_easy":   {"repeat_1": 90.0, "repeat_2": 80.0, "repeat_3": 70.0, "baseline": 20.0},
        "b_easy":   {"repeat_1": 60.0, "repeat_2": 60.0, "repeat_3": 60.0, "baseline": 30.0},
        "c_medium": {"repeat_1": 85.0, "repeat_2": 85.0, "repeat_3": 85.0, "baseline": 25.0},
        "d_hard":   {"repeat_1": 40.0, "repeat_2": 50.0, "repeat_3": 60.0, "baseline": 15.0},
    }
    for skill in ("creator", "house"):
        d = tmp_path / skill
        d.mkdir()
        (d / "metrics.json").write_text(json.dumps(_fake_metrics(scores, diffs)))

    first = write_results(tmp_path).read_text()
    second = write_results(tmp_path).read_text()
    assert first == second, "RESULTS.md must be byte-identical on re-render"

    # Section order: creator before house.
    assert first.index("## `creator`") < first.index("## `house`")

    # Prompt row order: easy alphabetical, then medium, then hard.
    creator_section = first.split("## `creator`")[1].split("## `house`")[0]
    row_order = [line for line in creator_section.splitlines() if line.startswith("| `")]
    assert row_order[0].startswith("| `a_easy`"), row_order[0]
    assert row_order[1].startswith("| `b_easy`"), row_order[1]
    assert row_order[2].startswith("| `c_medium`"), row_order[2]
    assert row_order[3].startswith("| `d_hard`"), row_order[3]

    # Numeric formatting: percentages with one decimal + %, lift with sign.
    row_a = row_order[0]
    assert "90.0%" in row_a
    assert "80.0%" in row_a
    assert "70.0%" in row_a
    assert "80.0%" in row_a  # mean of 90/80/70
    assert "20.0%" in row_a  # baseline
    assert "+60.0" in row_a  # lift (mean 80 - baseline 20)


def test_write_results_handles_missing_scores(tmp_path):
    from metrics_plots.results import write_results

    m = _fake_metrics(
        {"only_one": {"repeat_1": 42.0, "repeat_2": None, "repeat_3": None, "baseline": None}},
        {"only_one": "easy"},
    )
    d = tmp_path / "creator"
    d.mkdir()
    (d / "metrics.json").write_text(json.dumps(m))

    text = write_results(tmp_path).read_text()
    # Missing runs show as em-dash.
    assert "42.0%" in text
    assert "—" in text  # covers repeat_2, repeat_3, baseline, lift


def test_write_results_handles_no_metrics(tmp_path):
    from metrics_plots.results import write_results

    p = write_results(tmp_path)
    text = p.read_text()
    assert "# Per-prompt run results" in text
    assert "No scored skills" in text
