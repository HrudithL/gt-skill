#!/usr/bin/env python3
"""Regression tests for `runner.execution_tier.normalize_id` becoming
date-format-aware for row/group identity comparison.

Bug this fixes: `normalize_id` used to be plain `str(x).strip().casefold()`,
so semantically-identical date labels written in different (equally
reasonable) string formats -- e.g. "Jan 2010" (`prompts/hard/ground_truth/
sp500_monthly_performance.py`'s own `%b %Y` format) vs "2010-01" (a real
candidate's `%Y-%m` format, or the output of `.dt.to_period("M")`) vs
"January 2010" -- compared as completely unrelated strings. Since
`normalize_id` is the single choke point used by `row_set_identity`,
`_row_key`, and every comparator row/group-value match, that zeroed out row
matching and cascaded into failing every downstream per-row value check even
when a candidate's actual numbers were correct. The prompt never specifies
which date format to use, so both formats are legitimate.

`normalize_id` now tries a strict, explicit whitelist of `datetime.strptime`
formats (never a fuzzy/liberal parser, which would misparse ordinary
non-date identifiers like car names or town names as dates) against the
WHOLE trimmed string, and only falls back to the old casefold-strip
behavior when none match.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.execution_tier import _MISSING_ID, normalize_id  # noqa: E402


# ---------------------------------------------------------------------------
# The core bug: equivalent dates in different formats must now match.
# ---------------------------------------------------------------------------


def test_month_year_formats_all_normalize_equal():
    assert normalize_id("Jan 2010") == normalize_id("2010-01") == normalize_id("January 2010")


def test_month_year_formats_also_match_slash_format():
    assert normalize_id("01/2010") == normalize_id("Jan 2010")


def test_day_granularity_formats_normalize_equal():
    assert (
        normalize_id("2010-01-15")
        == normalize_id("01/15/2010")
        == normalize_id("Jan 15, 2010")
        == normalize_id("January 15, 2010")
    )


# ---------------------------------------------------------------------------
# Non-date identifiers: completely unaffected by the new date parsing.
# ---------------------------------------------------------------------------


def test_non_date_identifiers_use_old_casefold_strip_behavior():
    assert normalize_id("Roosevelt") == "roosevelt"
    assert normalize_id("aventador") == "aventador"
    assert normalize_id("ferrari laferrari") == "ferrari laferrari"


def test_whitespace_and_case_still_normalize_like_before_for_non_dates():
    assert normalize_id("  Foo  ") == "foo"
    assert normalize_id("FOO") == "foo"


# ---------------------------------------------------------------------------
# Distinct dates must not collide with each other.
# ---------------------------------------------------------------------------


def test_different_months_do_not_collide():
    assert normalize_id("Jan 2010") != normalize_id("Feb 2010")


def test_different_years_do_not_collide():
    assert normalize_id("Jan 2010") != normalize_id("Jan 2011")


def test_month_granularity_does_not_collide_with_day_granularity_same_month():
    # A bare month ("Jan 2010") and a specific day within that same month
    # ("2010-01-15") must NOT be treated as the same identity -- a stub
    # author who wrote a bare month presumably meant the whole month, not
    # one specific day of it.
    assert normalize_id("Jan 2010") != normalize_id("2010-01-15")


def test_month_and_day_granularity_keys_have_visibly_different_shapes():
    # Belt-and-suspenders on the "keep them from colliding" requirement:
    # the two granularities must use distinguishable internal key shapes
    # (different prefix / length), not just happen to differ by luck.
    month_key = normalize_id("Jan 2010")
    day_key = normalize_id("2010-01-15")
    assert month_key != day_key
    assert not month_key.startswith("__date_ymd__")
    assert day_key.startswith("__date_ymd__")


# ---------------------------------------------------------------------------
# `None` handling: unchanged.
# ---------------------------------------------------------------------------


def test_none_still_maps_to_missing_id_sentinel():
    assert normalize_id(None) == _MISSING_ID


def test_missing_id_sentinel_does_not_collide_with_literal_none_text():
    assert normalize_id(None) != normalize_id("None")
