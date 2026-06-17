"""Run the great_tables skill via the Claude Agent SDK, then have the SDK
judge the result.

Architecture (mirrors https://github.com/has2k1/skillshot):

  * Each run gets a directory under ``runs/<timestamp>/`` that doubles as the
    Claude Code workspace.
  * ``skill/`` is symlinked into ``<run_dir>/.claude/skills/great-tables/`` so
    the Claude Agent SDK auto-discovers it as a real skill (the agent sees a
    ``Skill(great-tables)`` capability and loads SKILL.md on demand).
  * If ``--dataset`` is given, the matching CSV from ``data/`` is copied into
    the workspace.
  * ``mcp-repl`` is wired in as an external stdio MCP server, exposing a
    persistent Python REPL (``mcp__repl__repl``) to the agent.
  * The agent is told to leave ``solution.py`` and ``table.png`` in the
    workspace when it's done. No JSON-extraction wrangling — we just look for
    those two files afterwards.
  * The judge is a second SDK run in the same workspace with just ``Read`` and
    ``Write``; it reads ``prompt.txt`` / ``solution.py`` / ``table.png`` and
    writes ``judgment.json``.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)


# ---------- Paths & config ----------------------------------------------------

ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / "skill"
DATA_DIR = ROOT / "data"

MCP_REPL_BIN = os.environ.get("MCP_REPL_BIN", "mcp-repl")
MCP_REPL_SANDBOX = os.environ.get("MCP_REPL_SANDBOX", "danger-full-access")

DEFAULT_AGENT_MODEL = os.environ.get("GTSKILL_AGENT_MODEL", "claude-haiku-4-5")
DEFAULT_JUDGE_MODEL = os.environ.get("GTSKILL_JUDGE_MODEL", "claude-haiku-4-5")


# ---------- Workspace staging -------------------------------------------------

def make_run_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = ROOT / "runs" / stamp
    p.mkdir(parents=True, exist_ok=True)
    return p


def stage_workspace(run_dir: Path, dataset: str | None) -> Path | None:
    """Wire ``.claude/skills/great-tables`` + drop the dataset CSV in.

    Returns the staged dataset path (relative-friendly), or None.
    """
    claude_dir = run_dir / ".claude"
    skills_dir = claude_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    link = skills_dir / "great-tables"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(SKILL_DIR.resolve())

    settings = {
        "defaultMode": "dontAsk",
        "permissions": {
            "allow": [
                "Skill(great-tables)",
                "mcp__repl",
                "Read",
                "Write",
                "Edit",
                "Bash",
                "Glob",
                "Grep",
            ],
            "deny": [],
        },
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    if not dataset:
        return None
    src = DATA_DIR / f"{dataset}.csv"
    if not src.is_file():
        avail = sorted(p.stem for p in DATA_DIR.glob("*.csv"))
        raise SystemExit(
            f"Unknown dataset {dataset!r}. Available: {', '.join(avail)}"
        )
    dst = run_dir / src.name
    shutil.copyfile(src, dst)
    return dst


# ---------- Tracing -----------------------------------------------------------

def _serialize(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[no-any-return]
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def _tool_result_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for c in content:
            if isinstance(c, dict):
                parts.append(c.get("text", "") or c.get("type", ""))
            else:
                parts.append(str(c))
        return "\n".join(p for p in parts if p)
    return str(content)


def log_message(msg: Any, trace_path: Path, transcript_lines: list[str]) -> None:
    """Append a structured trace record and pretty-print a transcript line."""

    record: dict[str, Any] = {"type": type(msg).__name__, "ts": time.time()}

    if isinstance(msg, AssistantMessage):
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        calls: list[dict[str, Any]] = []
        for b in msg.content:
            if isinstance(b, ThinkingBlock):
                thought = getattr(b, "thinking", "") or getattr(b, "text", "")
                if thought:
                    thinking_parts.append(thought)
                    transcript_lines.append(
                        "\n**thinking:**\n> " + thought.replace("\n", "\n> ") + "\n"
                    )
            elif isinstance(b, TextBlock):
                text_parts.append(b.text)
                transcript_lines.append(b.text)
            elif isinstance(b, ToolUseBlock):
                calls.append({"name": b.name, "input": b.input, "id": b.id})
                transcript_lines.append(
                    f"\n**tool call:** `{b.name}`\n```json\n"
                    + json.dumps(b.input, indent=2, default=str)
                    + "\n```\n"
                )
        if thinking_parts:
            record["thinking"] = "\n".join(thinking_parts)
        if text_parts:
            record["text"] = "\n".join(text_parts)
        if calls:
            record["tool_calls"] = calls

    elif isinstance(msg, UserMessage):
        results: list[dict[str, Any]] = []
        for b in getattr(msg, "content", []) or []:
            if isinstance(b, ToolResultBlock):
                content = _tool_result_text(b.content)
                results.append(
                    {
                        "tool_use_id": b.tool_use_id,
                        "is_error": bool(getattr(b, "is_error", False)),
                        "content": content[:8000],
                    }
                )
                transcript_lines.append(
                    f"\n**tool result** (id={b.tool_use_id}):\n```\n"
                    + content[:4000]
                    + "\n```\n"
                )
        if results:
            record["tool_results"] = results

    elif isinstance(msg, ResultMessage):
        record["result"] = {
            "num_turns": msg.num_turns,
            "duration_ms": getattr(msg, "duration_ms", None),
            "total_cost_usd": msg.total_cost_usd,
            "usage": getattr(msg, "usage", None),
            "is_error": msg.is_error,
        }
    else:
        record["raw"] = _serialize(msg)

    with trace_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=_serialize) + "\n")


def _sum_tokens(usage: Any) -> int:
    if not isinstance(usage, dict):
        return 0
    return int(
        (usage.get("input_tokens") or 0)
        + (usage.get("output_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0)
        + (usage.get("cache_read_input_tokens") or 0)
    )


# ---------- SDK options builder ----------------------------------------------

def build_options(run_dir: Path, model: str, *, agent: bool) -> ClaudeAgentOptions:
    mcp_servers: dict[str, Any] = {}
    allowed = ["Read", "Glob", "Grep", "Write"]
    disallowed: list[str] = []
    if agent:
        mcp_servers["repl"] = {
            "type": "stdio",
            "command": MCP_REPL_BIN,
            "args": [
                "--interpreter", "python",
                "--sandbox", MCP_REPL_SANDBOX,
            ],
        }
        allowed = [
            "Read", "Write", "Glob", "Grep",
            "Skill",
            "mcp__repl__repl",
            "mcp__repl__repl_reset",
        ]
        # Force code execution through mcp-repl (persistent Python session)
        # instead of one-shot Bash invocations. Without this the model picks
        # `python solution.py` via Bash and never exercises the REPL.
        

    return ClaudeAgentOptions(
        cwd=str(run_dir),
        model=model,
        max_turns=40 if agent else 10,
        permission_mode="bypassPermissions",
        setting_sources=["project"],   # load .claude/settings.json from cwd
        mcp_servers=mcp_servers,
        allowed_tools=allowed,
        env={"CLAUDECODE": "", "MPLBACKEND": "Agg"},
    )


# ---------- Actor ------------------------------------------------------------

AGENT_INSTRUCTIONS = """\
You are an autonomous coding agent. Your job is to fulfill the user's
request: produce a polished, correct, publication-quality artifact saved to
disk.

