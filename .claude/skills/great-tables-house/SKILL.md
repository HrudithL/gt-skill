---
name: great-tables-house
description: Use when building a table with `great_tables`, `gt.GT`, or `gtsave`, or turning tabular data (CSV, DataFrame, spreadsheet) into a rendered PNG. This is the THIN variant — one worked reference table plus a short per-column-kind rules file, no flowchart and no archetype directory. Prefer this over `great-tables`/`great-tables-ci` when you want the minimal path — read one annotated script, pattern-match the section that fits your data, adapt it, done. Prefer the sibling `great-tables`/`great-tables-ci` skills instead when you want the full deterministic 7-step procedure with a per-data-shape reference router and (for `great-tables-ci`) a mechanical checker.
---

# Great Tables — House Format

The mechanism is deliberately thin: **one script, one rules file, no
procedure.**

1. Read `scripts/house_table.py` once. It is both the worked example (run
   it directly to see `house_table.png`, the canonical reference render)
   and a helper module (`PALETTE` + `frame`/`finalize`/`band`/`stripe`/
   `stub_tint`/`heatmap`/`status_chip`/`summary_row`/`group_emphasis`/
   `humanize_labels`) you import into your own script the same way
   `great-tables-ci` imports `gt_consistency.py`.
2. Find the block in `house_table.py` that matches your data's shape — a
   plain magnitude, a currency hero measure, a signed percent, a
   categorical status column, a stub, a group, a summary row, a missing
   value — and copy/adapt it.
3. Open `references/RULES.md` for the one rule that applies to the
   column kind you just matched (it points back at the function/section
   in `house_table.py` by name — it does not duplicate the code).

That's the whole workflow. Nothing else to read.

## What this skill deliberately does NOT have

- **No numbered flowchart.** `great-tables`/`great-tables-ci` drive every
  table through a fixed 7-step sequence with a reference-router file
  (`REFERENCE.md`) that dispatches each decision to a pinned value. This
  skill has neither the sequence nor the router — one script's worked
  example stands in for both.
- **No per-archetype example directory** (`assets/examples/<shape>/`).
  `house_table.py` IS the one worked example; there is no second example
  to pick between.
- **No CI checker.** `great-tables-ci` ships `gt_check.py` and a
  run-until-`PASS` loop. This skill has no checker — the palette and
  helper functions in `house_table.py` are the only guardrail, and you're
  trusted to read the rendered PNG yourself.

This is additive: it does not change or replace `great-tables` or
`great-tables-ci`. Pick whichever skill's mechanism fits — thin worked
example here, full flowchart there.

## Rule 0 — the user's prompt overrides everything

Every rule in `references/RULES.md` and every pattern in
`house_table.py` is a **default**. An explicit instruction in the user's
prompt wins (a requested font, a column's format, "bold the totals,"
"show all rows"). Silently drop the conflicting default.

## The mandatory renderer

End every table with **`gt.gtsave("table.png", ...)`** — never `.save()`
(deprecated), never `.as_raw_html()` + a screenshot tool, never PIL/
imgkit/wkhtmltoimage/Playwright/Selenium. `finalize()` in
`house_table.py` wraps this with the house-format `expand=15, zoom=2.0`
defaults. If rendering fails, stop and surface the error verbatim — a
fallback produces a fake table.

## Imports

```python
from great_tables import GT, md, html, style, loc
```
