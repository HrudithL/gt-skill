# Small Color — the fixed Step-5 checklist

Step 5 is **overall formatting**, and it is **not a menu**. Every table runs this
checklist top to bottom. Each item is **gated** by a rule (the condition that fires
it) and, when it fires, uses the **one** `great_tables` mechanism given here. Every
light surface is drawn from the **washed-DA + neutral-grey** palette below — never a
saturated color.

This file is self-contained: all hexes are inlined so you never need a second hop.
(They mirror `references/palettes.md` §2 for neutrals and §1 for washed-DA tints.)

## The palette this checklist draws from

Neutral greys (the default for every quiet surface):

| Role | Hex | Weight |
|---|---|---|
| Light label band | `#F0F0F0` | — |
| Row stripe | `#F6F6F6` | — |
| Cell hairline (between rows) | `#E8E8E8` | 1px |
| Column-label bottom rule | `#CCCCCC` | 2px |
| Group / summary structural rule | `#BDBDBD` | — |
| Column-group vertical divider | `#D0D0D0` | 1px, light but noticeable |
| NA / empty cell | `#808080` | `na_color=` fill; `sub_missing("—")` text |

Washed-DA tints (used **instead of grey** when the table has Big Color, matched to
the dominant Big-Color hue — see the grey-budget rule):

| Big-Color hue | Washed tint |
|---|---|
| Navy (default) | `#EAF0F6` |
| Forest | `#EAF1EC` |
| Oxblood | `#F5EBEB` |
| Espresso | `#F1EADD` |
| Ochre | `#F5EFDC` |
| Tan | `#EFE7D6` (cream) |

---

## (a) Cell borders — ALWAYS

**Gate:** every table.

Light hairline between all body rows. Structurally meaningful rows (summary/total
rows, row-group boundaries) get a **slightly stronger but still restrained** rule so
structure reads without shouting. This is a **separate setting from (b)**.

```python
from great_tables import GT, style, loc

gt = (
    GT(df)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",     # hairline between every row
        table_body_hlines_width="1px",
    )
    # structural row (e.g. a totals row) — stronger, still restrained
    .tab_style(
        style=style.borders(sides="top", color="#BDBDBD", weight="1.5px"),
        locations=loc.body(rows=[totals_row_index]),
    )
)
```

Keep the **column-label bottom rule** at `#CCCCCC`, 2px (this is the Step-4 constant,
present under any heading band):

```python
gt = gt.tab_options(column_labels_border_bottom_color="#CCCCCC",
                    column_labels_border_bottom_width="2px")
```

---

## (b) Column-group vertical dividers

**Gate:** logical column groups / multiple spanners exist. No column groups → **none**.

A light, easily-noticeable vertical divider **at each group boundary only** — not
between every column, not a full grid. Put a right border on the **last column of each
group**, in **both** the body and the column labels so the seam runs full height.

```python
from great_tables import GT, style, loc

gt = (
    GT(df)
    .tab_spanner(label="Density", columns=["y1996", "y2001", "y2006"])
    .tab_spanner(label="Change",  columns=["c9601", "c0106"])
    .tab_style(                                       # seam in the body
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="y2006"),          # last col of the first group
    )
    .tab_style(                                       # matching seam in the header
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="y2006"),
    )
)
```

---

## (c) Row striping

**Gate:** **≥10 body rows** AND the body is **not essentially fully filled** by Big
Color. Skip when <10 rows, or when `data_color` already covers essentially the whole
body (stripes and fills fight). Stripes still show on an unfilled stub.

```python
gt = (
    GT(df)
    .opt_row_striping()                               # default very-pale stripe
    # optional explicit control:
    .tab_options(row_striping_background_color="#F6F6F6")
)
```

---

## (d) Stub tint

**Gate:** a stub (`rowname_col`) exists.

A light tint on the stub so the row labels separate from the value columns. **Grey by
default** (`#F0F0F0`); harmonize to the washed-DA tint of the Big-Color hue when there
is Big Color. Subject to the grey-budget rule below.

```python
from great_tables import GT, style, loc

gt = (
    GT(df, rowname_col="entity")
    .tab_style(
        style=style.fill(color="#F0F0F0"),            # grey default; e.g. "#EAF0F6" for a Blues table
        locations=loc.stub(),
    )
)
```

---

## (e) Formatting per column (`fmt_*`)

**Gate:** every value column. Match the semantic type; these precision defaults are
overridable by an explicit user instruction.

