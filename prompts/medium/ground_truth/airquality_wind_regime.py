"""Ground truth for prompts/medium/airquality_wind_regime.json.

Data: data/airquality.csv  (153 daily readings, New York, May-September 1973;
      columns Ozone, Solar_R, Wind, Temp, Month, Day).
Story: Compare summer air-quality conditions across three wind regimes.
       "Calm", "Moderate", and "Windy" days are the bottom, middle, and
       top TERCILES of the Wind column — for each regime, show the day
       count and the average ozone, temperature, and solar radiation.

Design decisions:

- Regime definition: the prompt names three regimes ("calm, moderate,
  windy") but doesn't specify the cutoffs. Terciles by the Wind column
  (pd.qcut, q=3) are the transparent, reproducible default:
  Calm = bottom third of wind speeds, Moderate = middle, Windy = top.
  Stated explicitly in the analytical caption note.
- Row scope: exactly 3 rows as a direct mathematical consequence of
  "three wind regimes" + tercile binning; REQUIRED_INSTRUCTIONS
  therefore pins row_count=3.
- Stub: `regime` label (Calm / Moderate / Windy).
- Colored measures (two, matching airquality_monthly_summary.py's own
  convention on this dataset):
  * `avg_ozone`: sequential Reds — ozone is the dataset's namesake and
    the one measure with a real "more = worse air quality" reading.
  * `avg_temp`: sequential Blues — plain neutral magnitude.
  `avg_solar` and `n_days` stay plain (secondary detail; no defensible
  good/bad direction for solar, and n_days is a bin count).
- Sort: regime order Calm -> Moderate -> Windy (wind-speed ascending), a
  natural ordering that mirrors "as wind picks up, ozone drops".
- Header/stub branding: DEEP navy (#08306B) band + washed navy stub —
  decoupled from the Reds/Blues heatmap hues.

`autocolor_text=True` on both `data_color()` calls is spelled out
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
    "regime": ["regime", "wind regime", "wind category", "category"],
    "n_days": ["days", "day count", "n days", "number of days", "count"],
    "avg_ozone": ["ozone", "avg ozone", "average ozone", "ozone level", "avg. ozone"],
    "avg_temp": ["temperature", "temp", "avg temperature", "average temperature", "avg. temp"],
    "avg_solar": ["solar", "solar radiation", "avg solar", "average solar", "avg. solar"],
}

# 3 rows is a direct consequence of the prompt's "three wind regimes".
REQUIRED_INSTRUCTIONS = {
    "row_count": 3,
}

CANONICAL_MEASURES = {
    "colored": ["avg_ozone", "avg_temp"],
    "hero_uncolored": ["avg_solar"],
}

SEMANTIC_TYPES = {
    "n_days": "integer",
    "avg_ozone": "number",
    "avg_temp": "number",
    "avg_solar": "number",
}

# ---- Data prep -------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "airquality.csv")

df["regime"] = pd.qcut(df["Wind"], q=3, labels=["Calm", "Moderate", "Windy"])

by_regime = (
    df.groupby("regime", observed=True)
      .agg(
          n_days=("Wind", "size"),
          avg_ozone=("Ozone", "mean"),
          avg_temp=("Temp", "mean"),
          avg_solar=("Solar_R", "mean"),
      )
      .reset_index()
)
by_regime["regime"] = by_regime["regime"].astype(str)

# ---- Color domains ---------------------------------------------------------
ozone_lo = float(np.nanmin(by_regime["avg_ozone"].to_numpy()))
ozone_hi = float(np.nanmax(by_regime["avg_ozone"].to_numpy()))
temp_lo = float(np.nanmin(by_regime["avg_temp"].to_numpy()))
temp_hi = float(np.nanmax(by_regime["avg_temp"].to_numpy()))

# ---- Table -----------------------------------------------------------------
gt = (
    GT(by_regime, rowname_col="regime")
    .tab_header(
        title="New York Summer Air Quality by Wind Regime",
        subtitle="Daily averages for ozone, temperature, and solar radiation, grouped into calm, moderate, and windy days by tercile of wind speed",
    )
    .tab_stubhead(label="Wind Regime")
    .cols_label(
        n_days="Days",
        avg_ozone="Avg. Ozone (ppb)",
        avg_temp="Avg. Temp (°F)",
        avg_solar="Avg. Solar (Langleys)",
    )
    .fmt_integer(columns=["n_days"])
    .fmt_number(columns=["avg_ozone", "avg_temp", "avg_solar"], decimals=1)
    .sub_missing(columns=["n_days", "avg_ozone", "avg_temp", "avg_solar"], missing_text="—")
    # Big Color 1/2: ozone -- warning-hued Reds, the "more = worse" story.
    .data_color(
        columns=["avg_ozone"],
        palette="Reds",
        domain=[ozone_lo, ozone_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Big Color 2/2: temp -- plain neutral magnitude, sequential Blues.
    .data_color(
        columns=["avg_temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_width(cases={
        "regime": "130px", "n_days": "80px",
        "avg_ozone": "140px", "avg_temp": "130px", "avg_solar": "160px",
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
    .cols_align(align="right", columns=["n_days", "avg_ozone", "avg_temp", "avg_solar"])
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    .tab_source_note(
        source_note=html(
            "Wind regimes are the bottom, middle, and top TERCILES of daily wind-speed readings "
            "(pd.qcut, q=3). Ozone plummets nearly threefold as wind picks up — 66 ppb on calm "
            "days versus 23 ppb on the windiest — while temperature falls a full 10 °F over the "
            "same range."
        )
    )
    .tab_source_note(
        source_note=html(
            "Source: <code>airquality</code> dataset — New York City daily air-quality readings, "
            "May-September 1973 (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "airquality_wind_regime.png"), zoom=2.0, expand=8)
