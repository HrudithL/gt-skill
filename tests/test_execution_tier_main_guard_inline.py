#!/usr/bin/env python3
"""Regression test for `runner/execution_tier.py`'s `_inline_main_guard`.

Real-sweep finding (2026-08-13, same shape as `runner/comparator.py`'s
`_walk_top_level` fix): a candidate wrapped its whole script in
`def build_table(): gt = ...` + `if __name__ == "__main__":
build_table()`. The comparator's own static AST checks already learned to
treat this as inlined, but `execution_tier.py`'s extractor still looked
for a literal `ns.get("gt")` after `exec`-ing the script -- which plain
`exec` never populates for a name assigned inside a function body, even
though the harness's real `python table.py` run renders a perfectly good
`table.png`. Two real house-skill candidates hit this in one sweep
(`gtcars_hp_price/repeat_3`, `islands_sizes/repeat_3`), both scoring
~35% purely from "no top-level `gt` GT instance" -- not a real quality
problem. `_inline_main_guard` fixes this the same way the comparator
does: detect the guard shape and run the function's body as if it were
already at module level.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.execution_tier import exec_table  # noqa: E402

_WRAPPED_SRC = """\
import pandas as pd
from great_tables import GT

def build_table():
    df = pd.DataFrame({"x": [1, 2, 3]})
    gt = GT(df)
    return gt

if __name__ == "__main__":
    build_table()
"""

_PLAIN_SRC = """\
import pandas as pd
from great_tables import GT

df = pd.DataFrame({"x": [1, 2, 3]})
gt = GT(df)
"""

_UNRESOLVABLE_SRC = """\
run = lambda: None   # not a module-level `def` -- nothing to unwrap

if __name__ == "__main__":
    run()
"""

_REQUIRED_ARG_SRC = """\
import pandas as pd
from great_tables import GT

def build_table(df):
    gt = GT(df)

if __name__ == "__main__":
    build_table()
"""

_DEFAULTED_ARG_SRC = """\
import pandas as pd
from great_tables import GT

def build_table(df=None):
    if df is None:
        df = pd.DataFrame({"x": [1, 2, 3]})
    gt = GT(df)

if __name__ == "__main__":
    build_table()
"""

_GUARD_BEFORE_DEF_SRC = """\
if __name__ == "__main__":
    build_table()

import pandas as pd
from great_tables import GT

def build_table():
    df = pd.DataFrame({"x": [1, 2, 3]})
    gt = GT(df)
"""


def _write(tmp_path: Path, src: str) -> Path:
    p = tmp_path / "table.py"
    p.write_text(src)
    return p


def test_wrapped_script_with_trailing_return_is_extracted(tmp_path):
    # The exact real-candidate shape: a trailing `return gt` inside the
    # wrapped function, which is a SyntaxError if inlined naively.
    result = exec_table(_write(tmp_path, _WRAPPED_SRC))
    assert result["ok"] is True, result.get("error")
    assert result["n_rows"] == 3


def test_plain_script_is_unaffected(tmp_path):
    result = exec_table(_write(tmp_path, _PLAIN_SRC))
    assert result["ok"] is True
    assert result["n_rows"] == 3


def test_unresolvable_guard_target_does_not_crash(tmp_path):
    result = exec_table(_write(tmp_path, _UNRESOLVABLE_SRC))
    assert result["ok"] is False
    assert "no top-level" in result["error"]


def test_required_arg_def_is_not_inlined(tmp_path):
    # `def build_table(df):` called bare as `build_table()` raises
    # TypeError at runtime and renders nothing -- must not be scored as
    # if it ran (round-3 review finding).
    result = exec_table(_write(tmp_path, _REQUIRED_ARG_SRC))
    assert result["ok"] is False


def test_defaulted_arg_def_is_not_inlined(tmp_path):
    # Unlike the comparator's purely-static equivalent check, inlining
    # here actually EXECUTES the body without ever calling the function --
    # a default is never applied, so a referenced `df` would raise
    # NameError. Only genuinely zero-parameter defs are safe to inline.
    result = exec_table(_write(tmp_path, _DEFAULTED_ARG_SRC))
    assert result["ok"] is False


def test_guard_before_def_is_not_inlined(tmp_path):
    # Same "def must precede the guard" rule as the comparator's fix --
    # calling it any earlier is a real NameError at runtime.
    result = exec_table(_write(tmp_path, _GUARD_BEFORE_DEF_SRC))
    assert result["ok"] is False


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
