"""Ground truth for prompts/medium/gibraltar_weekly_summary.json.

Data: data/gibraltar.csv  (Gibraltar hourly-ish weather observations for
      the month of May 2023; ~1,400 rows total, with `date`, `time`,
      `temp` (°C), `humidity` (fraction), `wind_speed` (mph — the
      dataset's units), and `condition` (short weather label).
Story: A 7-row daily digest for the week of May 8-14, 2023, with average
       temperature, average humidity, peak wind speed, and the day's
       dominant weather condition.

Design decisions:

- Row scope: the prompt names a 7-day window explicitly (May 8-14),
  which produces exactly 7 rows. REQUIRED_INSTRUCTIONS pins row_count=7.
- Stub: a constructed "Mon May 8" style date label — matches how a
  weather digest reads (weekday + short date).
- Colored measures (two):
  * `avg_temp`: sequential Blues — plain neutral magnitude (mild May
    temperatures, 19-23 °C, don't warrant Reds "warning" hue).
  * `avg_humidity`: sequential Blues would collide (same family) — so
    use sequential BUGN (Blue-Green) sequential to pair with a "moisture"
    reading, but keep hue collision avoidance. Actually the simplest
    house-consistent choice: temp Blues + humidity plain, since only ONE
    of the two magnitudes here is a genuine hero and pairing two Blues
    would collide. Instead I'm coloring temp only (Blues), leaving
    humidity/peak_wind as hero_uncolored plain text — matches the
    house "color what the request is actually about" restraint rule and
    the `airquality_monthly_summary.py` convention (where wind was
    hero_uncolored beside two colored magnitudes).
  Final: colored=[avg_temp], hero_uncolored=[avg_humidity, peak_wind].
- Condition stays plain text — categorical, no good/bad polarity.
- Sort: chronological (May 8 -> May 14), the natural reading for a
  weekly digest.
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub.

`autocolor_text=True` on the `data_color()` call is spelled out
explicitly even though it's great_tables' own default, for the same
self-documenting-intent reason `na_color`/`truncate` are always spelled
out here.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from great_tables import GT, html, loc, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
LABEL_SYNONYMS = {
    "avg_temp": ["temperature", "avg temp", "average temperature", "temp", "avg. temp"],
    "avg_humidity": ["humidity", "avg humidity", "average humidity", "avg. humidity"],
    "peak_wind": ["wind", "peak wind", "max wind", "peak wind speed", "wind speed"],
    "condition": ["condition", "weather", "dominant condition", "sky", "conditions"],
}

# 7 days is a direct consequence of the "May 8 through May 14" window.
REQUIRED_INSTRUCTIONS = {
    "row_count": 7,
}

CANONICAL_MEASURES = {
    "colored": ["avg_temp"],
    "hero_uncolored": ["avg_humidity", "peak_wind"],
}

SEMANTIC_TYPES = {
    "avg_temp": "number",
    "avg_humidity": "percent",
    "peak_wind": "number",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "gibraltar.csv")
df["date"] = pd.to_datetime(df["date"])

mask = (df["date"] >= "2023-05-08") & (df["date"] <= "2023-05-14")
week = df.loc[mask].copy()


def _mode_str(s):
    m = s.mode()
    return m.iat[0] if not m.empty else None


by_day = (
    week.groupby(week["date"].dt.date)
        .agg(
            avg_temp=("temp", "mean"),
            avg_humidity=("humidity", "mean"),
            peak_wind=("wind_speed", "max"),
            condition=("condition", _mode_str),
        )
        .reset_index()
)
by_day["date"] = pd.to_datetime(by_day["date"])
by_day["date_label"] = by_day["date"].dt.strftime("%a May %-d")
by_day = by_day.sort_values("date").reset_index(drop=True)
by_day = by_day[["date_label", "avg_temp", "avg_humidity", "peak_wind", "condition"]]

# ---- Color domain ----------------------------------------------------------
temp_lo = float(np.nanmin(by_day["avg_temp"].to_numpy()))
temp_hi = float(np.nanmax(by_day["avg_temp"].to_numpy()))

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_day, rowname_col="date_label")
    .tab_header(
        title="Gibraltar Weather, Week of May 8-14, 2023",
        subtitle="Daily average temperature and humidity, the day's peak wind speed, and the dominant weather condition",
    )
    .tab_stubhead(label="Day")
    .cols_label(
        avg_temp="Avg. Temp (°C)",
        avg_humidity="Avg. Humidity",
        peak_wind="Peak Wind (mph)",
        condition="Condition",
    )
    .fmt_number(columns=["avg_temp", "peak_wind"], decimals=1)
    .fmt_percent(columns=["avg_humidity"], decimals=0)
    .sub_missing(
        columns=["avg_temp", "avg_humidity", "peak_wind", "condition"],
        missing_text="—",
    )
    # Big Color 1/1: avg_temp -- plain neutral magnitude, sequential
    # Blues. Humidity and wind stay plain (hero_uncolored).
    .data_color(
        columns=["avg_temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "date_label": "130px", "avg_temp": "130px",
        "avg_humidity": "130px", "peak_wind": "140px", "condition": "130px",
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
    .cols_align(align="right", columns=["avg_temp", "avg_humidity", "peak_wind"])
    .cols_align(align="left", columns=["condition"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "A quiet spring week under a &ldquo;Fair&rdquo; sky every single day; temperatures held "
            "steady in the low 20s °C while humidity swung from 62% to 83% as onshore breezes "
            "came and went."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: Gibraltar weather-station observations, May 2023 — the <code>gibraltar</code> "
            "dataset (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "gibraltar_weekly_summary.png"), zoom=2.0, expand=8)
