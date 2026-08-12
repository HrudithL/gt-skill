"""Ground truth for prompts/hard/towny_growth_trends.json.

Data: data/towny.csv  (414 Ontario municipalities; density and growth
      across five Census windows from 1996 to 2021)
Story: The 15 towns that grew the most over the full 25-year span, with
       their density at every Census year and the percent change between
       each consecutive pair of Censuses.

Two colored measures (the ceiling): density is a neutral magnitude, so it
gets the sequential Blues gradient; the five inter-Census changes are
signed, so they get the RdYlGn diverging fill. "Fastest-growing" is
ambiguous (whole-period growth vs. average of the five windows) — the
canonical definition (whole-period growth) is picked once and stated in
the source note so the ranking is reproducible.

`autocolor_text=True` on both `data_color()` calls: written explicitly
even though it's great_tables' own default (`autocolor_text: bool = True`
in the installed 0.22.0's own signature -- omitting it renders
identically). Spelled out for the same self-documenting reason
`na_color`/`truncate` are always spelled out here too, even though THEIR
defaults also already match -- not because any of the three was ever
actually wrong when omitted.
"""
from pathlib import Path

import numpy as np
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
# label just has to name the right concept. Keys are the SOURCE CSV/derived
# column name(s) the label is standing in for.
LABEL_SYNONYMS = {
    "rank": ["rank", "#", "position"],
    "total_growth_pct": [
        "total growth", "growth 1996", "growth 1996-2021", "1996-2021",
        "total growth 1996-2021", "population growth",
    ],
    "density_1996": ["1996", "density 1996"],
    "density_2001": ["2001", "density 2001"],
    "density_2006": ["2006", "density 2006"],
    "density_2011": ["2011", "density 2011"],
    "density_2016": ["2016", "density 2016"],
    "density_2021": ["2021", "density 2021"],
    "pop_change_1996_2001_pct": ["1996-2001", "1996–2001"],
    "pop_change_2001_2006_pct": ["2001-2006", "2001–2006"],
    "pop_change_2006_2011_pct": ["2006-2011", "2006–2011"],
    "pop_change_2011_2016_pct": ["2011-2016", "2011–2016"],
    "pop_change_2016_2021_pct": ["2016-2021", "2016–2021"],
}

# Only present when the PROMPT TEXT explicitly demands something structural.
# Absence of a key means "not required" -- never inferred from prose at eval
# time, always decided here by whoever wrote this ground truth. The prompt
# says "top 15 fastest-growing" -- an explicit row count -- but does not
# explicitly demand grouping or a specific rendered sort order, so only
# row_count is set.
REQUIRED_INSTRUCTIONS = {
    "row_count": 15,
}

# Keyword-presence check for the caption/subtitle overlap rule (see
# CONSISTENCY_DEV.md Step 6). caption_should_mention are terms the footer's
# takeaway sentence must include; subtitle_should_not_duplicate are terms the
# subtitle must NOT lean on (they belong to the caption's insight, not the
# subtitle's organization-description). Verified against the actual rendered
# text below (case-insensitive substring): the subtitle legitimately says
# "percent change" / "consecutive" as organization-description (which
# columns exist), so those generic words can't be the caption-exclusivity
# check — the caption's actual unique insight is the "not the average"
# disambiguation, which the subtitle never states.
CAPTION_KEYWORDS = {
    "caption_should_mention": ["fastest-growing", "1996", "not the average"],
    "subtitle_should_not_duplicate": [
        "not the average", "highest percent change in total population",
    ],
}

