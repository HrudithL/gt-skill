# great_tables (gt) API cheatsheet

Verified against the official reference at
https://posit-dev.github.io/great-tables/reference/ (v0.22). Signatures here
are condensed to the arguments you'll actually use; consult the live docs for
anything not covered.

## Creating the table

```python
GT(data, rowname_col=None, groupname_col=None, auto_align=True, id=None, locale=None)
```
- `data`: a pandas or polars DataFrame.
- `rowname_col`: column whose values become row labels in the stub (left of
  the body, visually separated).
- `groupname_col`: column whose values become row-group headers.
- `locale`: e.g. `"en"`, `"fr"` -- sets default locale for all `fmt_*` calls
  that support one, so you don't need to repeat `locale=` everywhere.

## Header, footer, and structural parts

```python
.tab_header(title, subtitle=None, preheader=None)
.tab_spanner(label, columns, ...)          # group column headers under a shared label
.tab_spanner_delim(delim, ...)              # auto-create spanners by splitting col names on a delimiter
.tab_stubhead(label)                        # label for the stub's header cell
.tab_footnote(footnote, locations=None)     # attaches a marked footnote to a location
.tab_source_note(source_note)               # provenance / caption line below the table
```
`title=`/`subtitle=`/`source_note=` all accept a plain string, or `md(...)`/
`html(...)` (imported from `great_tables`) to render Markdown or raw HTML.

## Formatting column data (`fmt_*`)

All take `columns=` (name or list) and usually `rows=` to target a subset.
Applying a formatter to a column a second time overwrites the first --
formatters aren't cumulative.

| Method | Use for |
|---|---|
| `fmt_number(columns, decimals=2, use_seps=True, ...)` | plain numeric values |
| `fmt_integer(columns, ...)` | counts, whole-number quantities |
| `fmt_currency(columns, currency="USD", decimals=2, ...)` | money |
| `fmt_percent(columns, decimals=1, ...)` | already-fractional values (0.12 -> "12.0%") |
| `fmt_scientific` / `fmt_engineering` | very large/small magnitudes |
| `fmt_partsper(columns, pp_units="ppm", ...)` | parts-per quantities |
| `fmt_roman` | roman numerals |
| `fmt_bytes(columns, ...)` | file/data sizes |
| `fmt_date(columns, date_style="iso", ...)` / `fmt_time` / `fmt_datetime` | date/time values |
| `fmt_duration` | elapsed-time values |
| `fmt_tf(columns, tf_style=...)` | booleans as True/False-style text |
| `fmt_markdown(columns)` | cell text that itself contains Markdown |
| `fmt_units(columns)` | measurement unit strings |
| `fmt_image(columns)` / `fmt_flag(columns)` / `fmt_icon(columns)` | images, country flags, icon sets in cells |
| `fmt_nanoplot(columns, ...)` | tiny inline plots per row |
| `fmt(columns, fns=...)` | fully custom formatter function |

Substitutions (run after formatting, replace based on value/condition rather
than reformat):
```python
.sub_missing(columns=None, rows=None, missing_text=None)  # None -> em dash
.sub_zero(...) .sub_small_vals(...) .sub_large_vals(...) .sub_values(...)
```

## Coloring cells (`data_color`)

```python
.data_color(columns=None, rows=None, palette=None, domain=None,
            na_color=None, alpha=None, reverse=False,
            autocolor_text=True, truncate=False)
```
- Leaving `domain=None` infers the range from the targeted columns' own
  values -- fine for a quick look, but an explicit `domain=[min, max]` is
  preferable whenever an outlier would otherwise wash out the rest of the
  scale, or when several tables need a shared, comparable scale.
- `palette=`: a list of hex/color-name strings, **or** the name of a
  ColorBrewer palette, **or** `"viridis"`/`"plasma"`/`"inferno"`/`"magma"`/
  `"cividis"`.
- `autocolor_text=True` (default) automatically recolors text for contrast --
  leave this on unless you're also manually styling the text color.
- `na_color`: color for missing/out-of-domain values (defaults to gray if unset).

ColorBrewer palettes available by name in `palette=`:

