#!/usr/bin/env python3
"""The one globalized runner: build great_tables tables via the Claude Agent SDK.

One flag-driven entry over the shared ``runner/`` core. It exposes the same
settings as the web app (skill, prompts, repeats, model, baseline, ad-hoc
prompt), builds a ``RunSpec``, and hands it to ``runner.orchestrate`` — the exact
path ``POST /api/runs`` takes — so the file runner and the web app can never
diverge in behavior. This replaces the four old runners (run / consistency /
test / skill_creator), which are folded into this one flow.

Examples:
    # one corpus prompt, prose skill, once
    python run.py --skill prose --prompt sp500_monthly_performance

    # convergence: scripts skill, 3 repeats (baseline auto-on), Haiku
    python run.py --skill scripts --prompt sp500_monthly_performance --repeat 3

    # sweep every easy prompt under the creator skill
    python run.py --skill creator --difficulty easy

    # an ad-hoc prompt against a chosen data file
    python run.py --skill prose --prompt-text "Make a clean table" --data data/gtcars.csv

    # force the baseline control on at a single repeat
    python run.py --skill scripts --prompt islands_sizes --baseline
"""

from __future__ import annotations

import argparse
import os
import sys

import anyio
from dotenv import load_dotenv

# Re-export the engine's public surface for back-compat (see runner/engine.py).
from runner.engine import (  # noqa: F401
    CREATOR_SKILL_SRC,
    ROOT,
    SKILL_DIR,
    block_to_dict,
    message_to_dict,
    run,
)
from runner import discover, orchestrate
from runner.spec import (
    DEFAULT_MODEL,
    MODEL_LABELS,
    SKILL_LABELS,
    PromptRef,
    RunSpec,
)


def _build_prompts(args: argparse.Namespace) -> list[PromptRef]:
    """Assemble the run's PromptRefs from --prompt / --difficulty / --prompt-text."""
    prompts: list[PromptRef] = []

    for name in args.prompt or []:
        info = discover.find_prompt(name)
        if info is None:
            print(f"error: no corpus prompt named {name!r}", file=sys.stderr)
            raise SystemExit(2)
        prompts.append(
            PromptRef(
                prompt=info["prompt"], data=info["data"],
                name=info["name"], difficulty=info["difficulty"], source="corpus",
            )
        )

    if args.difficulty:
        for info in discover.discover_prompts(args.difficulty):
            prompts.append(
                PromptRef(
                    prompt=info["prompt"], data=info["data"],
                    name=info["name"], difficulty=info["difficulty"], source="corpus",
                )
            )

    if args.prompt_text:
        if not args.data:
            print("error: --prompt-text requires --data", file=sys.stderr)
            raise SystemExit(2)
        prompts.append(PromptRef(prompt=args.prompt_text, data=args.data, source="adhoc"))

    return prompts


def _cli_emit(event: dict) -> None:
    """Console progress for the CLI (engine.run already prints each message)."""
    t = event.get("type")
    if t == "stage":
        rep = f" repeat {event['repeat']}/{event.get('total')}" if event.get("repeat") else ""
        print(f"\n{'=' * 60}\n[{event['index']}/{event['total']}] "
              f"{event['prompt']} ({event['variant']}){rep}\n{'=' * 60}")
    elif t == "run_finished":
        agg = event["summary"]["aggregate"]
        print(f"\n{'=' * 60}\nRESULTS: {agg['passed']} passed, {agg['failed']} failed "
              f"of {agg['total']} | cost=${agg['total_cost_usd']}\n{'=' * 60}")
    elif t == "run_error":
        print(f"\nRUN ERROR: {event['error']}", file=sys.stderr)


def main() -> int:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY is not set (put it in .env)", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Build great_tables tables via the Claude Agent SDK (one runner for all flows).",
    )
    parser.add_argument("--skill", choices=SKILL_LABELS, default="prose",
                        help="Which self-contained skill to mount (default: prose).")
    parser.add_argument("--prompt", action="append", metavar="NAME",
                        help="Corpus prompt by file stem; repeatable for multiple prompts.")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "all"],
                        help="Add every corpus prompt of this difficulty.")
    parser.add_argument("--prompt-text", metavar="TEXT",
                        help="An ad-hoc prompt (requires --data).")
    parser.add_argument("--data", metavar="PATH",
                        help="Data CSV for --prompt-text (e.g. data/gtcars.csv).")
    parser.add_argument("--repeat", type=int, default=1,
                        help="With-skill invocations per prompt (default: 1).")
    parser.add_argument("--model", choices=MODEL_LABELS, default=DEFAULT_MODEL,
                        help=f"Model label (default: {DEFAULT_MODEL}).")
    parser.add_argument("--baseline", action=argparse.BooleanOptionalAction, default=None,
                        help="Force the no-skill baseline on/off (default: auto — on iff repeat>1).")
    args = parser.parse_args()

    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2

    prompts = _build_prompts(args)
    if not prompts:
        print("error: no prompts selected (use --prompt / --difficulty / --prompt-text)",
              file=sys.stderr)
        return 2

    spec = RunSpec(
        skill=args.skill, prompts=prompts, repeats=args.repeat,
        model=args.model, baseline=args.baseline,
    )
    spec.validate()

    run_dir = orchestrate.create_run_dir(spec)
    print(f"run dir:  {run_dir}")
    print(f"skill:    {spec.skill}  (variant={spec.variant()})")
    print(f"model:    {spec.model} -> {spec.model_id()}")
    print(f"prompts:  {len(prompts)}   repeats: {spec.repeats}   "
          f"baseline: {spec.baseline_enabled()}   invocations: {spec.invocation_count()}")

    summary = anyio.run(_run, spec, run_dir)
    return 0 if summary["aggregate"]["failed"] == 0 else 1


async def _run(spec: RunSpec, run_dir) -> dict:
    return await orchestrate.run_spec(spec, run_dir, emit=_cli_emit)


if __name__ == "__main__":
    raise SystemExit(main())
