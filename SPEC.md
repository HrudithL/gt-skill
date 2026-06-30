# Great Tables Skill — Project Specification

## Overview

This project defines and tests an **Agent Skill** for the [Great Tables](https://posit-dev.github.io/great-tables/) Python package. The skill's purpose is to help an LLM agent produce visually appealing, accurate, and informative display tables from user-supplied data, using the `great_tables` Python API.

The project has two top-level concerns:

1. **The Skill** (`gtskill/`) — a standalone `SKILL.md` conforming to the [agentskills.io specification](https://agentskills.io/specification) that can be dropped into any agent and work without external dependencies.
2. **The Testing Harness** (`tests/`) — a human-in-the-loop evaluation framework built on [chatlas](https://github.com/posit-dev/chatlas) and [nokap](https://github.com/posit-dev/nokap) that lets you run prompts against the skill (and against a baseline), collect outputs, and grade results.

---

## Repository Layout

```
gtskill/
├── spec.md                     # This file
│
├── gtskill/                    # The skill (agentskills.io compliant)
│   ├── SKILL.md                # Core: YAML frontmatter + instructions
│   ├── references/             # Loaded on demand by the model
│   │   ├── api.md              # great_tables API surface (method signatures, args)
│   │   └── design.md           # Visual design + aesthetic guidance (grows from failures)
│   └── assets/
│       └── examples/           # Rendered table images used as few-shot exemplars
│
└── tests/
    ├── README.md               # How to run the test harness
    ├── runner.py               # CLI: run one, many, or all prompts (side-by-side by default)
    ├── judge.py                # Optional LLM-as-judge evaluation (blind, separate chat)
    ├── baseline_system_prompt.md   # Generic harness-style system prompt (no skill content)
    ├── judge_system_prompt.md      # Judge-only system prompt
    ├── prompts/                # One JSON file per test case
    │   ├── 001_basic_currency.json
    │   ├── 002_date_formatting.json
    │   └── ...
    └── runs/                   # Output artifacts per run (auto-created)
        └── <run_id>/
            ├── with_skill/
            │   ├── output.py
            │   ├── table.png
            │   ├── transcript.json
            │   ├── metrics.json
            │   └── evaluation.md   # If --judge
            └── without_skill/
                ├── output.py
                ├── table.png
                ├── transcript.json
                ├── metrics.json
                └── evaluation.md   # If --judge
```

---

## The Skill

### Philosophy: Earn the Content

The skill should contain **exactly what the model needs and nothing more**. Overspecification bloats context and reduces the model's ability to reason flexibly.

**Rule:** every line in `SKILL.md` (and every file in `references/`) must be **earned through observed failure**. We do not preemptively write rules for things the model gets right on its own. The skill grows from evidence, not from speculation about what a model might do wrong.

The skill is:
- **Standalone** — no external references, no dependency on llms.txt or online docs.
- **Goal-driven** — it guides the model from a natural language request + data to a finished table.
- **Self-correcting** — it assumes the model will iterate (inspect code, reason about output) before committing to a final answer.
- **Minimal by default** — start with the smallest possible instructions; add content only when testing reveals a recurring failure mode.

### Skill Responsibilities

When activated, the model should:

1. **Understand the request** — parse the user's intent: what story does this table tell? what audience? what data is being shown?
2. **Understand the data** — examine the file or data structure: types, nulls, scale, units, column meanings.
3. **Plan the table** — decide: which columns to show/hide, how to format each one, whether to use spanners, a header/subtitle, row groups, etc.
4. **Write idiomatic GT code** — produce clean, readable Python using `great_tables`.
5. **Iterate via the REPL** — use the available persistent Python session to run, inspect, and refine the table before finalizing.
6. **Commit output** — write the final code to the designated output file. This is a one-way action; once committed, the model does not go back.

### Quality Dimensions (what the skill should optimize for)

These dimensions drive both the human and judge rubrics:

| Dimension | Description |
|---|---|
| **Correctness** | Code runs without errors; table displays expected data accurately |
| **Aesthetics** | Visual polish — header, subtitle, appropriate use of spanners, alignment, color |
| **Formatting intelligence** | Right format method chosen per data type (`fmt_currency`, `fmt_date`, `fmt_number`, `fmt_integer`, etc.) |
| **Contextual judgment** | Appropriate columns shown/hidden; row groups used when data has natural grouping |
| **Code quality** | Readable, idiomatic, no dead code, minimal magic numbers |
| **Efficiency** | Minimal turns / tokens to reach a correct result |

### SKILL.md Format (agentskills.io)

```
---
name: great-tables
description: >
  Build high-quality display tables in Python using the great_tables package.
  Use when a user wants to present data as a formatted, publication-ready table
  — including financial data, summaries, scientific results, or any tabular
  display with formatting, styling, or visual polish requirements.
compatibility: Requires Python 3.10+, great_tables, pandas or polars
allowed-tools: <determined during testing>
---
```

The body starts minimal. The initial draft will only contain:

- **When to use this skill** (trigger conditions)
- **Input contract** (where data lives, where output goes, what counts as "done")
- **Step-by-step process** (the agentic loop above, in short form)
- **Output contract** (write exactly one Python file to the specified path; that is the commit signal)
- **Pointers to references** (when to load `references/api.md` or `references/design.md`)

Anything else — formatting rules, aesthetic rules, gotchas, common mistakes — is **only added after testing demonstrates the model gets it wrong without the rule**. Every addition is tied to a specific failing test case.

### References (loaded on demand)

The `references/` folder follows the agentskills.io progressive-disclosure principle: these files are **only read when the model decides to look something up**. SKILL.md must tell the model when each file is worth loading.

Two files, both kept small:

| File | Purpose | When the model loads it |
|---|---|---|
| `references/api.md` | Method signatures, argument names, and short usage notes for the `great_tables` API surface | When the model needs to confirm exact arguments to a `fmt_*`, `tab_*`, `cols_*`, or styling method |
| `references/design.md` | Visual design and aesthetic guidance — what makes a table "good" | When the model needs guidance on layout, styling, or visual choices |

**`design.md` starts effectively empty.** Like `SKILL.md` itself, it grows only when testing shows that without specific guidance the model produces poor aesthetic choices. A pre-populated `design.md` is the same anti-pattern as a bloated `SKILL.md`: speculation, not evidence.

**Why no `patterns.md` or `recipes.md`:** rendered exemplars in `examples/` cover the "what does a good X table look like" need more efficiently than a prose recipe file.

### Assets

`examples/` holds rendered images of well-made tables (with their source code alongside), one archetype per subfolder. These serve as visual exemplars — concrete demonstrations of what "good" looks like for various table archetypes. SKILL.md may reference these by filename when relevant.

---

## Testing Harness

### Design Goals

- **Mimics reality** — the model runs in the same way it would in a real user interaction: multi-turn, with tool access, iterating until it is satisfied.
- **Side-by-side by default** — every test runs twice: once with the skill, once without. This is the only way to know if the skill is actually helping.
- **Reproducible** — same prompt + same model → same deterministic artifact stored for comparison.
- **Human-interpretable** — you can look at `table.png` and `transcript.json` and immediately understand what happened.
- **Modular** — prompts, runner, and judge are independent. You can swap models, disable the baseline, or add new prompts without changing infrastructure.

### Tooling

| Tool | Role |
|---|---|
| **chatlas** | Drives the LLM conversation; captures full turn-by-turn transcript |
| **mcp-repl** | Provides the model a persistent Python REPL session (token efficiency; not part of skill logic) |
| **nokap** | Renders the final `output.py` to `table.png` after the model commits |
| **LLM judge** (optional) | A second, isolated chat that grades `table.png` + `output.py` on the quality dimensions |

> **Important:** `mcp-repl` is **infrastructure only**. Its presence or absence does not change what the skill instructs the model to do — it only affects token consumption during testing. The skill must produce equivalent results without it.

### Side-by-Side Runs (default behavior)

Every prompt runs **twice in parallel**: once `with_skill`, once `without_skill`. Both runs use:

- The **same user prompt**
- The **same model**
- The **same data files**
- The **same baseline system prompt** (a generic harness-style prompt — see below)
- The **same access** to `mcp-repl`, file I/O, etc.

The **only** difference is whether the skill content (`SKILL.md` + permission to load `references/`) is appended to the system context.

This is opt-out: pass `--no-baseline` to skip the without-skill run when you only want to iterate quickly on the skill side.

### The Baseline System Prompt

Lives at `tests/baseline_system_prompt.md`. It is the same prompt used for **both** runs (with and without skill) — the with-skill run simply gets additional skill content appended.

The baseline prompt mimics a generic agent harness (Claude Code, Codex, etc.):

- Brief role framing ("You are a helpful coding agent.")
- Description of available tools (REPL, file I/O)
- Instruction to commit final work by writing to the designated output path
- **No mention of tables, great_tables, formatting, or anything table-related**

This ensures any difference in output quality is attributable to the skill, not to differing prompts.

### Prompt File Format

Each test case is a JSON file in `tests/prompts/`:

```json
{
  "id": "001_basic_currency",
  "description": "Simple financial table with currency formatting",
  "user_prompt": "Here is a CSV of quarterly revenue by product line. Make me a clean, professional table showing the data. The file is at data/revenue_q1.csv.",
  "data_files": ["data/revenue_q1.csv"],
  "output_path": "runs/<run_id>/<variant>/output.py",
  "tags": ["currency", "simple", "financial"],
  "notes": "Expected: fmt_currency on revenue columns, appropriate header/subtitle"
}
```

Fields:
- `id` — unique slug, used as directory name under `runs/`
- `description` — human-readable summary of what this test exercises
- `user_prompt` — the exact prompt sent to the model
- `data_files` — list of data file paths the model has access to
- `output_path` — where the model should write its final code (`<variant>` is `with_skill` or `without_skill`)
- `tags` — used to filter which tests to run
- `notes` — human hints for what "good" looks like; **never shown to the model and never shown to the judge**

### Runner (`tests/runner.py`)

CLI interface:

```bash
# Run a single test (side-by-side by default)
python tests/runner.py --prompt 001_basic_currency

# Run all tests with a given tag
python tests/runner.py --tag financial

# Run all tests
python tests/runner.py --all

# Run only the with-skill variant (faster iteration loop)
python tests/runner.py --prompt 001_basic_currency --no-baseline

# Run with judge scoring (judge runs on both variants if both present)
python tests/runner.py --prompt 001_basic_currency --judge

# Override judge model
python tests/runner.py --prompt 001_basic_currency --judge --judge-model claude-sonnet-4
```

Each run:
1. Loads the prompt JSON
2. For each variant (`with_skill`, `without_skill` unless `--no-baseline`):
   a. Initializes a fresh `chatlas` `Chat` object with the configured model
   b. Sends the appropriate system prompt (baseline; or baseline + skill content)
   c. Sends the user prompt
   d. Lets the model run until it writes to `output_path` (commit signal)
   e. Invokes `nokap` to render `output.py` → `table.png`
   f. Writes `transcript.json` and `metrics.json`
3. If `--judge` is passed, runs the judge (separately and blindly) on each variant and writes `evaluation.md`

### Metrics (`metrics.json`)

Captured automatically for every run (per variant):

```json
{
  "run_id": "001_basic_currency_20260617_143022",
  "prompt_id": "001_basic_currency",
  "variant": "with_skill",
  "model": "claude-opus-4-5",
  "wall_time_seconds": 42.3,
  "input_tokens": 1840,
  "output_tokens": 612,
  "total_tokens": 2452,
  "turns": 4,
  "repl_calls": 6,
  "committed": true,
  "render_success": true
}
```

A summary file at the `<run_id>/` level captures the comparison: deltas in tokens, turns, wall time between variants.

---

## The Judge

The judge is an **isolated, single-turn evaluation** by a second model. It has no shared context with the building chat and no awareness of which variant it is scoring.

### Design Principles

- **Completely separate chat.** A fresh `chatlas` `Chat` instance with its own system prompt. The judge sees no part of the building model's transcript.
- **Single purpose.** The judge's system prompt establishes one role and one role only: evaluating a finished table against a rubric.
- **Blind.** The judge does not know whether the run it is evaluating used the skill. Each variant is scored independently. Filenames passed to the judge are sanitized (e.g., `output.py` and `table.png`, never `with_skill/output.py`).
- **Configurable model.** Defaults to a cheap model (Claude Haiku) since the judge does a focused evaluation task, not generation. Override via `--judge-model`.
- **Optional.** Off by default — runs incur cost only when explicitly requested.

### Judge Inputs

The judge receives exactly these things and nothing else:

| Input | Purpose |
|---|---|
| Original `user_prompt` | What the human asked for |
| Final `output.py` | The committed code |
| Rendered `table.png` | The visual artifact |
| The `data_files` from the prompt | So the judge can verify accuracy against source data |
| The rubric (embedded in judge system prompt) | The scoring framework |

The judge **does not** see:
- The transcript (would bias toward effort over outcome)
- The `notes` field from the prompt JSON (judge should not be told the "expected" answer)
- The skill content
- The other variant's output
- Which variant this is

### Judge System Prompt

Lives at `tests/judge_system_prompt.md`. Establishes:

- Role: "You are an evaluator. You score data visualization tables against a rubric. You do not generate tables, suggest code, or have a conversation."
- The full rubric with score definitions (1–5 per dimension)
- The required output format (structured markdown — see below)
- An instruction to be specific and to cite evidence from the code and image

### Judge Output (`evaluation.md`)

Structured markdown so it is human-readable and machine-parsable:

```markdown
# Evaluation: <run_id> / <variant>

## Scores
| Dimension | Score | Rationale |
|---|---|---|
| Correctness | 4 | Code runs; one column shows 5 decimal places when 2 would suffice. |
| Aesthetics | 3 | ...
| Formatting | 5 | ...
| Judgment | 4 | ...
| Code quality | 4 | ...
| Efficiency | N/A | (not visible to judge from image+code alone — runner fills from metrics) |

## Overall: 4.0 / 5

## Strengths
- ...

## Improvement suggestions
- ...
```

The `Efficiency` row is filled in by the runner after-the-fact from `metrics.json`, since the judge cannot observe it from artifacts alone.

### Future: Comparative Judging

For now, the judge scores each variant blindly and independently. A future extension may add a comparative pass (show the judge both outputs side-by-side and ask which is better, per dimension). This is deferred until we have enough single-variant judgments to know whether blind scoring discriminates reliably between variants.

---

## Iterative Development Process

The workflow for improving the skill is **evidence-driven**:

```
Run a set of test prompts via runner.py (side-by-side)
        ↓
Review table.png + transcript.json for each run
        ↓
Optionally run --judge for structured scoring
        ↓
Compare with_skill vs without_skill: where did the skill help? where did it not help?
        ↓
Identify a RECURRING failure mode (not a one-off)
        ↓
Add the minimum content to SKILL.md (or references/design.md, or examples/)
that addresses that specific failure
        ↓
Re-run the same prompts to verify improvement + check for regression elsewhere
        ↓
Repeat
```

**The bar for adding content to SKILL.md is high:** the failure must be reproducible and the addition must demonstrably fix it without degrading other tests.

The `runs/` directory becomes your evaluation history. Each run is timestamped, so you can compare runs across skill versions.

---

## Evaluation Rubric (used by both human and judge)

| Dimension | 1 (Poor) | 3 (Acceptable) | 5 (Excellent) |
|---|---|---|---|
| **Correctness** | Code errors or wrong data displayed | Runs, minor data issues | Runs perfectly, all data correct |
| **Aesthetics** | No header, no styling, raw output | Some styling, functional | Polished, publication-ready |
| **Formatting** | Wrong or no format methods | Partially correct | Perfect type-appropriate formatting |
| **Judgment** | Wrong columns shown; no contextual adaptation | Mostly right, minor issues | Thoughtful column selection and grouping |
| **Code quality** | Messy, redundant, hard to read | Readable but verbose | Clean, idiomatic, minimal |
| **Efficiency** | Many redundant turns; needed nudging | Reached result in a few extra turns | Minimal turns, decisive |

---

## Open Questions / Decisions to Make During Development

These are things that will be resolved through testing, not speculation:

1. **Commit signal detection** — how does `runner.py` know the model is done? Most likely: detect when the model writes to `output_path` via a file write tool. Backup: a sentinel phrase in model output.
2. **System prompt injection mechanics** — exactly how the skill content is appended to the baseline prompt depends on chatlas's API.
3. **mcp-repl wiring** — how the chatlas session connects to mcp-repl (MCP tool registration in chatlas).
4. **Optimal SKILL.md length** — start near-empty, grow only from failures. Track token count over time.
5. **Judge model calibration** — does Haiku give discriminating scores, or do we need Sonnet? Determined by running the judge on known-good and known-bad outputs and checking score sensitivity.
6. **Test coverage** — what categories of prompts cover the skill's intended use cases? (financial, scientific, summary stats, time series, comparisons, etc.)
7. **What drives `references/design.md` growth** — which failures are aesthetic enough that putting the rule in a lazily-loaded reference makes more sense than putting it in SKILL.md? Generally: rules the model needs *sometimes* → references; rules the model needs *every time* → SKILL.md.

---

## Tech Stack Summary

| Component | Technology |
|---|---|
| Skill format | agentskills.io SKILL.md |
| LLM driver | chatlas (Python) |
| Persistent REPL | mcp-repl (Rust MCP server, Python interpreter) |
| Table rendering | nokap |
| Primary build LLM | Claude (Anthropic API), configurable |
| Default judge LLM | Claude Haiku, configurable via `--judge-model` |
| Table library | great_tables (Python) |
| Data formats | CSV, Parquet, JSON, raw data in scope |
| Language | Python 3.10+ |
