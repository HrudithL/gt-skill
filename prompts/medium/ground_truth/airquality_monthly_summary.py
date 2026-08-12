"""Ground truth for prompts/medium/airquality_monthly_summary.json.

Data: data/airquality.csv  (153 daily readings, New York, May-September 1973;
      columns Ozone, Solar_R, Wind, Temp, Month, Day)
Story: "Comparing ... for each month" is an AGGREGATION ask, not a daily
       listing -- one row per month (5 rows: May-September), each showing
       that month's average temperature, wind speed, and ozone level.

Two colored measures (the ceiling), one plain-uncolored: ozone is the
dataset's namesake and the one measure with a real "more is worse"
air-quality reading, so it gets the "warning" Reds sequential heatmap;
temperature is a plain neutral magnitude, so it gets the "neutral" Blues
sequential heatmap; wind speed -- no defensible "good/bad" direction and no
special narrative role here -- stays plain, uncolored text (the third
measure the ceiling forces out of a fill; no bold, matching the same plain
treatment gtcars_hp_price.py gives horsepower).

Column order, by author direction: ozone LEADS (Ozone, Temp, Wind), not the
prompt's own listed word order ("temperature, wind speed, and ozone") --
ozone is the primary/hero measure and the dataset's namesake, so it gets
top billing regardless of how the prompt happened to list the three.

Header/stub branding, by author direction: DEEP navy (#08306B), matching
every other table in this project -- decoupled from ozone's own Reds
heatmap. The per-measure heatmap palette (Reds for ozone, Blues for temp)
is a separate decision from the table's overall branding color, which
stays the same blue family across every table for consistency.

Ozone is missing on 37 of 153 days, most heavily in June (21 of 30 days
missing -- only 9 valid readings). `.mean()` skips NaN by default, so every
month still gets a real average, but June's average rests on a much
thinner sample than the other four months; that caveat is called out in
the source note rather than silently averaged over.

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
# label just has to name the right concept. "month" is included for
# documentation even though it's rendered via the stub (not a `cols_label`
# target), so the comparator's label-concept check never scores it.
LABEL_SYNONYMS = {
    "month": ["month"],
    "avg_temp": ["temperature", "temp", "avg temp", "average temperature"],
    "avg_wind": ["wind", "wind speed", "avg wind", "average wind"],
    "avg_ozone": ["ozone", "avg ozone", "average ozone", "ozone level"],
}

# Only present when the PROMPT TEXT explicitly demands something structural.
# The prompt says "for each month" -- since the data contains exactly 5
# distinct Month values (5-9, May-September), a correct group-by-month
# aggregation MUST produce exactly 5 rows as a direct mathematical
# consequence of doing what's asked, not a subjective pick. No explicit
# grouping-by-something-else or sort order is demanded (month IS the row
# grain; there's no separate category to group by), so those keys are
# omitted rather than inferred.
REQUIRED_INSTRUCTIONS = {
    "row_count": 5,
}

# Keyword-presence check for the caption/subtitle overlap rule. The
# caption's unique insight is the missing-ozone/thin-June-sample caveat --
# the subtitle only describes WHICH columns are shown, never that caveat,
# so the same two phrases serve as both "must appear in caption" and "must
# not leak into subtitle" (verified against the actual rendered text below).
CAPTION_KEYWORDS = {
    "caption_should_mention": ["missing", "recorded value"],
    "subtitle_should_not_duplicate": ["missing", "recorded value"],
}

# Underlying SOURCE/derived column(s) that are the canonical colored
# measure(s), used for value-based matching -- NOT the rendered label.
CANONICAL_MEASURES = {
    "colored": ["avg_temp", "avg_ozone"],
    "hero_uncolored": ["avg_wind"],
}

# Semantic type per rendered column, for the fmt_* correctness check. All
# three measures are plain averaged magnitudes (degrees / mph / ppb), none
# of them percentages or currency.
SEMANTIC_TYPES = {
    "avg_temp": "number",
    "avg_wind": "number",
    "avg_ozone": "number",
}

# ---- Data prep -----------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "airquality.csv")

MONTH_NAMES = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

# "Comparing ... for each month" -> one row per month, each showing that
# month's AVERAGE temperature/wind/ozone -- a groupby-mean aggregation, not
# a daily listing. `.mean()` skips NaN by default (Ozone has 37 missing of
# 153 rows; Wind/Temp have none), so every month still gets a real average
# from whatever days actually have a recorded value.
monthly = (
    df.groupby("Month")[["Temp", "Wind", "Ozone"]]
      .mean()
      .rename(columns={"Temp": "avg_temp", "Wind": "avg_wind", "Ozone": "avg_ozone"})
      .reset_index()
)
monthly["month"] = monthly["Month"].map(MONTH_NAMES)
# Column order: ozone LEADS (the primary/hero measure, and the dataset's
# namesake), then temp, then wind -- author-directed, not the prompt's own
# listed word order ("temperature, wind speed, and ozone").
monthly = monthly[["month", "avg_ozone", "avg_temp", "avg_wind"]].reset_index(drop=True)

# ---- Color domains ---------------------------------------------------------
# Each measure's domain is the full range of its own 5 monthly averages
# (data-driven, full-range -- not symmetric: both measures are plain
# positive magnitudes, never signed).
temp_lo = float(np.nanmin(monthly["avg_temp"].to_numpy()))
temp_hi = float(np.nanmax(monthly["avg_temp"].to_numpy()))
ozone_lo = float(np.nanmin(monthly["avg_ozone"].to_numpy()))
ozone_hi = float(np.nanmax(monthly["avg_ozone"].to_numpy()))

# ---- Table -----------------------------------------------------------------
gt = (
    GT(monthly, rowname_col="month")
    .tab_header(
        title="Monthly Air Quality in New York, 1973",
        subtitle="Average temperature, wind speed, and ozone level for each month, May through September",
    )
    .tab_stubhead(label="Month")
    .cols_label(
        avg_temp="Avg. Temperature (°F)",
        avg_wind="Avg. Wind Speed (mph)",
        avg_ozone="Avg. Ozone (ppb)",
    )
    .fmt_number(columns=["avg_temp", "avg_wind", "avg_ozone"], decimals=1)
    # Big Color 1/2: ozone, sequential Reds -- the dataset's namesake
    # measure and the one with a genuine "higher = worse air quality"
    # reading, so warning-hued rather than neutral. This is the per-measure
    # heatmap palette, independent of the header/stub branding color below.
    .data_color(
        columns=["avg_ozone"],
        palette="Reds",
        domain=[ozone_lo, ozone_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: temperature, sequential Blues -- a plain neutral
    # magnitude, no "good/bad" direction.
    .data_color(
        columns=["avg_temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Wind stays plain text -- no bold, no fill -- by author direction,
    # matching the same choice made for gtcars_hp_price's horsepower column.
    # Columns sized to their own content (+ a small buffer), not left to
    # auto-stretch -- author-directed.
    .cols_width(cases={
        "month": "110px", "avg_ozone": "130px", "avg_temp": "150px", "avg_wind": "140px",
    })
    # Column-label band -- DEEP navy (#08306B), bold, white text: the SAME
    # blue-family header/stub branding as every other table in this project,
    # by author direction, decoupled from which hue each measure's OWN
    # heatmap happens to use (ozone keeps Reds, temp keeps Blues above).
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
    # Stub tint -- washed navy, matching every other table's stub treatment.
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["avg_temp", "avg_wind", "avg_ozone"])
    # Row striping: added by author direction even at 5 rows, for
    # consistency with every other table (below the usual >=10-row floor,
    # but explicitly requested here anyway).
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # No spanner: month IS the row grain and there's no second column-group
    # dimension beyond the three measures to disambiguate.
    .tab_source_note(
        source_note=html(
            "Ozone readings are missing on 37 of 153 days, most heavily in June, so monthly "
            "averages are computed only from days with a recorded value."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: New York air quality measurements, May–September 1973 "
            "(base R <code>airquality</code> dataset, distributed here as "
            "<code>data/airquality.csv</code>)."
        )
    )
)

gt.gtsave(str(_HERE / "airquality_monthly_summary.png"), zoom=2.0, expand=8)
