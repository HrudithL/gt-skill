#!/usr/bin/env python3
"""Build a great_tables table from a data file using the Claude Agent SDK.

Usage:
    python run.py "Make a clean table of this data" data/gtcars.csv
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import anyio
from dotenv import load_dotenv
from nokap import Chrome

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    PermissionResultAllow,
    PermissionResultDeny,
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
SKILL_DIR = ROOT / ".claude" / "skills" / SKILL_NAME

# Harness-specific rendering instructions appended to the claude_code system
# prompt. Kept here (not in the skill) because they describe THIS environment's
# Chrome plumbing, not great_tables itself: the skill must stay portable.
_RENDER_INSTRUCTIONS = """\
## Rendering tables to PNG (this environment)

A long-lived headless Chrome browser is already running for you. To
attach to it, every `table.py` you write MUST follow these two rules:

1. The first import in `table.py` must be `import gtskill_chrome`. This
   module is already in the working directory; importing it rewires
   `nokap` to talk to the running browser over loopback CDP. Without it,
   `gt.gtsave()` will try to spawn its own Chrome and die inside the
   sandbox.
2. End the script with `gt.gtsave("table.png")`. Do NOT use the
   deprecated `gt.save()` — it relies on Selenium/chromedriver and is
   not wired up in this environment.

Run scripts with plain `python table.py`. The harness puts the
project's virtualenv (which has `great_tables`, `nokap`, `pandas`,
`polars`, `PIL`, etc. installed) on PATH ahead of any system Python,
so `python` and `python3` already resolve to the right interpreter.
Do NOT `pip install` anything — the sandbox blocks network access and
everything you need is already available.

You are expected to iterate: run `python table.py`, read `table.png`
back with the Read tool, judge the result against the user's request,
edit `table.py`, and re-run. Each rerun reuses the same browser, so
iteration is cheap.

