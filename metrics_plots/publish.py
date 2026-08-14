#!/usr/bin/env python3
"""Copy the deterministic outputs of a full eval-results tree into a
lightweight ``published-metrics/`` tree that is safe to commit.

A full ``eval-results/`` tree contains every per-sample ``table.py``,
``table.png``, and ``transcript.json`` — tens of MB of PNG blobs for even a
minimal run. That's fine as a runtime artifact under ``.gitignore``, but it
would balloon the repo (and every clone) if committed. ``publish`` extracts
only the deterministic summary outputs — the 2 plots per skill and the
overall ranking ``SUMMARY.md`` — into a flat layout that stays under a few
MB total.

Layout produced::

    <publish_root>/
      SUMMARY.md
      creator/
        usage.png
        comparator_score.png
      house/
        ...
      prose/
        ...
      scripts/
        ...

Called at the end of ``run.py --evaluate`` so a real evaluation always
refreshes ``published-metrics/`` alongside the (gitignored) ``eval-results/``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .render import SKILLS


def publish(source_root: Path, publish_root: Path) -> dict:
    """Copy plot PNGs + SUMMARY.md from ``source_root`` to ``publish_root``.

    ``source_root`` is a full eval-results tree (``<skill>/plots/*.png`` +
    top-level ``SUMMARY.md``). ``publish_root`` is emptied of previous plot
    output first so a smaller subsequent run does not leave stale plots
    behind. Returns a small summary dict for the caller.
    """
    source_root = Path(source_root)
    publish_root = Path(publish_root)

    written: list[str] = []
    skipped: list[str] = []

    for skill in SKILLS:
        src_plots = source_root / skill / "plots"
        dst_skill = publish_root / skill
        if dst_skill.is_dir():
            shutil.rmtree(dst_skill)
        if not src_plots.is_dir():
            skipped.append(skill)
            continue
        dst_skill.mkdir(parents=True, exist_ok=True)
        for png in sorted(src_plots.glob("*.png")):
            shutil.copyfile(png, dst_skill / png.name)
            written.append(str(dst_skill / png.name))

    src_summary = source_root / "SUMMARY.md"
    if src_summary.is_file():
        publish_root.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_summary, publish_root / "SUMMARY.md")
        written.append(str(publish_root / "SUMMARY.md"))
    else:
        skipped.append("SUMMARY.md")

    src_results = source_root / "RESULTS.md"
    if src_results.is_file():
        publish_root.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_results, publish_root / "RESULTS.md")
        written.append(str(publish_root / "RESULTS.md"))
    else:
        skipped.append("RESULTS.md")

    return {
        "source_root": str(source_root),
        "publish_root": str(publish_root),
        "written": written,
        "skipped": skipped,
    }