You are running in the current working directory. When you are done, these two
files MUST exist there:

  - solution.py : the complete final Python script that produces the artifact
  - table.png   : the rendered artifact as a PNG

Verify your work before declaring done \u2014 make sure it renders, the numbers
are right, and it actually looks good. When both files exist, reply with a
short confirmation and stop.
"""


async def run_agent(
    user_prompt: str,
    run_dir: Path,
    model: str,
    dataset_path: Path | None,
) -> dict[str, Any]:
    trace_path = run_dir / "trace.jsonl"
    transcript_lines: list[str] = []

    dataset_block = ""
    if dataset_path is not None:
        dataset_block = (
            f"\n\nData source: a CSV file is available at {dataset_path.name} "
            "(in the working directory). Load it with pandas."
        )

    full_prompt = (
        AGENT_INSTRUCTIONS
        + "\n\n---\n\nUSER REQUEST:\n"
        + user_prompt
        + dataset_block
    )
    (run_dir / "prompt.txt").write_text(full_prompt, encoding="utf-8")

    options = build_options(run_dir, model, agent=True)

    result: ResultMessage | None = None
    error: str | None = None
    t0 = time.perf_counter()
    try:
        async for msg in query(prompt=full_prompt, options=options):
            log_message(msg, trace_path, transcript_lines)
            if isinstance(msg, ResultMessage):
                result = msg
    except Exception as exc:  # noqa: BLE001 — SDK raises bare Exception
        error = repr(exc)
    wall = time.perf_counter() - t0

    (run_dir / "transcript.md").write_text(
        "\n".join(transcript_lines), encoding="utf-8"
    )

    code_path = run_dir / "solution.py"
    png_path = run_dir / "table.png"

    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    metrics = {
        "model": model,
        "wall_clock_seconds": round(wall, 3),
        "tokens": _sum_tokens(getattr(result, "usage", None)),
        # Cheap approximation; the SDK doesn't expose a tokenizer.
        "skill_tokens": max(1, len(skill_text) // 4),
        "num_turns": result.num_turns if result else 0,
        "total_cost_usd": result.total_cost_usd if result else 0.0,
        "is_error": bool(error) or (result.is_error if result else True),
    }
    if error:
        metrics["error"] = error
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )

    return {
        "code_path": str(code_path) if code_path.is_file() else "",
        "png_path": str(png_path) if png_path.is_file() else "",
        "metrics": metrics,
    }


# ---------- Judge ------------------------------------------------------------

JUDGE_INSTRUCTIONS = """\
You are a strict, fair judge. You are evaluating the output of an autonomous
agent that was asked to build a polished table.

