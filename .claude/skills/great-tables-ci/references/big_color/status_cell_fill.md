# Big Color — Status Cell Fill

Per-cell fill for a small categorical status column (pass/fail, on/off, ok/warn/error, tier A/B/C) so each state reads as a colored tag.

## When to use

- One column encodes a **discrete state** with 2–4 possible values.
- The state has meaning (good/bad, active/inactive, tier) and the reader scans for it.
- The column is short/narrow — the fills act as pill labels, not as data bars.

If the states are numeric and ordered, use `column_gradient_fill.md`. If sign matters, use `diverging_fill.md`.

## Recipe (binary, explicit)

```python
from great_tables import GT, style, loc

pass_rows = df.index[df["status"] == "pass"].tolist()
fail_rows = df.index[df["status"] == "fail"].tolist()

gt = (
    GT(df)
    .tab_style(
        style=[style.fill(color="#2F4A38"), style.text(color="#ffffff")],   # Forest solid = good
        locations=loc.body(columns="status", rows=pass_rows),
    )
    .tab_style(
        style=[style.fill(color="#5C2E2E"), style.text(color="#ffffff")],   # Oxblood solid = bad
        locations=loc.body(columns="status", rows=fail_rows),
    )
)
```

## Recipe (3–4 states, Dark Academia solids)

```python
from great_tables import GT

gt = (
    GT(df)
    .data_color(
        columns="tier",
        palette=["#2F4A38", "#9A7B33", "#5C2E2E"],         # DA solids, one per state
        domain=["A", "B", "C"],                            # explicit category order
        autocolor_text=True,                               # white/dark text auto-contrasts on each solid
    )
)
```

## Rules

- **Solid DA hexes, white text.** Per `references/palettes.md` §1: Forest `#2F4A38` = good/pass, Oxblood `#5C2E2E` = bad/fail, Navy `#22384F` = neutral, Ochre `#9A7B33` / Espresso `#4A3A2C` / Tan `#8A7452` = further tiers. Never a pale tint.
- **Two-state** → `tab_style`. **3–4 states** → `data_color` with DA solid hexes (not a brewer palette).
- **Status column only** — not the row (`full_row_highlight.md` is the row treatment).
- **Add a redundant text label** (e.g. "Pass"/"Fail") — don't rely on hue alone.
- **≤4 distinct fills.**

## Counts as

One Big Color treatment for the whole column, regardless of the number of states.
