#!/usr/bin/env python3
"""Tests for run.py's --random N flag (per-difficulty prompt sampling).

Covers the composition of --random with --prompt (de-dup by name), the
per-difficulty selection contract (N easy + N medium + N hard), and the
error paths (N < 1, N greater than any difficulty's pool).
"""
from __future__ import annotations

import argparse
import types
import unittest
from unittest.mock import patch

import run as run_module


def _fake_pool(name: str) -> dict:
    return {
        "name": name,
        "difficulty": name.split("_")[0],  # e.g. "easy_a" -> "easy"
        "prompt": f"prompt for {name}",
        "data": f"data/{name}.csv",
    }


_POOLS = {
    "easy": [_fake_pool(f"easy_{c}") for c in "abcd"],
    "medium": [_fake_pool(f"medium_{c}") for c in "abcd"],
    "hard": [_fake_pool(f"hard_{c}") for c in "abcd"],
}


def _fake_discover(difficulty=None):
    if difficulty in _POOLS:
        return list(_POOLS[difficulty])
    if difficulty is None or difficulty == "all":
        return sum((list(v) for v in _POOLS.values()), [])
    return []


def _fake_find(name: str):
    for pool in _POOLS.values():
        for info in pool:
            if info["name"] == name:
                return info
    return None


def _args(**over) -> argparse.Namespace:
    base = dict(prompt=None, difficulty=None, random=None, prompt_text=None, data=None)
    base.update(over)
    return argparse.Namespace(**base)


class RandomFlagTests(unittest.TestCase):
    def setUp(self) -> None:
        p1 = patch.object(run_module.discover, "discover_prompts", side_effect=_fake_discover)
        p2 = patch.object(run_module.discover, "find_prompt", side_effect=_fake_find)
        p1.start()
        p2.start()
        self.addCleanup(p1.stop)
        self.addCleanup(p2.stop)

    def test_random_picks_n_per_difficulty(self) -> None:
        prompts = run_module._build_prompts(_args(random=2))
        by_diff: dict[str, int] = {}
        for p in prompts:
            by_diff[p.difficulty] = by_diff.get(p.difficulty, 0) + 1
        self.assertEqual(by_diff, {"easy": 2, "medium": 2, "hard": 2})
        self.assertEqual(len(prompts), 6)

    def test_random_dedups_against_explicit_prompt(self) -> None:
        # Force the RNG to pick "easy_a" for the easy sample; the explicit
        # --prompt easy_a must not double-count.
        with patch.object(run_module.random, "sample",
                          side_effect=lambda pool, n: pool[:n]):
            prompts = run_module._build_prompts(_args(prompt=["easy_a"], random=1))
        names = [p.name for p in prompts]
        self.assertEqual(names.count("easy_a"), 1)
        self.assertEqual(len(prompts), 3)  # easy_a (already), medium_a, hard_a

    def test_random_too_large_errors(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            run_module._build_prompts(_args(random=99))
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
