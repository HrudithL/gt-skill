#!/usr/bin/env python3
"""Repetitive test runner for the great-tables skill.

Discovers prompt files from prompts/{easy,medium,hard}/, runs each through
run.py's core `run()` function, and writes all output into a timestamped
test-runs/ directory with a summary.json report.

Each prompt is a JSON file with {"prompt": "...", "data": "data/file.csv"}.

Usage examples:
    python test_runner.py
    python test_runner.py --difficulty easy
    python test_runner.py --difficulty hard --repeat 3
    python test_runner.py --model claude-sonnet-4-20250514
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anyio
from dotenv import load_dotenv

from run import run as run_agent

ROOT = Path(__file__).parent.resolve()
PROMPTS_DIR = ROOT / "prompts"
DIFFICULTIES = ["easy", "medium", "hard"]


def discover_prompts(difficulty: str | None) -> list[dict]:
    """Return a list of {name, difficulty, path, prompt, data} dicts for matching prompts."""
    if difficulty and difficulty != "all":
        dirs = [PROMPTS_DIR / difficulty]
    else:
        dirs = [PROMPTS_DIR / d for d in DIFFICULTIES]

    prompts = []
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            content = json.loads(f.read_text())
            data_path = ROOT / content["data"]
            if not data_path.is_file():
                print(f"warning: data file not found for {f.name}: {data_path}", file=sys.stderr)
                continue
            prompts.append(
                {
                    "name": f.stem,
                    "difficulty": d.name,
                    "path": str(f),
                    "prompt": content["prompt"],
                    "data": str(data_path.resolve()),
                }
            )
    return prompts


def extract_result_metrics(run_dir: Path) -> dict:
    """Extract metrics from a transcript.json produced by run.py."""
    transcript_path = run_dir / "transcript.json"
    if not transcript_path.exists():
        return {"status": "fail", "error": "no transcript.json produced"}

    transcript = json.loads(transcript_path.read_text())

    result_msg = None
    for entry in transcript:
        if entry.get("role") == "result":
            result_msg = entry
            break

    if result_msg is None:
        return {"status": "fail", "error": "no result message in transcript"}

    has_table_png = (run_dir / "table.png").exists()
    has_table_py = (run_dir / "table.py").exists()

    return {
        "status": "pass" if not result_msg.get("is_error") and has_table_png else "fail",
        "is_error": result_msg.get("is_error", True),
        "has_table_png": has_table_png,
        "has_table_py": has_table_py,
        "num_turns": result_msg.get("num_turns"),
        "duration_ms": result_msg.get("duration_ms"),
        "total_cost_usd": result_msg.get("total_cost_usd"),
        "usage": result_msg.get("usage"),
    }


async def run_single_prompt(
    prompt_text: str, data_path: Path, run_dir: Path
) -> dict:
    """Run a single prompt through the agent and return metrics."""
    run_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    try:
        await run_agent(prompt_text, data_path, run_dir)
        elapsed = time.time() - start
        metrics = extract_result_metrics(run_dir)
        metrics["wall_time_s"] = round(elapsed, 2)
        return metrics
    except Exception as e:
        elapsed = time.time() - start
        return {
            "status": "fail",
            "error": str(e),
            "wall_time_s": round(elapsed, 2),
        }


async def run_all(
    prompts: list[dict],
    test_run_dir: Path,
    repeat: int,
) -> list[dict]:
    """Run all prompts sequentially and collect results."""
    results = []
    total = len(prompts) * repeat

    for prompt_info in prompts:
        data_path = Path(prompt_info["data"])
        for rep in range(1, repeat + 1):
            current = len(results) + 1
            prompt_name = prompt_info["name"]

            if repeat > 1:
                run_subdir = test_run_dir / prompt_name / f"repeat_{rep}"
            else:
                run_subdir = test_run_dir / prompt_name

            print(
                f"\n{'=' * 60}\n"
                f"[{current}/{total}] {prompt_info['difficulty']}/{prompt_name}"
                f"{f' (repeat {rep}/{repeat})' if repeat > 1 else ''}\n"
                f"{'=' * 60}"
            )
            print(f"  prompt: {prompt_info['prompt'][:120]}...")
            print(f"  data:   {data_path}")
            print(f"  run_dir: {run_subdir}\n")

            metrics = await run_single_prompt(
                prompt_info["prompt"], data_path, run_subdir
            )

            result_entry = {
                "name": prompt_name,
                "difficulty": prompt_info["difficulty"],
                "prompt": prompt_info["prompt"],
                "data": prompt_info["data"],
                "repeat": rep,
                "run_dir": str(run_subdir),
                **metrics,
            }
            results.append(result_entry)

            status_icon = "✅" if metrics["status"] == "pass" else "❌"
            cost = metrics.get("total_cost_usd")
            cost_str = f"${cost:.4f}" if cost is not None else "n/a"
            print(
                f"\n  {status_icon} {metrics['status']} | "
                f"cost={cost_str} | "
                f"wall={metrics.get('wall_time_s', 'n/a')}s"
            )

    return results


def write_summary(test_run_dir: Path, results: list[dict], config: dict) -> None:
    """Write summary.json with all results and aggregate stats."""
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    total_cost = sum(r.get("total_cost_usd") or 0 for r in results)
    total_tokens_in = sum(
        (r.get("usage") or {}).get("input_tokens", 0) for r in results
    )
    total_tokens_out = sum(
        (r.get("usage") or {}).get("output_tokens", 0) for r in results
    )

    summary = {
        "timestamp": config["timestamp"],
        "config": {
            "difficulty": config["difficulty"],
            "model": config.get("model"),
            "repeat": config["repeat"],
        },
        "aggregate": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed / len(results) * 100:.1f}%" if results else "n/a",
            "total_cost_usd": round(total_cost, 4),
            "total_input_tokens": total_tokens_in,
            "total_output_tokens": total_tokens_out,
        },
        "results": results,
    }

    summary_path = test_run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n📄 Summary written to {summary_path}")


def main() -> int:
    load_dotenv(ROOT / ".env")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set (put it in .env)", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Run great-tables skill prompts and collect results.",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard", "all"],
        default="all",
        help="Which difficulty of prompts to run (default: all).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model override (sets GTSKILL_AGENT_MODEL env var).",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to run each prompt (default: 1).",
    )
    args = parser.parse_args()

    if args.model:
        os.environ["GTSKILL_AGENT_MODEL"] = args.model

    prompts = discover_prompts(args.difficulty)
    if not prompts:
        print(f"error: no prompts found for difficulty '{args.difficulty}'", file=sys.stderr)
        return 2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_run_dir = ROOT / "test-runs" / timestamp
    test_run_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "timestamp": timestamp,
        "difficulty": args.difficulty,
        "model": args.model,
        "repeat": args.repeat,
    }

    print(f"Test run:   {test_run_dir}")
    print(f"Difficulty: {args.difficulty}")
    print(f"Model:      {args.model or '(default)'}")
    print(f"Repeat:     {args.repeat}")
    print(f"Prompts:    {len(prompts)} found")

    results = anyio.run(run_all, prompts, test_run_dir, args.repeat)

    write_summary(test_run_dir, results, config)

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(results)} total")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
