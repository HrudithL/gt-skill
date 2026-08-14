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

    # random per-difficulty sample: 2 easy + 2 medium + 2 hard (6 prompts total)
    python run.py --skill prose --random 2

    # an ad-hoc prompt against a chosen data file
    python run.py --skill prose --prompt-text "Make a clean table" --data data/gtcars.csv

    # force the baseline control on at a single repeat
    python run.py --skill scripts --prompt islands_sizes --baseline

    # full skill evaluation: all 4 skills, 3 repeats each, random 2 per difficulty
    # (WARNING: this is 96 API invocations at ~$0.13 each — see README cost table)
    python run.py --evaluate --random 2 --repeat 3
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
from pathlib import Path

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
from runner.plan import unique_prompt_dir_names
from runner.spec import (
    DEFAULT_MODEL,
    MODEL_LABELS,
    SKILL_LABELS,
    PromptRef,
    RunSpec,
)

import metrics_plots


_RANDOM_DIFFICULTIES = ("easy", "medium", "hard")

# `--evaluate` bounds (from the human's spec): a real evaluation needs at
# least 3 repeats to see any consistency signal, and per-difficulty prompt
# counts stay between 2 (bare minimum coverage) and 5 (a 5-repeat,
# 5-prompt-per-difficulty run is already 360 invocations ≈ $47).
_EVAL_MIN_REPEAT = 3
_EVAL_MIN_PER_DIFFICULTY = 2
_EVAL_MAX_PER_DIFFICULTY = 5


def _build_prompts(args: argparse.Namespace) -> list[PromptRef]:
    """Assemble the run's PromptRefs from --prompt / --difficulty / --random / --prompt-text.

    Corpus prompts are de-duplicated by name so `--prompt X` combined with a
    `--difficulty` (or `--random`) that also includes X (or the same `--prompt`
    twice) runs X once. The ad-hoc data path is validated later in
    orchestrate.create_run_dir, before any Chrome/API spend.
    """
    prompts: list[PromptRef] = []
    seen: set[str] = set()

    def add_corpus(info: dict) -> None:
        if info["name"] in seen:
            return
        seen.add(info["name"])
        prompts.append(
            PromptRef(
                prompt=info["prompt"], data=info["data"],
                name=info["name"], difficulty=info["difficulty"], source="corpus",
            )
        )

    for name in args.prompt or []:
        info = discover.find_prompt(name)
        if info is None:
            print(f"error: no corpus prompt named {name!r}", file=sys.stderr)
            raise SystemExit(2)
        add_corpus(info)

    if args.difficulty:
        for info in discover.discover_prompts(args.difficulty):
            add_corpus(info)

    if args.random is not None:
        # Pick N distinct prompts per difficulty. Requested + human-confirmed
        # semantics: --random 2 == 2 easy + 2 medium + 2 hard (unseeded).
        for d in _RANDOM_DIFFICULTIES:
            pool = discover.discover_prompts(d)
            if len(pool) < args.random:
                print(
                    f"error: --random {args.random} needs at least {args.random} "
                    f"{d} prompts, only {len(pool)} available",
                    file=sys.stderr,
                )
                raise SystemExit(2)
            for info in random.sample(pool, args.random):
                add_corpus(info)

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
    # --skill default is None (not "prose") so we can tell "user explicitly set
    # a skill" from "default kicked in" — --evaluate rejects the former and
    # supplies its own per-skill loop, while single-run mode falls back to
    # "prose" when nothing was given.
    parser.add_argument("--skill", choices=SKILL_LABELS, default=None,
                        help="Which self-contained skill to mount (default: prose; "
                             "must be omitted under --evaluate).")
    parser.add_argument("--prompt", action="append", metavar="NAME",
                        help="Corpus prompt by file stem; repeatable for multiple prompts.")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "all"],
                        help="Add every corpus prompt of this difficulty.")
    parser.add_argument("--random", type=int, metavar="N",
                        help="Pick N random prompts from each difficulty "
                             "(easy+medium+hard = 3*N prompts total).")
    parser.add_argument("--prompt-text", metavar="TEXT",
                        help="An ad-hoc prompt (requires --data; not allowed under --evaluate).")
    parser.add_argument("--data", metavar="PATH",
                        help="Data CSV for --prompt-text (e.g. data/gtcars.csv).")
    parser.add_argument("--repeat", type=int, default=1,
                        help="With-skill invocations per prompt (default: 1; "
                             f"must be >= {_EVAL_MIN_REPEAT} under --evaluate).")
    parser.add_argument("--model", choices=MODEL_LABELS, default=DEFAULT_MODEL,
                        help=f"Model label (default: {DEFAULT_MODEL}).")
    parser.add_argument("--baseline", action=argparse.BooleanOptionalAction, default=None,
                        help="Force the no-skill baseline on/off (default: auto — on iff repeat>1).")
    parser.add_argument("--evaluate", action="store_true",
                        help="Full skill evaluation: run the same prompt set across all "
                             f"{len(SKILL_LABELS)} skills, populate eval-results/, regenerate plots, "
                             "and refresh the checked-in published-metrics/ tree. "
                             f"Requires --repeat >= {_EVAL_MIN_REPEAT} and "
                             f"{_EVAL_MIN_PER_DIFFICULTY}-{_EVAL_MAX_PER_DIFFICULTY} prompts per difficulty.")
    args = parser.parse_args()

    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2

    if args.random is not None and args.random < 1:
        print("error: --random must be >= 1", file=sys.stderr)
        return 2

    if args.evaluate:
        err = _validate_evaluate_args(args)
        if err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        prompts = _build_prompts(args)
        err = _validate_evaluate_prompts(prompts)
        if err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        return anyio.run(_run_evaluation, prompts, args)

    # Non-evaluate path: same behavior as before, with the skill default
    # applied here instead of via argparse.
    if args.skill is None:
        args.skill = "prose"

    prompts = _build_prompts(args)
    if not prompts:
        print("error: no prompts selected (use --prompt / --difficulty / --random / --prompt-text)",
              file=sys.stderr)
        return 2

    spec = RunSpec(
        skill=args.skill, prompts=prompts, repeats=args.repeat,
        model=args.model, baseline=args.baseline,
    )

    # create_run_dir validates the spec and every data file up front, so a bad
    # --data / stale corpus path fails here — before Chrome or any API spend.
    try:
        spec.validate()
        run_dir = orchestrate.create_run_dir(spec)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"run dir:  {run_dir}")
    print(f"skill:    {spec.skill}  (variant={spec.variant()})")
    print(f"model:    {spec.model} -> {spec.model_id()}")
    print(f"prompts:  {len(prompts)}   repeats: {spec.repeats}   "
          f"baseline: {spec.baseline_enabled()}   invocations: {spec.invocation_count()}")

    summary = anyio.run(_run, spec, run_dir)
    # Non-zero on any failing invocation OR a run-level (infra) error, so a
    # sidecar/finalization failure doesn't exit 0 with an empty summary.
    ok = summary["aggregate"]["failed"] == 0 and not summary.get("error")
    return 0 if ok else 1


