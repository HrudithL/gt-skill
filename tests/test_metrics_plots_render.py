"""Smoke test for the ``metrics_plots`` package.

Renders the frozen ``eval-results-demo/creator`` skill against a temp copy
of the tree (so the checked-in demo tree is not mutated) and asserts that
both plots are produced and metrics.json is (re)written with the same
schema shape the demo tree already ships.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DEMO = REPO / "eval-results-demo"


def test_render_skill_produces_condensed_plots_against_demo(tmp_path):
    if not DEMO.is_dir():
        pytest.skip("eval-results-demo/ not present in this checkout")
    from metrics_plots import render_skill

    dst = tmp_path / "tree"
    shutil.copytree(DEMO / "creator", dst / "creator")
    # Copy only the creator skill; render_skill scopes to one skill.

    result = render_skill(dst, "creator")

    assert result["layout"] == "condensed"
    assert result["plots"]["usage.png"] is True
    assert result["plots"]["tokens_and_cost.png"] is True
    assert result["plots"]["evaluation_score.png"] is True

    plots_dir = dst / "creator" / "plots"
    assert (plots_dir / "usage.png").stat().st_size > 1000
    assert (plots_dir / "tokens_and_cost.png").stat().st_size > 1000
    assert (plots_dir / "evaluation_score.png").stat().st_size > 1000

    metrics = json.loads((dst / "creator" / "metrics.json").read_text())
    assert metrics["skill"] == "creator"
    assert set(metrics["prompts"].keys()) == {
        "gtcars_hp_price",
        "islands_sizes",
        "airquality_monthly_summary",
        "gtcars_top10_by_country",
        "sp500_monthly_performance",
        "towny_growth_trends",
    }
    for entry in metrics["prompts"].values():
        assert entry["difficulty"] in ("easy", "medium", "hard")
        assert "variants" in entry
        # Demo tree has no transcript.json in samples/, so cost_tokens comes
        # from the cached metrics.json fallback (the fresh path returns None).
        v = entry["variants"].get("repeat_1")
        assert v is not None
        assert v["cost_tokens"] is not None


def test_split_layout_triggers_when_a_difficulty_has_more_than_three_prompts():
    """Unit-scope check of the layout policy in render._should_split.

    Constructs a fake per-difficulty grouping and asserts split=True when
    any difficulty exceeds 3.
    """
    from metrics_plots import render

    assert render._should_split({"easy": [], "medium": [], "hard": []}) is False
    assert render._should_split({"easy": ["a", "b"], "medium": ["c", "d"], "hard": ["e", "f"]}) is False
    assert render._should_split({"easy": ["a", "b", "c"], "medium": ["d", "e", "f"], "hard": ["g", "h", "i"]}) is False
    assert render._should_split({"easy": ["a", "b", "c", "d"], "medium": [], "hard": []}) is True
    assert render._should_split({"easy": ["a"], "medium": ["b", "c", "d", "e"], "hard": ["f"]}) is True


def test_every_corpus_prompt_has_a_curated_label():
    """Guardrail — as prompts are added to `prompts/{easy,medium,hard}/`,
    each one needs an entry in `metrics_plots.render.PROMPT_LABELS` so
    plots' x-axis labels stay curated (not autoderived) for the whole
    corpus. If a prompt is added without a label, this test tells you
    which one is missing before it lands in `--evaluate` output."""
    from metrics_plots.render import PROMPT_LABELS

    corpus_ids: set[str] = set()
    for difficulty in ("easy", "medium", "hard"):
        d = REPO / "prompts" / difficulty
        if not d.is_dir():
            continue
        for json_file in d.glob("*.json"):
            corpus_ids.add(json_file.stem)

    missing = corpus_ids - set(PROMPT_LABELS)
    assert not missing, (
        f"prompts missing curated labels in metrics_plots.render.PROMPT_LABELS: "
        f"{sorted(missing)}"
    )


def test_label_shape_is_two_lines_for_each_curated_label():
    """Each curated label is a two-line "dataset\\nfacet" string so the
    grouped bar chart x-axis stays balanced."""
    from metrics_plots.render import PROMPT_LABELS

    for pid, label in PROMPT_LABELS.items():
        assert "\n" in label, f"{pid} label {label!r} is not two-line"
        lines = label.split("\n")
        assert len(lines) == 2, f"{pid} label {label!r} has >2 lines"
        assert all(line.strip() for line in lines), f"{pid} label has an empty line"
