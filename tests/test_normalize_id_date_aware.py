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
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.execution_tier import (  # noqa: E402
    _DATE_YM_PREFIX,
    _DATE_YMD_PREFIX,
    _DATE_YMDHMS_PREFIX,
    _MISSING_ID,
    normalize_id,
)


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
    assert not month_key.startswith(_DATE_YMD_PREFIX)
    assert day_key.startswith(_DATE_YMD_PREFIX)
    assert month_key.startswith(_DATE_YM_PREFIX)


# ---------------------------------------------------------------------------
# `None` handling: unchanged.
# ---------------------------------------------------------------------------


def test_none_still_maps_to_missing_id_sentinel():
    assert normalize_id(None) == _MISSING_ID


def test_missing_id_sentinel_does_not_collide_with_literal_none_text():
    assert normalize_id(None) != normalize_id("None")


# ---------------------------------------------------------------------------
# pandas/datetime default stringification (round-4 review finding #1).
# ---------------------------------------------------------------------------


def test_pandas_timestamp_default_str_form_is_parsed_as_a_date():
    # `str(pd.Timestamp("2010-01-15"))` / `str(datetime.datetime(2010, 1, 15))`
    # both render as "2010-01-15 00:00:00" -- the single most common way a
    # plain (non-Period) pandas datetime column stringifies. Avoid a hard
    # pandas dependency in this test file; the stub string is what actually
    # reaches `normalize_id` regardless of which object produced it. This
    # must still be recognized as a date at all (not fall back to plain
    # casefold) -- see the granularity tests below for whether it collides
    # with a bare "2010-01-15" (round-5 review finding: it must NOT).
    assert normalize_id(str(datetime(2010, 1, 15))) == normalize_id("2010-01-15 00:00:00")
    assert normalize_id("2010-01-15 00:00:00").startswith(_DATE_YMDHMS_PREFIX)


# ---------------------------------------------------------------------------
# Timestamp-vs-date granularity separation (round-5 review finding #2): a
# full "%Y-%m-%d %H:%M:%S" timestamp must NOT collapse into the same identity
# as a bare "%Y-%m-%d" date, nor may two different timestamps on the same
# calendar day collapse into each other. The previous round normalized both
# to the same `_DATE_YMD_PREFIX` key, discarding time-of-day entirely --
# contradicting this same function's own month-vs-day granularity
# separation just above.
# ---------------------------------------------------------------------------


def test_timestamp_does_not_collide_with_bare_date_same_day():
    assert normalize_id("2010-01-15") != normalize_id("2010-01-15 13:45:00")


def test_midnight_timestamp_does_not_collide_with_bare_date():
    # Even midnight (the "no time information lost" case at first glance)
    # must stay distinct from the bare date -- the two formats represent
    # different claims (a specific instant vs. the whole day) even when the
    # instant happens to be midnight.
    assert normalize_id("2010-01-15") != normalize_id("2010-01-15 00:00:00")


def test_different_timestamps_same_day_do_not_collide():
    assert normalize_id("2010-01-15 00:00:00") != normalize_id("2010-01-15 13:45:00")


def test_timestamp_and_day_granularity_keys_have_visibly_different_shapes():
    day_key = normalize_id("2010-01-15")
    ts_key = normalize_id("2010-01-15 13:45:00")
    assert day_key != ts_key
    assert day_key.startswith(_DATE_YMD_PREFIX)
    assert not day_key.startswith(_DATE_YMDHMS_PREFIX)
    assert ts_key.startswith(_DATE_YMDHMS_PREFIX)


# ---------------------------------------------------------------------------
# Case-insensitive round-trip guard (round-5 review finding #1, regression):
# `strptime`'s `%b`/`%B` accept month names case-insensitively, but
# `strftime` always re-renders its own canonical capitalization, so a
# byte-exact round-trip comparison wrongly rejected case variants -- a
# strict regression versus the pre-round-4 plain-casefold behavior, in
# exactly the domain this PR targets.
# ---------------------------------------------------------------------------


def test_month_name_case_variants_still_match_after_roundtrip_guard():
    assert normalize_id("Jan 2010") == normalize_id("JAN 2010")
    assert normalize_id("Jan 2010") == normalize_id("jan 2010")
    assert normalize_id("January 2010") == normalize_id("JANUARY 2010")


def test_month_name_case_variants_match_in_day_granularity_formats_too():
    assert normalize_id("Jan 15, 2010") == normalize_id("JAN 15, 2010")
    assert normalize_id("January 15, 2010") == normalize_id("january 15, 2010")


def test_case_insensitive_roundtrip_guard_still_rejects_zero_padding_gaps():
    # The casefold fix must not loosen the round-trip guard's actual job:
    # non-zero-padded numeric components must still fail to round-trip and
    # fall back to plain casefold instead of merging with the zero-padded
    # form.
    assert normalize_id("2010-1") != normalize_id("2010-01")
    assert normalize_id("1/2/2010") != normalize_id("01/02/2010")
    assert normalize_id("2010-01-1") != normalize_id("2010-01-01")


# ---------------------------------------------------------------------------
# Zero-padding round-trip guard (round-4 review finding #2): non-zero-padded
# numbers must NOT silently merge with their zero-padded equivalents.
# ---------------------------------------------------------------------------


def test_non_zero_padded_month_does_not_merge_with_zero_padded():
    assert normalize_id("2010-1") != normalize_id("2010-01")


# ---------------------------------------------------------------------------
# Near-misses: strings that must NOT match any date format, and must fall
# back to plain casefold instead of silently matching the wrong thing.
# ---------------------------------------------------------------------------


def test_near_miss_strings_fall_back_to_plain_casefold():
    assert normalize_id("October") == "october"
    assert normalize_id("2010") == "2010"
    assert normalize_id("Jan 2010 sales") == "jan 2010 sales"
    assert normalize_id("Jan-2010") == "jan-2010"
    assert normalize_id("2010/01") == "2010/01"
    assert normalize_id("15 Jan 2010") == "15 jan 2010"


# ---------------------------------------------------------------------------
# Sentinel collision-safety (round-4 review finding #3): a literal candidate
# string shaped like the internal prefix must not collide with a real date.
# ---------------------------------------------------------------------------


def test_literal_prefix_shaped_string_does_not_collide_with_real_date():
    # If the prefix were plain ASCII (e.g. "__date_ym__2010-01"), a
    # hypothetical row id that happens to read exactly that would collide
    # with the real date-normalization output for "Jan 2010"/"2010-01". The
    # `\x00`-wrapped prefix makes this structurally impossible: no
    # user-authored identifier can contain a `\x00` control character.
    fake_id = "__date_ym__2010-01"
    assert normalize_id(fake_id) != normalize_id("Jan 2010")
    assert normalize_id(fake_id) != normalize_id("2010-01")
    assert normalize_id(fake_id) == fake_id.casefold()

    fake_day_id = "__date_ymd__2010-01-15"
    assert normalize_id(fake_day_id) != normalize_id("2010-01-15")
    assert normalize_id(fake_day_id) == fake_day_id.casefold()
