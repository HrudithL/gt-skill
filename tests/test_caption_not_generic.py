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

Round-4 review (2026-08-13) fixed a recurring bug shape across 3 findings:
several checks treated a PREFIX pattern (a citation label, a generic
opener) as a verdict on the WHOLE caption instead of stripping the prefix
and grading whatever remains. Tests below marked "round-4" cover:
  - a generic opener with substantive content after it now passes instead
    of zeroing the whole caption (the prefix is stripped, not the
    sentence/caption);
  - a multi-sentence caption with one generic-sounding sentence and real
    content elsewhere now passes;
  - the citation-clause terminator is now boundary-aware (must be
    followed by whitespace/end-of-string) so a period embedded in a
    filename/URL doesn't truncate the clause at the wrong point and leak
    a meaningless fragment through as "real" content;
  - en-dash is now a recognized citation-clause terminator alongside
    em-dash/semicolon, so otherwise-identical prose separated by an
    en-dash reaches the same verdict as one separated by a semicolon or
    em-dash;
  - the content-word filter/floor/stemming-order were loosened/fixed so
    short-but-real insights with domain abbreviations (HP, MSRP, USD)
    aren't zeroed just for being terse.
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


def test_pure_generic_template_with_nothing_after_it_fails():
    # round-4: only fails on "generic" grounds when NOTHING distinctive is
    # left after the opener prefix is stripped -- this caption's entire
    # content IS the opener, so nothing survives the strip.
    cand = _cand(["The table shows."], title="Islands by Size", subtitle="Land area in thousands of square kilometers")
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


