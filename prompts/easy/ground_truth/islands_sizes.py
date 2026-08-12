"""Ground truth for prompts/easy/islands_sizes.json.

Data: data/islands.csv (the base R `islands` dataset — 48 landmasses whose
      land area exceeds 10,000 square miles; area is given in THOUSANDS of
      square miles). "Landmass" here means both literal islands (Borneo,
      Cuba, ...) and continents (Asia, Africa, ...) side by side — that is
      the source dataset's own scope, not a narrowing/broadening choice
      made here.
Story: Every island/landmass and its size, one row each, biggest first.

Design decisions:
- Row scope: the prompt puts no limit on which islands to show ("the
  islands and their sizes") -- all 48 rows are shown. 48 is simply this
  data's own row count, not a number the prompt asked for, so no
  `row_count` is recorded in REQUIRED_INSTRUCTIONS below.
- Sort: nothing in the prompt states an order. Descending by size ("biggest
  first") is the natural reading for a plain "table of sizes" and is what
  most size-ranked lists default to -- stated here as a deliberate pick,
  not left implicit.
- Color: `size` is a single, plain magnitude column with no inherent
  direction -- and it IS the entire point of this table, so it gets the
  sequential Blues heatmap, still linear (no log/rank transform -- a
  transformed domain would misrepresent the actual magnitude relationship
  between e.g. Asia and Vancouver Island). Domain floor, by author
  direction: a NEGATIVE pre-tint buffer, NOT 0 and NOT the sample's own
  minimum (12). The sample min (or even a literal 0) as the domain floor
  still puts the smallest island(s) at, or arbitrarily close to, t=0 --
  the palette's absolute lightest swatch, which renders visually
  indistinguishable from an uncolored/background cell (a reader could
  easily misread that as "this cell's color wasn't computed" rather than
  "this is a genuinely small landmass"). Reserving the bottom 20% of the
  scale as a buffer -- domain floor = `-0.2 * size_hi` -- guarantees every
  real value (even the smallest, 12) lands at a visibly non-zero, if pale,
  shade, while the domain ceiling stays the data's real max (16,988) so
  the largest continent still anchors the darkest swatch exactly. This
  is a deliberate, reproducible rule (20% of the real max, not a magic
  literal), not a literal [min, max] domain -- an explicit exception to
  the usual "domain must be the data's own [min, max]" default, made here
  because that default actively misleads on a range this skewed. Text
  stays legible either way via `autocolor_text=True`.
- Striping: with only ONE non-stub column (`size`), coloring it alone
  already accounts for 100% of the visible body columns -- by the same
  "essentially fully covered" logic that skips striping on a heavily
  colored wide table, a fully-colored single-column body is just as
  "covered" even though it's narrow. Striping is skipped for that reason,
  not because of the (also true) >=10-row gate.
- No grouping/spanner: the prompt names no organizing category and the
  data has none (just name + size) -- neither is invented.
"""
from pathlib import Path

import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
# Read directly by scripts/gt_compare.py via module import. Keep these as
# literal dict/list assignments (no computation) so they're both a plain-text
# answer key a human can review and something a script can load without exec
# risk beyond what already happens to render the table.

# Acceptable label synonyms per underlying data column. Wording is free; the
# label just has to name the right concept. Keys are the SOURCE CSV column
# name(s) the label is standing in for.
LABEL_SYNONYMS = {
    "name": ["island", "landmass", "name"],
    "size": ["size", "area", "land area", "thousand sq", "square miles"],
}

# The prompt ("Make a table of the islands and their sizes") makes no
# explicit structural demand -- no stated row count, sort order, or
# grouping -- so nothing is required here. Absence of a key means "not
# required," never inferred from prose at eval time.
REQUIRED_INSTRUCTIONS = {}

# Keyword-presence check for the caption/subtitle overlap rule. The caption
# (first source note) states the sort order and the color-scale rationale;
# the subtitle only describes units/scope, so it must not lean on the same
# "largest to smallest" phrasing the caption owns.
CAPTION_KEYWORDS = {
    "caption_should_mention": ["largest to smallest", "land area"],
    "subtitle_should_not_duplicate": ["largest to smallest"],
}

# Underlying SOURCE CSV column(s) that are the canonical colored measure(s),
# used for value-based matching -- NOT the rendered column name/label.
CANONICAL_MEASURES = {
    "colored": ["size"],
    "hero_uncolored": [],
}

# Semantic type per rendered column, for the fmt_* correctness check. `name`
# is the stub (never fmt_*-formatted), so it has no entry here.
SEMANTIC_TYPES = {
    "size": "number",
}

# ---- Data prep -----------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "islands.csv")

# Biggest first -- see "Sort" in the module docstring above.
top = df.sort_values("size", ascending=False).reset_index(drop=True)

# ---- Color domain ----------------------------------------------------------
# Single sequential measure, linear, ceiling = the actual data max. Floor is
# a NEGATIVE 20%-of-max pre-tint buffer, NOT 0 and NOT top["size"].min() --
# see "Color" in the module docstring for why a zero/sample-minimum floor
# would make the smallest row(s) look uncolored rather than genuinely small.
size_hi = float(top["size"].max())
size_lo = -0.2 * size_hi

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="name")
    .tab_header(
        title="Islands of the World, by Size",
        subtitle="Land area in thousands of square miles, continents and smaller islands together",
    )
    .tab_stubhead(label="Landmass")
    .cols_label(size="Size (thousand sq. mi.)")
    .fmt_number(columns=["size"], decimals=0, use_seps=True)
    # Big Color (the only one -- there is only one numeric column): size is
    # a plain magnitude and the entire point of the table, sequential
    # Blues, explicit domain=[min, max] over the real data.
    .data_color(
        columns=["size"],
        palette="Blues",
        domain=[size_lo, size_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Columns sized to their own content (+ a small buffer), not left to
    # auto-stretch -- author-directed, to kill excess whitespace.
    .cols_width(cases={"name": "180px", "size": "150px"})
    # Column-label band -- DEEP navy (#08306B, sampled from the dark end of
    # the size Blues heatmap, matching the gtcars tables' header treatment
    # for consistency across all tables), bold, white text.
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        column_labels_border_bottom_style="solid",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
        # Tighter padding throughout -- less whitespace per cell, by author
        # direction.
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint -- the quieter washed navy, one tier down from the band, so
    # the stub stays subtler than the louder column-label band above it.
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["size"])
    .tab_source_note(
        source_note=html(
            "Ordered largest to smallest by land area; “landmass” includes continents "
            "(Asia, Africa, ...) alongside literal islands in one ranking."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: R's built-in <code>islands</code> dataset — land area, in thousands of "
            "square miles, for landmasses exceeding 10,000 square miles."
        )
    )
)

gt.gtsave(str(_HERE / "islands_sizes.png"), zoom=2.0, expand=8)
