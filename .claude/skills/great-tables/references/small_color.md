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

## Deterministic triggers — resolve these at Step 2, BEFORE the constructor

These three triggers set **`GT(...)` constructor arguments** (`rowname_col=`,
`groupname_col=`) and the canonical-metric definition, so resolve them when you
**organize columns (Step 2)** — before you write the constructor — not at Step 5 with
the rest of this checklist. (REFERENCE.md §1 routes you here at Step 2 for exactly this
reason.) Each is a decision the model **executes** on a computable condition, not a
judgment call. Read the condition first; if it fires, the action is mandatory.

### Stub default — a computable trigger (PP-13)

**IF a column holds row identifiers (name / date / ID) ⇒ it IS the stub**
(`rowname_col=…`) — **default ON, not optional.** Do not leave an obvious identifier
as a plain value column. A `tab_stubhead(label=…)` **requires** that the stub already
exist — **no orphan label** (setting a stubhead when there is no `rowname_col` is
wrong, PP-25).

**A month/date-and-year stub is always formatted `"Mon YYYY"`**
(`strftime("%b %Y")` — e.g. `"Apr 2010"`), never `"YYYY-MM"`, `"YYYY-Mon"`, or a raw
`Period`'s default string form (`str(period)` yields `"2010-04"` — always route it
through an explicit `strftime` instead). A day-level date stub is `"Mon DD, YYYY"`
(`strftime("%b %d, %Y")`). This is a pinned, deterministic choice like every hex in
this file — the same input must produce the same spelling on every run, not whatever
a library's default stringification happens to yield.

### Grouping — a computable trigger (PP-1)

**IF the user's prompt names a grouping dimension** ("grouped by X", "by country",
"per region"), **OR the data has a low-cardinality categorical that is the organizing
story ⇒ use `groupname_col=…`.** When the prompt says group, grouping is
**MANDATORY** (Rule 0) — never render that dimension as a plain column. (Stub + groups
may coexist.)

### Ambiguous measures — pick ONE canonical definition (F-canonical-metric, PP-18)

**IF a requested measure has more than one reasonable definition** (e.g. a ranking
metric vs. a display column, or which of several plausible formulas to use) **⇒ pick
ONE canonical definition, compute it, and STATE the chosen definition** in the
subtitle or a source note so the number is reproducible. Do **not** silently pick
one — an unstated choice makes the same prompt yield different numbers across runs.

