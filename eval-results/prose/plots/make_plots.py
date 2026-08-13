#!/usr/bin/env python3
"""Three plots for the `prose` skill's full sweep, built from `../metrics.json`
(see `eval-results/_lib.py` for how that file was produced, and
`eval-results/_plots.py` for the actual plot-drawing logic shared by all 4
skills' copies of this script).

Run with the repo's venv active:

    python eval-results/prose/plots/make_plots.py

Regenerates `usage.png`, `consistency.png`, `comparator_score.png` next to
this script and refreshes `../metrics.json` from the latest
`runs/sweep/*_prose_6prompts` sweep first.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
EVAL_RESULTS = SKILL_DIR.parent
SKILL = "prose"

sys.path.insert(0, str(EVAL_RESULTS))
import _lib as lib  # noqa: E402
import _plots as plots  # noqa: E402

PROMPT_IDS = [p for p, _ in lib.PROMPTS]
PROMPT_LABELS = {
    "gtcars_hp_price": "gtcars\nhp/price",
    "islands_sizes": "islands\nsizes",
    "airquality_monthly_summary": "airquality\nmonthly",
    "gtcars_top10_by_country": "gtcars\ntop10/country",
    "sp500_monthly_performance": "sp500\nmonthly",
    "towny_growth_trends": "towny\ngrowth",
}


def _load_metrics() -> dict:
    metrics_path = SKILL_DIR / "metrics.json"
    return lib.dump_metrics(SKILL, metrics_path, max_workers=6)


def main() -> None:
    metrics = _load_metrics()
    plots.plot_usage(metrics, PROMPT_IDS, PROMPT_LABELS, SKILL, HERE / "usage.png")
    plots.plot_consistency(metrics, PROMPT_IDS, PROMPT_LABELS, SKILL, HERE / "consistency.png")
    plots.plot_comparator_score(metrics, PROMPT_IDS, PROMPT_LABELS, SKILL, HERE / "comparator_score.png")
    lib.curate_runs(metrics, SKILL_DIR / "samples")
    print(f"wrote 3 plots to {HERE} and curated runs under {SKILL_DIR / 'runs'}")


if __name__ == "__main__":
    main()