async def _run(spec: RunSpec, run_dir) -> dict:
    return await orchestrate.run_spec(spec, run_dir, emit=_cli_emit)


def _validate_evaluate_args(args: argparse.Namespace) -> str | None:
    """Pre-build validation for --evaluate. Returns an error string or None.

    Post-build per-difficulty coverage is checked separately by
    ``_validate_evaluate_prompts`` after ``_build_prompts`` runs.
    """
    if args.skill is not None:
        return (
            "--evaluate runs all skills automatically; do not pass --skill "
            f"(got --skill {args.skill!r})."
        )
    if args.prompt_text or args.data:
        return (
            "--evaluate cannot use --prompt-text / --data (evaluation only "
            "runs corpus prompts, which have ground truth to score against)."
        )
    if args.repeat < _EVAL_MIN_REPEAT:
        return (
            f"--evaluate requires --repeat >= {_EVAL_MIN_REPEAT} "
            f"(got --repeat {args.repeat})."
        )
    if args.random is not None:
        if not (_EVAL_MIN_PER_DIFFICULTY <= args.random <= _EVAL_MAX_PER_DIFFICULTY):
            return (
                f"--evaluate requires --random in [{_EVAL_MIN_PER_DIFFICULTY}, "
                f"{_EVAL_MAX_PER_DIFFICULTY}] (got --random {args.random})."
            )
    else:
        # Not using --random: need explicit --prompt or --difficulty.
        if not args.prompt and not args.difficulty:
            return (
                "--evaluate requires either --random N or an explicit "
                "--prompt / --difficulty selection covering all three "
                f"difficulties with {_EVAL_MIN_PER_DIFFICULTY}-"
                f"{_EVAL_MAX_PER_DIFFICULTY} prompts each."
            )
    return None


