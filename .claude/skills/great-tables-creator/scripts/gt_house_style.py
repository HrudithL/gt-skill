"""
gt_house_style.py
------------------
Shared visual-design helpers for building tables with the `great_tables` (gt)
package. Import these into every table-building script so that tables produced
by this skill look and behave the same way every time, no matter what the
underlying data source is (a DataFrame already in memory, a CSV/Excel file, a
SQL query result, or something messier).

The point of centralizing this in one file instead of writing the styling
calls fresh in every script is consistency: the "house look" (theme color,
row striping, font stack, header alignment, heatmap palette choice) is decided
once, here, rather than re-decided -- possibly differently -- on every request.
If you want to deviate from the house style for a specific request (the user
asks for a specific color, a monochrome look, etc.), just pass different
arguments to these functions or skip them and call the underlying gt methods
directly. Nothing here is mandatory, it's a sensible, tested default.

Usage:
    from gt_house_style import apply_house_style, add_heatmap, HOUSE_STYLE
"""
from __future__ import annotations

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


# ---------------------------------------------------------------------------
# Design tokens. This is the one place that defines what a "house style"
# table looks like. Change values here (or override per-call) rather than
# hard-coding one-off theme choices inside individual table scripts.
# ---------------------------------------------------------------------------
HOUSE_STYLE = {
    # opt_stylize() preset: 1-6. Style 1 is the most subdued/professional;
    # higher numbers add more borders and stronger color blocking.
    "stylize_style": 1,
    # opt_stylize() color: one of "blue", "cyan", "pink", "green", "red", "gray".
    "stylize_color": "blue",
    # Row striping is on by default -- it's one of the cheapest ways to make
    # a wide/tall table scannable, and there's rarely a reason to omit it.
    "row_striping": True,
    # A font stack keyword understood by opt_table_font(stack=...). "system-ui"
    # renders using each viewer's native system font, which looks clean and
    # professional everywhere without depending on a specific font being
    # installed (important since gtsave() renders via headless Chrome).
    "font_stack": "system-ui",
    "align_header": "center",
    # Colorbrewer palette names (see data_color() docs) used by add_heatmap().
    # Both are colorblind-friendly.
    "heatmap_palette_sequential": "Blues",
    "heatmap_palette_diverging": "RdBu",
    # A muted, neutral gray for missing/out-of-domain cells in a heatmap --
    # visually distinct from real data colors without looking like an error.
    "na_color": "#EDEDED",
    # Placeholder text for missing values in the table body generally
    # (independent of heatmaps). An em dash reads as "intentionally blank"
    # rather than "broken."
    "missing_text": "—",
}


def apply_house_style(
    gt_tbl,
    *,
    stylize: bool = True,
    style: int | None = None,
    color: str | None = None,
    striping: bool | None = None,
    align_header: str | None = None,
):
    """
    Apply the shared visual theme to a GT table: color/border preset, row
    striping, font stack, and header alignment. Call this near the end of a
    table-building chain, after content (headers, formatting, spanners) is in
    place, so options like row striping apply to the final structure.

    Every argument has a house default (see HOUSE_STYLE above) but can be
    overridden per call, e.g. apply_house_style(gt_tbl, color="green") for a
    table about growth/revenue, or apply_house_style(gt_tbl, stylize=False)
    for a plainer look when the user wants something minimal.
    """
    style = HOUSE_STYLE["stylize_style"] if style is None else style
    color = HOUSE_STYLE["stylize_color"] if color is None else color
    striping = HOUSE_STYLE["row_striping"] if striping is None else striping
    align_header = HOUSE_STYLE["align_header"] if align_header is None else align_header

    if stylize:
        gt_tbl = gt_tbl.opt_stylize(style=style, color=color, add_row_striping=striping)
    else:
        gt_tbl = gt_tbl.opt_row_striping(striping)

    gt_tbl = (
        gt_tbl.opt_table_font(stack=HOUSE_STYLE["font_stack"])
        .opt_align_table_header(align=align_header)
    )
    return gt_tbl


