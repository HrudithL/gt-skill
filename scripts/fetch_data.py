#!/usr/bin/env python3
"""Materialize the sample CSVs the harness uses into ``data/``.

Reads pandas DataFrames from ``great_tables.data`` (the sample datasets the
Great Tables package ships for its own examples) and writes each one as a
CSV under ``data/`` at the repository root. ``data/`` is gitignored, so a
fresh clone doesn't ship the CSVs -- run this once after cloning and the
harness has everything it needs.

Usage:
    python scripts/fetch_data.py             # write missing CSVs; skip existing
    python scripts/fetch_data.py --force     # overwrite existing CSVs too
    python scripts/fetch_data.py --list      # just print what would be written

The dataset names are read directly from ``great_tables.data``; whatever
subset that module exposes as pandas DataFrames is materialized.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import great_tables.data as gt_data
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def _dataframe_attrs() -> list[str]:
    """Return the sorted list of public attribute names in ``gt_data`` that
    hold ``pandas.DataFrame`` instances."""
    names: list[str] = []
    for name in dir(gt_data):
        if name.startswith("_"):
            continue
        obj = getattr(gt_data, name)
        if isinstance(obj, pd.DataFrame):
            names.append(name)
    return sorted(names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing CSVs instead of skipping them.")
    parser.add_argument("--list", action="store_true",
                        help="Print the dataset names that would be written and exit.")
    args = parser.parse_args(argv)

    names = _dataframe_attrs()
    if args.list:
        for n in names:
            print(n)
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    for name in names:
        target = DATA_DIR / f"{name}.csv"
        if target.exists() and not args.force:
            skipped += 1
            continue
        df = getattr(gt_data, name)
        df.to_csv(target, index=False)
        written += 1
        print(f"wrote {target.relative_to(REPO_ROOT)}")

    print(f"\n{written} written, {skipped} skipped "
          f"(use --force to overwrite).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
