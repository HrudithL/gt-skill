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

import glob
import importlib.util
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from runner.comparator import _hairlines_present  # noqa: E402
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


def test_dead_code_does_not_pass():
    # Round-2 review finding: an earlier version used unrestricted
    # `ast.walk`, so a `hairlines(gt)` call trapped inside a never-invoked
    # helper function counted as real styling. Must fail now, matching the
    # comparator (which only sees the exported call chain).
    src = "def _never_called():\n    gt = hairlines(gt)\ngt = GT(df)\n"
    assert _fails(src)


def test_white_hairline_is_not_treated_as_transparent():
    # Round-2 review finding: an earlier version hardcoded "#ffffff"/"#fff"
    # as invisible, but a white hairline IS visible -- the comparator's own
    # `_is_effectively_transparent` doesn't treat white as transparent
    # either. Must pass.
    src = """\
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#ffffff",
    table_body_hlines_width="1px",
)
"""
    assert not _fails(src)


def test_later_tab_options_call_wins_in_source_order():
    # Round-2 review finding: "last occurrence wins" must mean last in
    # SOURCE order, not last in `ast.walk`'s (breadth-first) traversal
    # order. A disabling first call followed by an enabling second call
    # must pass -- that's what actually renders at runtime.
    src = """\
gt = gt.tab_options(table_body_hlines_style="none")
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)
"""
    assert not _fails(src)


# Only `scripts` (great-tables-ci) candidates ever actually run through
# gt_check.py -- house/prose have no CI checker (see their own SKILL.md) and
# use a different helper library (house_table.py's own wrapped-example
# convention, which the comparator's function-body unwrap handles but this
# standalone checker has no equivalent for and was never meant to). Testing
# agreement against house/prose samples would fail on exactly that mismatch
# without it being a real bug -- scope this to the skill that actually uses it.
_REAL_SAMPLES = sorted(glob.glob(os.path.join(REPO_ROOT, "eval-results", "scripts", "samples", "*", "*", "table.py")))


@pytest.mark.parametrize("path", _REAL_SAMPLES, ids=[os.path.relpath(p, REPO_ROOT) for p in _REAL_SAMPLES])
def test_checker_agrees_with_comparator_on_every_real_sample(path):
    # Round-2 review finding: the checker and the real scorer had drifted
    # apart in several ways (scope, ordering, transparency handling) that
    # happened not to fire on the checked-in samples -- pin agreement
    # directly so a future drift is caught here instead of staying latent.
    source = open(path, encoding="utf-8").read()
    assert bool(gt_check.check_hairlines(source)) == (not _hairlines_present(source))


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
