# Big Color — Diverging Fill

Apply `data_color` with a diverging palette to a signed numeric column so that negatives and positives get opposite hues around a neutral midpoint.

## When to use

- The column contains **signed values** (returns, P&L, YoY change, budget variance, deltas).
- Positive and negative carry **opposite meaning** (up = good and down = bad, or vice versa).
- Zero (or another explicit midpoint) is the natural neutral.

If the column is one-directional (only positive, only "more = more"), use `column_gradient_fill.md` instead.

## Recipe

```python
import numpy as np
from great_tables import GT

max_abs = float(np.nanmax(np.abs(df["return"])))    # symmetric around 0

gt = (
    GT(df, rowname_col="period")
    .fmt_percent(columns="return", decimals=1, force_sign=True)
    .data_color(
        columns="return",
        palette="RdYlGn",                            # red = bad, green = good
        domain=[-max_abs, max_abs],                  # symmetric so 0 is the midpoint
    )
)
```

## Rules

- **Symmetric domain**: always `[-max_abs, max_abs]` (or symmetric around whatever the neutral point is). An asymmetric domain visually shifts the midpoint off zero and makes similar-magnitude gains and losses look different.
- **`force_sign=True`** in the formatter so the `+`/`−` is part of the cell text — the reader shouldn't have to infer sign from color alone.
- **Palette choice**:
  - `"RdYlGn"` — canonical financial (red = loss, green = gain). Avoid if colorblind accessibility is a hard requirement.
  - `"RdBu"` — anomalies, sentiment, thermal-style.
  - `"PuOr"` — balanced, colorblind-safe.
- **Do not also color the text** red/green on top of the fill. Redundant encoding on top of the fill adds no signal and crowds the cell. Pick fill *or* colored-bold-text, not both. (If you want colored bold text for outliers only, use `bold_colored_number.md` and skip the fill.)
- **Leave `truncate=False`** (default) so extreme outliers still get the strongest hue.

## Counts as

One Big Color treatment.