If `gt.gtsave()` ever fails, STOP and surface the full error verbatim
so the environment can be fixed. Do NOT fall back to PIL/Pillow,
imgkit, wkhtmltoimage, weasyprint, playwright, puppeteer,
`chrome --screenshot`, `.write_raw_html()` / `.as_raw_html()` piped
into another screenshot tool, or any other html-to-image route. The
deliverable is a real great_tables render and nothing else qualifies.
"""


def _path_within(path: str | os.PathLike, root: Path) -> bool:
    """Lexical containment check — does NOT follow symlinks.

    A symlink inside `root` pointing outside still counts as inside.
    `..` segments are normalized away first, so they cannot escape.
    """
    if not path:
        return False
    abs_path = Path(os.path.abspath(os.fspath(path)))
    try:
        abs_path.relative_to(root)
        return True
    except ValueError:
        return False


def _make_can_use_tool(run_dir: Path):
    file_path_keys = {
        "Read": "file_path",
        "Edit": "file_path",
        "Write": "file_path",
        "NotebookEdit": "notebook_path",
    }
    write_tools = {"Edit", "Write", "NotebookEdit"}

    async def can_use_tool(tool_name, tool_input, context):
        key = file_path_keys.get(tool_name)
        if key is None:
            return PermissionResultAllow()

        path = tool_input.get(key, "")
        in_run = _path_within(path, run_dir)
        in_skill = _path_within(path, SKILL_DIR)

        if tool_name in write_tools:
            if in_run:
                return PermissionResultAllow()
            return PermissionResultDeny(
                message=f"{tool_name} denied: {path!r} is outside the run directory."
            )

        if in_run or in_skill:
            return PermissionResultAllow()
        return PermissionResultDeny(
            message=f"Read denied: {path!r} is outside the run directory and skill directory."
        )

    return can_use_tool


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


async def run(
    user_prompt: str, data_path: Path, run_dir: Path, chrome_ws: str
) -> None:
    data_link = run_dir / data_path.name
    if not data_link.is_symlink() and not data_link.exists():
        data_link.symlink_to(data_path)

    claude_link = run_dir / ".claude"
    if not claude_link.is_symlink() and not claude_link.exists():
        claude_link.symlink_to(ROOT / ".claude")

    # Symlink the nokap monkey-patch shim into the run dir so the agent's
    # `table.py` can `import gtskill_chrome` and reuse the sidecar browser.
    shim_link = run_dir / "gtskill_chrome.py"
    if not shim_link.is_symlink() and not shim_link.exists():
        shim_link.symlink_to(ROOT / "gtskill_chrome.py")

    full_prompt = (
        f"{user_prompt}\n\n"
        f"Reference data file (read it from this path inside the working "
        f"directory, do NOT copy it elsewhere): ./{data_link.name}\n\n"
        f"Working directory: {run_dir}\n"
        f"Final code goes to `table.py` and the rendered image to `table.png`, "
        f"both inside the working directory. After writing `table.py`, run it "
        f"and confirm `table.png` was created — the task is not complete until "
        f"the PNG exists on disk. You can iterate: run `python table.py`, "
        f"view `table.png`, refine the script, and re-run until you're "
        f"satisfied with the result."
    )

    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": _RENDER_INSTRUCTIONS,
        },
        skills=[SKILL_NAME],
        setting_sources=["project"],
        # Allowed_tools in ClaudeAgentOptions doesn't shrink the CLIs inventory (this is why the transcript shows all tools), it gets translated into permission rules that are checked when the model tries to call a tool
        # There is a chance that in the system prompt for the agent it may see all available skills and the allowlist just limits running the tools (dependent on the SDK itself), luckily this doesnt happen rn, but could in future possibly
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        cwd=str(run_dir),
        # Sidecar Chrome runs in the parent process (outside sandbox-exec)
        # and the agent's Python connects to it over loopback CDP. The shim
        # `gtskill_chrome.py` (symlinked into run_dir) picks up the WS URL
        # from GTSKILL_CHROME_WS and monkey-patches `nokap._api._browser` so
        # `gt.gtsave("table.png")` attaches to it instead of trying to spawn
        # a new Chrome (which would die inside the sandbox).
        #
        # Forcing TMPDIR=<run_dir> keeps `nokap.from_html`'s temp HTML files
        # inside the cwd that the sandbox already grants write access to, so
        # we don't need to punch a hole for /var/folders.
        #
        # Prepending the project venv to PATH makes plain `python` resolve to
        # the interpreter that actually has great_tables/nokap/pandas
        # installed. Without this the agent's `python` falls through to the
        # macOS system interpreter, the first `import great_tables` fails,
        # and the agent burns a lot of turns trying to `pip install` things
        # the sandbox won't allow (or worse, falls back to PIL).
        env={
            "GTSKILL_CHROME_WS": chrome_ws,
            "TMPDIR": str(run_dir),
            "PATH": f"{ROOT / '.venv' / 'bin'}:{os.environ.get('PATH', '')}",
            "VIRTUAL_ENV": str(ROOT / ".venv"),
        },
        permission_mode="default",
        can_use_tool=_make_can_use_tool(run_dir),
        sandbox={
            "enabled": True,
            "autoAllowBashIfSandboxed": True,
            # Agent's Python opens a TCP connection to 127.0.0.1:<port> on the
            # sidecar Chrome. Keep loopback access enabled.
            "network": {"allowLocalBinding": True},
        },
        model=os.environ.get("GTSKILL_AGENT_MODEL") or None,
    )

    async def prompt_stream():
        yield {
            "type": "user",
            "message": {"role": "user", "content": full_prompt},
            "parent_tool_use_id": None,
            "session_id": "default",
        }

    transcript: list[dict] = []
    async for msg in query(prompt=prompt_stream(), options=options):
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

    # Launch one headless Chrome in the parent process (outside the agent's
    # macOS sandbox). The agent will attach to it over CDP via `nokap`/`gtsave`.
    # `--user-data-dir` keeps this Chrome isolated from any normal Chrome the
    # user may already have open.
    chrome_profile = run_dir / ".chrome-profile"
    chrome_profile.mkdir(exist_ok=True)
    chrome = Chrome(extra_args=[f"--user-data-dir={chrome_profile}"])
    print(f"chrome:  {chrome.ws_url}\n")

    try:
        anyio.run(run, args.prompt, data_path, run_dir, chrome.ws_url)
    finally:
        chrome.close()
        # The Chrome user-data-dir holds the sidecar's cache, cookies,
        # GPU shader cache, Crashpad database, and singleton lock. None
        # of it is referenced again once Chrome has exited, so clean it
        # up to keep run dirs tidy. ignore_errors covers the (harmless)
        # case where Chrome is still flushing files on a slow shutdown.
        shutil.rmtree(chrome_profile, ignore_errors=True)

    print(f"\nartifacts in {run_dir}:")
    for f in sorted(run_dir.iterdir()):
        print(f"  - {f.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
