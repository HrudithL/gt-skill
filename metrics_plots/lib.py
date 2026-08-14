#!/usr/bin/env python3
"""Metrics extraction over an eval-results tree.

Reads a ``<root>/<skill>/samples/<prompt>/<variant>/`` layout (produced by
``run.py --evaluate``'s post-run copy step) and computes, per variant:
cost/tokens (from the copied ``transcript.json``'s final ``result`` message
— no re-derivation) and a ground-truth comparator score
(``runner.comparator.compare()``, same path as ``scripts/gt_compare.py``).

Prompt discovery is dynamic: whatever prompts exist under ``samples/`` are
the ones scored. Each prompt's difficulty is looked up by checking which
``prompts/{easy,medium,hard}/<name>.json`` file exists — so any subset the
``--evaluate`` sweep chose (via ``--random N`` or explicit prompts) is
supported without editing this file.

If a sample dir lacks a ``transcript.json`` (as is the case for the frozen
``eval-results-demo/`` snapshot), that variant's cost/tokens block falls
back to whatever's in the tree's existing ``metrics.json`` — so the demo
tree still re-renders correctly.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

# Resolve the repo root from this file's location (metrics_plots/lib.py).
ROOT = Path(__file__).resolve().parent.parent

import sys  # noqa: E402

# Make the runner importable when this file is loaded from any cwd.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import comparator  # noqa: E402

DIFFICULTIES = ("easy", "medium", "hard")
VARIANTS = ("repeat_1", "repeat_2", "repeat_3", "repeat_4", "repeat_5", "baseline")


def _resolve_difficulty(prompt_id: str) -> str | None:
    for d in DIFFICULTIES:
        if (ROOT / "prompts" / d / f"{prompt_id}.json").is_file():
            return d
    return None


def _resolve_ground_truth(prompt_id: str, difficulty: str) -> Path:
    return ROOT / "prompts" / difficulty / "ground_truth" / f"{prompt_id}.py"


def _resolve_prompt_text(prompt_id: str, difficulty: str) -> str:
    path = ROOT / "prompts" / difficulty / f"{prompt_id}.json"
    if not path.is_file():
        return ""
    try:
        return json.loads(path.read_text()).get("prompt", "") or ""
    except (json.JSONDecodeError, OSError):
        return ""


def discover_samples(samples_dir: Path) -> list[tuple[str, str, str, Path]]:
    """Yield ``(prompt_id, difficulty, variant, variant_dir)`` for every
    sample subdirectory under ``samples_dir``. Prompts whose difficulty
    can't be resolved (not in ``prompts/<d>/``) are skipped with a warning —
    scoring needs a ground truth."""
    out: list[tuple[str, str, str, Path]] = []
    if not samples_dir.is_dir():
        return out
    for prompt_dir in sorted(samples_dir.iterdir()):
        if not prompt_dir.is_dir():
            continue
        difficulty = _resolve_difficulty(prompt_dir.name)
        if difficulty is None:
            print(
                f"metrics_plots: skipping {prompt_dir} — no matching "
                f"prompts/<d>/{prompt_dir.name}.json"
            )
            continue
        for variant in VARIANTS:
            vdir = prompt_dir / variant
            if vdir.is_dir():
                out.append((prompt_dir.name, difficulty, variant, vdir))
    return out


def load_cost_tokens(vdir: Path) -> dict[str, Any] | None:
    """Read the harness's own final ``result`` message from ``transcript.json``
    (same shape ``eval-results-demo/_lib.py`` used) — returns ``None`` if
    the transcript is missing, which is how a cached (transcript-less)
    demo sample signals "use the fallback.""""
    transcript_path = vdir / "transcript.json"
    if not transcript_path.is_file():
        return None
    try:
        transcript = json.loads(transcript_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not transcript:
        return None
    final = transcript[-1]
    if final.get("role") != "result":
        return None
    usage = final.get("usage", {}) or {}
    return {
        "cost_usd": final.get("total_cost_usd", 0.0) or 0.0,
        "input_tokens": usage.get("input_tokens", 0) or 0,
        "output_tokens": usage.get("output_tokens", 0) or 0,
        "cache_read_tokens": usage.get("cache_read_input_tokens", 0) or 0,
        "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0) or 0,
        "duration_ms": final.get("duration_ms", 0) or 0,
        "num_turns": final.get("num_turns", 0) or 0,
        "is_error": bool(final.get("is_error", False)),
    }


def compute_score(vdir: Path, prompt_id: str, difficulty: str) -> dict[str, Any] | None:
    """Score ``vdir/table.py`` against its prompt's ground truth via
    ``runner.comparator.compare()`` — same path ``scripts/gt_compare.py``
    drives. Returns ``None`` when the candidate script or ground truth is
    missing (a cached demo tree with only ``report.txt`` copied in falls
    into this path)."""
    candidate = vdir / "table.py"
    if not candidate.is_file():
        return None
    gt_path = _resolve_ground_truth(prompt_id, difficulty)
    if not gt_path.is_file():
        return None
    prompt_text = _resolve_prompt_text(prompt_id, difficulty)
    report = comparator.compare(candidate, gt_path, prompt_text)
    total_possible = report.total_possible
    return {
        "report_text": comparator.format_report(report),
        "data_earned": report.data_earned,
        "data_possible": report.data_possible,
        "format_earned": report.format_earned,
        "format_possible": report.format_possible,
        "total_earned": report.total_earned,
        "total_possible": total_possible,
        "pct": 100 * report.total_earned / total_possible if total_possible else None,
        "checks": [
            {
                "name": c.name,
                "points_earned": c.points_earned,
                "points_possible": c.points_possible,
                "passed": c.passed,
                "detail": c.detail,
                "tier": c.tier,
            }
            for c in report.checks
        ],
    }


def _load_cached_metrics(root: Path, skill: str) -> dict[str, Any] | None:
    p = root / skill / "metrics.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _cached_variant(cached: dict | None, prompt_id: str, variant: str) -> dict:
    """Pull a variant's cached ``{cost_tokens, score}`` block from a cached
    metrics.json (or an empty stub if the cache doesn't cover it)."""
    if not cached:
        return {"cost_tokens": None, "score": None}
    entry = (cached.get("prompts") or {}).get(prompt_id) or {}
    v = (entry.get("variants") or {}).get(variant) or {}
    return {
        "cost_tokens": v.get("cost_tokens"),
        "score": v.get("score"),
    }


def collect_metrics(root: Path, skill: str, *, max_workers: int = 6) -> dict[str, Any]:
    """The full metrics tree for one skill's samples — per prompt, per
    variant: cost/tokens + comparator score. Falls back to a cached
    ``metrics.json`` on a per-variant, per-field basis (so a partial
    recompute — say, ``transcript.json`` present but ``table.py`` corrupt —
    doesn't blow away every score, just the ones that failed to compute)."""
    samples_dir = root / skill / "samples"
    jobs = discover_samples(samples_dir)
    cached = _load_cached_metrics(root, skill)

    def _score_job(job):
        prompt_id, difficulty, variant, vdir = job
        return (prompt_id, variant, compute_score(vdir, prompt_id, difficulty))

    scores: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for prompt_id, variant, score in pool.map(_score_job, jobs):
            scores.setdefault(prompt_id, {})[variant] = score

    prompts_out: dict[str, Any] = {}
    for prompt_id, difficulty, variant, vdir in jobs:
        entry = prompts_out.setdefault(
            prompt_id,
            {"difficulty": difficulty, "variants": {}},
        )
        fresh_cost = load_cost_tokens(vdir)
        fresh_score = scores.get(prompt_id, {}).get(variant)
        fallback = _cached_variant(cached, prompt_id, variant)
        entry["variants"][variant] = {
            "cost_tokens": fresh_cost if fresh_cost is not None else fallback["cost_tokens"],
            "score": fresh_score if fresh_score is not None else fallback["score"],
        }

    return {
        "skill": skill,
        "samples_dir": str(samples_dir),
        "prompts": prompts_out,
    }


def dump_metrics(root: Path, skill: str, metrics: dict[str, Any]) -> Path:
    out_path = root / skill / "metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2))
    return out_path
