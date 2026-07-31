"""house_table.py — the "house format" reference table AND its helper module.

This file is two things at once:

1. **A reusable helper module.** ``PALETTE`` and the functions below are meant
   to be imported into a real table script exactly the way
   ``great-tables-ci/scripts/gt_consistency.py`` is imported by that skill:

       from house_table import PALETTE, frame, finalize, band, stripe, \
           stub_tint, heatmap, status_chip, summary_row, group_emphasis, \
           humanize_labels

2. **The one worked example.** Running this file directly
   (``python house_table.py``) builds a single synthetic "Regional Product
   Line Performance" table that exercises every generic formatting feature
   the skill covers — stub, groups, spanners, a sequential heatmap, a
   diverging heatmap, categorical status chips, a summary row, striping,
   stub tint, band, frame, footnote, source note, and a missing value — and
   saves it to ``house_table.png`` next to this script.

Why a single script instead of a flowchart + per-shape reference files (the
``great-tables`` / `great-tables-ci` design)? Those two skills solve
"same input -> same output" with a **procedure**: a numbered decision
sequence plus a directory of archetype examples to route to. This skill
solves the same problem with a **worked example**: read this file once,
find the block that matches your data's shape (a magnitude column, a
percent column, a status column, a group, a summary row, ...), copy/adapt
it, and look up the matching row in ``references/RULES.md`` for the one
formatting rule that block encodes. There is no router file and no
per-archetype directory — this script IS the one example, annotated in
place.

The palette, hexes, and color rules below are copied **verbatim** from
``great-tables-ci/scripts/gt_consistency.py`` (mirroring
``references/palettes.md``). Reusing the already-validated visual system is
deliberate — only the *decision process* around it is thinner here, not the
colors themselves.
"""

from __future__ import annotations

import pandas as pd
from great_tables import GT, loc, md, style

# ---------------------------------------------------------------------------
# PALETTE — copied verbatim from great-tables-ci/scripts/gt_consistency.py,
# which itself mirrors great-tables-ci/references/palettes.md. Do not invent
# new colors here; if a hex needs to change, change it in that skill first
# and re-copy it into both places.
# ---------------------------------------------------------------------------
PALETTE = {
    # Dark Academia SOLID Big-Color palette (white text on every solid). Each
    # hue exists for a specific subject-matter cue, not decoration — see the
    # "Use when..." comment on each entry. Navy is the deterministic default
    # when no other cue applies (references/palettes.md §1's hue-selection
    # rule: match an existing heatmap hue first, else the data's subject,
    # else any color already in the table, else Navy).
    "solid": {
        "navy": "#22384F",      # default with no other cue
        "forest": "#2F4A38",    # nature, growth, environment, money/finance
        "oxblood": "#5C2E2E",   # risk, alerts, deficits, intensity
        "espresso": "#4A3A2C",  # historical, literary, food/wine, vintage
        "ochre": "#9A7B33",     # premium / awards / highlight (accent)
        "tan": "#8A7452",       # secondary warm accent / mid (cream tint)
    },
    # The washed light tint paired with each solid above (same keys). Used
    # for quiet structural surfaces (band, stub, stripe) so the quiet polish
    # echoes whichever solid hue is doing the loud work elsewhere.
    "washed": {
        "navy": "#EAF0F6",
        "forest": "#EAF1EC",
        "oxblood": "#F5EBEB",
        "espresso": "#F1EADD",
        "ochre": "#F5EFDC",
        "tan": "#EFE7D6",       # cream
    },
    # Neutral structural surfaces (light greys) — the default for every quiet
    # surface when there's no Big-Color hue to harmonize to.
    "neutral": {
        "label_band": "#F0F0F0",         # light label band
        "row_stripe": "#F6F6F6",         # row stripe
        "hairline": "#E8E8E8",           # cell hairline between rows, 1px
        "column_label_rule": "#CCCCCC",  # column-label bottom rule, 2px; also the frame border
        "structural_rule": "#BDBDBD",    # group / summary structural rule
        "vertical_divider": "#D0D0D0",   # column-group vertical divider
        "na_cell": "#808080",            # NA / empty cell fill
    },
    # Sequential palette NAMES (matplotlib/brewer), keyed by semantic
    # meaning — passed to data_color(palette=...), never a fixed hex. A
    # single neutral magnitude (money/price/volume/count) is always "Blues";
    # Greens/Reds are reserved for measures with an explicit direction.
    "sequential": {
        "positive": "Greens",    # growth / "more is better"
        "warning": "Reds",       # worse / "more is worse"
        "warning_alt": "Oranges",
        "neutral": "Blues",      # volume / count / price / population
    },
    # Diverging palette NAMES for signed values. RdYlGn is the default
    # (green = good); reverse it only when positive genuinely means worse.
    "diverging": {
        "default": "RdYlGn",
        "colorblind_safe": ["RdBu", "PuOr"],
    },
}


