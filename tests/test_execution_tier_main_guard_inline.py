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

_SHADOWED_DEF_SRC = """\
import pandas as pd
from great_tables import GT

def build_table():
    df = pd.DataFrame({"x": [1, 2, 3]})
    gt = GT(df)

def build_table(df):
    gt = GT(df)

if __name__ == "__main__":
    build_table()
"""

_EARLY_RETURN_SRC = """\
import pandas as pd
from great_tables import GT

def build_table():
    gt = GT(pd.DataFrame({"x": [1, 2, 3]}))
    if True:
        return gt
    gt = GT(pd.DataFrame({"x": [9] * 7}))

if __name__ == "__main__":
    build_table()
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
    # if it ran (round-3 review finding). Asserting on the SPECIFIC error
    # (round-4 review finding: asserting only `ok is False` here is
    # vacuous -- it also arrives, via a different NameError, if the arity
    # check is deleted and the body is wrongly inlined anyway) pins that
    # the real script itself was run, unmodified, and hit its own real
    # TypeError -- not that inlining happened and failed differently.
    result = exec_table(_write(tmp_path, _REQUIRED_ARG_SRC))
    assert result["ok"] is False
    assert "TypeError" in result["error"] and "missing 1 required positional argument" in result["error"]


def test_defaulted_arg_def_is_not_inlined(tmp_path):
    # Unlike the comparator's purely-static equivalent check, inlining
    # here actually EXECUTES the body without ever calling the function --
    # a default is never applied, so a referenced `df` would raise
    # NameError. Only genuinely zero-parameter defs are safe to inline.
    # Same specific-error reasoning as the required-arg test above: a
    # generic "no top-level gt" (the real, un-inlined script's own result)
    # is the correct outcome here, not a NameError from a wrongly-inlined
    # body.
    result = exec_table(_write(tmp_path, _DEFAULTED_ARG_SRC))
    assert result["ok"] is False
    assert result["error"] == "no top-level `gt` GT instance in table.py"


def test_guard_before_def_is_not_inlined(tmp_path):
    # Same "def must precede the guard" rule as the comparator's fix --
    # calling it any earlier is a real NameError at runtime. Specific
    # assertion (round-4 review finding, same reasoning as above): the
    # real, un-inlined script raises NameError on `build_table` itself
    # (called before it's defined); a wrongly-inlined version would
    # instead NameError on `GT` (an import that comes after the guard).
    result = exec_table(_write(tmp_path, _GUARD_BEFORE_DEF_SRC))
    assert result["ok"] is False
    assert "NameError" in result["error"] and "build_table" in result["error"]


_DECORATED_TARGET_SRC = """\
import pandas as pd
from great_tables import GT

def tag(fn):
    return "not a function"

@tag
def build_table():
    gt = GT(pd.DataFrame({"x": [1, 2, 3]}))

if __name__ == "__main__":
    build_table()
"""

_CLASS_SHADOWED_SRC = """\
import pandas as pd
from great_tables import GT

def build_table():
    gt = GT(pd.DataFrame({"x": [1, 2, 3]}))

class build_table:
    pass

if __name__ == "__main__":
    build_table()
"""

_REASSIGNED_SRC = """\
import pandas as pd
from great_tables import GT

def build_table():
    gt = GT(pd.DataFrame({"x": [1, 2, 3]}))

build_table = None

if __name__ == "__main__":
    build_table()
"""


def test_decorated_guard_target_is_not_inlined(tmp_path):
    # Round-5 review finding: a decorator can replace the function
    # entirely -- calling the bare name runs the decorator's wrapper, not
    # the plain body. The real script raises TypeError and renders
    # nothing; must not be scored as if it ran.
    result = exec_table(_write(tmp_path, _DECORATED_TARGET_SRC))
    assert result["ok"] is False
    assert "TypeError" in result["error"]


def test_class_shadowed_def_is_not_inlined(tmp_path):
    # Round-5 review finding: a LATER `class build_table: ...` shadows an
    # earlier `def build_table(): ...` at real runtime -- the real script
    # constructs an instance and never assigns a top-level `gt`.
    result = exec_table(_write(tmp_path, _CLASS_SHADOWED_SRC))
    assert result["ok"] is False


def test_reassigned_def_is_not_inlined(tmp_path):
    # Same shadowing class as the class-def case, via a plain reassignment
    # instead -- the real script's bare `build_table()` call raises
    # TypeError (`None` is not callable), not a rendered table.
    result = exec_table(_write(tmp_path, _REASSIGNED_SRC))
    assert result["ok"] is False
    assert "TypeError" in result["error"]


def test_shadowed_def_resolves_to_the_last_one(tmp_path):
    # Round-4 review finding: a LATER same-name `def` with a required
    # parameter shadows an earlier zero-param one at real runtime (plain
    # Python name rebinding) -- `build_table()` calls the parameterized
    # version and raises TypeError, rendering nothing. Resolving to the
    # earlier (shadowed) def instead would fabricate a 3-row result for a
    # script that actually crashes.
    result = exec_table(_write(tmp_path, _SHADOWED_DEF_SRC))
    assert result["ok"] is False
    assert "TypeError" in result["error"] and "missing 1 required positional argument" in result["error"]


def test_return_before_other_code_declines_to_inline(tmp_path):
    # Round-4 review finding: an early `return` with more code after it
    # (dead code at real runtime) must not be silently stripped -- doing
    # so previously fell through to the dead code and fabricated a
    # 7-row result for a script that actually renders 3 rows. Declining
    # to inline (falling back to the existing "no top-level gt" result)
    # is the safe outcome for this shape, not a wrongly-produced value.
    result = exec_table(_write(tmp_path, _EARLY_RETURN_SRC))
    assert result["ok"] is False
    assert result["error"] == "no top-level `gt` GT instance in table.py"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
