"""Consistency helpers for the great-tables skill (scripted variant).

This module encodes **zero design decisions**. It holds only:

  * ``PALETTE`` — the color-hex / palette-NAME constants, and
  * a handful of **mechanical execution helpers** — ``frame`` / ``finalize``
    (global constants) and ``heatmap`` / ``band`` / ``stripe`` / ``stub_tint``
    (Step-3/4/5 execution).

Every *decision* (which measure gets Big Color, band light vs. dark, which
Step-5 checklist items fire, which hue, which columns) lives in the skill's
prose, which BOTH the prose and scripted variants read. The helpers here take
those decisions **as arguments** and only guarantee that two runs which made the
*same* decision execute it **identically** — they choose nothing. This is the
"thin execution helper" port (R8): the model decides *what*, this module
executes *how*, and the "how" can no longer drift because it is one function
call instead of five hand-written lines (kills PP-6/PP-7/PP-8 and the
hand-typed-hex half of PP-12/PP-13).

SOURCE OF TRUTH: ``references/palettes.md`` is the single human-readable source
of truth for every hex and palette NAME. This file must **mirror it exactly**.
The drift-guard test ``tests/test_palette_parity.py`` asserts that the hexes
here equal the hexes parsed from ``palettes.md`` and fails CI if they diverge —
so when the doc changes, update this file (never the reverse). The same test
also asserts that the execution helpers below never inline a stray hex or
palette NAME: every color they touch is read from ``PALETTE`` or passed in by
the caller.

This module deliberately does NOT ``import great_tables`` at the top: every
helper only calls methods on the ``gt`` object passed to it (``band`` imports
``style``/``loc`` lazily, inside the function, only for the dark-band case), so
the parity test can import ``PALETTE`` dependency-free.
"""

# ---------------------------------------------------------------------------
# PALETTE — mirrors references/palettes.md §1 (solids + washed tints), §2
# (neutral roles), and §3 (sequential / diverging palette NAMES). Hexes are
# UPPERCASE to match the doc.
# ---------------------------------------------------------------------------
PALETTE = {
    # §1 — Dark Academia SOLID Big-Color palette (white text on every solid).
    "solid": {
        "navy": "#22384F",      # default with no other cue
        "forest": "#2F4A38",    # nature, growth, environment, money/finance
        "oxblood": "#5C2E2E",   # risk, alerts, deficits, intensity
        "espresso": "#4A3A2C",  # historical, literary, food/wine, vintage
        "ochre": "#9A7B33",     # premium / awards / highlight (accent)
        "tan": "#8A7452",       # secondary warm accent / mid (cream tint)
    },
    # §1 — the washed light tint paired with each solid (same keys).
    "washed": {
        "navy": "#EAF0F6",
        "forest": "#EAF1EC",
        "oxblood": "#F5EBEB",
        "espresso": "#F1EADD",
        "ochre": "#F5EFDC",
        "tan": "#EFE7D6",       # cream
    },
    # §2 — neutral structural surfaces (light greys).
    "neutral": {
        "label_band": "#F0F0F0",         # light label band
        "row_stripe": "#F6F6F6",         # row stripe
        "hairline": "#E8E8E8",           # cell hairline between rows, 1px
        "column_label_rule": "#CCCCCC",  # column-label bottom rule, 2px
        "structural_rule": "#BDBDBD",    # group / summary structural rule
        "vertical_divider": "#D0D0D0",   # column-group vertical divider
        "na_cell": "#808080",            # NA / empty cell fill
    },
    # §3 — sequential palette NAMES (matplotlib/brewer), keyed by semantic
    # meaning. Passed to data_color(palette=...), not fixed hexes.
    "sequential": {
        "positive": "Greens",    # growth / "more is better"
        "warning": "Reds",       # worse / "more is worse"
        "warning_alt": "Oranges",
        "neutral": "Blues",      # volume / count / price / population
    },
    # §3 — diverging palette NAMES for signed values.
    "diverging": {
        "default": "RdYlGn",                 # red = bad, green = good
        "colorblind_safe": ["RdBu", "PuOr"],
    },
}