def test_short_but_real_metadata_caption_passes_after_floor_recalibration():
    # Real committed candidate (creator/sp500_monthly_performance/repeat_1):
    # 3 real content words survive tokenization (daily, price, volume) once
    # stopwords, digits, and "S&P"'s single-letter fragments are dropped.
    # Prior round set the floor at 4 specifically to zero this caption; the
    # round-4 review found the floor itself was zeroing genuinely short-but-
    # real insights ("Price is the MSRP in USD." -- also exactly 3 content
    # words -- is a real committed candidate that should pass), and lowered
    # it to 3. By that same, now-consistently-applied bar, this caption
    # (frequency: daily; columns: price/volume; range: 2010-2015) also
    # carries real information and correctly passes.
    cand = _cand(["Data: S&P 500 daily prices and volumes, 2010–2015."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


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

def test_generic_opener_verbs_are_still_recognized_and_their_prefix_stripped():
    # round-4: the opener regex still needs to recognize every one of these
    # verbs -- what changed is what happens on a match. Verify directly on
    # the stripping helper that each verb's prefix (not the whole sentence)
    # is what gets removed, leaving the rest of the sentence intact.
    from runner.comparator import _strip_generic_opener_sentences

    for verb in ["shows", "displays", "presents", "contains", "summarizes", "illustrates", "represents", "lists", "provides"]:
        sentence = f"This table {verb} the area of islands across the world."
        fragments = _strip_generic_opener_sentences([sentence])
        assert fragments == ["the area of islands across the world"], (
            f"expected '{verb}' opener prefix to be stripped, leaving the rest of the sentence; got {fragments}"
        )


# --- round-4 (2026-08-13): Bugs A+B, structural strip-and-grade fix for the ---
# --- generic-opener check (a prefix match no longer vetoes the WHOLE caption) ---

def test_generic_opener_with_substantive_content_after_it_now_passes():
    # Bug A: verified with the ground truth's own airquality caption --
    # prepending "The data shows " dropped a 3/3 caption to 0/3 even though
    # everything after the prefix was exactly as substantive as before.
    # Fixed: strip only the matched prefix and grade what's left.
    cand = _cand(
        [
            "The data shows air quality readings by month across three monitoring "
            "stations, highlighting a winter smog spike in January and February."
        ],
        title="Air Quality Monitoring", subtitle="Monthly readings, three stations",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


def test_multi_sentence_caption_with_one_generic_sentence_now_passes():
    # Bug B: verified -- this exact caption used to score 0/3 solely
    # because of the middle sentence ("The table shows all 47 models."),
    # even though the sentences before and after carry real content.
    # Deleting only the middle sentence used to flip the verdict to 3/3;
    # now the middle sentence is stripped down (contributing nothing) and
    # the caption is graded on what's left everywhere else, so the verdict
    # no longer depends on whether that one sentence happens to be there.
    cand = _cand(
        [
            "Bentley costs more than the Corvette despite fewer horsepower. "
            "The table shows all 47 models. Prices are MSRP in USD."
        ],
        title="GT Cars: Horsepower and Price",
        subtitle="All 47 makes and models, sorted from highest to lowest MSRP",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


def test_generic_opener_with_nothing_after_it_in_second_note_still_fails():
    # A generic-opener sentence with nothing distinctive after the prefix,
    # sitting in the SECOND note, is still detected regardless of position
    # (the original point of this regression test) -- but now it's
    # stripped down to nothing rather than veto-ing the whole caption. Its
    # own words ("table"/"shows") don't leak into the content-word count.
    # Combined with the first note's own single word, there still isn't
    # enough real content anywhere, so the caption correctly fails -- just
    # via the vacuity floor, not a generic-opener veto.
    cand = _cand(["Note.", "The table shows."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "table" not in result.detail
    assert "note" in result.detail


def test_generic_opener_with_nothing_after_it_mid_note_still_fails():
    # A leading filler phrase in the SAME note, before the generic-opener
    # sentence, used to defeat the old single `^`-anchored-at-position-0
    # check. Detection still works regardless of position; the opener
    # sentence still contributes nothing once its prefix is stripped.
    cand = _cand(["Note. The table shows."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "table" not in result.detail
    assert "note" in result.detail


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


# --- round-4 (2026-08-13): Bug C, boundary-aware citation-clause termination ---

def test_citation_with_internal_period_in_filename_still_fails_as_attribution_only():
    # Bug C: the old regex took the FIRST "."/";"/"-" occurring anywhere
    # after the citation label -- including a period embedded INSIDE a
    # filename ("airquality.csv") -- truncating the clause at the wrong
    # point and leaving a meaningless fragment ("csv, R datasets package,
    # May-September observations") that then got graded as if it were real
    # caption content: a false PASS on a caption that's actually pure
    # attribution. Fixed: the terminator must be followed by whitespace or
    # end-of-string, so the mid-filename period is skipped and (since
    # there's no other real sentence boundary here) the whole thing is
    # correctly recognized as one long citation clause with nothing after it.
    cand = _cand(
        ["Source: airquality.csv, R datasets package, May–September observations"],
        title="X", subtitle="Y",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert result.points_earned == 0
    assert "data-source citation" in result.detail


def test_en_dash_and_em_dash_citation_separators_verdict_agree():
    # Bug C: identical prose reached opposite verdicts depending on
    # whether the separator after the citation label was ";"/em-dash
    # (recognized terminators, so the clause ended in the right place and
    # the insight sentence after it was graded and passed) or an en-dash
    # (not recognized, so the terminator search ran past it to the next
    # sentence-ending period -- at the very end of the string -- consuming
    # the insight sentence into the "citation clause" and leaving nothing).
    # This corpus uses en-dashes pervasively for ranges/separators
    # ("1996–2021"), so the inconsistency mattered. En-dash is now a
    # recognized terminator alongside em-dash and semicolon.
    semicolon = _cand(["Source: Statistics Canada; fastest-growing means highest percent change."], title="X", subtitle="Y")
    em_dash = _cand(["Source: Statistics Canada— fastest-growing means highest percent change."], title="X", subtitle="Y")
    en_dash = _cand(["Source: Statistics Canada– fastest-growing means highest percent change."], title="X", subtitle="Y")

    semicolon_result = check_caption_not_generic(semicolon, _TRUTH_WITH_CAPTION, {})
    em_dash_result = check_caption_not_generic(em_dash, _TRUTH_WITH_CAPTION, {})
    en_dash_result = check_caption_not_generic(en_dash, _TRUTH_WITH_CAPTION, {})

    assert semicolon_result.passed is True
    assert em_dash_result.passed == en_dash_result.passed == semicolon_result.passed
    assert em_dash_result.points_earned == en_dash_result.points_earned == semicolon_result.points_earned == 3


def test_bare_hyphen_is_deliberately_not_a_citation_terminator():
    # A bare hyphen is far more often part of a compound word or a numeric
    # range than an actual clause boundary, so it's deliberately NOT
    # recognized (unlike en-dash/em-dash/semicolon above) -- the clause
    # search runs past it to the final period at the end of the string,
    # consuming the whole thing and correctly still failing as
    # attribution-only, not a false pass on a truncated fragment.
    cand = _cand(["Source: Statistics Canada- fastest-growing means highest percent change."], title="X", subtitle="Y")
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is False
    assert "data-source citation" in result.detail


# --- round-4 (2026-08-13): Bug D, word-length filter + stemming/stopword order ---

def test_short_caption_with_domain_abbreviations_now_passes():
    # Bug D: "HP" (2 characters) used to be dropped by the `len(w) > 2`
    # filter, leaving only 3 counted words (msrp/move/together) -- one
    # short of the (then-4) floor. Loosening the filter to `len(w) >= 2`
    # lets short domain abbreviations like "HP" count toward the floor.
    cand = _cand(
        ["HP and MSRP do not move together."],
        title="GT Cars: Horsepower and Price",
        subtitle="All 47 makes and models, sorted from highest to lowest MSRP",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


def test_short_real_insight_without_short_tokens_passes_after_floor_recalibration():
    # Bug D: a real committed candidate (house/gtcars_hp_price/repeat_3)
    # that's a genuine, substantive caption but tokenizes to exactly 3
    # content words (corvette/outgun/bentley) -- no word-length-filter
    # tweak can raise this count, since none of its words are short. The
    # floor itself (4 -> 3, see `_CAPTION_MIN_CONTENT_WORDS`) is what
    # stops this from being zeroed for brevity alone.
    cand = _cand(
        ["The Corvette outguns the Bentley."],
        title="GT Cars: Horsepower and Price",
        subtitle="All 47 makes and models, sorted from highest to lowest MSRP",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


def test_price_is_the_msrp_in_usd_real_candidate_passes():
    # Real committed candidate (house/gtcars_hp_price/repeat_3): exactly 3
    # content words (price/msrp/usd), all length >= 3, so this is purely a
    # floor-recalibration fix, not a word-filter fix.
    cand = _cand(
        ["Price is the MSRP in USD."],
        title="GT Cars: Horsepower and Price",
        subtitle="All 47 makes and models, sorted from highest to lowest MSRP",
    )
    result = check_caption_not_generic(cand, _TRUTH_WITH_CAPTION, {})
    assert result.passed is True
    assert result.points_earned == 3


def test_stopword_plural_no_longer_leaks_through_as_content_word():
    # Bug D: the stopword filter used to run BEFORE stemming, so a plural
    # of a stopword (e.g. "displays", plural of the stopword "display")
    # never matched the singular stopword and leaked through as a counted
    # content word. Stemming first, then filtering the stemmed form, fixes
    # this regardless of which surface form (singular or plural) is used.
    from runner.comparator import _caption_content_words

    assert "display" not in _caption_content_words("The dashboard displays live totals for review.")
    assert "display" not in _caption_content_words("The dashboard display is live for review.")


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
