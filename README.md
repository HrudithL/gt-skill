# gtskill

Evaluate a one-paragraph **Great Tables** skill with [chatlas](https://posit-dev.github.io/chatlas/) on Anthropic Claude, then have a second model judge the result.

The agent gets:
- A tiny skill file ([skill/SKILL.md](skill/SKILL.md)) loaded as its system prompt.
- A persistent Python REPL via [`mcp-repl`](https://github.com/posit-dev/mcp-repl) (state survives across tool calls).
- [`nokap`](https://github.com/posit-dev/nokap) to screenshot the rendered table to PNG.

Every run produces a directory under `runs/` with the trace, the generated code, the PNG, programmatic metrics, and the judge's JSON evaluation.

## Setup

```bash
# 1. mcp-repl binary (https://github.com/posit-dev/mcp-repl)
curl -fsSL https://raw.githubusercontent.com/posit-dev/mcp-repl/main/scripts/install.sh | sh

# 2. project deps — install into a .venv at the project root so mcp-repl
#    auto-discovers great_tables + nokap when it walks up from cwd.
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e .

# 3. API key
cp .env.example .env   # then paste ANTHROPIC_API_KEY
```

Chrome / Chromium must be installed (nokap drives it via CDP).

## Run

```bash
python run.py "Build a top-10 sales summary table from /path/to/sales.csv, formatting revenue as USD and highlighting the top row."
```

You will get back the metrics + judgment as JSON, and the same files written under `runs/<timestamp>/`:

| File | What |
| --- | --- |
| `prompt.txt`         | The user prompt |
| `system_prompt.txt`  | Skill + run-dir hint, sent as system prompt |
| `trace.jsonl`        | Every tool request and result, with timestamps |
| `final_text.txt`     | Raw final assistant message |
| `generated.py`       | The agent's final python script |
| `table.png`          | The rendered table |
| `metrics.json`       | Wall-clock, token totals, skill size, PNG size |
| `judgment.json`      | Judge model's scored evaluation |
| `summary.json`       | Metrics + judgment combined |

## Evaluation criteria

Programmatic (in `metrics.json`):
- `wall_clock_seconds` — time from sending the prompt to the agent's final reply
- `tokens.input / output / total` — chatlas session totals
- `skill_tokens` — `chat.token_count(SKILL.md)` — how much budget the skill itself costs
- `png_exists`, `png_bytes` — did the agent actually produce a PNG, and how heavy is it

Subjective, scored 1-5 by the judge LLM (in `judgment.json`):
- `correctness` — does the table answer the prompt
- `aesthetics` — does the PNG look good
- `code_readability` — is the code idiomatic great_tables
- `overall` + `summary`

## Models

Default agent + judge are both `claude-haiku-4-5`. Override per-run with `--agent-model` / `--judge-model`, or globally via `GTSKILL_AGENT_MODEL` / `GTSKILL_JUDGE_MODEL` in `.env`.

## Environment knobs

| Var | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY`  | (required) | API key |
| `GTSKILL_AGENT_MODEL` | `claude-haiku-4-5` | Model under test |
| `GTSKILL_JUDGE_MODEL` | `claude-haiku-4-5` | Judge model |
| `MCP_REPL_BIN`        | `mcp-repl` | Path/name of the mcp-repl binary |
| `MCP_REPL_SANDBOX`    | `danger-full-access` | Passed to `mcp-repl --sandbox`. Use `workspace-write` to keep network disabled, but nokap needs a localhost websocket to Chrome — `danger-full-access` is the easy default for an eval harness. |
