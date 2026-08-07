import pandas as pd
import numpy as np
from great_tables import GT, html, style, loc

# Step 1: Read and clean the data
df = pd.read_csv("airquality.csv")

# Coerce numeric columns to proper types
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Create month names for better readability
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
df["Month_Name"] = df["Month"].map(month_names)

# Step 2: Aggregate by month - compute averages for the three measures
monthly_summary = df.groupby("Month_Name").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Rename for display
monthly_summary.columns = ["Month", "Temperature", "Wind Speed", "Ozone"]

# Step 3: Create the table with great_tables
# Temperature and Ozone qualify as colored measures (both > 5 rows, ordered magnitudes)
# Priority: Temperature is explicitly requested first, then Ozone
# So we color both (ceiling is 2)

cols_to_color_temp = ["Temperature"]
cols_to_color_ozone = ["Ozone"]

# Compute domains for data_color
temp_lo = float(np.nanmin(monthly_summary[cols_to_color_temp].to_numpy()))
temp_hi = float(np.nanmax(monthly_summary[cols_to_color_temp].to_numpy()))

ozone_lo = float(np.nanmin(monthly_summary[cols_to_color_ozone].to_numpy()))
ozone_hi = float(np.nanmax(monthly_summary[cols_to_color_ozone].to_numpy()))

gt = (
    GT(monthly_summary, rowname_col="Month")
    .fmt_number(columns=["Temperature", "Wind Speed", "Ozone"], decimals=1, use_seps=False)
    .sub_missing(columns=["Temperature", "Wind Speed", "Ozone"], missing_text="—")
    # Color Temperature with Blues (neutral magnitude)
    .data_color(
        columns=cols_to_color_temp,
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Color Ozone with Greens (treated as a measure where more data is better for monitoring)
    # Using Blues as secondary per the fallback ladder since both are neutral magnitudes
    .data_color(
        columns=cols_to_color_ozone,
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - light band due to Big Color presence
    .tab_options(
        heading_title_font_size="18px",
        heading_subtitle_font_size="14px",
        heading_background_color="#EAF0F6",  # light Navy tint for Blues/Greens Big Color
        column_labels_text_transform="capitalize",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5b: No column groups needed
    # Step 5c: Row striping (5 rows >= minimum of 10 is not met, so skip)
    # Step 5d: Stub tint - light Navy tint to harmonize with Big Color
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 5e: Formatting is already done with fmt_number
    # Frame border on all sides
    .tab_options(
        table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
        table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
    )
    # Add title and subtitle
    .tab_header(
        title="Air Quality Monthly Averages",
        subtitle="Average temperature, wind speed, and ozone levels by month"
    )
    # Add a source note
    .tab_source_note(
        html("Data source: Air quality measurements across 5 months")
    )
)

# Render and save
gt.gtsave("table.png", expand=15)
