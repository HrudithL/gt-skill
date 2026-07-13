# gtskill

A tiny, lightweight harness that uses the [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/) plus a one-paragraph [Great Tables](https://posit-dev.github.io/great-tables/) skill to turn a CSV + a natural-language prompt into a formatted table.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install claude-agent-sdk great_tables pandas python-dotenv anyio
# also need the Claude Code CLI on PATH:
npm install -g @anthropic-ai/claude-code
```

Create a `.env` with your key:

```
ANTHROPIC_API_KEY=sk-ant-...
# Optional (usually chosen with --model instead): a concrete model id override
GTSKILL_AGENT_MODEL=claude-haiku-4-5
```

## Usage

One flag-driven runner drives every flow (the web app calls the same core):

```bash
# one corpus prompt under the prose skill
python run.py --skill prose --prompt sp500_monthly_performance

# convergence: scripts skill, 3 repeats (baseline auto-on), Haiku
python run.py --skill scripts --prompt sp500_monthly_performance --repeat 3

# sweep every easy prompt under the creator skill
python run.py --skill creator --difficulty easy

# an ad-hoc prompt against a chosen data file
python run.py --skill prose --prompt-text "Top 10 cars by MSRP" --data data/gtcars.csv
```

Flags: `--skill {prose,scripts,creator}`; `--prompt NAME` (repeatable) /
`--difficulty {easy,medium,hard,all}` / `--prompt-text TEXT --data PATH`;
`--repeat N`; `--model {haiku,sonnet,opus}`; `--baseline` / `--no-baseline`
(default auto — the no-skill control runs iff `--repeat > 1`).

Each run writes one tree under `runs/<ts>_<skill>_<slug>/`:

- `run.json` — the RunSpec + resolved config + status + timings
- `summary.json` — aggregate pass/fail + tokens/cost across all prompts
- `prompts/<name>/{baseline,repeat_1…N}/` — each with `table.py`, `table.png`,
  `transcript.json`, the data snapshot, and the mounted `.claude/`
- `prompts/<name>/{convergence.json,contact_sheet.png}` — only when `--repeat > 1`

The CSV stays where it is — the agent reads it from a symlink in the run dir and
is **never** asked to copy it elsewhere.

## How it works

- Three self-contained skills live under `.claude/skills/great-tables` (prose),
  `.claude/skills/great-tables-ci` (scripts), and `.claude-skill-creator`
  (creator); the runner mounts exactly one per run into an ephemeral `.claude/`.
- `runner/engine.py` calls `claude_agent_sdk.query` with the one mounted skill
  plus `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`. The agent loads the
  skill, reads the data, writes `table.py`, runs it, and the script renders
  `table.png` via `gt.gtsave("table.png")` (attached to a sidecar Chrome over CDP).
