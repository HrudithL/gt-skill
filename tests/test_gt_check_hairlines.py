#!/usr/bin/env python3
"""Regression tests for `gt_check.py`'s `check_hairlines` (great-tables-ci).

Review finding (2026-08-13): the first version of this check was a raw
`re.search(r"\\bhairlines\\s*\\(", source)` plus an exact-hex-literal match on
`table_body_hlines_color` -- false-FAILed the skill's own taught
`table_body_hlines_color=PALETTE["neutral"]["hairline"]` form (a real sample,
`eval-results/scripts/samples/towny_growth_trends/repeat_1/table.py`, which
`runner/comparator.py::_hairlines_present` scores as present), and false-
PASSed a bare comment, an unused `def hairlines(...):`, or a string mention --
exactly the false-positive class `_hairlines_present`'s own docstring says
AST-based detection exists to avoid. `check_hairlines` is now AST-based
(`_is_call_named` + `_hairlines_tab_options_ok`), mirroring
`runner/comparator.py`'s `_has_real_call`/`_option_line_present`.
"""
from __future__ import annotations

import importlib.util
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT_CHECK_PATH = os.path.join(
    REPO_ROOT, ".claude", "skills", "great-tables-ci", "scripts", "gt_check.py"
)


def _import_gt_check():
    spec = importlib.util.spec_from_file_location("gt_check", GT_CHECK_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gt_check", module)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


gt_check = _import_gt_check()


def _fails(source: str) -> bool:
    return bool(gt_check.check_hairlines(source))


def test_palette_lookup_form_passes():
    # The taught, expected form -- a non-literal color expression that
    # `_hairlines_tab_options_ok` cannot resolve, tolerated the same way
    # `runner/comparator.py::_option_line_present` tolerates it (style/width
    # alone, both literal, are enough).
    src = """\
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color=PALETTE['neutral']['hairline'],
    table_body_hlines_width='1px',
)
"""
    assert not _fails(src)


def test_hairlines_helper_call_passes():
    src = "from gt_consistency import hairlines\ngt = hairlines(gt)\n"
    assert not _fails(src)


def test_bare_hex_literal_passes():
    src = """\
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)
"""
    assert not _fails(src)


def test_comment_mention_does_not_pass():
    src = "gt = GT(df)\n# TODO: hairlines(gt) later\n"
    assert _fails(src)


def test_unused_def_does_not_pass():
    src = "def hairlines(gt):\n    return gt\ngt = GT(df)\n"
    assert _fails(src)


def test_string_mention_does_not_pass():
    src = 'gt = GT(df).tab_source_note(source_note="see hairlines (below)")\n'
    assert _fails(src)


def test_disabled_style_does_not_pass():
    src = """\
gt = gt.tab_options(
    table_body_hlines_style="none",
    table_body_hlines_color="#E8E8E8",
)
"""
    assert _fails(src)


def test_nothing_set_does_not_pass():
    assert _fails("gt = GT(df)\n")


def test_syntax_error_does_not_crash():
    assert gt_check.check_hairlines("def broken(:\n") == []


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
