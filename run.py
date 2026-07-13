#!/usr/bin/env python3
"""Build a great_tables table from a data file using the Claude Agent SDK.

Usage:
    python run.py "Make a clean table of this data" data/gtcars.csv

The engine (the single ``claude_agent_sdk.query()`` choke point, the skill-variant
mounting, the permission gate, the transcript writer) now lives in
``runner/engine.py`` and the sidecar Chrome lifecycle in ``runner/sidecar.py``.
This file is just the thin single-prompt CLI over that core; the web backend
imports the same ``runner`` package rather than shelling out here, so the two can
never diverge. The public names the sibling runners import (``run``,
``CREATOR_SKILL_SRC``, …) are re-exported below so this stays their entry point.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import anyio
from dotenv import load_dotenv

# Re-export the engine's public surface so `from run import run` /
# `from run import CREATOR_SKILL_SRC` (consistency_runner, test_runner,
# skill_creator_runner) keep resolving to the exact same objects after the move.
from runner.engine import (  # noqa: F401
    BASELINE_VARIANT,
    CREATOR_SKILL_SRC,
    ROOT,
    SKILL_CI_DIR,
    SKILL_CI_NAME,
    SKILL_DIR,
    SKILL_NAME,
    SKILL_VARIANTS,
    block_to_dict,
    message_to_dict,
    run,
)
from runner.sidecar import sidecar_chrome


def main() -> int:
    load_dotenv(ROOT / ".env")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set (put it in .env)", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Build a great_tables table from a data file using the Claude Agent SDK.",
    )
    parser.add_argument("prompt", help="Describe the table you want.")
    parser.add_argument("data", help="Path to the data file (e.g. data/gtcars.csv).")
    args = parser.parse_args()

    data_path = Path(args.data).expanduser().resolve()
    if not data_path.is_file():
        print(f"error: data file not found: {data_path}", file=sys.stderr)
        return 2

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"run dir: {run_dir}")
    print(f"data:    {data_path}")
    print(f"prompt:  {args.prompt}\n")

    # Launch one headless Chrome in the parent process (outside the agent's
    # macOS sandbox); the agent attaches to it over CDP via `nokap`/`gtsave`.
    # The sidecar context manager owns the profile dir and cleanup.
    with sidecar_chrome(run_dir) as chrome:
        print(f"chrome:  {chrome.ws_url}\n")
        anyio.run(run, args.prompt, data_path, run_dir, chrome.ws_url)

    print(f"\nartifacts in {run_dir}:")
    for f in sorted(run_dir.iterdir()):
        print(f"  - {f.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