# ---------------------------------------------------------------------------
# Reusable helpers. Every helper takes the DECISION as an argument (which
# columns, which hue, light vs dark, good/bad/neutral, ...) — none of them
# choose anything themselves. That mirrors gt_consistency.py's philosophy:
# the model decides *what*, the helper only guarantees *how* it's executed
# is identical every time it's called with the same arguments.
# ---------------------------------------------------------------------------


def humanize_labels(gt, df, overrides=None):
    """Turn snake_case column names into Title Case via ``cols_label``.

    WHAT: relabels every column of ``df`` from its snake_case name (e.g.
    ``yoy_change``) to a human Title Case label (``Yoy Change``), then
    applies ``overrides`` on top for anything the naive rule gets wrong —
    an acronym that shouldn't title-case letter-by-letter ("YoY", not
    "Yoy"), a currency/unit suffix, or any label an explicit request names.

    WHY: naive Title Case is right often enough to not deserve a decision
    every time, but wrong often enough (acronyms, units) that it needs an
    escape hatch — ``overrides`` is that hatch, applied last so it always
    wins.
    """
    overrides = overrides or {}
    labels = {}
    for col in df.columns:
        labels[col] = overrides.get(col, col.replace("_", " ").title())
    return gt.cols_label(**labels)


def frame(gt, color=None, width="1px", style="solid"):
    """Apply the boxed enclosing border on all four sides.

    WHAT: sets the table's top/bottom/left/right border color, width, and
    style identically.

    WHY: ``great_tables`` defaults the *left/right* border style to
    ``"none"`` — setting only ``color``/``width`` would leave the side
    borders invisible and render only top/bottom rules, not a box. The
    style must be set explicitly on all four sides to get an actual frame.
    Defaults to the neutral ``#CCCCCC`` used as the frame color everywhere
    in this skill (see ``references/RULES.md``'s "Global constants").
    """
    if color is None:
        color = PALETTE["neutral"]["column_label_rule"]
    return gt.tab_options(
        table_border_top_style=style,
        table_border_top_color=color,
        table_border_top_width=width,
        table_border_bottom_style=style,
        table_border_bottom_color=color,
        table_border_bottom_width=width,
        table_border_left_style=style,
        table_border_left_color=color,
        table_border_left_width=width,
        table_border_right_style=style,
        table_border_right_color=color,
        table_border_right_width=width,
    )


def finalize(gt, path="table.png", **overrides):
    """Save the table with the house-format ``gtsave`` defaults.

    WHAT: calls ``gt.gtsave(path, expand=15, zoom=2.0, **overrides)`` — a
    raised outer margin and a retina zoom, with any keyword in
    ``overrides`` (e.g. ``vwidth``/``vheight``) taking precedence.

    WHY ``path`` defaults to ``"table.png"``: that's the mandatory renderer
    target this skill (and the harness that runs it) expects — see
    ``SKILL.md``'s "The mandatory renderer" section. A real table script
    that imports this helper and calls ``finalize(gt)`` with no explicit
    path should produce the expected file, not silently write something
    else. The demo below passes an explicit ``path="house_table.png"`` to
    override this default, since its output is the reference render, not a
    generated table.

    WHY the other defaults: the default 5px ``gtsave`` margin crowds the
    frame border against the image edge; ``zoom=2.0`` keeps text crisp at
    normal viewing sizes. If a table renders too big, grow room/zoom before
    ever shrinking font size (see ``references/RULES.md``'s font-size fit
    order).
    """
    opts = {"expand": 15, "zoom": 2.0}
    opts.update(overrides)
    return gt.gtsave(path, **opts)


