#!/usr/bin/env python3
"""Regression test for `runner/comparator.py::check_caption_keywords`.

Real-sweep finding (2026-08-13): `_source_note_texts_local` returns
`str | None` per note (`None` when a note's text isn't a static string
literal -- e.g. built from an f-string or a computed expression).
`check_caption_keywords` did `" ".join(cand["tier1"].get("source_note_texts")
or [])`, which raises `TypeError` the moment that list is non-empty AND
contains a `None` entry -- crashing the whole comparator run on an otherwise
valid candidate. Two real candidates hit this in independent sweeps
(`prose/sp500_monthly_performance`, `scripts/airquality_monthly_summary`),
already flagged as a known issue in `eval-results/SUMMARY.md`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.comparator import check_caption_keywords  # noqa: E402


def test_none_source_note_does_not_crash():
    cand = {"tier1": {"source_note_texts": ["a real caption mentions bentley", None]}}
    truth = {}
    meta = {"CAPTION_KEYWORDS": {"caption_should_mention": ["bentley"], "subtitle_should_not_duplicate": []}}
    result = check_caption_keywords(cand, truth, meta)
    assert result.points_earned == result.points_possible


def test_all_none_source_notes_does_not_crash():
    cand = {"tier1": {"source_note_texts": [None, None]}}
    truth = {}
    meta = {"CAPTION_KEYWORDS": {"caption_should_mention": ["bentley"], "subtitle_should_not_duplicate": []}}
    result = check_caption_keywords(cand, truth, meta)
    assert result.points_earned == 0


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
