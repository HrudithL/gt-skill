# Big Color — Status Cell Fill

Apply a per-cell background fill to a small categorical status column so each state (pass/fail, on/off, ok/warn/error, tier A/B/C) reads instantly as a colored tag.

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
        style=style.fill(color="#c6efce"),                 # pale green
        locations=loc.body(columns="status", rows=pass_rows),
    )
    .tab_style(
        style=style.fill(color="#ffc7ce"),                 # pale red
        locations=loc.body(columns="status", rows=fail_rows),
    )
)
```

## Recipe (3–4 states, categorical palette)

```python
from great_tables import GT

gt = (
    GT(df)
    .data_color(
        columns="tier",
        palette="Set2",                                    # qualitative, colorblind-friendly
        domain=["A", "B", "C", "D"],                       # explicit category order
    )
)
```

## Rules

- **Pale fills, not saturated ones.** These cells read as *labels*, not warnings. Saturated red for "fail" turns the column into an alarm even for benign rows.
- **Two-state → explicit fill with `tab_style`.** Three-or-more-state → `data_color` with a qualitative palette (`"Set2"`, `"Pastel2"`).
- **Only fill the status column** — do not spread the fill across the whole row (that's `full_row_highlight.md`, a different treatment).
- **Add a redundant encoding** (the text of the state name in the cell, or a short-word label like "Pass"/"Fail") so the cell is readable without color. Do not rely on hue alone.
- **≤4 distinct fills**, otherwise the column becomes a rainbow and the states blur together.

## Counts as

One Big Color treatment for the whole column, regardless of the number of states.