def band(gt, *, shade, hue):
    """Apply the heading band (light tint or dark solid) + the mandatory rule.

    WHAT: ``shade="light"`` paints the column-label background with the
    washed tint of ``hue`` (or the neutral grey band when ``hue="grey"``).
    ``shade="dark"`` paints it with the DA solid for ``hue`` and whitens the
    column-label (and spanner-label, if any) text so it stays legible.
    Either way, the 2px ``#CCCCCC`` column-label bottom rule is ALWAYS
    applied — it is the one Step-4 constant that holds regardless of shade.

    WHY light vs dark: when the table already has Big Color (a heatmap, a
    status chip, any saturated fill), a second dark saturated band on top
    of it competes for attention — use the quiet light tint instead. With
    no Big Color anywhere in the table, the band IS the color story, so it
    goes dark+saturated.
    """
    rule = PALETTE["neutral"]["column_label_rule"]
    options = {
        "column_labels_border_bottom_color": rule,
        "column_labels_border_bottom_width": "2px",
        "column_labels_border_bottom_style": "solid",
    }
    if shade == "light":
        if hue == "grey":
            options["column_labels_background_color"] = PALETTE["neutral"]["label_band"]
        else:
            options["column_labels_background_color"] = PALETTE["washed"][hue]
        return gt.tab_options(**options)
    if shade == "dark":
        options["column_labels_background_color"] = PALETTE["solid"][hue]
        gt = gt.tab_options(**options)
        locations = [loc.column_labels()]
        spanners = getattr(gt, "_spanners", None)
        if spanners:
            spanner_ids = [s.spanner_id for s in spanners]
            if spanner_ids:
                locations.append(loc.spanner_labels(ids=spanner_ids))
        return gt.tab_style(style=style.text(color="white"), locations=locations)
    raise ValueError("band(): shade must be 'light' or 'dark', got %r" % (shade,))


def stripe(gt):
    """Apply zebra row striping in the pinned neutral stripe hex.

    THE GATE (this function does not check it — the caller must): use
    striping only when the table has **>= 10 body rows AND the body isn't
    essentially fully covered by colored cells** (data_color fills and
    stripes fight each other visually). Below 10 rows, or with most cells
    already colored, skip this call entirely.
    """
    return gt.opt_row_striping().tab_options(
        row_striping_background_color=PALETTE["neutral"]["row_stripe"],
    )


def stub_tint(gt, *, hue):
    """Tint the stub background so row labels separate from the value columns.

    ``hue="grey"`` uses the neutral label-band grey (the default with no
    Big Color). Any other hue key (``navy``/``forest``/``oxblood``/
    ``espresso``/``ochre``/``tan``) uses that hue's washed tint — pick the
    hue that matches the table's dominant heatmap family (see the DA
    hue-selection rule: a Blues heatmap harmonizes to the washed-navy tint,
    Greens to washed-forest, etc.) so the quiet stub surface doesn't clash
    with the loud color elsewhere.
    """
    if hue == "grey":
        color = PALETTE["neutral"]["label_band"]
    else:
        color = PALETTE["washed"][hue]
    return gt.tab_style(style=style.fill(color=color), locations=loc.stub())


def _is_missing(value):
    """True if ``value`` is a missing scalar — ``None`` / NaN / ``pd.NA`` / null.

    ``value != value`` is ``True`` for float NaN, but pandas' *nullable*
    dtypes (``pd.NA``) make ``pd.NA != pd.NA`` return ``pd.NA`` itself, and
    ``bool(pd.NA)`` raises (its truth value is ambiguous) rather than
    returning ``False`` — so a bare ``value != value`` check silently
    crashes on nullable columns instead of just being wrong. The ``except``
    below treats that ambiguity as "yes, missing."
    """
    if value is None:
        return True
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return True


def _column_min_max(data, cols):
    """Return ``(lo, hi)`` as floats across every column in ``cols``, skipping NaN/NA.

    A column that is entirely missing yields NaN (float dtype) or ``pd.NA``
    (nullable dtype) from ``.min()``/``.max()`` — never a plain Python
    ``None`` — so a naive ``is None`` guard lets a ``[nan, nan]`` domain
    through, and ``float(pd.NA)`` raises outright. Skip any column whose
    min/max is missing; raise a clear error only if EVERY selected column is
    entirely missing (no numeric extent exists to build a domain from at
    all), rather than an opaque numpy/pandas crash.
    """
    lo = None
    hi = None
    for col in cols:
        series = data[col]
        c_min, c_max = series.min(), series.max()
        if _is_missing(c_min) or _is_missing(c_max):
            continue
        c_min, c_max = float(c_min), float(c_max)
        lo = c_min if lo is None else min(lo, c_min)
        hi = c_max if hi is None else max(hi, c_max)
    if lo is None or hi is None:
        raise ValueError(
            "heatmap(): every selected column %r is all-missing (no numeric "
            "values to build a domain from)" % (cols,)
        )
    return lo, hi


