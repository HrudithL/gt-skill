#!/usr/bin/env python3
"""Regression tests for ``runner/convergence.py``'s `band(...)`/`stub_tint(...)`
helper-call parsing (the "Header branding" / "Stub tint" comparator checks).

A fresh eval sweep (2026-08-12) found three bugs in this parsing:

  1. ``_bare_call_blocks``/``_bare_call_blocks_pos`` matched `func(...)`-shaped
     text inside `#` comments (e.g. ``# Branding: band (dark navy)``), not
     just real code -- a raw regex scan with no comment-awareness.
  2. ``_find_band_helper``/``_find_stub_tint_hue`` took the FIRST matching
     call (``blocks[0]``) instead of the LAST -- the wrong "which call wins"
     policy for this codebase (a later call/reassignment is what actually
     renders; see ``_find_stub_fill_hex``'s sibling literal-hex path).
  3. An omitted ``hue`` kwarg defaulted to the literal string ``"unknown"``,
     which isn't a key in the hue->hex lookup tables, so a bare
     ``band(gt)``/``stub_tint(gt)`` call (the runtime helpers' own
     documented default, per the 2026-08-12 branding redesign) always
     resolved to ``None`` instead of the fixed branding hex.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner import convergence  # noqa: E402


def test_band_shaped_comment_is_not_misread_as_a_call():
    """A `# ... band (...) ...` COMMENT must not be mistaken for a real
    `band(...)` call (Bug 1) -- confirmed real case:
    `gtcars_top10_by_country/repeat_1/table.py` had a comment
    `# Step 4: Heading band (branding tier)` that used to be misread as a
    call to `band("branding tier")`, producing spurious partial credit on
    checks that shouldn't apply at all (the script never calls the helper).
    """
    source = (
        "import pandas as pd\n"
        "from great_tables import GT\n"
        "# Step 4: Heading band (branding tier)\n"
        "gt = GT(pd.DataFrame({'a': [1]}))\n"
        "gt = gt.tab_header(title='x')\n"
    )
    assert convergence._bare_call_blocks(source, "band") == []
    assert convergence._find_band_helper(source) is None


def test_bare_call_blocks_pos_shares_the_same_comment_awareness():
    """`_bare_call_blocks_pos` (the position-paired sibling) must skip a
    comment-shaped match the same way `_bare_call_blocks` does -- they
    share one comment-detection helper rather than duplicating the logic.
    """
    source = "# stub_tint(gt, hue='navy') -- just a note, not a call\n"
    assert convergence._bare_call_blocks_pos(source, "stub_tint") == []


def test_hex_string_containing_hash_is_not_treated_as_a_comment():
    """A `#` INSIDE a string literal (a hex color) must not be misread as
    starting a comment -- the naive "strip everything after `#`" approach
    this fix deliberately avoids.
    """
    source = 'gt = gt.tab_options(column_labels_background_color="#08306B")\ngt = band(gt, hue="navy")\n'
    blocks = convergence._bare_call_blocks(source, "band")
    assert len(blocks) == 1
    assert "navy" in blocks[0]


def test_real_comment_false_positive_no_longer_wins_over_the_real_call():
    """Confirmed real case: `towny_growth_trends/repeat_2/table.py` had a
    comment `# Branding: band (dark navy), stub tint (navy washed),
    striping` ahead of a real `band(gt, hue="navy")` call. Before this fix,
    the comment-derived fake match was `blocks[0]` and (Bug 2) won over the
    real call. After the fix, the comment produces no match at all, and the
    one real call resolves correctly.
    """
    source = (
        "from gt_consistency import band\n"
        "# Branding: band (dark navy), stub tint (navy washed), striping\n"
        "gt = band(gt, hue='navy')\n"
    )
    assert convergence._find_band_helper(source) == ("dark", "navy")


def test_last_call_wins_not_first():
    """Bug 2: a script calling the helper more than once (a reassignment)
    renders the LAST call, not the first."""
    source = "gt = band(gt, shade='dark', hue='forest')\ngt = band(gt, shade='dark', hue='navy')\n"
    assert convergence._find_band_helper(source) == ("dark", "navy")

    stub_source = "gt = stub_tint(gt, hue='forest')\ngt = stub_tint(gt, hue='navy')\n"
    assert convergence._find_stub_tint_hue(stub_source) == "navy"


def test_bare_band_call_with_no_hue_kwarg_resolves_to_fixed_hex():
    """Bug 3: a bare `band(gt)` call (no `hue=` kwarg at all -- confirmed
    real case: `gtcars_hp_price/repeat_1/table.py`) must resolve to the
    fixed branding hex `#08306B`, matching `gt_consistency.band()`'s own
    `shade="dark"` branch, which renders that hex regardless of hue.
    """
    source = "from gt_consistency import band\ngt = band(gt)\n"
    design = convergence.parse_design_choices(source)
    assert design["heading_band_shade"] == "dark"
    assert design["heading_band_hex"] == "#08306B"


def test_bare_stub_tint_call_with_no_hue_kwarg_resolves_to_fixed_hex():
    """The `stub_tint` analog of the above -- an omitted `hue` must resolve
    to the fixed washed-navy hex `#EAF0F6`, not `None`.
    """
    source = "from gt_consistency import stub_tint\ngt = stub_tint(gt)\n"
    assert convergence._find_stub_fill_hex(source) == "#EAF0F6"


def test_band_call_with_non_navy_hue_under_light_shade_is_unaffected():
    """Scope boundary: the fixed-hex-regardless-of-hue resolution is scoped
    to `shade == "dark"` only (band's default) -- house's own separate
    `shade="light"` escape hatch is genuinely hue-varying and this fix must
    not touch it. A `shade="light"` call with a non-navy hue still resolves
    to no hex (the pre-existing, out-of-scope behavior), not a fabricated
    fixed value.
    """
    source = "gt = band(gt, shade='light', hue='forest')\n"
    design = convergence.parse_design_choices(source)
    assert design["heading_band_shade"] == "light"
    assert design["heading_band_hex"] is None


def test_stub_tint_non_navy_hue_lookup_is_unchanged():
    """Scope boundary: a stub_tint hue OTHER than "navy" (e.g. house's
    `"forest"`) is left exactly as before -- unresolved (`None`), since
    `_HELPER_HUE_TO_WASHED_HEX` intentionally only has a `"navy"` entry
    (expanding it is out of scope for this fix).
    """
    source = "gt = stub_tint(gt, hue='forest')\n"
    assert convergence._find_stub_fill_hex(source) is None
