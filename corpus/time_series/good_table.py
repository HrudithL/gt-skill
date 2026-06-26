"""Time-series archetype — good example.

Source: ../../data/airquality.csv  (NYC daily air quality, May–Sep 1973)
Story:  Monthly summary of New York City air quality across the summer
        of 1973 — what an environmental reporter would lead a recap
        with: ozone (the regulated pollutant), temperature (the driver),
        and a sparkline of daily ozone within each month so the eye can
        see the within-month volatility, not just the mean.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))
import gtskill_chrome  # noqa: F401

import pandas as pd
from great_tables import GT, html

# ---- Data prep ---------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "airquality.csv")

# Map numeric Month (5..9) to human labels. The raw integer column would force
# the reader to translate "Month=7" → "July" mentally for every row.
month_name = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

# Per-month aggregates. We compute the mean for the headline numbers and pack
# the full daily Ozone series into a list cell that fmt_nanoplot will render
# as an inline sparkline. fmt_nanoplot needs a list-typed cell, so the column
# is built explicitly with .apply rather than .agg.
monthly = df.groupby("Month").agg(
    ozone_mean=("Ozone", "mean"),
    temp_mean=("Temp", "mean"),
    wind_mean=("Wind", "mean"),
    solar_mean=("Solar_R", "mean"),
).reset_index()

# Build the ozone sparkline series per month. Drop NaNs because fmt_nanoplot
# refuses missing values; the underlying CSV has gaps in Ozone.
sparks = (
    df.dropna(subset=["Ozone"])
      .groupby("Month")["Ozone"]
      .apply(lambda s: " ".join(f"{v:.0f}" for v in s.tolist()))
      .reset_index()
      .rename(columns={"Ozone": "ozone_trend"})
)
monthly = monthly.merge(sparks, on="Month")

# Month-over-month delta on Ozone — directional signal that complements the
# sparkline (sparkline shows shape, delta shows change vs prior month).
monthly["ozone_delta"] = monthly["ozone_mean"].diff()

monthly["month_label"] = monthly["Month"].map(month_name)
monthly = monthly[[
    "month_label", "ozone_mean", "ozone_delta", "ozone_trend",
    "temp_mean", "wind_mean", "solar_mean",
]]

# ---- Table -------------------------------------------------------------------
gt = (
    GT(monthly)
    .tab_header(
        title="NYC Air Quality — Summer 1973",
        subtitle="Monthly means and within-month ozone trend",
    )
    # Spanner labels match the underlying variables, so the reader can map
    # the four-column block under "Pollutant & atmosphere" to the data
    # without scanning each header.
    .tab_spanner(label="Ozone (ppb)", columns=["ozone_mean", "ozone_delta", "ozone_trend"])
    .tab_spanner(label="Conditions", columns=["temp_mean", "wind_mean", "solar_mean"])
    .cols_label(
        month_label="Month",
        ozone_mean="Mean",
        ozone_delta=html("&Delta; vs prev"),
        ozone_trend="Daily trend",
        temp_mean=html("Temp (&deg;F)"),
        wind_mean="Wind (mph)",
        solar_mean=html("Solar (W/m&sup2;)"),
    )
    # Means rounded to 1 decimal — half a ppb is below the measurement
    # precision of the underlying instrument, so further decimals would be
    # spurious precision.
    .fmt_number(columns=["ozone_mean", "temp_mean", "wind_mean", "solar_mean"], decimals=1)
    # Delta with force_sign — same rationale as the financial table: the
    # leading + or − is what tells the reader "month was worse/better than
    # the prior one" without arithmetic.
    .fmt_number(columns=["ozone_delta"], decimals=1, force_sign=True)
    # Sparkline: fmt_nanoplot draws a tiny inline plot of the daily Ozone
    # series for that month. Chose this over a separate chart because the
    # row IS the time-series unit; the trend belongs next to its summary.
    .fmt_nanoplot(columns="ozone_trend", plot_type="line")
    .sub_missing(columns=["ozone_delta"], missing_text="—")
    .cols_align(align="left", columns=["month_label"])
    .tab_source_note(
        source_note="Source: New York State Department of Conservation, daily measurements May–September 1973."
    )
)

gt.gtsave(str(_HERE / "good_table.png"), zoom=3.0)
