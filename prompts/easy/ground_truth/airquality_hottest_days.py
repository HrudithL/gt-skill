"""Ground truth for prompts/easy/airquality_hottest_days.json.

Data: data/airquality.csv  (153 daily readings from New York City,
      May-September 1973; columns Ozone, Solar_R, Wind, Temp, Month, Day).
Story: The 10 hottest days on record in that summer, with each day's
       ozone reading and wind speed — the "peak of summer" snapshot.

Design decisions:

- Row scope: the prompt names "the 10 hottest days" explicitly, so
  REQUIRED_INSTRUCTIONS pins row_count=10.
- Stub: a constructed date label "Aug 28" (from Month + Day). No single
  raw column identifies a day uniquely; the composite label is the row
  identity. Confirmed unique across the top 10.
- Colored measure: Temp only — the "hottest" ranking criterion. High
  temperature has a real "more extreme" reading in an air-quality
  context, so sequential REDS (matches the warning-hued heatmap
  pattern in airquality_monthly_summary.py's ozone treatment).
- Ozone and Wind stay plain text — secondary readings the prompt names
  but doesn't make the hero of.
- Sort: descending by Temp.
- Missing values: two of the ten hottest days have no ozone reading
  (June 11 and June 12, 1973). Handled via `sub_missing` with the
  em-dash, matching every other table in this project.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  decoupled from Temp's own Reds heatmap hue.

`autocolor_text=True` on the `data_color()` call is spelled out
explicitly even though it's great_tables' own default, for the same
self-documenting-intent reason `na_color`/`truncate` are always spelled
out here.
"""
from pathlib import Path

import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "Temp": ["temp", "temperature", "temperature (°f)", "temp (°f)", "max temp", "high"],
    "Ozone": ["ozone", "ozone (ppb)", "ozone level"],
    "Wind": ["wind", "wind speed", "wind (mph)", "wind speed (mph)"],
}

REQUIRED_INSTRUCTIONS = {
    "row_count": 10,
}

CANONICAL_MEASURES = {
    "colored": ["Temp"],
    "hero_uncolored": [],
}

SEMANTIC_TYPES = {
    "Temp": "integer",
    "Ozone": "number",
    "Wind": "number",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "airquality.csv")

MONTH_ABBR = {5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep"}
df["date_label"] = df["Month"].map(MONTH_ABBR) + " " + df["Day"].astype(str)

top = (
    df.nlargest(10, "Temp")
    .loc[:, ["date_label", "Temp", "Ozone", "Wind"]]
    .reset_index(drop=True)
)
top["Temp"] = top["Temp"].astype(int)

# ---- Color domain ----------------------------------------------------------
temp_lo = float(top["Temp"].min())
temp_hi = float(top["Temp"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="date_label")
    .tab_header(
        title="The 10 Hottest Days of New York's 1973 Summer",
        subtitle="Daily maximum temperature, with ozone level and wind speed for each of the ten hottest days on record",
    )
    .tab_stubhead(label="Date")
    .cols_label(
        Temp="Max Temp (°F)",
        Ozone="Ozone (ppb)",
        Wind="Wind (mph)",
    )
    .fmt_integer(columns=["Temp"])
    .fmt_number(columns=["Ozone", "Wind"], decimals=1)
    .sub_missing(columns=["Temp", "Ozone", "Wind"], missing_text="—")
    # Big Color 1/1: Temp -- the "hottest" ranking criterion, plain
    # positive magnitude with a "more extreme" reading in an air-quality
    # context, so sequential REDS (matches the warning-hued pattern
    # airquality_monthly_summary.py uses for ozone).
    .data_color(
        columns=["Temp"],
        palette="Reds",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Ozone / Wind stay plain -- secondary readings the prompt names but
    # doesn't make the hero of.
    .cols_width(cases={
        "date_label": "110px", "Temp": "150px", "Ozone": "140px", "Wind": "140px",
    })
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    .cols_align(align="right", columns=["Temp", "Ozone", "Wind"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Late August produced a cluster of the summer's peak heat — four of the ten hottest "
            "days fell in a single week (Aug 28-31), with the season's hottest day (97 °F) landing "
            "on August 28."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>airquality</code> dataset — New York City daily air-quality readings, "
            "May-September 1973 (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "airquality_hottest_days.png"), zoom=2.0, expand=8)