# Underlying SOURCE CSV column(s) that are the canonical colored measure(s),
# used for value-based matching -- NOT the rendered column name/label.
CANONICAL_MEASURES = {
    "colored": [
        "density_1996", "density_2001", "density_2006",
        "density_2011", "density_2016", "density_2021",
        "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ],
    "hero_uncolored": ["rank", "total_growth_pct"],
}

# Semantic type per rendered column, for the fmt_* correctness check.
SEMANTIC_TYPES = {
    "rank": "number",
    "total_growth_pct": "percent",
    "density_1996": "number", "density_2001": "number", "density_2006": "number",
    "density_2011": "number", "density_2016": "number", "density_2021": "number",
    "pop_change_1996_2001_pct": "percent",
    "pop_change_2001_2006_pct": "percent",
    "pop_change_2006_2011_pct": "percent",
    "pop_change_2011_2016_pct": "percent",
    "pop_change_2016_2021_pct": "percent",
}

# ---- Data prep -----------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "towny.csv")

density_cols = [
    "density_1996", "density_2001", "density_2006",
    "density_2011", "density_2016", "density_2021",
]
change_cols = [
    "pop_change_1996_2001_pct", "pop_change_2001_2006_pct",
    "pop_change_2006_2011_pct", "pop_change_2011_2016_pct",
    "pop_change_2016_2021_pct",
]

# Canonical "fastest-growing" (F-canonical-metric): whole-period growth,
# population_2021 vs. population_1996 — not the mean of the five window
# percentages, which would rank differently. Stated in the source note
# below so the same prompt always yields the same 15 towns.
df["total_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# A row must have a defined change for all five windows to be usable for
# "the percentage changes between each period" — one municipality
# (Cockburn Island, population 2 -> 16) has near-zero population in most
# Census years, so four of its five window changes are undefined and its
# single defined "+700%" is a small-denominator artifact, not a real growth
# trend. Excluding rows that can't answer the full comparison also drops
# every other municipality whose pre-amalgamation history is missing.
top = (
    df.dropna(subset=change_cols)
      .nlargest(15, "total_growth_pct")
      .loc[:, ["name", "total_growth_pct"] + density_cols + change_cols]
      .reset_index(drop=True)
)
top.insert(1, "rank", range(1, len(top) + 1))

# ---- Color domains ---------------------------------------------------------
# Density: one shared domain across all six Census-year columns (neutral
# magnitude -> Blues, per the palette lookup).
dens_lo = float(np.nanmin(top[density_cols].to_numpy()))
dens_hi = float(np.nanmax(top[density_cols].to_numpy()))

# Growth: signed measure -> diverging, symmetric about 0 so a +40% window
# and a -40% window render at equal saturation regardless of which sign
# happens to have the larger magnitude in this slice of data.
chg_lo = float(np.nanmin(top[change_cols].to_numpy()))
chg_hi = float(np.nanmax(top[change_cols].to_numpy()))
chg_m = max(abs(chg_lo), abs(chg_hi))

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="name")
    .tab_header(
        title="Ontario's Fastest-Growing Towns, 1996–2021",
        subtitle="Density at each Census year and the percent change between consecutive Censuses, "
                  "ranked by total population growth over the full period",
    )
    .tab_stubhead(label="Town")
    .tab_spanner(label="Population density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Inter-Census growth", columns=change_cols)
    .cols_label(
        rank="#",
        total_growth_pct=html("Total growth<br>1996–2021"),
        density_1996="1996", density_2001="2001", density_2006="2006",
        density_2011="2011", density_2016="2016", density_2021="2021",
        pop_change_1996_2001_pct="1996–2001",
        pop_change_2001_2006_pct="2001–2006",
        pop_change_2006_2011_pct="2006–2011",
        pop_change_2011_2016_pct="2011–2016",
        pop_change_2016_2021_pct="2016–2021",
    )
    .fmt_integer(columns=["rank"])
    .fmt_percent(columns=["total_growth_pct"], decimals=1, force_sign=True)
    .fmt_number(columns=density_cols, decimals=1)
    .fmt_percent(columns=change_cols, decimals=1, force_sign=True)
    .sub_missing(columns=["total_growth_pct"] + density_cols + change_cols, missing_text="—")
    # Big Color 1/2: density, sequential Blues, one domain shared by all six columns.
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[dens_lo, dens_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: inter-Census growth, diverging RdYlGn; positive = good
    # (more residents), so no reverse. Symmetric domain keeps 0% at the
    # palette midpoint no matter which sign is larger in this slice.
    .data_color(
        columns=change_cols,
        palette="RdYlGn",
        domain=[-chg_m, chg_m],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Rank / Total Growth % stay plain text -- no bold -- by author
    # direction, matching the same plain treatment used for gtcars_hp_price's
    # horsepower and airquality's wind speed.
    # Columns sized to their own content (+ a small buffer), not left to
    # auto-stretch -- author-directed.
    .cols_width(cases={
        "name": "190px", "rank": "50px", "total_growth_pct": "100px",
        **{c: "75px" for c in density_cols},
        **{c: "95px" for c in change_cols},
    })
    # Column-label band -- DEEP navy (#08306B), bold, white text: the same
    # header/stub branding used across every table in this project, by
    # author direction, decoupled from this table's own Blues/RdYlGn
    # heatmap hues.
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
        column_labels_padding_horizontal="6px",
        data_row_padding="5px",
        data_row_padding_horizontal="6px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint -- washed navy, matching every other table's stub treatment.
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping: added by author direction for cross-table consistency,
    # even though 11 of 13 body columns are already heatmapped -- the stripe
    # still shows through on Rank and Total Growth %, the two plain columns.
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Column-group dividers at each spanner boundary only.
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.body(columns="total_growth_pct"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.column_labels(columns="total_growth_pct"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.body(columns="density_2021"))
    .tab_style(style=style.borders(sides="right", color="#D0D0D0", weight="1px"), locations=loc.column_labels(columns="density_2021"))
    .cols_align(align="right", columns=["rank", "total_growth_pct"] + density_cols + change_cols)
    .tab_source_note(
        source_note=html(
            "“Fastest-growing” = highest percent change in total population from 1996 to 2021, "
            "not the average of the five inter-Census windows."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: Statistics Canada Census of Population, 1996–2021, via the "
            "<code>towny</code> dataset (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "towny_growth_trends.png"), zoom=2.0, expand=8)
