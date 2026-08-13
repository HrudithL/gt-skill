#!/usr/bin/env python3
"""Regression test for `_walk_top_level`/`_walk_exported_scope`'s
2026-08-13 `if __name__ == "__main__":` unwrap.

Confirmed twice in `eval-results/house/SUMMARY.md`
(`towny_growth_trends/repeat_1`, `airquality_monthly_summary/repeat_1`):
a candidate that wraps its ENTIRE table-building script in
`def build_table(): ...` and only calls it via `if __name__ ==
"__main__": build_table()` is ordinary, idiomatic Python -- it executes
identically to an inlined top-level script when the harness runs `python
table.py`, and both real candidates' rendered `table.png` were fine. But
`_walk_top_level`'s blanket "never descend into a def/class body" rule
(see its own docstring) made every AST-based check built on it --
`_frame_present`, `_hairlines_present`, `_render_call_present`, color
mechanics, formatter detection, etc. -- see an empty top-level scope,
scoring both candidates ~18% purely from this blind spot, not from any
real quality problem.

This constructs a minimal candidate shaped exactly like those two real
cases (a `build_table()` wrapping `GT`, `hairlines(gt)`, `frame(gt)`, and
`finalize(gt, path="table.png")`, invoked only via the `__main__` guard)
and asserts that the checks reading `_walk_exported_scope`/`_walk_top_
level` now see it -- before this fix, every one of them was `False`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.comparator import (  # noqa: E402
    _frame_present,
    _hairlines_present,
    _render_call_present,
)

_WRAPPED_SRC = """\
from great_tables import GT

def build_table():
    gt = GT(df)
    gt = gt.data_color(columns=["x"])
    gt = hairlines(gt)
    gt = frame(gt)
    finalize(gt, path="table.png")

if __name__ == "__main__":
    build_table()
"""


def test_wrapped_script_hairlines_call_is_recognized():
    assert _hairlines_present(_WRAPPED_SRC) is True


def test_wrapped_script_frame_call_is_recognized():
    assert _frame_present(_WRAPPED_SRC) is True


def test_wrapped_script_render_call_is_recognized():
    assert _render_call_present(_WRAPPED_SRC) is True


def test_unwrap_is_one_level_only_nested_helper_def_still_excluded():
    # `build_table` itself defines a nested helper that also calls
    # `hairlines(...)` -- the unwrap only inlines `build_table`'s own
    # body, it does NOT recurse into a `def` nested inside that body, so
    # a call trapped inside a NEVER-INVOKED nested helper still doesn't
    # count (same bounded-scope guarantee `_walk_top_level` always gave
    # for any other nested def).
    src = """\
from great_tables import GT

def build_table():
    def _never_called_helper():
        return hairlines(gt)
    gt = GT(df)
    finalize(gt, path="table.png")

if __name__ == "__main__":
    build_table()
"""
    assert _hairlines_present(src) is False


def test_main_guard_calling_an_unresolvable_name_is_left_alone():
    # `run()` isn't a module-level `def` here (e.g. imported from
    # elsewhere) -- nothing to unwrap, and this must not raise.
    src = """\
from other_module import run

if __name__ == "__main__":
    run()
"""
    assert _hairlines_present(src) is False
    assert _render_call_present(src) is False


def test_self_referential_guard_does_not_hang():
    # Review finding (2026-08-13): a function whose OWN body contains
    # another `__main__`-guard shape re-triggered the same special case
    # inside `_walk_top_level`'s stack loop, which never terminated for a
    # self-referential `def build(): if __name__=="__main__(): build()`.
    # `guard_ids`/`body_index` now restrict the unwrap to the guard
    # literally sitting in `tree.body` -- anything reached BY an unwrap
    # gets no second chance to unwrap again.
    src = """\
def build():
    if __name__ == "__main__":
        build()

if __name__ == "__main__":
    build()
"""
    # Must terminate and must not raise -- the exact regression was an
    # unbounded `while stack` loop, not a wrong return value.
    assert _hairlines_present(src) is False


def test_chained_guards_do_not_unwrap_transitively():
    # Review finding (2026-08-13): `a()`'s own body contains a SECOND
    # `__main__`-guard calling `b()`, and the pre-fix code unwrapped both,
    # contradicting the "one level of unwrapping only" design intent this
    # module's docstrings state. Only `a`'s own body is inlined; `b`'s
    # `hairlines(gt)` call, one level deeper, must not be seen.
    src = """\
def b():
    gt = hairlines(gt)

def a():
    if __name__ == "__main__":
        b()

if __name__ == "__main__":
    a()
"""
    assert _hairlines_present(src) is False


def test_guard_before_def_is_not_unwrapped():
    # Review finding (2026-08-13): the guard's target `def` must appear
    # BEFORE the guard in source order -- calling it any earlier raises a
    # real `NameError` when the harness runs `python table.py`, so this is
    # not an inlined-equivalent script and must not be scored as if it
    # rendered fine.
    src = """\
if __name__ == "__main__":
    build_table()

def build_table():
    gt = hairlines(gt)
    finalize(gt, path="table.png")
"""
    assert _hairlines_present(src) is False
    assert _render_call_present(src) is False


def test_plain_unwrapped_script_is_unaffected():
    # A normal, already-linear top-level script (no wrapper function at
    # all) must keep working exactly as before.
    src = """\
from great_tables import GT

gt = GT(df)
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path="table.png")
"""
    assert _hairlines_present(src) is True
    assert _frame_present(src) is True
    assert _render_call_present(src) is True
