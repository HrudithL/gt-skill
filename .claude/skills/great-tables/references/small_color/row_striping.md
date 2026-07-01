# Small Color — Row Striping

Apply an alternating pale background color to every other body row so the reader can track a value across a wide row without their eye jumping to the wrong line.

## When to use

- The table has **≥10 body rows** — below that, striping adds visual weight without measurable benefit.
- The table is **wide** (5+ display columns) so tracking left-to-right is genuinely hard.
- No Big Color fill is already covering most of the body (a heatmap matrix + stripes = mud).

## Recipe

```python
from great_tables import GT

gt = (
    GT(df)
    .opt_row_striping()                                 # default very-pale stripe
)
```

Or explicitly control the stripe color:

```python
gt = (
    GT(df)
    .tab_options(
        row_striping_background_color="#f7f7f9",        # near-white grey
    )
    .opt_row_striping()
)
```

## Rules

- **Very pale stripe.** The default is close to right; if you customize, stay within a few percentage points of white. If you can read the hex code and think "that's clearly grey," it's too dark.
- **No stripes under a heatmap or full-column fill.** The stripe interacts with the fill and turns half the cells a different shade than the other half — that reads as data variation.
- **Do not stripe with a saturated color.** Pale grey, pale warm-off-white, pale cool-off-white — nothing else.
- **Consistent across the whole body.** Do not stripe only the top half or only certain row groups.

## Counts as

One Small Color treatment.