def frame(gt, color=None, width="1px", style="solid"):
    """Apply the boxed enclosing light border on all four sides.

    Mechanical only — no decisions. Sets the top/bottom/left/right table
    border color, width, and style to give the non-negotiable enclosing box.
    The ``style`` is set explicitly because Great Tables defaults the left/right
    border style to ``"none"`` — setting only color/width would leave the side
    borders invisible and render top/bottom rules instead of a box.
    ``color``/``width``/``style`` may be overridden but default to values
    derived from ``PALETTE``.

    Returns the GT object (``tab_options`` is chainable).
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
    """Save the table with the CONSISTENCY_DEV ``gtsave`` defaults.

    Mechanical only — no decisions. Calls ``gt.gtsave(path, ...)`` with a
    raised outer margin (``expand=15``) and retina zoom (``zoom=2.0``), letting
    any keyword in ``**overrides`` take precedence (e.g. ``vwidth``/``vheight``
    when the layout needs room).
    """
    opts = {"expand": 15, "zoom": 2.0}
    opts.update(overrides)
    return gt.gtsave(path, **opts)


# ---------------------------------------------------------------------------
# Thin execution helpers (R8). Each takes the model's flowchart decision as an
# argument and guarantees identical execution. They make NO design choice: they
# do not auto-detect ``kind``, do not pick ``columns``, do not choose ``hue``.
# Every hex / palette NAME they emit is read from ``PALETTE`` or supplied by the
# caller — none is inlined here.
# ---------------------------------------------------------------------------

def _as_columns(columns):
    """Normalize a str-or-list of column names to a list (order preserved)."""
    if isinstance(columns, str):
        return [columns]
    return list(columns)


def _is_missing(value):
    """True if ``value`` is a missing scalar — ``None`` / NaN / ``pd.NA`` / null.

    Written to work without importing pandas or numpy at module top (keeps the
    parity test dependency-free). Detection by cases:

    * ``None`` — pandas/polars return this for an all-null column's ``.min()``
      only in polars; the explicit check also covers plain ``None``.
    * float ``NaN`` (pandas float dtype, numpy scalars) — ``NaN != NaN`` is
      ``True``, so ``bool(value != value)`` is ``True``.
    * ``pd.NA`` (pandas *nullable* dtypes) — ``pd.NA != pd.NA`` yields ``pd.NA``
      and ``bool(pd.NA)`` raises (ambiguous), so the ``except`` treats it as
      missing. This is the case that made ``float(pd.NA)`` crash before.
    """
    if value is None:
        return True
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return True


def _column_min_max(data, cols):
    """Return ``(lo, hi)`` as floats across every column in ``cols``.

    Works for both a pandas and a polars ``gt._tbl_data``: indexing a column by
    name (``data[col]``) and calling ``.min()`` / ``.max()`` is supported by
    both, and both skip nulls. All-missing columns are SKIPPED: a pandas
    all-null column yields ``NaN`` (float dtype) or ``pd.NA`` (nullable dtype)
    from ``.min()`` — NOT ``None`` — so a plain ``is None`` guard would let a
    ``[nan, nan]`` domain through (and ``float(pd.NA)`` would raise); ``_is_missing``
    catches all three. Raises ``ValueError`` if EVERY column is all-missing so no
    numeric extent exists (a clear error, not a numpy crash).
    """
    lo = None
    hi = None
    for col in cols:
        series = data[col]
        c_min = series.min()
        c_max = series.max()
        if _is_missing(c_min) or _is_missing(c_max):
            continue
        c_min = float(c_min)
        c_max = float(c_max)
        lo = c_min if lo is None else min(lo, c_min)
        hi = c_max if hi is None else max(hi, c_max)
    if lo is None or hi is None:
        raise ValueError(
            "heatmap(): every selected column %r is all-missing (no numeric "
            "values to build a domain from)" % (cols,)
        )
    return lo, hi


def _heatmap_domain(data, cols, kind):
    """Compute the shared ``data_color`` domain across every facet column.

    * ``diverging`` → symmetric about 0: ``[-M, M]`` with ``M = max(|lo|,|hi|)``.
    * ``sequential`` → the full data range ``[lo, hi]``.

    One domain spans every column in ``cols`` (never per-column domains), which
    is what makes two runs that colored the same columns byte-identical and
    kills PP-6 (asymmetric diverging) and PP-7 (arbitrary bounds).
    """
    lo, hi = _column_min_max(data, cols)
    if kind == "diverging":
        m = max(abs(lo), abs(hi))
        if m == 0:
            # Every selected value is exactly 0 (or all-missing collapsed to 0):
            # a [-0.0, 0.0] domain has identical endpoints, which GT rescales to
            # the low-end (extreme) color — painting genuinely neutral data as
            # the most-negative hue. Use a small nonzero symmetric domain so 0
            # maps to the palette's center (neutral). Deterministic.
            return [-1.0, 1.0]
        return [-m, m]
    if kind == "sequential":
        return [lo, hi]
    raise ValueError(
        "heatmap(): kind must be 'sequential' or 'diverging', got %r" % (kind,)
    )


def _resolve_palette(kind, hue):
    """Resolve a semantic ``hue`` key to a palette NAME, else pass it through.

    The model decides ``hue``; this only translates. A semantic key is looked
    up in ``PALETTE``; anything else (an explicit palette NAME the model chose)
    is returned unchanged. No palette NAME is inlined here — every mapped value
    comes from ``PALETTE``.

    * sequential → ``PALETTE["sequential"]`` keys: ``positive`` / ``warning`` /
      ``warning_alt`` / ``neutral``.
    * diverging → ``PALETTE["diverging"]`` keys: ``default`` (→ the default
      name) or ``colorblind_safe`` (→ the first colorblind-safe alternative).
      An explicit alternative name already in that list, or any other literal
      palette NAME, passes through unchanged.
    """
    if kind == "sequential":
        return PALETTE["sequential"].get(hue, hue)
    if kind == "diverging":
        diverging = PALETTE["diverging"]
        if hue in diverging:
            resolved = diverging[hue]
            if isinstance(resolved, (list, tuple)):
                return resolved[0]
            return resolved
        return hue
    raise ValueError(
        "heatmap(): kind must be 'sequential' or 'diverging', got %r" % (kind,)
    )


def heatmap(gt, columns, *, kind, hue, domain=None):
    """Color one measure's column(s) by value — the mechanical half of Step 3.

    The model decides everything; this only executes:

    * ``columns`` — str or list of column names to color **together** (one
      shared domain/palette so the facets stay comparable).
    * ``kind`` — ``"sequential"`` or ``"diverging"`` (model's Step-3 call; this
      does NOT auto-detect signedness).
    * ``hue`` — a semantic key resolved through ``PALETTE`` (see
      ``_resolve_palette``) OR an explicit palette NAME passed straight through.
    * ``domain`` — normally ``None`` so the domain is computed from the GT's own
      data (``gt._tbl_data``) across all ``columns`` (symmetric ``[-M, M]`` for
      diverging, full ``[min, max]`` for sequential). Pass a list to override
      (model's explicit choice, used verbatim).

    Applies ``data_color`` with the pinned ``na_color`` / ``truncate=False`` /
    ``autocolor_text=True`` and returns the GT.
    """
    cols = _as_columns(columns)
    if domain is None:
        domain = _heatmap_domain(gt._tbl_data, cols, kind)
    palette = _resolve_palette(kind, hue)
    return gt.data_color(
        columns=cols,
        palette=palette,
        domain=domain,
        na_color=PALETTE["neutral"]["na_cell"],
        truncate=False,
        autocolor_text=True,
    )


def band(gt, *, shade, hue):
    """Apply the Step-4 heading band + the mandatory bottom rule.

    * ``shade`` — ``"light"`` or ``"dark"`` (model's Step-4 call).
    * ``hue`` — a solid/washed key (``navy`` / ``forest`` / ``oxblood`` /
      ``espresso`` / ``ochre`` / ``tan``) or ``"grey"``.

    light → ``column_labels_background_color`` = the washed tint (or the neutral
    grey label band when ``hue == "grey"``). dark → the DA solid, plus white
    column-label text (``great_tables`` has no ``tab_options`` option for
    column-label text color, so the white is applied via
    ``tab_style(style.text(color="white"), loc.column_labels())``).

    ALWAYS also applies the mandatory column-label bottom rule
    (``PALETTE["neutral"]["column_label_rule"]`` = the 2px rule) — this is the
    Step-4 constant present under any band, and pinning it kills PP-8.

    Returns the GT.
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
        # No tab_options option sets column-label text color; use tab_style. Also
        # whiten SPANNER labels so they match the dark band — otherwise they keep
        # their default dark text and read as low-contrast on the solid. This
        # great_tables version's loc.spanner_labels() requires explicit ids (a
        # bare call raises), so pull them from the GT's own spanners and only add
        # that location when spanners exist.
        from great_tables import loc, style

        locations = [loc.column_labels()]
        spanners = getattr(gt, "_spanners", None)
        if spanners:
            spanner_ids = [s.spanner_id for s in spanners]
            if spanner_ids:
                locations.append(loc.spanner_labels(ids=spanner_ids))
        return gt.tab_style(
            style=style.text(color="white"),
            locations=locations,
        )
    raise ValueError("band(): shade must be 'light' or 'dark', got %r" % (shade,))


def stripe(gt):
    """Apply zebra row striping in the pinned neutral stripe hex (Step 5(c)).

    Mechanical only. ``opt_row_striping()`` turns striping on;
    ``row_striping_background_color`` pins the exact stripe hex
    (``PALETTE["neutral"]["row_stripe"]``) so it can't drift. Returns the GT.
    """
    return gt.opt_row_striping().tab_options(
        row_striping_background_color=PALETTE["neutral"]["row_stripe"],
    )


def stub_tint(gt, *, hue):
    """Tint the stub background so row labels separate from values (Step 5(d)).

    * ``hue`` — ``"grey"`` → the neutral label-band grey; otherwise the washed
      tint for that DA hue. The model decides which; this only applies it via
      ``stub_background_color``. Returns the GT.
    """
    if hue == "grey":
        color = PALETTE["neutral"]["label_band"]
    else:
        color = PALETTE["washed"][hue]
    return gt.tab_options(stub_background_color=color)
