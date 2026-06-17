# gtskill

Evaluate a [great_tables](https://posit-dev.github.io/great-tables/) skill with the
[Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python), then
have a second SDK run judge the result. The runner mirrors
[skillshot](https://github.com/has2k1/skillshot): each run is a Claude Code
workspace, the skill is installed under `.claude/skills/great-tables/`, and the
agent gets a persistent Python REPL via
[`mcp-repl`](https://github.com/posit-dev/mcp-repl).

The agent gets:

- A real Claude Code **skill** at `.claude/skills/great-tables/SKILL.md`,
  surfaced as the `Skill(great-tables)` capability \u2014 the prompt tells the
  model to load it.
- A persistent **Python REPL** via `mcp-repl` (`mcp__repl__repl`, state
  survives across tool calls). `Bash` / `Edit` / `NotebookEdit` are explicitly
  disallowed so all code execution goes through the REPL.
- `Read`, `Write`, `Glob`, `Grep` for filesystem work.
- The chosen dataset CSV copied into the workspace.

Every run produces a directory under `runs/<timestamp>/` containing the trace,
the generated code, the PNG, programmatic metrics, and the judge's evaluation.

## Setup

```bash
# 1. mcp-repl binary
curl -fsSL https://raw.githubusercontent.com/posit-dev/mcp-repl/main/scripts/install.sh | sh

# 2. Project deps. Install into a .venv at the project root so mcp-repl
#    auto-discovers great_tables + nokap by walking up from cwd.
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e .

# 3. API key
cp .env.example .env   # then paste ANTHROPIC_API_KEY
```

The Claude Code CLI is bundled with `claude-agent-sdk` — no separate install.
The agent renders the PNG via `great_tables.GT.gtsave()`.

## Run

```bash
python run.py --list-datasets

python run.py --dataset sp500 \
  "Build a high-level overview table of the S&P 500 over the last 5 years."
```

Per-run artifacts in `runs/<timestamp>/`:

| File | What |
| --- | --- |
| `prompt.txt`            | Full prompt sent to the agent |
| `.claude/skills/...`    | Symlinked skill the agent can load |
| `<dataset>.csv`         | Staged data (when `--dataset` is given) |
| `trace.jsonl`           | One JSON record per SDK message (assistant text, tool calls, tool results, final `ResultMessage`) |
| `transcript.md`         | Human-readable transcript |
| `solution.py`           | The agent's final Python script |
| `table.png`             | The rendered table |
| `metrics.json`          | Model, wall clock, tokens, skill_tokens, num_turns, cost |
| `judge_trace.jsonl`     | Trace for the judge run |
| `judge_transcript.md`   | Judge's transcript |
| `judgment.json`         | Judge's scored evaluation |
| `summary.json`          | Metrics + judgment combined |

## Evaluation criteria

Programmatic (`metrics.json`):

- `model`, `wall_clock_seconds`
- `tokens` — input + output + cache from the SDK's `ResultMessage.usage`
- `skill_tokens` — rough estimate of `SKILL.md` size (chars / 4)
- `num_turns`, `total_cost_usd`, `is_error`

Subjective, 1-5 by the judge (`judgment.json`):

- `correctness` — does the table answer the prompt
- `aesthetics` — does the PNG actually look good (the judge reads the PNG with
  the `Read` tool, which gives it the image)
- `code_readability` — is the code idiomatic great_tables
- `overall` + `summary`

## Models

Defaults: `claude-haiku-4-5` for both. Override per-run with `--agent-model` /
`--judge-model`, or globally via `GTSKILL_AGENT_MODEL` / `GTSKILL_JUDGE_MODEL`.

## Environment knobs

| Var | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY`   | (required) | API key for the SDK |
| `GTSKILL_AGENT_MODEL` | `claude-haiku-4-5` | Model under test |
| `GTSKILL_JUDGE_MODEL` | `claude-haiku-4-5` | Judge model |
| `MCP_REPL_BIN`        | `mcp-repl` | Path/name of the mcp-repl binary |
| `MCP_REPL_SANDBOX`    | `danger-full-access` | Passed to `mcp-repl --sandbox`. Use `workspace-write` to disable network. |
