import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data cleaning
df = pd.read_csv("airquality.csv")

# Group by month and compute means
monthly = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Create month names for readability
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Reorder and select columns
monthly = monthly[["Month_Name", "Temp", "Wind", "Ozone"]]
monthly = monthly.rename(columns={"Month_Name": "Month"})

# Step 2: Organize columns
# Month is the stub (row identifier)
# Temp, Wind, Ozone are ordered numeric measures

# Step 3: Big Color - determine which measures to color
# All three are ordered numeric magnitudes with ≥5 rows, so all qualify
# Temperature (Temp) and Ozone are core to the request
# Wind speed is secondary (mentioned but not emphasized)
# Per small_color.md §F-canonical-metric: color the primary measures (Temp, Ozone)

# Compute domains for colored measures
temp_cols = ["Temp"]
ozone_cols = ["Ozone"]
temp_lo = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly[temp_cols].to_numpy()))
ozone_lo = float(np.nanmin(monthly[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(monthly[ozone_cols].to_numpy()))

# Build the table
gt = (
    GT(monthly, rowname_col="Month")
    .fmt_number(columns=["Temp", "Wind", "Ozone"], decimals=1, use_seps=False)
    .sub_missing(columns=["Temp", "Wind", "Ozone"], missing_text="—")
    # Step 3: Big Color - heatmaps for Temperature and Ozone
    .data_color(
        columns="Temp",
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns="Ozone",
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - dark navy with white text (branding constant)
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels by Month",
    )
    # Step 5: Small Color polish
    # (a) Cell borders and column-label rule
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # Frame
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
        # Compact layout padding
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
        # (c) Row striping
        row_striping_background_color="#F6F6F6",
    )
    # (c) Row striping activation
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Heading band styling
    .tab_style(
        style=style.fill(color="#08306B"),
        locations=loc.header(),
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.header(),
    )
    # Step 6: Titles & annotations (already set via tab_header)
    .tab_source_note(
        source_note="Temperature and ozone display average monthly values; wind speed is secondary context."
    )
    .tab_source_note(
        source_note="Source: Air Quality Dataset (airquality.csv)"
    )
)

# Render
gt.gtsave("table.png", expand=15, zoom=2.0)
