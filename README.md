# gtskill

A tiny, lightweight harness that uses the [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/) plus a one-paragraph [Great Tables](https://posit-dev.github.io/great-tables/) skill to turn a CSV + a natural-language prompt into a formatted table.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install claude-agent-sdk great_tables pandas python-dotenv anyio
# for the web UI backend:
pip install starlette uvicorn sse-starlette websockets
# also need the Claude Code CLI on PATH:
npm install -g @anthropic-ai/claude-code
```

Create a `.env` with your key:

```
ANTHROPIC_API_KEY=sk-ant-...
# Optional:
GTSKILL_AGENT_MODEL=claude-sonnet-4-5
```

## Usage

```bash
python run.py "Make a clean, professional table of the top 10 cars by MSRP." data/gtcars.csv
```

Each invocation creates a fresh directory under `runs/<timestamp>/` containing:

- `table.py` — the model-authored Python script
- `table.png` — the rendered table image
- `transcript.json` — the full agent conversation (assistant text, tool calls, results)

The CSV stays where it is — the agent reads it by absolute path and is **never** asked to copy it into the run directory.

## How it works

- `.claude/skills/great-tables/SKILL.md` is a one-paragraph skill discovered by the Claude Code CLI via the project skills directory.
- `run.py` calls `claude_agent_sdk.query` with `skills=["great-tables"]` (which auto-enables the `Skill` tool) plus `Read`, `Write`, `Edit`, `Bash`. The agent invokes the `Skill` tool to load `SKILL.md`, then reads the data, writes `table.py`, runs it, and the script saves `table.png` via `GT.save()`.