| Diverging (colorblind-friendly) | Diverging (not) | Sequential (all colorblind-friendly) | Qualitative |
|---|---|---|---|
| BrBG, PiYG, PRGn, PuOr, RdBu, RdYlBu | RdGy, RdYlGn, Spectral | Blues, BuGn, BuPu, GnBu, Greens, Greys, Oranges, OrRd, PuBu, PuBuGn, PuRd, Purples, RdPu, Reds, YlGn, YlGnBu, YlOrBr, YlOrRd | Dark2, Paired, Set1, Set2, Set3, Accent, Pastel1, Pastel2 |

Use a **diverging** palette when sign/direction is meaningful (a positive vs.
negative change, above vs. below target). Use a **sequential** palette for
magnitude-only data (revenue, counts, scores) where there's no natural
"good/bad" midpoint.

## Custom cell/location styling (`tab_style` + `loc` + `style`)

For anything the house-style helpers and formatters don't cover -- one-off
borders, conditional text color, targeting a specific cell range:

```python
.tab_style(style=style.fill(color="yellow"), locations=loc.body(columns="x", rows=[1, 2]))
```
- `style.fill(color=...)`, `style.text(color=, font=, weight=, ...)`,
  `style.borders(sides=, color=, style=, weight=...)`, `style.css(rule=...)`.
  Pass a list to `style=` to apply several at once.
- `loc.body`, `loc.header`, `loc.title`, `loc.subtitle`, `loc.column_labels`,
  `loc.stub`, `loc.row_groups`, `loc.source_notes`, `loc.footer`, etc. --
  target any structural part of the table, not just the body.
- Style values can come from a data column via `from_column("col_name")`
  instead of a fixed value, useful for encoding a color/weight per row from
  the data itself.

## Table-wide theming (`opt_*`)

```python
.opt_stylize(style=1, color="blue", add_row_striping=True)   # style: 1-6, color: blue/cyan/pink/green/red/gray
.opt_row_striping(True)                                       # striping without the rest of opt_stylize's look
.opt_table_font(font=None, stack=None, weight=None, style=None, add=True)
.opt_align_table_header(align="center")                       # "center" | "left" | "right"
.opt_all_caps()
.opt_table_outline()
.opt_vertical_padding(scale=...) .opt_horizontal_padding(scale=...)
.opt_footnote_marks(marks=...)
.opt_css(css=...)                                              # raw CSS escape hatch
```
`opt_table_font(stack=...)` keywords (cross-platform font families, no
specific font needs to be installed): `system-ui`, `transitional`,
`old-style`, `humanist`, `geometric-humanist`, `classical-humanist`,
`neo-grotesque`, `monospace-slab-serif`, `monospace-code`, `industrial`,
`rounded-sans`, `slab-serif`, `antique`, `didone`, `handwritten`.

## Modifying columns

```python
.cols_label(old_name="New Label", ...)     # rename headers without touching data
.cols_align(align="left", columns=...)     # "left" | "center" | "right"
.cols_move(columns, after) / .cols_move_to_start(...) / .cols_move_to_end(...)
.cols_hide(columns) / .cols_unhide(columns)
.cols_merge(columns, ...) / .cols_merge_range / .cols_merge_uncert / .cols_merge_n_pct
```

## Summary rows

```python
.summary_rows(groups=..., columns=..., fns=..., ...)   # per-group summary row(s)
.grand_summary_rows(columns=..., fns=..., ...)          # one table-wide summary row
```

## Exporting

```python
.gtsave(file, selector="table", expand=5, zoom=2.0, delay=0.2, vwidth=992, vheight=744)
```
- Format is inferred from the extension: `.png`/`.jpg`/`.jpeg`/`.webp` for
  raster images, `.pdf` for a PDF (`zoom` is ignored for PDF).
- Renders via a real headless Chrome/Chromium under the hood (through the
  `nokap` package) -- see `scripts/setup_gt_chrome.sh` if this errors with a
  Chrome-not-found message.
- `.show("browser")` opens the live, interactive-styling-accurate table in a
  browser tab -- useful mid-build sanity check, especially since some IDEs
  (e.g. VS Code notebooks) suppress certain style rendering in-line.
- `.as_raw_html()` / `.write_raw_html(file)` for embedding the table as HTML
  instead of an image. `.as_latex()` for LaTeX output.

## Helpers

```python
md("**bold** text")          # interpret a string as Markdown wherever a Text argument is accepted
html("<b>bold</b> text")     # interpret a string as raw HTML
from_column("col_name")      # fetch a per-row style value (e.g. fill color) from a data column
google_font("Font Name")     # reference a Google Font by name in opt_table_font(font=...)
```