| Type | Formatter | Default precision |
|---|---|---|
| Percent | `fmt_percent(columns=…, decimals=1)` | 1 decimal |
| Currency (whole-dollar / large) | `fmt_currency(columns=…, decimals=0)` | 0 decimals |
| Currency (small money) | `fmt_currency(columns=…, decimals=2)` | 2 decimals |
| Number | `fmt_number(columns=…, decimals=1)` | meaningful precision (default 1) |

Always: `use_seps=True` for thousands separators, and `sub_missing(columns=…,
missing_text="—")` for empty cells. Put units in the column **label** only when the
formatter doesn't already convey them.

---

## The grey-budget rule

Count the light-grey elements in play (label band, stripes, stub, empty/NA cells,
hairlines). When grey becomes **monotonous** — several large grey areas stacking —
re-color the **highest-priority** element to the **washed-DA tint of the Big-Color
hue** (the tint table above). Shift only as many elements as needed to break the
monotony (usually just one).

**Priority order:** `stub → labels → row design (striping / empty cells)`

> Example: grey band + grey stripes + grey stub with `Blues` fills → recolor the
> **stub** (highest priority) to pale-blue `#EAF0F6`.

---

## Sub-note — row-group emphasis

**Gate:** the table uses `groupname_col=`. An unstyled group label sits in the flow of
body rows and the reader loses the section boundary.

Give each `groupname_col` header row a **light background fill AND bold weight** — the
pair is non-negotiable. Fill alone reads as noise; bold alone reads as a stray body
row; together they read as a section heading. Use the **same** light shade for every
group (grey `#F0F0F0` by default, or the washed-DA tint when the table has Big Color —
keep it consistent with the stub/band per the grey-budget rule). The structural rule
above/below the label is `#BDBDBD`.

```python
gt = (
    GT(df, groupname_col="Region")
    .tab_options(
        row_group_background_color="#F0F0F0",    # grey default; washed-DA tint if Big Color
        row_group_font_weight="bold",            # required
        row_group_border_top_color="#BDBDBD",    # structural rule (item a)
        row_group_border_bottom_color="#BDBDBD",
        row_group_padding="6px",                 # a touch more air than a body row
    )
)
```

Never fill a group header with a saturated color — that would make structural chrome
compete with the data. Editorial weight belongs on the **column labels** (Step-4 band),
not on group headers.

## Sub-note — themed baseline (`opt_stylize`)

An optional one-call starting point for a **categorical / textual grid** with no
natural numeric column to color (the no-Big-Color branch — a top-N list, a small
comparison table). `opt_stylize` ships a colored column-label band, striped body, and
matching hairline dividers in a single call, giving a cohesive base you then reconcile
with the checklist above.

```python
gt = (
    GT(df, groupname_col="Region")
    .opt_stylize(style=2, color="gray")          # band + stripes + dividers in one call
)
```

`style=` 1–6 (2 = colored labels + stripes + light dividers, a good default);
`color=` one of `"blue" "cyan" "pink" "green" "red" "gray"`. Later `tab_options(...)`
calls win, so you can override any chrome piece afterward (e.g. reset the bottom rule
to `#CCCCCC`/2px, or match the band color to the table's DA hue).

- **Skip `opt_stylize` when the table commits to a strong Big Color story** (a
  gradient/diverging fill, full-column fill, status pills) — its theme chrome doubles
  up on and fights the data-driven fill.
- **Do not stack `opt_stylize` with `opt_row_striping()`** — the theme already stripes;
  layering produces darker-than-intended stripes.

## Frame & render parameters (the Global-constant values)

SKILL.md and `REFERENCE.md` route the **Frame** and **font-size fit** global constants
here for their exact values.

**Frame — the boxed enclosing border (every table).** A light border on **all four
sides** plus an outer margin; never flat/edge-to-edge. The border color is the neutral
`#CCCCCC`, 1px, `solid`. Great Tables defaults the *left/right* border style to
`"none"`, so you MUST set the style explicitly or the sides render invisible (you'd get
top/bottom rules, not a box):

```python
gt = gt.tab_options(
    table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
    table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
    table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
    table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
)
```

**Outer margin.** `gt.gtsave("table.png", expand=15)` — raise from the 5px default to
**~15–20** so the box has breathing room. (Scripted variant: `finalize(gt)` applies
this.)

**Render / fit order.** Keep the default **`zoom=2.0`**. When a table renders too big,
in order: (1) raise `gtsave(vwidth=…, vheight=…)` to give it room; (2) raise
`gtsave(zoom=…)` to keep it crisp; (3) only then reduce font size, minimally. Never
*lower* `zoom` below 2.0 to force a fit — that just blurs the render.
