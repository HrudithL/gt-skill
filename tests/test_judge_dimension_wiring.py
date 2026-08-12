#!/usr/bin/env python3
"""Regression tests pinning two invariants the color-restraint-dimension PR
relies on:

1. `judge_rubric.SYSTEM_PROMPT`'s stated dimension count is actually wired
   up to `len(DIMENSIONS)` -- not a hardcoded literal that can silently
   drift out of sync whenever a dimension is added or removed (see
   `judge_rubric.py`'s own module docstring: "SYSTEM_PROMPT is rendered
   from [DIMENSIONS] so the text actually sent to the model can never
   drift out of sync with the anchors a reviewer sees here").

2. A judge-backed check gated as not-applicable (via `comparator._na()`,
   the shared degrade path every judge-backed check -- and several
   mechanical ones -- funnel through) always contributes 0 to BOTH earned
   and possible points, so an N/A dimension shrinks the report's
   denominator instead of silently awarding or docking a point.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner import comparator  # noqa: E402
from runner import judge_rubric  # noqa: E402


def test_system_prompt_dimension_count_matches_dimensions_dict():
    # Deliberately re-derived from the live DIMENSIONS dict, not a literal
    # -- if a future edit adds/removes a dimension without also updating
    # the interpolation, this fails instead of silently going stale.
    expected = len(judge_rubric.DIMENSIONS)
    assert f"exactly {expected} named dimensions" in judge_rubric.SYSTEM_PROMPT
    assert f"## The {expected} dimensions" in judge_rubric.SYSTEM_PROMPT
    assert f"all {expected} keys above" in judge_rubric.SYSTEM_PROMPT


def test_na_check_result_has_zero_earned_and_possible_points():
    result = comparator._na("some not-applicable check", "nothing to grade this run")
    assert result.points_earned == 0
    assert result.points_possible == 0
    assert result.passed is True
