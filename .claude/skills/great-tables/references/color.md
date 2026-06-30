# Color Reference — Scenario Recipes

Scenario-specific applications of the color rules in `SKILL.md` → Design Guide. Load this file when you've already decided you need color and you want a concrete recipe for a common situation. The rules themselves (color budget, `data_color` trigger, structural element treatment, palette selection) live in `SKILL.md` and are not repeated here.

---

## Scenario 1 — Financial signed-delta column

**Situation.** A column of signed values (returns, P&L, YoY change, budget variance) where negatives and positives carry opposite meaning.

**Treatment.** One **loud** treatment: diverging `data_color` on that single column. The column is the story.

```python
from great_tables import GT, loc

gt = (
    GT(df, rowname_col="period")
    .fmt_percent(columns="return", decimals=1, force_sign=True)
    .data_color(
        columns="return",
        palette="RdYlGn",
        domain=[-max_abs, max_abs],   # symmetric around 0
    )
)
```

**Notes.**
- Always compute `max_abs = max(abs(df["return"].min()), abs(df["return"].max()))` so the domain is symmetric and the neutral midpoint aligns with zero.
- Do **not** also color text red/green on top of the fill — that's stacking two loud treatments on the same cell. Pick one.
- Use `force_sign=True` in `fmt_percent` / `fmt_number` so the `+`/`−` is part of the cell text.

---

## Scenario 2 — Ranking / top-N highlight

**Situation.** A leaderboard or top-N list where the rank order itself is the message.

**Treatment.** One **loud** treatment: highlight only the top 1–3 rows (or just the #1 row). Do not color every row.

```python
top_3 = df.nsmallest(3, "rank").index.tolist()   # rank=1 is best

gt = (
    GT(df, rowname_col="rank")
    .tab_style(
        style=style.fill(color="#fff4cc"),       # warm pale highlight
        locations=loc.body(rows=top_3),
    )
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(rows=top_3),
    )
)
```

**Notes.**
- For a 10-row table, fewer than 5 rows colored = signal. More than half colored = noise.
- A `data_color` gradient across all rows is the wrong tool here — it implies a continuous magnitude, but ranking is *ordinal* and the top values usually carry disproportionate meaning.

---

## Scenario 3 — Heatmap-style full-fill

**Situation.** A genuine matrix view (months × metrics, regions × products, hours × days) where every cell is comparable on the same scale.

**Treatment.** One **loud** treatment: sequential `data_color` across the whole value matrix. This is the *only* scenario where filling the majority of cells is correct.

```python
value_cols = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]

gt = (
    GT(df, rowname_col="metric")
    .data_color(
        columns=value_cols,
        palette="Blues",
        domain=[df[value_cols].min().min(), df[value_cols].max().max()],
    )
)
```

**Notes.**
- The domain must be computed across the entire matrix, not per-column — otherwise cells with similar values get different colors and the comparison breaks.
- Stub (`metric`) stays unfilled; it's an identifier.
- Keep quiet treatments to a minimum here — the matrix fill is already carrying a lot of visual weight.

---

## Scenario 4 — Binary status indicators (pass/fail, on/off, ok/error)

**Situation.** A small categorical column with two states that carry meaning.

**Treatment.** One **loud** treatment: conditional fill on the status column only. Two colors, nothing more.

```python
pass_rows = df[df["status"] == "pass"].index.tolist()
fail_rows = df[df["status"] == "fail"].index.tolist()

gt = (
    GT(df)
    .tab_style(
        style=style.fill(color="#c6efce"),       # pale green
        locations=loc.body(columns="status", rows=pass_rows),
    )
    .tab_style(
        style=style.fill(color="#ffc7ce"),       # pale red
        locations=loc.body(columns="status", rows=fail_rows),
    )
)
```

**Notes.**
- Use pale fills, not saturated ones — these cells read as "label tags," not as warnings.
- For 3+ states, switch from explicit per-state fill to a small categorical palette via `data_color(palette="Set2")`, but only if the states have no inherent good/bad direction.

---

## Scenario 5 — Domain-clipping pitfalls

**Situation.** Using `data_color` and accidentally hiding outliers.

**Wrong.**
```python
.data_color(columns="return", palette="RdYlGn", domain=[-20, 30])
# data actually ranges -30 to +40 → extreme values clip to the boundary
# color, making the most interesting cells indistinguishable from
# merely-extreme ones.
```

**Right.**
```python
import numpy as np
max_abs = float(np.nanmax(np.abs(df["return"])))
.data_color(columns="return", palette="RdYlGn", domain=[-max_abs, max_abs])
```

**Rules of thumb.**
- Always compute the domain from the data, not from a guessed round number.
- For diverging palettes: symmetric domain around the neutral midpoint (usually 0).
- Leave `truncate=False` (the default) so out-of-range values still get the most extreme palette color rather than disappearing.

---

## Scenario 6 — When to add "quiet" polish vs leaving white space

**Situation.** The table looks correct but feels stark — a blank white canvas with black text. Should you add light-grey accents?

**Add a quiet treatment when:**
- The table has ≥10 body rows and would benefit from row striping for line-tracking (`opt_row_striping()`).
- The stub column blurs into the value columns and a faint stub fill would separate them.
- The column-label row is hard to distinguish from the body (add a subtle tinted heading background or a slightly heavier bottom border).
- There's a totals row that needs to read as structural rather than data (subtle top border + light fill).

**Leave it alone when:**
- The table has fewer than ~6 rows — there's not enough surface area for quiet treatments to register; they just add noise.
- A loud treatment (a `data_color` column, a heatmap matrix) is already carrying the visual load. Adding quiet treatments on top crowds the table.
- The container the table will appear in (slide, PDF section) already has a tinted background — let the white table breathe by contrast.

Remember the budget: **2–4 quiet treatments max.** Beyond that you're decorating, not designing.
