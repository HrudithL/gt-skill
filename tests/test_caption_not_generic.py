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
    # Fix 5 (2026-08-13 review round): this used to assert
    # `points_earned == points_possible`, which `0 == 0` also satisfies --
    # it would still have passed even if the function wrongly zeroed every
    # candidate. Assert the actual expected value instead.
    cand = _cand(["a real caption with enough distinctive words to pass easily", None], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.points_possible == 3
    assert result.points_earned == 3
    assert result.passed is True


def test_all_none_source_notes_treated_as_no_caption():
    cand = _cand([None, None], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.points_earned == 0
    assert result.passed is False


def test_empty_caption_after_tokenization_has_no_real_content_words():
    # Fix 5: covers the `if not cap_words:` branch (a caption that survives
    # citation-stripping and the generic-opener check but tokenizes to zero
    # real content words -- distinct from the >=1-but-<4 vacuity-floor
    # branch below).
    cand = _cand(["1234 56.78 -- 90"], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "no real content words" in result.detail


# --- Fix 1 (2026-08-13 review round): Source:-prefix stripping, not a full-note zero ---

def test_source_prefix_with_real_insight_after_semicolon_passes():
    # Real committed candidate example (creator/towny_growth_trends/repeat_1
    # and repeat_3): a genuine methodology note after the citation used to
    # be wrongly zeroed just because the note opened with "Source:".
    cand = _cand(
        ["Source: Statistics Canada; density calculated as population divided by land area."],
        title="Towny Growth Trends",
        subtitle="Population change by municipality",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


def test_bolded_source_prefix_scores_the_same_as_unbolded():
    # The old regex's `^` anchor was broken by a leading "**", so a bolded
    # citation label passed regardless of substance while an identical
    # unbolded caption was correctly graded. Both must now reach the same
    # verdict, since only the substance after the label should matter.
    bolded = _cand(
        ["**Source:** Statistics Canada. Fastest-growing means highest percent change."],
        title="Towny Growth Trends",
        subtitle="Population change by municipality",
    )
    unbolded = _cand(
        ["Source: Statistics Canada. Fastest-growing means highest percent change."],
        title="Towny Growth Trends",
        subtitle="Population change by municipality",
    )
    bolded_result = check_caption_not_generic(bolded, _TRUTH_WITH_CAPTION, {})
    unbolded_result = check_caption_not_generic(unbolded, _TRUTH_WITH_CAPTION, {})
    assert bolded_result.passed == unbolded_result.passed
    assert bolded_result.points_earned == unbolded_result.points_earned == 3


def test_source_prefix_with_nothing_after_still_fails_as_attribution_only():
    cand = _cand(["Source: Statistics Canada."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "data-source citation" in result.detail


# --- Fix 2 (2026-08-13 review round): vacuity floor + bare-citation detection ---

def test_vacuous_one_word_caption_fails_the_content_word_floor():
    cand = _cand(["Whatever."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "vacuous" in result.detail


def test_two_word_caption_fails_the_content_word_floor():
    cand = _cand(["Bentley outliers."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0


def test_vacuous_but_wordy_caption_fails_the_content_word_floor():
    # Real committed candidate (creator/sp500_monthly_performance/repeat_1):
    # only 3 real content words survive tokenization (daily, prices,
    # volumes) once stopwords, digits, and "S&P"'s single-letter fragments
    # are dropped -- it used to pass on raw overlap/opener checks alone.
    cand = _cand(["Data: S&P 500 daily prices and volumes, 2010–2015."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0


def test_bare_dataset_citation_without_colon_fails_as_attribution_only():
    cand = _cand(["From R islands dataset"], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "data-source citation" in result.detail


def test_bare_source_dataset_citation_without_colon_fails_as_attribution_only():
    cand = _cand(["Source R islands dataset"], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "data-source citation" in result.detail


def test_bare_dataset_citation_with_trailing_insight_keeps_the_insight():
    cand = _cand(
        ["From this dataset, we can see that price and horsepower move in opposite directions for outliers."],
        title="X", subtitle="Y",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


# --- Fix 3 (2026-08-13 review round): broadened openers, per-note/sentence anchoring, stemming ---

def test_generic_opener_verb_dodges_now_caught():
    for verb in ["represents", "lists", "provides", "illustrates", "summarizes", "contains"]:
        cand = _cand([f"This table {verb} the area of islands across the world in detail."], title="X", subtitle="Y")
        result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
        assert result.passed is False, f"expected '{verb}' opener to fail"
        assert result.points_earned == 0


def test_generic_opener_in_second_source_note_is_still_caught():
    # Old check only ever looked at the first note (or the joined-and-
    # anchored-at-start string) -- a generic opener sitting in the second
    # note used to dodge detection entirely.
    cand = _cand(
        ["Note.", "The table shows the area of islands across the world."],
        title="X", subtitle="Y",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "generic" in result.detail


def test_generic_opener_not_at_start_of_joined_text_is_still_caught():
    # A leading filler phrase in the SAME note used to defeat the old
    # single `^`-anchored-at-position-0 check.
    cand = _cand(
        ["Note. The table shows the area of islands across the world."],
        title="X", subtitle="Y",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0


def test_stemmed_plural_counts_as_overlap_for_restatement_check():
    # Real corpus inconsistency (house/islands_sizes/repeat_1 vs. repeat_2):
    # "Size" vs. "Sizes" used to count as different words, so two
    # semantically equivalent captions got opposite verdicts. With suffix
    # stemming, a caption whose only "new" word is a plural of a
    # title/subtitle singular is correctly treated as a restatement.
    cand = _cand(
        ["Sizes are shown in thousands of square kilometers."],
        title="Island Size",
        subtitle="Geographic area in thousands of square kilometers",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert "restatement" in result.detail


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