def heatmap(gt, columns, *, kind, hue, domain=None, reverse=False):
    """Color one measure's column(s) by value — the mechanical half of Big Color.

    ``columns``: str or list of column names colored together under one
    shared domain/palette, so multi-column facets of the same measure stay
    comparable.

    ``kind``: ``"sequential"`` (a plain magnitude, no inherent direction) or
    ``"diverging"`` (a signed value where negative/positive both matter).
    This function does NOT infer ``kind`` from the data's sign — that is
    the model's decision.

    ``hue``: a semantic key resolved against ``PALETTE["sequential"]`` /
    ``PALETTE["diverging"]`` (e.g. ``"neutral"`` -> Blues, ``"default"`` ->
    RdYlGn), or any other string, passed straight through as an explicit
    palette NAME.

    ``domain``: when ``None``, computed from ``columns`` across the GT's own
    data (missing-only columns are skipped rather than crashing — see
    ``_column_min_max``) — sequential gets the full ``[min, max]``;
    diverging gets a **symmetric** ``[-M, M]`` with ``M = max(abs(min),
    abs(max))``. Pass an explicit ``domain`` to override (e.g. to exclude a
    summary/total row from the color scale so it doesn't compress the real
    data's range — see ``revenue`` in ``build_house_table`` below for
    exactly this case).

    ``reverse``: for a **diverging** measure where positive genuinely means
    *worse* (cost overrun, error rate, latency, churn — "more is worse"),
    pass ``reverse=True`` so the palette's low/high ends swap (green stays
    "good" = negative, red stays "bad" = positive) instead of literally
    reversing the color list. Actually ignored (forced ``False``) for
    ``kind="sequential"`` — a plain magnitude has no good/bad orientation to
    flip, so passing ``True`` there would silently flip the intended
    light-to-dark magnitude encoding instead of doing nothing. This is the
    parameter ``references/RULES.md``'s "Percent / rate / change" rule tells
    callers to pass.

    THE GOTCHA this function exists to prevent: ``fmt_percent`` expects
    *fractional* values (``0.12`` renders as ``12%``) — a percent column
    stored as already-scaled ``12`` needs ``scale_values=False`` wherever
    it's formatted, and the same fractional-vs-scaled question applies to
    the domain passed here. A bare ``data_color(...)`` call with no
    explicit ``domain`` is a **correctness bug**, not a style nit: without
    a pinned domain, the color a given value renders as can shift between
    runs (or between two tables) depending on what else happens to be in
    the column at that moment.
    """
    cols = [columns] if isinstance(columns, str) else list(columns)
    if domain is None:
        lo, hi = _column_min_max(gt._tbl_data, cols)
        if kind == "diverging":
            m = max(abs(lo), abs(hi))
            domain = [-m, m] if m != 0 else [-1.0, 1.0]
        elif kind == "sequential":
            domain = [lo, hi]
        else:
            raise ValueError("heatmap(): kind must be 'sequential' or 'diverging', got %r" % (kind,))
    if kind == "sequential":
        palette = PALETTE["sequential"].get(hue, hue)
    elif kind == "diverging":
        resolved = PALETTE["diverging"].get(hue, hue)
        palette = resolved[0] if isinstance(resolved, (list, tuple)) else resolved
    else:
        raise ValueError("heatmap(): kind must be 'sequential' or 'diverging', got %r" % (kind,))
    return gt.data_color(
        columns=cols,
        palette=palette,
        domain=domain,
        na_color=PALETTE["neutral"]["na_cell"],
        truncate=False,
        autocolor_text=True,
        reverse=reverse if kind == "diverging" else False,
    )


