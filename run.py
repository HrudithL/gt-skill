"""Run the Great Tables skill against an Anthropic model, then judge the result.

Usage:
    python run.py "Build a top-10 sales summary table from this CSV: sales.csv"

Produces a `runs/<timestamp>/` directory containing the trace, the generated
code, the rendered PNG, metrics, and the judge's JSON evaluation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from chatlas import ChatAnthropic, content_image_file, token_usage
from chatlas.types import ContentToolRequest, ContentToolResult


ROOT = Path(__file__).resolve().parent
SKILL_PATH = ROOT / "skill" / "SKILL.md"

# `mcp-repl` is a standalone binary (https://github.com/posit-dev/mcp-repl). It
# discovers `.venv/bin/python` by walking up from cwd, so launching from the
# project root picks up the venv where great_tables + nokap are installed.
MCP_REPL_BIN = os.environ.get("MCP_REPL_BIN", "mcp-repl")
MCP_REPL_SANDBOX = os.environ.get("MCP_REPL_SANDBOX", "danger-full-access")


# ---------- Skill loading ----------

def load_skill(path: Path = SKILL_PATH) -> tuple[dict[str, str], str]:
    """Split a SKILL.md file into (frontmatter dict, body markdown)."""
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body.strip()


# ---------- Judge schema ----------

class CriterionScore(BaseModel):
    score: int = Field(ge=1, le=5, description="1 (terrible) to 5 (excellent)")
    rationale: str


class Judgment(BaseModel):
    correctness: CriterionScore = Field(
        description="Did the generated table actually answer the user's prompt?"
    )
    aesthetics: CriterionScore = Field(
        description="Visual quality of the rendered PNG (layout, alignment, formatting, hierarchy)."
    )
    code_readability: CriterionScore = Field(
        description="Is the generated Python code idiomatic, clean, and easy to follow?"
    )
    overall: int = Field(ge=1, le=5)
    summary: str


JUDGE_SYSTEM = """\
You evaluate the output of a "Great Tables" agent. You receive:
  1. The original user prompt.
  2. The Python code the agent produced.
  3. A PNG screenshot of the rendered table.

Score three subjective criteria from 1 (terrible) to 5 (excellent):
  - correctness:      Does the table actually fulfill the user's request?
  - aesthetics:       Is the rendered PNG visually polished?
  - code_readability: Is the code idiomatic great_tables usage and clean?

