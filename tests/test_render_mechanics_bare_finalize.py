#!/usr/bin/env python3
"""Regression test for `runner.comparator._stmt_targets_name`'s bare-call
branch: a bare `finalize(gt, ...)` statement must be recognized as
targeting the script's exported name, but ONLY for `finalize(...)`
specifically -- not any other bare call (e.g. `print(gt)`), which would
reopen the false-positive class `_walk_exported_scope`'s round-14 fix
exists to prevent (a throwaway table's calls counting toward the exported
table's own checks). See `check_render_mechanics`'s own false-negative
history for why the first half of this matters at all.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.comparator import _stmt_targets_name  # noqa: E402


def _targets(src: str, name: str) -> bool:
    stmt = ast.parse(src).body[0]
    return _stmt_targets_name(stmt, name)


def test_bare_finalize_targets_its_first_argument():
    assert _targets('finalize(gt, path="table.png")', "gt") is True


def test_bare_finalize_on_a_different_variable_does_not_target_gt():
    assert _targets('finalize(other, path="table.png")', "gt") is False


def test_bare_call_other_than_finalize_is_not_treated_as_a_render_call():
    # A real prior bug: matching ANY bare call's first argument (not just
    # finalize's) would have made this return True.
    assert _targets("print(gt)", "gt") is False


def test_bare_call_other_than_finalize_does_not_pull_a_throwaway_chain_into_scope():
    assert _targets('debug_dump(gt, GT(df).data_color(columns=["x"]))', "gt") is False


def test_chained_gtsave_still_targets_the_receiver():
    assert _targets('gt.tab_header(title="x").gtsave("table.png")', "gt") is True


def test_bare_finalize_only_checks_the_first_argument_not_any_argument():
    # `name` appearing as a LATER argument doesn't count -- only finalize's
    # first positional argument is its render target (matches
    # `_exported_gt_name`'s own convention).
    assert _targets('finalize(other, gt)', "gt") is False


def test_plain_assignment_still_targets_the_name():
    assert _targets("gt = GT(df)", "gt") is True


def test_bare_finalize_with_no_positional_args_does_not_target_anything():
    assert _targets("finalize()", "gt") is False
