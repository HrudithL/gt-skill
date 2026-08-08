import pandas as pd
import numpy as np
from great_tables import GT, html, style, loc
from gt_consistency import PALETTE, band, frame, finalize, stripe, stub_tint, heatmap

df = pd.read_csv("airquality.csv")

# Data cleaning: coerce columns to numeric, handle missing values
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")

# Map numeric Month codes to human labels
month_name = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}

# Aggregate to monthly means
monthly = df.groupby("Month").agg(
    temp_mean=("Temp", "mean"),
    wind_mean=("Wind", "mean"),
    ozone_mean=("Ozone", "mean"),
).reset_index()

monthly["month_label"] = monthly["Month"].map(month_name)
monthly = monthly[["month_label", "temp_mean", "wind_mean", "ozone_mean"]]

gt = (
    GT(monthly, rowname_col="month_label")
    .tab_header(
        title="Air Quality Summary",
        subtitle="Monthly average temperature, wind speed, and ozone levels (May–September 1973)",
    )
    .cols_label(
        temp_mean=html("Temperature (&deg;F)"),
        wind_mean="Wind Speed (mph)",
        ozone_mean=html("Ozone (ppb)"),
    )
    .fmt_number(columns=["temp_mean", "wind_mean", "ozone_mean"], decimals=1, use_seps=True)
    .sub_missing(columns=["temp_mean", "wind_mean", "ozone_mean"], missing_text="—")
)

# Apply Big Color to the two colored measures (Temperature: neutral, Wind: growth/"more is better")
# By prompt priority: temperature first, then wind speed; ozone is third so not colored
gt = heatmap(gt, columns="temp_mean", kind="sequential", hue="neutral")
gt = heatmap(gt, columns="wind_mean", kind="sequential", hue="positive")

# Apply heading band (light tint since we have Big Color) with navy hue
gt = band(gt, shade="light", hue="navy")

# Apply Small Color polish
gt = stub_tint(gt, hue="navy")
gt = stripe(gt)

# Apply frame with tab_options
gt = frame(gt)

gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

gt = gt.tab_source_note(
    source_note="Source: New York State Department of Conservation, daily measurements May–September 1973."
)

gt = finalize(gt)
