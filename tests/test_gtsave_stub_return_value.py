#!/usr/bin/env python3
"""Regression test for the ``GT.gtsave``/``GT.save`` no-render stubs in
``runner/execution_tier.py`` and ``runner/convergence.py``.

Both real methods return ``self`` (documented chaining contract), so a
script using the common ``gt = gt.gtsave(...)`` idiom must still have a
live ``GT`` instance in ``gt`` afterward -- a stub that returns ``None``
instead silently breaks that idiom and the runner then wrongly reports
"no top-level `gt` GT instance" for a perfectly correct table.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.execution_tier import exec_table  # noqa: E402
from runner import convergence  # noqa: E402

_TABLE_PY = """\
import pandas as pd
from great_tables import GT

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
gt = GT(df)
gt = gt.gtsave("table.png", zoom=2.0)
"""


def _write_table_py(tmp_path: Path) -> Path:
    p = tmp_path / "table.py"
    p.write_text(_TABLE_PY)
    return p


def test_exec_table_survives_reassigned_gtsave_idiom(tmp_path):
    py_path = _write_table_py(tmp_path)
    result = exec_table(py_path)
    assert result["ok"] is True, result.get("error")


def test_convergence_data_hash_survives_reassigned_gtsave_idiom(tmp_path):
    _write_table_py(tmp_path)
    # _compute_data_hash takes the RUN DIR (it execs "<run_dir>/table.py")
    # and execs the same reassignment idiom under its own (separately
    # monkeypatched) stub -- see runner/convergence.py.
    digest = convergence._compute_data_hash(tmp_path)
    assert digest is not None