The working directory contains:
  - prompt.txt   : the original user prompt — read it first
  - solution.py  : the agent's generated Python (may be missing)
  - table.png    : the rendered table as a PNG (may be missing — read it with
                   the Read tool so you can actually see it)

Score three criteria from 1 (terrible) to 5 (excellent):
  - correctness:      Does the table actually fulfill the user's request?
  - aesthetics:       Is the rendered PNG visually polished (alignment,
                      hierarchy, formatting, no clutter)?
  - code_readability: Is the code idiomatic great_tables usage and clean?

Then use the Write tool to create judgment.json in the working directory with
EXACTLY this shape (no extra keys, no prose outside JSON):

{
  "correctness":      {"score": <1-5>, "rationale": "<one or two sentences>"},
  "aesthetics":       {"score": <1-5>, "rationale": "<one or two sentences>"},
  "code_readability": {"score": <1-5>, "rationale": "<one or two sentences>"},
  "overall":          <1-5>,
  "summary":          "<short overall summary>"
}

If a required file is missing, score that dimension as 1 and say so in the
rationale. After writing judgment.json, reply with one short confirmation line
and stop.
"""


async def run_judge(run_dir: Path, model: str) -> dict[str, Any]:
    trace_path = run_dir / "judge_trace.jsonl"
    transcript_lines: list[str] = []

    options = build_options(run_dir, model, agent=False)

    t0 = time.perf_counter()
    error: str | None = None
    try:
        async for msg in query(prompt=JUDGE_INSTRUCTIONS, options=options):
            log_message(msg, trace_path, transcript_lines)
    except Exception as exc:  # noqa: BLE001
        error = repr(exc)
    wall = round(time.perf_counter() - t0, 3)

    (run_dir / "judge_transcript.md").write_text(
        "\n".join(transcript_lines), encoding="utf-8"
    )

    judgment_path = run_dir / "judgment.json"
    if judgment_path.is_file():
        try:
            return json.loads(judgment_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return {
                "error": f"judgment.json present but unparseable: {exc!r}",
                "judge_wall_seconds": wall,
            }
    return {
        "error": f"no judgment.json produced",
        "judge_wall_seconds": wall,
        "judge_error": error,
    }


# ---------- Entry point ------------------------------------------------------

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Run + judge the great-tables skill via the Claude Agent SDK."
    )
    parser.add_argument("prompt", nargs="?", help="User prompt describing the table.")
    parser.add_argument(
        "--dataset",
        default=None,
        help="Name of a CSV in data/ (without .csv). See --list-datasets.",
    )
    parser.add_argument("--list-datasets", action="store_true")
    parser.add_argument("--agent-model", default=DEFAULT_AGENT_MODEL)
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL)
    args = parser.parse_args()

    if args.list_datasets:
        for p in sorted(DATA_DIR.glob("*.csv")):
            print(p.stem)
        return
    if not args.prompt:
        sys.exit("prompt is required (or use --list-datasets).")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set (put it in a .env file).")

    run_dir = make_run_dir()
    print(f"Run directory: {run_dir}", file=sys.stderr)
    dataset_path = stage_workspace(run_dir, args.dataset)

    agent_result = asyncio.run(
        run_agent(args.prompt, run_dir, args.agent_model, dataset_path)
    )
    print(json.dumps(agent_result["metrics"], indent=2))

    judgment = asyncio.run(run_judge(run_dir, args.judge_model))

    summary = {
        "run_dir": str(run_dir),
        "metrics": agent_result["metrics"],
        "code_path": agent_result["code_path"],
        "png_path": agent_result["png_path"],
        "judgment": judgment,
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