def status_chip(gt, column, meaning):
    """Fill a DISCRETE categorical column's cells by a value -> meaning map.

    ``meaning`` maps each cell VALUE (e.g. ``"On Track"``) to one of
    ``"good"`` / ``"bad"`` / ``"neutral"``. ``good``/``bad`` fill with the
    forest/oxblood DA solids + white text (the same solids the sequential
    "positive"/"warning" semantics lean on elsewhere); ``neutral`` fills
    with the tan DA solid + white text — a deliberately mid, non-alarming
    color, not a second "bad".

    THE POINT of this function: a red/green column is not always a
    continuous heatmap. When the column's values are a small fixed set of
    categories (status, state, pass/fail) rather than a magnitude, use THIS
    function, never ``data_color``/``heatmap`` — the good/bad resolution
    must land on the exact same two solids either way (continuous heatmap
    or discrete chip), because the meaning is the same: color here is never
    decorative, it always encodes good/bad/neutral, resolved the same
    deterministic way regardless of whether the underlying data is
    continuous or discrete.

    A missing cell (``None``/NaN/``pd.NA`` — e.g. a nullable pandas string
    dtype) is skipped rather than compared: ``v == value`` on a ``pd.NA``
    scalar returns ``pd.NA`` itself, and ``bool(pd.NA)`` raises (ambiguous
    truth value) instead of being simply ``False``, which would otherwise
    crash this function on the exact kind of missing status cell
    ``sub_missing(missing_text="—")`` is meant to handle gracefully
    elsewhere.

    ``loc.body(rows=...)`` interprets a list of INTEGERS as **display**
    positions — but with ``groupname_col=`` set, ``great_tables`` renders
    rows grouped into sections, which can reorder them relative to the
    underlying data's original row order (this table's own demo rows
    happen to already be sorted by group, so it wouldn't show the bug, but
    a caller whose source rows interleave groups would silently color the
    wrong cells). When the table has a stub (``rowname_col=``), target rows
    by their **row NAME** instead — a string, matched to the row's actual
    identity regardless of how ``great_tables`` reorders it for display —
    by reading ``gt._stub.rows`` (each entry's ``.rowname``, in original
    data order, one per row of ``gt._tbl_data``). Without a stub there is
    no row name to match against, so integer display positions are used as
    a fallback (correct as long as the table has no ``groupname_col``, or
    its groups already appear in source-row order).
    """
    fills = {
        "good": PALETTE["solid"]["forest"],
        "bad": PALETTE["solid"]["oxblood"],
        "neutral": PALETTE["solid"]["tan"],
    }
    values = gt._tbl_data[column]
    rownames = [r.rowname for r in gt._stub.rows]
    has_stub = all(name is not None for name in rownames) and len(rownames) == len(values)
    for value, state in meaning.items():
        if state not in fills:
            raise ValueError("status_chip(): meaning must map to 'good'/'bad'/'neutral', got %r" % (state,))
        if has_stub:
            selector = [name for name, v in zip(rownames, values) if not _is_missing(v) and v == value]
        else:
            selector = [i for i, v in enumerate(values) if not _is_missing(v) and v == value]
        if not selector:
            continue
        gt = gt.tab_style(
            style=[style.fill(color=fills[state]), style.text(color="white")],
            locations=loc.body(columns=column, rows=selector),
        )
    return gt


def summary_row(gt, row_index, *, bold=True):
    """Mark one ORDINARY DATA row as a totals/summary row, distinct from a plain row.

    For a **whole-table grand total**, prefer ``gt.grand_summary_rows(...)``
    (native to `great_tables`) + ``tab_style(..., locations=loc.grand_summary())``
    — see the "Total" row in ``build_house_table()`` below. That native
    mechanism keeps the total structurally separate from any
    ``groupname_col`` section (no fake group label needed) and it's excluded
    from `data_color`'s domain automatically. Reach for THIS helper only for
    a row that must live inline as an actual data row instead (e.g. a
    per-group subtotal you want positioned among that group's own rows,
    which ``grand_summary_rows`` cannot do — it always places the total(s)
    at the very top or bottom of the whole table).

    Applies a stronger — but still restrained — top border rule
    (``#BDBDBD``, ~1.5px, vs. the default hairline between ordinary rows)
    and, by default, bold text weight to ``row_index`` (a 0-based display
    position, per ``loc.body()``'s indexing — not a DataFrame index).
    """
    styles = [style.borders(sides="top", color=PALETTE["neutral"]["structural_rule"], weight="1.5px")]
    if bold:
        styles.append(style.text(weight="bold"))
    return gt.tab_style(style=styles, locations=loc.body(rows=[row_index]))


