#!/usr/bin/env python3
"""Regenerate docs/assets/plots/{skill}/{comparator_score,usage}.png.

Reads the local (gitignored) eval-results-demo/{skill}/metrics.json files and
draws with the current eval-results/_plots.py, so the shipped renders carry
whatever wording the tracked plot script has right now. Idempotent -- re-running
overwrites the four skills' plots.

Not part of the CI docs build; it's a one-shot to refresh the pre-rendered
assets after a plot-code change.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO = REPO_ROOT / "eval-results-demo"
DOCS_PLOTS = REPO_ROOT / "docs" / "assets" / "plots"

# Import the tracked plot module the same way make_plots.py did.
sys.path.insert(0, str(REPO_ROOT / "eval-results"))
import _plots as plots  # noqa: E402

SKILLS = ("prose", "scripts", "creator", "house")
PROMPT_IDS = [
    "gtcars_hp_price",
    "islands_sizes",
    "airquality_monthly_summary",
    "gtcars_top10_by_country",
    "sp500_monthly_performance",
    "towny_growth_trends",
]
PROMPT_LABELS = {
    "gtcars_hp_price": "gtcars\nhp/price",
    "islands_sizes": "islands\nsizes",
    "airquality_monthly_summary": "airquality\nmonthly",
    "gtcars_top10_by_country": "gtcars\ntop10/country",
    "sp500_monthly_performance": "sp500\nmonthly",
    "towny_growth_trends": "towny\ngrowth",
}


def main() -> int:
    if not DEMO.exists():
        print(f"error: {DEMO} not found -- this script needs the local demo copy",
              file=sys.stderr)
        return 2

    for skill in SKILLS:
        metrics_path = DEMO / skill / "metrics.json"
        if not metrics_path.exists():
            print(f"skip {skill}: no metrics.json at {metrics_path}")
            continue
        metrics = json.loads(metrics_path.read_text())
        out_dir = DOCS_PLOTS / skill
        out_dir.mkdir(parents=True, exist_ok=True)
        ok_usage = plots.plot_usage(metrics, PROMPT_IDS, PROMPT_LABELS, out_dir / "usage.png")
        ok_cmp = plots.plot_comparator_score(
            metrics, PROMPT_IDS, PROMPT_LABELS, out_dir / "comparator_score.png"
        )
        print(f"{skill}: usage={'ok' if ok_usage else 'skip'}, "
              f"comparator_score={'ok' if ok_cmp else 'skip'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
