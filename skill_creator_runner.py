#!/usr/bin/env python3
"""Temporary runner for the candidate skill in .claude-skill-creator/.

This drives the SAME harness (run.run) as run.py / test_runner.py /
consistency_runner.py, but mounts the candidate skill from
``.claude-skill-creator/`` as the great-tables skill (skill_variant="creator")
instead of the promoted one in ``.claude/skills/great-tables/``. Everything
else about the environment — the sidecar Chrome, the render instructions, the
read/write permission gates, the venv on PATH — is identical, so a difference in
output is a difference in the *skill*, not the harness.

It exposes the two evaluation shapes the repo already has, behind one CLI:

    # convergence of ONE prompt: baseline (no skill) + N creator repeats,
    # contact_sheet.png + consistency_report.json  (consistency_runner shape)
    python skill_creator_runner.py consistency "Make a clean table" data/gtcars.csv --repeat 3

    # pass/fail sweep across the prompt corpus, summary.json  (test_runner shape)
    python skill_creator_runner.py test --difficulty easy --repeat 1

All artifacts land under ``test-runs/`` in a ``creator_``-prefixed dir and use
the exact same files (summary.json / consistency_report.json / contact_sheet.png)
the promoted runners emit, so existing tooling reads them without changes.

Notes for interpreting results — the candidate skill was authored to be
portable, so its SKILL.md tells the model to ``source scripts/setup_gt_chrome.sh``
and ``gtsave("output.png")``. This harness overrides both (a browser is already
running; the deliverable is ``table.png``) via run.py's render instructions.
Friction there — wrong output filename, a wasted setup attempt, a failed
``import gt_house_style`` — is a real portability finding about the candidate,
not a harness bug.

This file is disposable: once the candidate is promoted into
``.claude/skills/great-tables/``, delete it and use test_runner.py /
consistency_runner.py directly (the "creator" variant in run.py can go too).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import anyio
from dotenv import load_dotenv
from nokap import Chrome

# Reuse the promoted runners' metric/report code verbatim so results are
# directly comparable and this stays a thin dispatcher, not a fork.
from consistency_runner import (
    _finalize_outputs,
    _print_summary,
    run_consistency,
    slugify,
)
from run import CREATOR_SKILL_SRC
from run import run as run_agent
from test_runner import discover_prompts, extract_result_metrics, write_summary

ROOT = Path(__file__).parent.resolve()
VARIANT = "creator"


# --------------------------------------------------------------------------- #
# consistency mode  (delegates to consistency_runner, variant forced to creator)
# --------------------------------------------------------------------------- #
def cmd_consistency(args: argparse.Namespace) -> int:
    data_path = Path(args.data).expanduser().resolve()
    if not data_path.is_file():
        print(f"error: data file not found: {data_path}", file=sys.stderr)
        return 2
    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2
    if args.model:
        os.environ["GTSKILL_AGENT_MODEL"] = args.model

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "test-runs" / f"{timestamp}_creator_{slugify(args.prompt)}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"out dir: {out_dir}")
    print(f"skill:   {CREATOR_SKILL_SRC}  (variant={VARIANT})")
    print(f"data:    {data_path}")
    print(f"runs:    baseline=none + {args.repeat}x {VARIANT}")
    print(f"prompt:  {args.prompt}\n")

    chrome_profile = out_dir / ".chrome-profile"
    chrome_profile.mkdir(exist_ok=True)
    chrome = Chrome(extra_args=[f"--user-data-dir={chrome_profile}"])
    print(f"chrome:  {chrome.ws_url}\n")

    try:
        baseline_dir, repeat_dirs = anyio.run(
            run_consistency, args.prompt, data_path, out_dir, args.repeat, VARIANT, chrome.ws_url
        )
    finally:
        chrome.close()
        shutil.rmtree(chrome_profile, ignore_errors=True)

    meta = {
        "timestamp": timestamp,
        "prompt": args.prompt,
        "data": str(data_path),
        "variant": VARIANT,
        "skill_src": str(CREATOR_SKILL_SRC),
        "repeat": args.repeat,
        "model": args.model,
    }
    report = _finalize_outputs(out_dir, baseline_dir, repeat_dirs, meta)
    _print_summary(report, out_dir)
    return 0


# --------------------------------------------------------------------------- #
# test mode  (test_runner shape, but every run uses skill_variant="creator")
# --------------------------------------------------------------------------- #
async def _test_single(prompt_text: str, data_path: Path, run_dir: Path, chrome_ws: str) -> dict:
    """Run one prompt under the candidate skill; mirror test_runner metrics."""
    run_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    try:
        await run_agent(prompt_text, data_path, run_dir, chrome_ws, skill_variant=VARIANT)
        metrics = extract_result_metrics(run_dir)
        metrics["wall_time_s"] = round(time.time() - start, 2)
        return metrics
    except Exception as e:
        return {"status": "fail", "error": str(e), "wall_time_s": round(time.time() - start, 2)}


async def _test_all(prompts: list[dict], test_run_dir: Path, repeat: int, chrome_ws: str) -> list[dict]:
    """Sequentially run every (prompt × repeat) under the candidate skill."""
    results: list[dict] = []
    total = len(prompts) * repeat
    for info in prompts:
        data_path = Path(info["data"])
        for rep in range(1, repeat + 1):
            name = info["name"]
            run_subdir = test_run_dir / name / f"repeat_{rep}" if repeat > 1 else test_run_dir / name
            current = len(results) + 1
            print(
                f"\n{'=' * 60}\n"
                f"[{current}/{total}] {info['difficulty']}/{name}"
                f"{f' (repeat {rep}/{repeat})' if repeat > 1 else ''}\n"
                f"{'=' * 60}"
            )
            print(f"  prompt: {info['prompt'][:120]}...")
            print(f"  data:   {data_path}")
            print(f"  run_dir: {run_subdir}\n")

            metrics = await _test_single(info["prompt"], data_path, run_subdir, chrome_ws)
            results.append(
                {
                    "name": name,
                    "difficulty": info["difficulty"],
                    "prompt": info["prompt"],
                    "data": info["data"],
                    "repeat": rep,
                    "run_dir": str(run_subdir),
                    **metrics,
                }
            )
            icon = "✅" if metrics["status"] == "pass" else "❌"
            cost = metrics.get("total_cost_usd")
            cost_str = f"${cost:.4f}" if cost is not None else "n/a"
            print(f"\n  {icon} {metrics['status']} | cost={cost_str} | wall={metrics.get('wall_time_s', 'n/a')}s")
    return results


def cmd_test(args: argparse.Namespace) -> int:
    if args.model:
        os.environ["GTSKILL_AGENT_MODEL"] = args.model

    prompts = discover_prompts(args.difficulty)
    if not prompts:
        print(f"error: no prompts found for difficulty '{args.difficulty}'", file=sys.stderr)
        return 2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_run_dir = ROOT / "test-runs" / f"{timestamp}_creator_test"
    test_run_dir.mkdir(parents=True, exist_ok=True)

    print(f"test run:   {test_run_dir}")
    print(f"skill:      {CREATOR_SKILL_SRC}  (variant={VARIANT})")
    print(f"difficulty: {args.difficulty}")
    print(f"model:      {args.model or '(default)'}")
    print(f"repeat:     {args.repeat}")
    print(f"prompts:    {len(prompts)} found")

    chrome_profile = test_run_dir / ".chrome-profile"
    chrome_profile.mkdir(exist_ok=True)
    chrome = Chrome(extra_args=[f"--user-data-dir={chrome_profile}"])
    print(f"chrome:     {chrome.ws_url}")

    try:
        results = anyio.run(_test_all, prompts, test_run_dir, args.repeat, chrome.ws_url)
    finally:
        chrome.close()
        shutil.rmtree(chrome_profile, ignore_errors=True)

    config = {
        "timestamp": timestamp,
        "difficulty": args.difficulty,
        "model": args.model,
        "repeat": args.repeat,
        "variant": VARIANT,
    }
    write_summary(test_run_dir, results, config)

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(results)} total")
    print(f"{'=' * 60}")
    return 0 if failed == 0 else 1


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main() -> int:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set (put it in .env)", file=sys.stderr)
        return 2
    if not CREATOR_SKILL_SRC.is_dir():
        print(f"error: candidate skill not found at {CREATOR_SKILL_SRC}", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Evaluate the .claude-skill-creator/ candidate skill through the "
        "existing harness, in either the consistency or test-sweep shape.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_con = sub.add_parser("consistency", help="Convergence of one prompt (baseline + N creator repeats).")
    p_con.add_argument("prompt", help="Describe the table you want.")
    p_con.add_argument("data", help="Path to the data file (e.g. data/gtcars.csv).")
    p_con.add_argument("--repeat", type=int, default=3, help="Creator repeats, N (default: 3).")
    p_con.add_argument("--model", default=None, help="Model override (sets GTSKILL_AGENT_MODEL).")
    p_con.set_defaults(func=cmd_consistency)

    p_test = sub.add_parser("test", help="Pass/fail sweep across the prompt corpus.")
    p_test.add_argument(
        "--difficulty", choices=["easy", "medium", "hard", "all"], default="all",
        help="Which difficulty of prompts to run (default: all).",
    )
    p_test.add_argument("--repeat", type=int, default=1, help="Runs per prompt (default: 1).")
    p_test.add_argument("--model", default=None, help="Model override (sets GTSKILL_AGENT_MODEL).")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
