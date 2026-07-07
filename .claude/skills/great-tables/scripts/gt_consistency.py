"""Consistency helpers for the great-tables skill (scripted variant).

This module encodes **zero design decisions**. It holds only:

  * ``PALETTE`` — the color-hex constants, and
  * ``frame`` / ``finalize`` — two mechanical helpers.

Every *decision* (which measure gets Big Color, band light vs. dark, which
Step-5 checklist items fire, etc.) lives in the skill's prose, which BOTH the
prose and scripted variants read. The script never makes the model smarter; it
only removes the chance to fat-finger a hex or forget a ``gtsave`` argument.

SOURCE OF TRUTH: ``references/palettes.md`` is the single human-readable source
of truth for every hex. This file must **mirror it exactly**. The drift-guard
test ``tests/test_palette_parity.py`` asserts that the hexes here equal the
hexes parsed from ``palettes.md`` and fails CI if they diverge — so when the doc
changes, update this file (never the reverse).

This module deliberately does NOT ``import great_tables``: ``frame`` and
``finalize`` only call methods on the ``gt`` object passed to them, so the
parity test can import ``PALETTE`` dependency-free.
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