**One specific case is NOT a discretionary pick, despite looking like one:** a
"day-over-day"/"single-period change" measure requested **within** an aggregation
window ("highest single-day gain **within the month**", "week-over-week change
**within the quarter**") names two ADJACENT observations in the FULL underlying
continuous series — the window is how you're asked to *report* it, not a
computation boundary the series itself resets at. Compute the change across the
**entire sorted series first** (`series.pct_change()`, unconditionally — a period's
first row still gets a real value relative to the PRIOR period's last one, never
`NaN`), filter to the requested range **after**, then aggregate within each window
over that already-computed column. A same-period computation (e.g. `close − open`
on one row) answers a different, narrower question (intraday movement) the request
didn't ask, even though it only needs a single grouped-and-filtered DataFrame to
compute. When the request's wording is genuinely ambiguous between same-period and
day-over-day, the ordinary "pick one, state it" rule above still applies — but when
it specifically says day-over-day/period-over-period, the continuous-series
definition is the canonical one, not one of several equally-valid choices.

**A frequent, specific instance of this trigger: a request that names a ranking/
selection metric AND separate display columns in the same sentence.** "Population
growth trends for the top 15 fastest-growing towns, comparing their density changes"
mixes two questions — what to **rank/select by** (which rows make the list) and what
to **display** once selected (which columns appear). Resolve BOTH with this
precedence, then STATE the result in the subtitle/source note:

1. **Find the ranking metric SEPARATELY from the display columns** — it's usually
   the request's stated TOPIC (the noun phrase right after "a table of/showing..."),
   not whichever measure sits nearest "top N"/"fastest-growing" in the sentence. An
   explicitly named ranking metric ("top 15 by revenue") always wins outright. If the
   topic metric and the named display columns differ, show BOTH as columns — a table
   titled "population growth trends" with zero population data reads as incomplete
   regardless of how well it answers the display question.
2. **Entity/category scope matches every row the term plausibly covers, never the
   narrower literal subset** — "Ontario towns" means Ontario municipalities
   generically; if a type/category column exists (`town`/`city`/`township`/...),
   include every type unless the request is explicit about excluding some. State the
   scope choice.
3. **A stated date range means the FULL span** ("1996 to 2021" compares the 2021 and
   1996 values, not an interior period) **as a percentage/relative change**, not an
   absolute difference, whenever the request says "growth"/"fastest-growing"/"rate."
   **Guard the baseline against the ACTUAL data before computing**: check whether any
   eligible row's starting value is zero/negative — a measure that's merely
   *capable* of going negative but happens to be positive everywhere needs no special
   handling. When a real zero/negative baseline exists and the metric was left
   **unstated**, fall back to absolute change for the whole table and say so. When
   the request **explicitly** asked for a rate, exclude only the non-positive-
   baseline rows (a rate is genuinely undefined for them) and note the exclusion,
   rather than silently swapping the whole table to a different metric. This guard
   applies per-cell too, not just to the overall ranking figure: `np.where(start > 0,
   (end - start) / start, None)` catches both the zero-baseline `inf` case (which
   `sub_missing` does NOT catch on its own — it only substitutes `None`/`NaN`) and
   the negative-baseline case (a finite but meaningless sign-reversed value, e.g.
   `(5 - (-10)) / (-10) = -1.5`) — mask on the condition before formatting, not on
   whether the rendered number happens to look broken.
4. **"Show X across all periods, with changes between each period" means BOTH** —
   include the per-checkpoint values AND the between-period deltas as separate
   columns when the request names both, rather than picking one to stand in for the
   other. This is a *display* choice; it never overrides the ranking metric from (1).

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

## (f) Titles, caption, and source note (Step 6)

**Gate:** title + subtitle are unconditional, every table. Caption fires at **≥5
rows**; source note fires whenever provenance is known (write a generic one —
"Source: provided dataset." — rather than omitting it when it isn't).

**Caption and source note are two SEPARATE `tab_source_note(...)` calls, not one
combined sentence.** The caption's job is to state a non-obvious computational
choice made elsewhere in the table (an ambiguous-measure resolution, the
continuous-series rule above, a baseline-guard exclusion) — it should name the
specific words that make the choice concrete ("continuous", "day-over-day", "not
reset"), not gesture vaguely at "see methodology." The source note's job is the
plain citation. Stack them, methodology first:

```python
gt = (
    gt.tab_source_note(
        source_note="Single-day gain/loss use a continuous day-over-day change "
                     "across the full historical series, not reset at each month's start."
    )
    .tab_source_note(source_note="Source: provided S&P 500 dataset.")
)
```

A single combined sentence tends to drop the methodology half, since the citation
phrasing ("Source: ...") is what comes to mind first when writing one note. If the
table made no non-obvious computational choice, the plain citation alone is
enough — don't invent a methodology caption with nothing to say.

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

## Sub-note — do NOT use `opt_stylize` as a whole-table styler (PP-17)

**Do NOT use `opt_stylize(...)` to theme the whole table** — it bypasses Steps 4–5.
Build the heading **band (Step 4)** and the **Small-Color polish (Step 5)** explicitly
from this checklist, so the band hue, stripes, and dividers are the pinned hexes and
not a built-in theme. Escaping to `opt_stylize(style=N)` is exactly the off-flowchart
drift that made "same-prompt" runs render as different products.

`opt_stylize(...)` is a full **theme preset** — it sets backgrounds, line colors, and
styles across the whole table. There is **no** exception: do **not** call it for the
whole table, for the container, for "just the rounded corners", or for anything else.
Any use reintroduces exactly the unpinned styling this checklist exists to remove.

**Rounded corners.** `great_tables` has **no** pinned `tab_options(...)` corner-radius
option, so there is **no deterministic rounded-corner mechanism** — the **square**
four-side Frame border below (color `#CCCCCC`, 1px, all sides) **is** the deterministic
Frame, and SKILL.md explicitly declares a square light border acceptable. If (and only
if) rounded corners are explicitly requested, the **only** border-radius-only escape
that touches nothing else is a single `opt_css("table { border-radius: 6px; }")` rule —
CSS scoped to `border-radius` alone, never `opt_stylize`. Default to the square Frame.

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