def group_emphasis(gt, *, hue="grey"):
    """Emphasize every ``groupname_col`` header row so section breaks read clearly.

    Applies a light background fill (grey by default, or the washed tint of
    ``hue`` when the table has Big Color — harmonizing to the same hue as
    the stub/band) AND bold weight to each group label row — the pair is
    non-negotiable: fill alone reads as noise, bold alone as a stray body
    row. Also pins the ``#BDBDBD`` structural rule above and below each
    group label, for use whenever the table is built with ``groupname_col=``.
    """
    color = PALETTE["neutral"]["label_band"] if hue == "grey" else PALETTE["washed"][hue]
    rule = PALETTE["neutral"]["structural_rule"]
    return gt.tab_options(
        row_group_background_color=color,
        row_group_font_weight="bold",
        row_group_border_top_color=rule,
        row_group_border_bottom_color=rule,
        row_group_padding="6px",
    )


# ---------------------------------------------------------------------------
# The demo: "Regional Product Line Performance" — 12 products, 3 region
# groups of 4, exercising every helper above at once. This is the ONE worked
# example the whole skill points at; pattern-match the piece of it (and the
# matching row in references/RULES.md) that fits your actual data.
# ---------------------------------------------------------------------------


def build_house_table():
    """Build and render the house-format reference table.

    Column roles (walk through references/RULES.md alongside this):

    - ``product``    -> stub (rowname_col) — a row identifier.
    - ``region``     -> groupname_col — the organizing category.
    - ``units_sold`` -> plain magnitude, thousands separator, UNCOLORED.
    - ``revenue``    -> the sequential heatmap HERO measure (Blues/neutral).
    - ``yoy_change`` -> the diverging heatmap measure (RdYlGn/default) — the
                        2nd and LAST colored measure. Two is the ceiling;
                        a 3rd colored column would break the rule.
    - ``status``     -> categorical good/bad/neutral via status_chip, NOT a
                        heatmap — it is 3 discrete states, not a magnitude.
    - ``rank``       -> plain integer, no color, no decimals — a rank's
                        information is its order, not its size.
    """
    products = pd.DataFrame(
        [
            # product,           region,          units_sold, revenue, yoy_change, status,      rank
            ("Alpha Widget",     "North America",  1240,      482000,   0.18,      "On Track",  1),
            ("Beta Gadget",      "North America",   860,      305000,  -0.07,      "Watch",      4),
            ("Gamma Tool",       "North America",   430,      178500,   0.05,      "On Track",   7),
            ("Delta Device",     "North America",   210,       64000,  -0.22,      "At Risk",   11),
            ("Epsilon Unit",     "Europe",           980,      410000,   0.12,      "On Track",  2),
            ("Zeta Kit",         "Europe",           560,      239000,   None,      "Watch",      6),
            ("Eta Module",       "Europe",           340,      142000,  -0.15,      "At Risk",    9),
            ("Theta Part",       "Europe",           125,       38500,   0.02,      "Watch",     12),
            ("Iota Component",   "Asia-Pacific",     915,      396000,   0.27,      "On Track",  3),
            ("Kappa Assembly",   "Asia-Pacific",     705,      298000,   0.09,      "On Track",  5),
            ("Lambda System",    "Asia-Pacific",     388,      165000,  -0.11,      "At Risk",    8),
            ("Mu Product",       "Asia-Pacific",     245,       71500,  -0.04,      "Watch",     10),
        ],
        columns=["product", "region", "units_sold", "revenue", "yoy_change", "status", "rank"],
    )

    kappa_row_index = products.index[products["product"] == "Kappa Assembly"][0]  # footnote target

    gt = (
        GT(products, rowname_col="product", groupname_col="region")
        .tab_header(
            title="Regional Product Line Performance",
            subtitle=md("Full-year revenue, volume, and trend by product — grouped by region"),
        )
        .tab_stubhead(label="Product")
        .tab_spanner(label="Volume & Revenue", columns=["units_sold", "revenue"])
        .tab_spanner(label="Trend", columns=["yoy_change", "status"])
        # spanner-seam vertical divider — right edge of the LAST column in the
        # first group, applied to both the body and the column-labels row so
        # the seam runs the full height of the table (small_color.md (b)).
        .tab_style(
            style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
            locations=loc.body(columns="revenue"),
        )
        .tab_style(
            style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
            locations=loc.column_labels(columns="revenue"),
        )
        .fmt_number(columns="units_sold", decimals=0, use_seps=True)
        .fmt_currency(columns="revenue", decimals=0)
        .fmt_percent(columns="yoy_change", decimals=1)
        .fmt_integer(columns="rank")
        .sub_missing(columns=["yoy_change", "status", "rank"], missing_text="—")
    )
    gt = humanize_labels(
        gt,
        products,
        overrides={"units_sold": "Units Sold", "yoy_change": "YoY Change"},
    )

    # Big Color: exactly 2 colored measures (the ceiling). `revenue` is the
    # sequential hero (a neutral magnitude -> Blues); `yoy_change` is the
    # diverging 2nd-and-last measure (signed, positive=good -> RdYlGn
    # default orientation, no reverse). `status` is a categorical good/bad/
    # neutral column, NOT a 3rd heatmap — status_chip, not data_color. The
    # domain for each is computed from `products` alone (heatmap()'s default
    # when domain=None) — safe because the grand-summary Total added below
    # is NOT part of `gt._tbl_data`; unlike a manually appended total ROW, it
    # can never stretch/compress the color scale.
    gt = heatmap(gt, "revenue", kind="sequential", hue="neutral")
    gt = heatmap(gt, "yoy_change", kind="diverging", hue="default")
    gt = status_chip(gt, "status", {"On Track": "good", "At Risk": "bad", "Watch": "neutral"})

    # Heading band: Big Color is present (both heatmaps + the status chips)
    # -> LIGHT band, harmonized to the Blues heatmap's navy family (the DA
    # hue-selection rule: match an existing heatmap hue first).
    gt = band(gt, shade="light", hue="navy")

    # Small-Color polish: 12 body rows clears the >=10-row striping gate,
    # and only 2 of 6 columns carry continuous color (revenue, yoy_change)
    # — the body is far from "essentially fully covered," so striping and
    # fills don't fight. Stub tint and group emphasis harmonize to the same
    # navy family as the band.
    gt = stripe(gt)
    gt = stub_tint(gt, hue="navy")
    gt = group_emphasis(gt, hue="navy")

    # Grand summary "Total" row — the NATIVE mechanism for a whole-table
    # total (great_tables' own `grand_summary_rows`), not a manually
    # appended data row. This is deliberately NOT the `summary_row()`
    # helper above: grand_summary_rows() places the total in its own
    # structural section below every groupname_col group, with no fake
    # group label required (a manually appended row needs SOME value in
    # the `region` column, and `None`/NaN renders as the literal text
    # "nan" — grand_summary_rows sidesteps the whole problem). Only
    # `units_sold`/`revenue` are meaningfully summable — `yoy_change`,
    # `status`, and `rank` have no sensible total, so the aggregation
    # function only returns the two summable columns and the rest render
    # via `missing_text="—"` (overriding the `"---"` default so it matches
    # this table's `sub_missing` em dash elsewhere).
    #
    # `fns` values must return a `pandas.Series`; `grand_summary_rows`
    # applies at most ONE `fmt=` formatter to every summarized column, so
    # with two columns needing different formats (thousands-separated
    # integer vs. currency) the values are pre-formatted as display
    # strings inside the function itself instead of using `fmt=`.
    def _totals(d):
        return pd.Series(
            {
                "units_sold": f"{int(d['units_sold'].sum()):,}",
                "revenue": f"${int(d['revenue'].sum()):,}",
            }
        )

    gt = gt.grand_summary_rows(fns={"Total": _totals}, missing_text="—")
    gt = gt.tab_style(
        style=[
            style.text(weight="bold"),
            style.borders(sides="top", color=PALETTE["neutral"]["structural_rule"], weight="1.5px"),
        ],
        locations=loc.grand_summary(),
    )
    gt = gt.tab_style(
        style=style.text(weight="bold"),
        locations=loc.grand_summary_stub(),
    )

    gt = (
        gt.tab_footnote(
            footnote="Restated to include a distributor rebate posted in Q4.",
            locations=loc.body(columns="revenue", rows=[kappa_row_index]),
        )
        .tab_source_note(source_note="Source: internal sales ledger, FY close. Figures in USD.")
    )

    gt = frame(gt)
    finalize(gt, path="house_table.png")
    return gt


if __name__ == "__main__":
    build_house_table()
