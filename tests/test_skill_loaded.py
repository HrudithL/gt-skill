"""Smoke test: did the agent load the great-tables skill on a table prompt?

Runs the agent on a small, table-shaped task, then greps the trace for a
`Skill(name="great-tables")` tool call. Exits non-zero if it didn't happen.

Usage:
    python tests/test_skill_loaded.py
    python tests/test_skill_loaded.py --agent-model claude-sonnet-4-5
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv

import run as gtskill


def skill_was_loaded(trace_path: Path) -> tuple[bool, list[str]]:
    """Return (loaded?, list of skill names invoked)."""
    invoked: list[str] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        for call in rec.get("tool_calls", []) or []:
            if call.get("name") == "Skill":
                invoked.append((call.get("input") or {}).get("name", "?"))
    return ("great-tables" in invoked, invoked)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-model", default=gtskill.DEFAULT_AGENT_MODEL)
    args = parser.parse_args()

    prompt = (
        "Build a small comparison table of the top 5 cars by horsepower (hp) "
        "showing manufacturer, model, year, hp, and msrp."
    )

    run_dir = gtskill.make_run_dir()
    print(f"Run directory: {run_dir}")
    dataset_path = gtskill.stage_workspace(run_dir, "gtcars")

    asyncio.run(gtskill.run_agent(prompt, run_dir, args.agent_model, dataset_path))

    loaded, invoked = skill_was_loaded(run_dir / "trace.jsonl")
    print(f"Skill tool calls: {invoked or '(none)'}")

    if loaded:
        print("PASS: agent loaded the great-tables skill.")
        return 0
    print("FAIL: agent never invoked Skill(name='great-tables').")
    return 1


if __name__ == "__main__":
    sys.exit(main())