def add_heatmap(
    gt_tbl,
    df,
    columns,
    *,
    kind: str = "auto",
    palette=None,
    domain=None,
    na_color: str | None = None,
    reverse: bool = False,
    alpha=None,
    center: float | None = None,
):
    """
    Color body cells by value ("heatmap" a column) with defaults chosen to
    avoid the most common data_color() mistakes: leaving the domain fully
    auto-inferred (which makes one outlier wash out the rest of the palette),
    using a sequential palette on data that's meaningfully signed (where a
    diverging palette communicates "good vs. bad" much more clearly), and
    forgetting that "diverging" isn't always centered on zero.

    df: the underlying DataFrame (used to compute a sensible domain and to
        auto-detect sequential vs. diverging -- gt itself only sees formatted
        display values, not the raw numbers, so this needs the source data).
    columns: a column name or list of column names to colorize together
        (sharing one domain/palette so they stay visually comparable).
    kind: "sequential" for magnitude-only data (revenue, counts, scores),
        "diverging" for data where sign/direction *relative to a reference
        point* matters (% change from zero, profit vs. loss, attainment
        relative to a 100% target), or "auto" to decide based on whether the
        data contains both negative and positive values. Auto-detection only
        catches divergence around zero -- a column like "quota attainment"
        (values like 0.76, 1.04, 1.22, all positive but meaningfully diverging
        around 100%) needs an explicit `kind="diverging", center=1.0`.
    center: the reference point diverging data is centered on (e.g. `0` for
        a plain % change column, `1.0` for a ratio-to-target stored as a
        fraction, `100` if the same ratio is stored in percentage points).
        Defaults to `0` when `kind="diverging"` and `center` isn't given.
    domain: pass explicit [min, max] to override the computed one -- do this
        whenever there's a natural fixed scale (e.g. a 0-100 score, or you
        want several tables to share one color scale for comparability).
    """
    if pd is None:
        raise ImportError("pandas is required for add_heatmap()'s domain detection")

    cols = [columns] if isinstance(columns, str) else list(columns)
    numeric_cols = [c for c in cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]

    if kind == "auto":
        has_negative = any((df[c].dropna() < 0).any() for c in numeric_cols)
        kind = "diverging" if has_negative else "sequential"

    if palette is None:
        palette = (
            HOUSE_STYLE["heatmap_palette_diverging"]
            if kind == "diverging"
            else HOUSE_STYLE["heatmap_palette_sequential"]
        )

    if domain is None and numeric_cols:
        lo = min(df[c].min() for c in numeric_cols)
        hi = max(df[c].max() for c in numeric_cols)
        if kind == "diverging":
            ref = 0 if center is None else center
            bound = max(abs(lo - ref), abs(hi - ref))
            domain = [ref - bound, ref + bound]
        else:
            domain = [lo, hi]

    return gt_tbl.data_color(
        columns=cols,
        palette=palette,
        domain=domain,
        na_color=na_color or HOUSE_STYLE["na_color"],
        reverse=reverse,
        alpha=alpha,
        autocolor_text=True,
    )


def humanize_labels(gt_tbl, df, *, overrides: dict[str, str] | None = None, exclude=None):
    """
    Relabel columns so headers never ship as raw snake_case/camelCase source
    names (e.g. "yoy_change" -> "Yoy Change"). This is a starting point, not
    a final answer: automatic title-casing gets acronyms, units, and currency
    symbols wrong (e.g. "usd_amt" -> "Usd Amt" instead of "Amount (USD)"), so
    always pass `overrides=` for any column where that matters. The goal is
    that no table this skill produces ever shows a column literally named
    `yoy_change` or `col_3` to a reader.

    overrides: {"raw_col_name": "Display Label"} for columns needing a
        specific label instead of the auto title-cased version.
    exclude: column names to leave untouched (e.g. a column already renamed,
        or one intentionally left in a technical style).
    """
    overrides = overrides or {}
    exclude = set(exclude or [])
    labels = {}
    for col in df.columns:
        if col in exclude:
            continue
        labels[col] = overrides.get(col, col.replace("_", " ").replace("-", " ").strip().title())
    return gt_tbl.cols_label(**labels)