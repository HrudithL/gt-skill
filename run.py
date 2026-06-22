#!/usr/bin/env python3
"""Build a great_tables table from a data file using the Claude Agent SDK.

Usage:
    python run.py "Make a clean table of this data" data/gtcars.csv
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anyio
from dotenv import load_dotenv

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

ROOT = Path(__file__).parent.resolve()
SKILL_NAME = "great-tables"


def block_to_dict(block):
    if isinstance(block, TextBlock):
        return {"type": "text", "text": block.text}
    if isinstance(block, ThinkingBlock):
        return {"type": "thinking", "text": getattr(block, "thinking", "")}
    if isinstance(block, ToolUseBlock):
        return {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
    if isinstance(block, ToolResultBlock):
        content = block.content
        if isinstance(content, list):
            content = [c if isinstance(c, (dict, str)) else repr(c) for c in content]
        return {
            "type": "tool_result",
            "tool_use_id": block.tool_use_id,
            "is_error": block.is_error,
            "content": content,
        }
    return {"type": "unknown", "repr": repr(block)}


def message_to_dict(msg):
    if isinstance(msg, AssistantMessage):
        return {
            "role": "assistant",
            "model": msg.model,
            "message_id": msg.message_id,
            "stop_reason": msg.stop_reason,
            "usage": msg.usage,
            "uuid": msg.uuid,
            "content": [block_to_dict(b) for b in msg.content],
        }
    if isinstance(msg, UserMessage):
        content = msg.content
        if isinstance(content, list):
            content = [block_to_dict(b) for b in content]
        return {
            "role": "user",
            "content": content,
            "tool_use_result": msg.tool_use_result,
            "parent_tool_use_id": msg.parent_tool_use_id,
        }
    if isinstance(msg, SystemMessage):
        return {"role": "system", "subtype": msg.subtype, "data": msg.data}
    if isinstance(msg, ResultMessage):
        return {
            "role": "result",
            "subtype": msg.subtype,
            "is_error": msg.is_error,
            "num_turns": msg.num_turns,
            "duration_ms": msg.duration_ms,
            "total_cost_usd": msg.total_cost_usd,
            "usage": msg.usage,
            "result": msg.result,
        }
    return {"role": "unknown", "repr": repr(msg)}


def _fmt_usage(usage: dict | None) -> str:
    if not usage:
        return ""
    parts = []
    inp = usage.get("input_tokens")
    out = usage.get("output_tokens")
    cache_r = usage.get("cache_read_input_tokens")
    cache_c = usage.get("cache_creation_input_tokens")
    if inp is not None:
        parts.append(f"in={inp}")
    if out is not None:
        parts.append(f"out={out}")
    if cache_r:
        parts.append(f"cache_r={cache_r}")
    if cache_c:
        parts.append(f"cache_w={cache_c}")
    return " ".join(parts)


def log_message(d: dict) -> None:
    role = d.get("role")
    if role == "assistant":
        usage_str = _fmt_usage(d.get("usage"))
        suffix = f"  [{usage_str}]" if usage_str else ""
        for b in d["content"]:
            if b["type"] == "text" and b["text"].strip():
                snippet = b["text"].strip().replace("\n", " ")
                print(f"[assistant] {snippet[:220]}{suffix}")
            elif b["type"] == "tool_use":
                keys = ", ".join(list(b["input"].keys())[:3])
                print(f"[tool-use] {b['name']}({keys}){suffix}")
    elif role == "result":
        cost = d.get("total_cost_usd")
        cost_str = f"${cost:.4f}" if cost is not None else "n/a"
        usage_str = _fmt_usage(d.get("usage"))
        print(
            f"[done] turns={d['num_turns']} cost={cost_str} "
            f"error={d['is_error']} totals={{{usage_str}}}"
        )


async def run(user_prompt: str, data_path: Path, run_dir: Path) -> None:
    full_prompt = (
        f"{user_prompt}\n\n"
        f"Reference data file (read it from this absolute path, do NOT copy it "
        f"into the working directory): {data_path}\n\n"
        f"Working directory: {run_dir}\n"
        f"Final code goes to `table.py` and the rendered image to `table.png`, "
        f"both inside the working directory."
    )

    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            # This is essential to get the agent to use the skill tool and call the great tables skill
            # Without it, only smarter models consider using the skill at all
            "append": (
                "Before starting work, check the available skills listing. "
                "If any skill's description matches the user's task, you MUST "
                "invoke the `Skill` tool to load it before writing code or "
                "running commands. Do not rely on prior knowledge when a "
                "matching skill is available."
            ),
        },
        skills=[SKILL_NAME],
        setting_sources=["project"],
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        cwd=str(ROOT),
        add_dirs=[str(run_dir), str(data_path.parent)],
        permission_mode="bypassPermissions",
        model=os.environ.get("GTSKILL_AGENT_MODEL") or None,
    )

    transcript: list[dict] = []
    async for msg in query(prompt=full_prompt, options=options):
        d = message_to_dict(msg)
        transcript.append(d)
        log_message(d)

    (run_dir / "transcript.json").write_text(
        json.dumps(transcript, indent=2, default=str)
    )


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

    anyio.run(run, args.prompt, data_path, run_dir)

    print(f"\nartifacts in {run_dir}:")
    for f in sorted(run_dir.iterdir()):
        print(f"  - {f.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