Also give an `overall` 1-5 and a short `summary`. Be honest and concise.
"""


# ---------- Helpers ----------

def make_run_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = ROOT / "runs" / stamp
    p.mkdir(parents=True, exist_ok=True)
    return p


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Try plain json.loads first, then pull out the first {...} block."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip common ```json fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass
    # Greedy first { ... last } slice
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return None
    return None


def make_trace_logger(trace_path: Path):
    """Return (on_request, on_result) callbacks that append to a JSONL file.

    Each tool_request records its start wall-clock time; each tool_result
    records its duration (paired on the request id).
    """

    started: dict[str, float] = {}
    run_start = time.perf_counter()

    def _write(record: dict[str, Any]) -> None:
        with trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def _elapsed() -> float:
        return round(time.perf_counter() - run_start, 3)

    def on_request(req: ContentToolRequest) -> None:
        rid = getattr(req, "id", None)
        now = time.perf_counter()
        if rid:
            started[rid] = now
        _write({
            "type": "tool_request",
            "elapsed": _elapsed(),
            "id": rid,
            "name": getattr(req, "name", None),
            "arguments": getattr(req, "arguments", None),
        })

    def on_result(res: ContentToolResult) -> None:
        rid = getattr(res, "id", None)
        duration = None
        if rid and rid in started:
            duration = round(time.perf_counter() - started.pop(rid), 3)
        value = getattr(res, "value", None)
        if value is not None and not isinstance(value, str):
            value = repr(value)
        _write({
            "type": "tool_result",
            "elapsed": _elapsed(),
            "duration_seconds": duration,
            "id": rid,
            "name": getattr(res, "name", None),
            "value": value,
            "error": str(getattr(res, "error", None)) if getattr(res, "error", None) else None,
        })

    return on_request, on_result


# ---------- Transcript / per-turn trace ----------

def _content_text(c: Any) -> str | None:
    for attr in ("text", "content", "value"):
        v = getattr(c, attr, None)
        if isinstance(v, str):
            return v
    return None


def write_transcript_and_turn_trace(
    chat, transcript_path: Path, trace_path: Path
) -> None:
    """Walk chat.get_turns() and write:

    - `transcript_path` (markdown): human-readable conversation including
      thinking, assistant text, tool calls, and tool results.
    - Append per-turn `{type: "turn", ...}` records to `trace_path` with
      token counts (chatlas reports them per assistant turn).
    """
    lines: list[str] = []
    for i, turn in enumerate(chat.get_turns(include_system_prompt=False)):
        role = getattr(turn, "role", "?")
        tokens = getattr(turn, "tokens", None)

        with trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "turn",
                "index": i,
                "role": role,
                "tokens": tokens,
            }, default=str) + "\n")

        lines.append(f"## [{i}] {role}")
        if tokens:
            lines.append(f"_tokens: {tokens}_")
        lines.append("")

        for c in getattr(turn, "contents", []) or []:
            cls = type(c).__name__
            if cls == "ContentThinking":
                txt = _content_text(c) or ""
                if txt.strip():
                    lines.append("**thinking:**")
                    lines.append("> " + txt.replace("\n", "\n> "))
                    lines.append("")
            elif cls == "ContentText":
                txt = _content_text(c) or ""
                if txt.strip():
                    lines.append(txt)
                    lines.append("")
            elif cls == "ContentToolRequest":
                name = getattr(c, "name", "?")
                args = getattr(c, "arguments", None)
                lines.append(f"**tool call:** `{name}`")
                lines.append("```json")
                lines.append(json.dumps(args, indent=2, default=str))
                lines.append("```")
                lines.append("")
            elif cls == "ContentToolResult":
                name = getattr(c, "name", "?")
                value = getattr(c, "value", None)
                if value is not None and not isinstance(value, str):
                    value = repr(value)
                err = getattr(c, "error", None)
                lines.append(f"**tool result:** `{name}`" + (" (error)" if err else ""))
                lines.append("```")
                lines.append((str(err) if err else (value or ""))[:4000])
                lines.append("```")
                lines.append("")
            else:
                txt = _content_text(c)
                if txt:
                    lines.append(f"_({cls})_ {txt}")
                    lines.append("")

        lines.append("---")
        lines.append("")

    transcript_path.write_text("\n".join(lines), encoding="utf-8")



def sum_tokens(chat) -> dict[str, int]:
    """Pull aggregated input/output token counts from chatlas."""
    totals = {"input": 0, "output": 0, "total": 0}

    # Preferred: session-wide usage table.
    try:
        for u in token_usage() or []:
            inp = int(getattr(u, "input", 0) or u.get("input", 0) or 0) if not isinstance(u, dict) else int(u.get("input", 0) or 0)
            out = int(getattr(u, "output", 0) or u.get("output", 0) or 0) if not isinstance(u, dict) else int(u.get("output", 0) or 0)
            totals["input"] += inp
            totals["output"] += out
    except Exception:
        pass

    # Fallback: sum per-turn counts on this chat.
    if totals["input"] == 0 and totals["output"] == 0:
        try:
            for t in chat.get_tokens():
                role = t.get("role")
                n = int(t.get("tokens", 0) or 0)
                if role == "user":
                    totals["input"] += n
                elif role == "assistant":
                    totals["output"] += n
        except Exception:
            pass

    totals["total"] = totals["input"] + totals["output"]
    return totals


# ---------- Agent run ----------

async def run_agent(user_prompt: str, run_dir: Path, model: str) -> dict[str, Any]:
    meta, skill_body = load_skill()
    skill_name = (meta.get("name") or "great_tables").replace("-", "_")
    skill_description = meta.get(
        "description",
        "Reference guidance for building polished tables with great_tables.",
    )
    trace_path = run_dir / "trace.jsonl"

    system_prompt = (
        "You are an autonomous coding agent. Your job is to fulfill the user's "
        "table-building request: produce a polished, correct, publication-quality "
        "table and render it as a PNG image saved to disk.\n\n"
        f"Work in: {run_dir}\n\n"
        "Use the tools available to you. Verify your work before declaring done — "
        "make sure the table renders, the numbers are right, and it actually looks good. "
        "Iterate until you are satisfied.\n\n"
        "Final response format: when (and only when) you are completely done, reply "
        "with a single JSON object and nothing else — no prose, no markdown fences:\n"
        '  {"code": "<the complete final python script>", '
        '"png_path": "<absolute path to the rendered PNG>"}'
    )
    (run_dir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
    (run_dir / "prompt.txt").write_text(user_prompt, encoding="utf-8")

    chat = ChatAnthropic(model=model, system_prompt=system_prompt)

    on_req, on_res = make_trace_logger(trace_path)
    chat.on_tool_request(on_req)
    chat.on_tool_result(on_res)

    # Expose the skill as a tool the model can choose to call on demand.
    skill_invoked = {"count": 0}

    def skill_tool() -> str:
        skill_invoked["count"] += 1
        return skill_body

    skill_tool.__name__ = skill_name
    skill_tool.__doc__ = skill_description
    chat.register_tool(skill_tool)

    await chat.register_mcp_tools_stdio_async(
        command=MCP_REPL_BIN,
        args=[
            "--interpreter", "python",
            "--sandbox", MCP_REPL_SANDBOX,
        ],
    )

    t0 = time.perf_counter()
    try:
        resp = await chat.chat_async(user_prompt, echo="none", stream=False)
        final_text = str(resp)
    finally:
        wall = time.perf_counter() - t0
        try:
            await chat.cleanup_mcp_tools()
        except Exception:
            pass

    # Persist raw final text
    (run_dir / "final_text.txt").write_text(final_text, encoding="utf-8")

    # Build a readable transcript and append per-turn token counts to the trace.
    write_transcript_and_turn_trace(chat, run_dir / "transcript.md", trace_path)

    parsed = extract_json_object(final_text) or {}
    code = parsed.get("code", "")
    png_path = parsed.get("png_path", "")

    if code:
        (run_dir / "generated.py").write_text(code, encoding="utf-8")

    local_png = run_dir / "table.png"
    if png_path and Path(png_path).is_file():
        if Path(png_path).resolve() != local_png.resolve():
            shutil.copyfile(png_path, local_png)
    elif png_path and (run_dir / png_path).is_file():
        shutil.copyfile(run_dir / png_path, local_png)

    tokens = sum_tokens(chat)
    skill_tokens = chat.token_count(skill_body)

    metrics = {
        "model": model,
        "wall_clock_seconds": round(wall, 3),
        "tokens": tokens["total"],
        "skill_tokens": skill_tokens,
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    return {
        "code": code,
        "png_path": str(local_png) if local_png.is_file() else "",
        "metrics": metrics,
        "final_text": final_text,
    }


# ---------- Judge run ----------

def run_judge(
    user_prompt: str,
    agent_result: dict[str, Any],
    run_dir: Path,
    model: str,
) -> dict[str, Any]:
    chat = ChatAnthropic(model=model, system_prompt=JUDGE_SYSTEM)

    parts: list[Any] = []
    parts.append(
        "USER PROMPT:\n" + user_prompt
        + "\n\nGENERATED CODE:\n```python\n" + (agent_result["code"] or "(none)")
        + "\n```\n\nPROGRAMMATIC METRICS (context only, do not score):\n"
        + json.dumps(agent_result["metrics"], indent=2)
    )

    png = agent_result.get("png_path")
    if png and Path(png).is_file():
        parts.append("\nRendered table (PNG attached):")
        parts.append(content_image_file(png))
    else:
        parts.append("\n(No PNG was produced — penalise correctness and aesthetics accordingly.)")

    judgment: Judgment = chat.chat_structured(*parts, data_model=Judgment, echo="none")
    out = judgment.model_dump()
    (run_dir / "judgment.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


# ---------- Entry point ----------

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run + judge the Great Tables skill.")
    parser.add_argument("prompt", help="User prompt describing the table to build.")
    parser.add_argument(
        "--agent-model",
        default=os.environ.get("GTSKILL_AGENT_MODEL", "claude-haiku-4-5"),
    )
    parser.add_argument(
        "--judge-model",
        default=os.environ.get("GTSKILL_JUDGE_MODEL", "claude-haiku-4-5"),
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set (put it in a .env file).")

    run_dir = make_run_dir()
    print(f"Run directory: {run_dir}", file=sys.stderr)

    agent_result = asyncio.run(run_agent(args.prompt, run_dir, args.agent_model))
    print(json.dumps(agent_result["metrics"], indent=2))

    judgment = run_judge(args.prompt, agent_result, run_dir, args.judge_model)

    summary = {
        "run_dir": str(run_dir),
        "metrics": agent_result["metrics"],
        "judgment": judgment,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