def _validate_evaluate_prompts(prompts: list[PromptRef]) -> str | None:
    """Post-build coverage check for --evaluate: every difficulty (easy,
    medium, hard) must have 2-5 prompts."""
    counts = {d: 0 for d in _RANDOM_DIFFICULTIES}
    for p in prompts:
        if p.difficulty in counts:
            counts[p.difficulty] += 1
    problems: list[str] = []
    for d, n in counts.items():
        if n < _EVAL_MIN_PER_DIFFICULTY:
            problems.append(f"{d}={n} (need >= {_EVAL_MIN_PER_DIFFICULTY})")
        elif n > _EVAL_MAX_PER_DIFFICULTY:
            problems.append(f"{d}={n} (need <= {_EVAL_MAX_PER_DIFFICULTY})")
    if problems:
        return (
            "--evaluate needs "
            f"{_EVAL_MIN_PER_DIFFICULTY}-{_EVAL_MAX_PER_DIFFICULTY} prompts "
            f"per difficulty; got: {', '.join(problems)}."
        )
    return None


def _copy_samples(run_dir: Path, samples_dst: Path, prompts: list[PromptRef]) -> None:
    """Copy each prompt's per-variant output tree from the run into
    ``samples_dst/<name>/``. Uses the same prompt-dir naming as orchestrate
    (via ``unique_prompt_dir_names``) so a duplicate/ad-hoc-labelled prompt
    lands in the right subdir. Whole tree copy (repeat_*/baseline/) so
    metrics_plots has table.py, table.png, and transcript.json for scoring.
    """
    names = unique_prompt_dir_names(prompts)
    for name in names:
        src = run_dir / "prompts" / name
        if not src.is_dir():
            continue
        dst = samples_dst / name
        shutil.copytree(src, dst, dirs_exist_ok=True)


async def _run_evaluation(prompts: list[PromptRef], args: argparse.Namespace) -> int:
    """Full-skill evaluation loop. Runs the same prompt set across every
    skill, copies each skill's per-prompt outputs into
    eval-results/<skill>/samples/, then regenerates metrics.json and plots
    for every skill via metrics_plots.render_all.

    Exit code: non-zero if any skill had a failing invocation OR if
    metrics_plots raised. A skill's failure doesn't stop the loop — the
    remaining skills still run so an operator sees whichever data is
    available.
    """
    eval_root = ROOT / "eval-results"
    # Fresh snapshot per --evaluate: the previous run's data (if any) is
    # wiped so a smaller/different prompt subset doesn't leave stale
    # unrelated samples behind.
    shutil.rmtree(eval_root, ignore_errors=True)
    eval_root.mkdir(parents=True)

    print(f"\n{'#' * 60}")
    print(f"# --evaluate")
    print(f"# {len(SKILL_LABELS)} skills x {len(prompts)} prompts x --repeat {args.repeat}")
    print(f"# prompts: {', '.join(sorted(p.name or '<adhoc>' for p in prompts))}")
    print(f"# eval-results: {eval_root}")
    print(f"{'#' * 60}\n")

    overall_ok = True
    for skill in SKILL_LABELS:
        print(f"\n{'#' * 60}\n# skill: {skill}\n{'#' * 60}")
        spec = RunSpec(
            skill=skill, prompts=prompts, repeats=args.repeat,
            model=args.model, baseline=args.baseline,
        )
        try:
            spec.validate()
            run_dir = orchestrate.create_run_dir(spec)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            overall_ok = False
            continue
        summary = await orchestrate.run_spec(spec, run_dir, emit=_cli_emit)
        _copy_samples(run_dir, eval_root / skill / "samples", prompts)
        if summary["aggregate"]["failed"] > 0 or summary.get("error"):
            overall_ok = False

    print(f"\n{'#' * 60}\n# rendering plots + metrics.json\n{'#' * 60}")
    try:
        results = metrics_plots.render_all(eval_root)
        for r in results:
            print(f"  {r['skill']:8s} layout={r['layout']:14s} "
                  f"plots={list(r['plots'].keys())}")
    except Exception as e:  # noqa: BLE001
        print(f"error: metrics_plots.render_all failed: {e}", file=sys.stderr)
        overall_ok = False

    print(f"\n{'#' * 60}\n# publishing to published-metrics/\n{'#' * 60}")
    try:
        pub = metrics_plots.publish(eval_root, ROOT / "published-metrics")
        print(f"  wrote {len(pub['written'])} files to {pub['publish_root']}")
        if pub["skipped"]:
            print(f"  skipped: {', '.join(pub['skipped'])}")
    except Exception as e:  # noqa: BLE001
        print(f"error: metrics_plots.publish failed: {e}", file=sys.stderr)
        overall_ok = False

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
