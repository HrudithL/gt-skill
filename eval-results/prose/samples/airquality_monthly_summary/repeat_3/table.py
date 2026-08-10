import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df_raw = pd.read_csv("./airquality.csv")
df_raw["Ozone"] = pd.to_numeric(df_raw["Ozone"], errors="coerce")
df_raw["Solar_R"] = pd.to_numeric(df_raw["Solar_R"], errors="coerce")
df_raw["Wind"] = pd.to_numeric(df_raw["Wind"], errors="coerce")
df_raw["Temp"] = pd.to_numeric(df_raw["Temp"], errors="coerce")
df_raw["Month"] = pd.to_numeric(df_raw["Month"], errors="coerce")

# Aggregate by month
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df = df_raw.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean",
}).reset_index()

df["Month"] = df["Month"].map(month_names)
df = df.rename(columns={"Month": "month", "Temp": "avg_temp", "Wind": "avg_wind", "Ozone": "avg_ozone"})

# Step 2: Organize columns with stub
# Step 3: Big Color - Temp and Wind qualify (≥5 rows); Ozone gets bold text
# Compute domains for temperature and wind
temp_cols = ["avg_temp"]
wind_cols = ["avg_wind"]
temp_lo = float(np.nanmin(df[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(df[temp_cols].to_numpy()))
wind_lo = float(np.nanmin(df[wind_cols].to_numpy()))
wind_hi = float(np.nanmax(df[wind_cols].to_numpy()))

# Step 4: LIGHT heading band (washed-DA Navy tint) since Big Color exists
# Step 5: Small Color polish
gt = (
    GT(df, rowname_col="month")
    # Format columns
    .fmt_number(columns=["avg_temp", "avg_wind"], decimals=1, use_seps=True)
    .fmt_number(columns=["avg_ozone"], decimals=1, use_seps=True)
    # Big Color - Temperature gradient (Blues for neutral magnitude)
    .data_color(
        columns=["avg_temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color - Wind gradient (Blues for neutral magnitude)
    .data_color(
        columns=["avg_wind"],
        palette="Blues",
        domain=[wind_lo, wind_hi],
        truncate=False,
        na_color="#808080",
    )
    # Bold the uncolored ozone measure
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["avg_ozone"]),
    )
    # Step 4: Light heading band (washed Navy tint)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5 (a): Cell borders - hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5 (c): Row striping (≥10 rows and body not fully filled)
    .opt_row_striping()
    # Step 5 (d): Stub tint (washed-DA Navy tint to harmonize with Big Color)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5: Frame border - light border on all four sides
    .tab_options(
        table_border_top_style="solid",
        table_border_top_color="#CCCCCC",
        table_border_top_width="1px",
        table_border_bottom_style="solid",
        table_border_bottom_color="#CCCCCC",
        table_border_bottom_width="1px",
        table_border_left_style="solid",
        table_border_left_color="#CCCCCC",
        table_border_left_width="1px",
        table_border_right_style="solid",
        table_border_right_color="#CCCCCC",
        table_border_right_width="1px",
    )
    # Step 6: Titles and annotations
    .tab_header(
        title="Air Quality by Month",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels",
    )
    .tab_source_note(
        source_note="Temperature (°F) and Wind (mph) are shown with color gradients indicating magnitude; Ozone is in ppb.",
    )
    .tab_source_note(
        source_note="Source: Air Quality dataset, May–September measurements.",
    )
)

gt.gtsave("table.png", expand=15, zoom=2.0)
