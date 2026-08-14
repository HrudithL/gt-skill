# gtskill

[\![Docs](https://img.shields.io/badge/docs-quarto-2a78d6)](https://hrudithl.github.io/gt-skill/)

A tiny, testable evaluation harness for a
[Great Tables](https://posit-dev.github.io/great-tables/) skill that
runs on the [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/).
Given a CSV and a natural-language prompt, the harness mounts exactly
one skill into an ephemeral `.claude/` directory, launches an agent
with a bounded tool set, and captures the rendered table plus the full
conversation trace.

## Quickstart

```bash
git clone https://github.com/HrudithL/gt-skill && cd gt-skill
python -m venv .venv && source .venv/bin/activate
pip install claude-agent-sdk great_tables pandas python-dotenv anyio pillow anthropic plotnine
npm install -g @anthropic-ai/claude-code
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env

python scripts/fetch_data.py                                # provision data/*.csv
python run.py --skill prose --prompt sp500_monthly_performance
```

## What next

The full documentation lives under [`docs/`](docs/) and renders to a
Quarto website:

- **[Setup](docs/setup.qmd)** — prerequisites, install, API key, sample data.
- **[Skills](docs/skills.qmd)** — the four skill variants and when to pick each.
- **[Harness](docs/harness.qmd)** — architecture, sandboxing, sidecar Chrome.
- **[Runner](docs/runner.qmd)** — CLI reference for every `run.py` flag.
- **[Methodology](docs/methodology.qmd)** — how the skill was engineered.
- **[Reproduce](docs/reproduce.qmd)** — end-to-end reproduction guide.

Published site: **<https://hrudithl.github.io/gt-skill/>** (once Pages
is enabled).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. It
describes the branch tree, the review loop, the model-tier rules that
govern how work lands, and the hard prohibitions.

## License

See [LICENSE](LICENSE).
