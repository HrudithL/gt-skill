#!/usr/bin/env python3
"""Regression tests for two fresh-sweep (2026-08-12) comparator fixes,
both found against real `house`-skill candidates in
`runs/sweep/20260812_193614_house_6prompts/`:

1. `_hairlines_present` didn't recognize a genuine call to `great-tables-
   house`'s own unconditional `hairlines(gt, ...)` helper (its `tab_
   options(table_body_hlines_...)` effect lives inside the helper's own
   function body, invisible to source-level parsing of a candidate that
   only imports/calls it) -- mirrors `_frame_present`'s existing `frame(
   ...)` helper-recognition check, via the same `_has_real_call` AST
   approach.

2. `_blocks_target_table_png` (and, via it, `_render_call_present`) and
   `_render_params_local`'s own nested call-selector both treated a call
   whose path argument is entirely absent as "can't tell, skip it" --
   correct for `gtsave(file, ...)` (no default; omitting `file` is a
   `TypeError` in `great_tables`'s own `GT.save`/`gtsave` signature), but
   wrong for `finalize(gt, path="table.png", **overrides)`, whose OWN
   signature defaults `path` to `"table.png"` -- a bare `finalize(gt)`
   call genuinely renders to `table.png` via that documented default.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.comparator import (  # noqa: E402
    _blocks_target_table_png,
    _hairlines_present,
    _render_call_present,
    _render_params_local,
)


# ---------------------------------------------------------------------------
# `_hairlines_present` -- helper-call recognition (mirrors `_frame_present`).
# ---------------------------------------------------------------------------


def test_hairlines_helper_call_is_recognized():
    src = "from house_table import hairlines\ngt = hairlines(gt)\n"
    assert _hairlines_present(src) is True


def test_hairlines_helper_call_as_bare_name_without_import_is_still_recognized():
    # `_has_real_call(..., allow_bare=True)` only cares that a genuine
    # `hairlines(...)` call node exists, not whether the name resolves.
    assert _hairlines_present("gt = hairlines(gt, width='2px')\n") is True


def test_defining_a_hairlines_function_without_calling_it_does_not_count():
    # Same precedent as `_frame_present`'s own `frame` check: a candidate
    # merely DEFINING `def hairlines(...):` (e.g. it copy-pasted the
    # helper's source instead of importing it, but the resulting script
    # never actually calls it) must not be credited.
    src = (
        "def hairlines(gt, color=None, width='1px', style='solid'):\n"
        "    return gt\n"
        "gt = build()\n"
    )
    assert _hairlines_present(src) is False


def test_hairlines_mentioned_only_in_a_comment_does_not_count():
    src = "gt = build()  # remember to call hairlines(gt) eventually\n"
    assert _hairlines_present(src) is False


# ---------------------------------------------------------------------------
# `_blocks_target_table_png` / `_render_call_present` -- `finalize`'s own
# `path="table.png"` default.
# ---------------------------------------------------------------------------


def test_bare_finalize_call_resolves_to_table_png_via_its_default():
    src = "gt = build()\nfinalize(gt)\n"
    assert _render_call_present(src) is True


def test_finalize_with_explicit_non_table_png_path_is_not_credited():
    src = "gt = build()\nfinalize(gt, path='backup.png')\n"
    assert _render_call_present(src) is False


def test_bare_gtsave_call_with_no_path_argument_is_not_credited():
    # `gtsave`/`GT.save` has NO default for its `file` argument in the
    # real `great_tables` API -- omitting it is a `TypeError`, not a
    # silent fallback to `table.png`. Must not crash, and must not be
    # treated as targeting `table.png`.
    src = "gt = build()\ngt.gtsave()\n"
    assert _render_call_present(src) is False


def test_blocks_target_table_png_default_path_only_applies_when_path_is_absent():
    # An explicit (non-table.png) literal path is a real, provable miss --
    # `default_path` must never override a resolved-but-wrong literal.
    blocks = [((1, 0), "gt, path='backup.png'")]
    assert _blocks_target_table_png(blocks, "path", 1, default_path="table.png") is False


def test_blocks_target_table_png_default_path_fills_in_for_absent_argument():
    blocks = [((1, 0), "gt")]
    assert _blocks_target_table_png(blocks, "path", 1, default_path="table.png") is True


def test_blocks_target_table_png_without_default_path_falls_through_on_absent_argument():
    # `gtsave`'s own call site never passes `default_path` -- preserves
    # the original "can't tell, skip it" behavior. `block` here is the
    # method call's own argument-list text (the receiver `gt` is not
    # part of it, matching `gt.gtsave()`'s zero real arguments).
    blocks = [((1, 0), "")]
    assert _blocks_target_table_png(blocks, "file", 0) is False


# ---------------------------------------------------------------------------
# `_render_params_local` -- the same default-path gap in its own,
# independent call-selection logic.
# ---------------------------------------------------------------------------


def test_render_params_selects_bare_finalize_over_an_unrelated_decoy_gtsave():
    src = (
        "gt = build()\n"
        "finalize(gt)\n"
        "gt.gtsave('backup.png', zoom=1.0, expand=5)\n"
    )
    # The bare `finalize(gt)` call is the one that actually produces
    # `table.png` (via its own default); the later `gtsave('backup.png',
    # ...)` call is unrelated and must not win just for being last.
    assert _render_params_local(src) == {"expand": "15", "zoom": "2.0"}
