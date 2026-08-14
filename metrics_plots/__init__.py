#!/usr/bin/env python3
"""Plot + metric regeneration for an eval-results tree.

Two entry points:

- ``render_skill(root, skill)`` — read ``root/skill/samples/`` (and any cached
  ``root/skill/metrics.json``), (re)compute the per-skill metrics, and write
  the plots into ``root/skill/plots/``. Adaptive layout: one condensed plot
  pair when every difficulty has ≤3 prompts, one plot per difficulty when
  any difficulty has >3.
- ``render_all(root)`` — the same for every skill directory found under
  ``root`` (the 4 known skills: creator / house / prose / scripts).

This is what ``run.py --evaluate`` calls at end-of-run against the runtime
``eval-results/`` tree. It also works against the frozen
``eval-results-demo/`` tree (which has cached ``metrics.json`` but no
per-sample transcripts) — in that case the render skips recomputation and
just re-draws plots from the cached metrics.
"""

from __future__ import annotations

from .render import render_all, render_skill
from .summary import write_summary

__all__ = ["render_all", "render_skill", "write_summary"]
