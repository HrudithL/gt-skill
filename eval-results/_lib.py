#!/usr/bin/env python3
"""Shared metrics-extraction helpers for eval-results/<skill>/plots/make_plots.py.

Reads a completed `run.py --skill <skill> --difficulty all --repeat 3` sweep
directory (`runs/sweep/<timestamp>_<skill>_6prompts/`) and computes, per
invocation: cost/token usage (from `transcript.json`'s final `result`
message -- no re-derivation, the harness already totals these), a
ground-truth comparator score (`runner.comparator.compare()`, the same path
`scripts/gt_compare.py` uses), and per-prompt consistency (the
`convergence.json` the harness already writes per prompt -- not a new
metric, just read).

One shared module so the four skills' `plots/make_plots.py` scripts don't
each re-implement this parsing; each of them is still a short, independently
runnable, skill-specific script (see that file's docstring).
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

import sys  # noqa: E402

sys.path.insert(0, str(ROOT))

from runner import comparator  # noqa: E402

PROMPTS: list[tuple[str, str]] = [
    ("gtcars_hp_price", "easy"),
    ("islands_sizes", "easy"),
    ("airquality_monthly_summary", "medium"),
    ("gtcars_top10_by_country", "medium"),
    ("sp500_monthly_performance", "hard"),
    ("towny_growth_trends", "hard"),
]
VARIANTS = ["repeat_1", "repeat_2", "repeat_3", "baseline"]


def find_latest_sweep_dir(skill_label: str) -> Path:
    """The most recent `runs/sweep/*_<skill_label>_6prompts` dir.

    `run.py` timestamps every run dir fresh (never overwrites), so a skill
    that was swept more than once locally (e.g. an earlier partial/test
    invocation) can have several matching dirs -- the latest one is the
    full 6-prompt x repeat=3 sweep this tooling expects.
    """
    candidates = sorted((ROOT / "runs" / "sweep").glob(f"*_{skill_label}_6prompts"))
    if not candidates:
        raise FileNotFoundError(
            f"no runs/sweep/*_{skill_label}_6prompts directory found under {ROOT}"
        )
    return candidates[-1]


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


def invocation_dirs(sweep_dir: Path):
    """Yield (prompt_id, difficulty, variant, dir) for every invocation that
    actually ran (a `--prompt` subset sweep just won't have every prompt's
    subdirectory; skip what's missing rather than erroring)."""
    for prompt_id, difficulty in PROMPTS:
        prompt_dir = sweep_dir / "prompts" / prompt_id
        if not prompt_dir.is_dir():
            continue
        for variant in VARIANTS:
            vdir = prompt_dir / variant
            if vdir.is_dir():
                yield prompt_id, difficulty, variant, vdir


def load_cost_tokens(vdir: Path) -> dict[str, Any] | None:
    """The harness's own final `result` message already totals cost/tokens
    for this one invocation -- read it rather than re-summing per-turn
    `usage` blocks, which would double count cached/thinking turns."""
    transcript_path = vdir / "transcript.json"
    if not transcript_path.is_file():
        return None
    transcript = json.loads(transcript_path.read_text())
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
    """Score `vdir/table.py` against its prompt's ground truth via the same
    `runner.comparator.compare()` path `scripts/gt_compare.py` drives."""
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


def load_convergence(sweep_dir: Path, prompt_id: str) -> dict[str, Any] | None:
    path = sweep_dir / "prompts" / prompt_id / "convergence.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def collect_metrics(skill_label: str, *, max_workers: int = 4) -> dict[str, Any]:
    """The full metrics tree for one skill's latest sweep: per prompt, per
    variant -- cost/tokens + comparator score; per prompt -- convergence.

    The comparator score calls out to `runner.judge` (one real Sonnet vision
    call per invocation) -- run those across a small thread pool since each
    is I/O-bound network latency, not CPU work.
    """
    sweep_dir = find_latest_sweep_dir(skill_label)
    jobs = list(invocation_dirs(sweep_dir))

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
            {"difficulty": difficulty, "variants": {}, "convergence": None},
        )
        entry["variants"][variant] = {
            "cost_tokens": load_cost_tokens(vdir),
            "score": scores.get(prompt_id, {}).get(variant),
        }
    for prompt_id in prompts_out:
        prompts_out[prompt_id]["convergence"] = load_convergence(sweep_dir, prompt_id)

    return {
        "skill": skill_label,
        "sweep_dir": str(sweep_dir),
        "prompts": prompts_out,
    }


def dump_metrics(skill_label: str, out_path: Path, **kwargs) -> dict[str, Any]:
    metrics = collect_metrics(skill_label, **kwargs)
    out_path.write_text(json.dumps(metrics, indent=2))
    return metrics


def curate_runs(metrics: dict[str, Any], out_root: Path) -> None:
    """Copy just the reviewable artifacts (candidate script + rendered PNG +
    the comparator's human-readable report) for every invocation into
    `out_root/<prompt>/<variant>/` -- skips the harness's `.claude*` mount,
    `__pycache__`, the shared chrome profile, and `transcript.json`, none of
    which are useful to a GitHub reader browsing the eval results."""
    import shutil

    sweep_dir = Path(metrics["sweep_dir"])
    for prompt_id, entry in metrics["prompts"].items():
        for variant, v in entry["variants"].items():
            vdir = sweep_dir / "prompts" / prompt_id / variant
            out_dir = out_root / prompt_id / variant
            out_dir.mkdir(parents=True, exist_ok=True)
            for name in ("table.py", "table.png"):
                src = vdir / name
                if src.is_file():
                    shutil.copyfile(src, out_dir / name)
            score = v.get("score")
            if score and score.get("report_text"):
                (out_dir / "report.txt").write_text(score["report_text"])
