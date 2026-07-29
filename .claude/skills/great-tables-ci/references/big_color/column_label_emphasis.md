# Big Color — Column Label Emphasis (the heading band)

The column-label band is decided by the **Step-4 rule**, and it keys **only off Big
Color** (fills, colored text, a highlighted column/row from Step 3). The quiet
washed/grey surfaces of Step 5 do **not** count.

```
Does the table have ANY Big Color?
  ├─ NO  → DARK saturated band  (Dark Academia solid, white text) — THIS FILE.
  │        The band is the table's anchor; hue per the DA hue-selection rule → usually Navy.
  └─ YES → LIGHT band  (washed-DA tint of the Big-Color hue, or grey).
           Let the data color dominate; the band stays quiet. See the light branch below.
```

## When to use the DARK band (no-Big-Color branch)

Use it when the body is intentionally quiet (no fill/pills/highlights) and the header
must be the anchor — e.g. tables with spanners/many columns, or an editorial top band.

## Recipe — DARK band (no Big Color)

```python
from great_tables import GT

gt = (
    GT(df)
    .tab_options(
        column_labels_background_color="#22384F",        # Dark Academia solid (Navy default)
        column_labels_font_weight="bold",
        column_labels_text_transform="uppercase",        # optional editorial touch
        column_labels_border_bottom_color="#CCCCCC",      # keep the 2px bottom rule (Step-4 constant)
        column_labels_border_bottom_width="2px",
    )
)
```

White label text on the solid comes from great-tables' automatic contrast (this applies
to `tab_options` only — `tab_style` does NOT auto-contrast, so the single-column recipe
below sets `style.text(...)` explicitly); override with `column_labels.style` if a theme
overrode it. Hue per DA hue-selection rule, `references/palettes.md` §1 — default
**Navy** `#22384F`, else Forest `#2F4A38`, Oxblood `#5C2E2E`, Espresso `#4A3A2C`, Ochre
`#9A7B33`, Tan `#8A7452`.

For a single-column emphasis (anchor just the one "answer" column's header):

```python
from great_tables import style, loc

gt = gt.tab_style(
    style=[style.fill(color="#22384F"), style.text(color="#ffffff", weight="bold")],
    locations=loc.column_labels(columns="focus_col"),
)
```

## The LIGHT band (Big Color present)

When the table has any Big Color, **do not use a dark band.** The header becomes a
quiet washed-DA tint (matched to the dominant Big-Color hue) or grey — a Small-Color
surface, set via `tab_options(column_labels_background_color=…)` with a washed tint
from `references/palettes.md` §1 (e.g. `#EAF0F6` for `Blues`) or grey `#F0F0F0`, bold
labels dark. Bottom rule stays `#CCCCCC`, 2px, either way. Governed by the grey-budget
rule in `references/small_color.md`.

## Rules

- **Dark band ⇒ no Big Color**; never stack a dark saturated band on a colored body.
- **Dark fill + white text** (never dark-on-dark). Light fill ⇒ dark bold text.
- **Header emphasis ≥ spanner emphasis** — if labels are loud-filled, spanners need at
  least the same weight.
- **One strong header treatment per table** — don't also loud-color row-group labels,
  source note, and stub.
- **Stub column labels are part of the header** — fill the stubhead to match or leave it
  explicitly blank; a mismatched stubhead reads as a bug.

## Counts as

One Big Color treatment (the dark-band case; filling spanners to match is still the same
treatment). The light-band case is **not** a Big Color treatment — it's Small-Color chrome.
