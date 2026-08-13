#!/usr/bin/env python3
"""Tests for `runner.comparator.check_caption_not_generic`, the lenient
replacement (2026-08-13) for the old exact-keyword `check_caption_keywords`
(see that function's removal and this one's docstring in comparator.py for
the full rationale). The old mechanism required a candidate's caption to
contain the ground truth's OWN authored words verbatim and failed a uniform
~82-83% of real candidates across every skill -- never discriminating skill
quality. This check instead only fails a caption that's a near-verbatim
restatement of the title/subtitle or a generic "this table shows..."
template; everything else passes.

Includes the None-source-note regression this replaces from
`test_caption_keywords_none_source_note.py` (real-sweep finding,
2026-08-13): `source_note_texts` entries are `str | None`, and joining them
without dropping `None` used to raise `TypeError` on an otherwise-valid
candidate.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.comparator import check_caption_not_generic  # noqa: E402


def _truth(source_note_texts, title="Islands of the World, by Size", subtitle="Land area in thousands of square miles"):
    return {"tier1": {"source_note_texts": source_note_texts, "title_text": title, "subtitle_text": subtitle}}


def _cand(source_note_texts, title, subtitle):
    return {"tier1": {"source_note_texts": source_note_texts, "title_text": title, "subtitle_text": subtitle}}


_TRUTH_WITH_CAPTION = _truth(["Ordered largest to smallest by land area; landmass includes continents."])


def test_distinctive_caption_passes():
    cand = _cand(
        ["Price and horsepower don't move together: the Bentley costs more than the Corvette despite fewer horsepower."],
        title="GT Cars: Horsepower and Price",
        subtitle="All 47 makes and models, sorted from highest to lowest MSRP",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == result.points_possible == 3


def test_near_verbatim_restatement_of_subtitle_fails():
    cand = _cand(
        ["Island sizes are expressed in thousands of square kilometers."],
        title="Island Sizes",
        subtitle="Geographic area in thousands of square kilometers",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "restatement" in result.detail


def test_generic_template_opener_fails():
    cand = _cand(
        ["Data shows the area of islands across the world."],
        title="Islands by Size",
        subtitle="Land area in thousands of square kilometers",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "generic" in result.detail


def test_missing_caption_when_truth_expects_one_fails():
    cand = _cand([], title="GT Cars Specifications", subtitle="Horsepower and Price")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "no caption" in result.detail


def test_attribution_only_caption_fails_like_a_missing_one():
    # Real candidate example (prose/islands_sizes/repeat_1): the only source
    # note is a bare data-source citation, no accompanying insight sentence.
    cand = _cand(["Source: World island size data"], title="Island Sizes", subtitle="Land area in thousands of square miles")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "data-source citation" in result.detail


def test_ground_truth_with_no_caption_is_na():
    truth = _truth([])
    cand = _cand(["Anything at all."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, truth, {})
    assert result.points_possible == 0
    assert result.points_earned == 0
    assert result.passed is True


def test_none_source_note_does_not_crash():
    cand = _cand(["a real caption with enough distinctive words to pass easily", None], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.points_earned == result.points_possible


def test_all_none_source_notes_treated_as_no_caption():
    cand = _cand([None, None], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.points_earned == 0
    assert result.passed is False


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
