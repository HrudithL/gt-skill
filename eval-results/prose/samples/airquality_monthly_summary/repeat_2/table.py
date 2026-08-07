import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Coerce numeric columns to ensure proper typing
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Solar_R"] = pd.to_numeric(df["Solar_R"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

# Group by month and calculate means
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Map month numbers to month names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month"] = monthly["Month"].map(month_names)

# Rename for clarity
monthly.columns = ["Month", "Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"]

# Step 2: Organize columns with Month as stub
# Step 3: Big Color — three numeric measures qualify (≥5 rows). Pick top 2 by prompt order.
#         "temperature, wind speed, and ozone levels" = Temp first, Wind second, Ozone uncolored.
#         Temp = neutral magnitude → Blues
#         Wind = neutral magnitude (volume) → Greens (secondary per tie-breaker)

# Compute domains for the two colored measures
temp_cols = ["Avg Temp (°F)"]
wind_cols = ["Avg Wind (mph)"]

temp_lo = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly[temp_cols].to_numpy()))

wind_lo = float(np.nanmin(monthly[wind_cols].to_numpy()))
wind_hi = float(np.nanmax(monthly[wind_cols].to_numpy()))

# Step 4: Heading band — Big Color present, so use LIGHT band (washed tint for Blues)
# Step 5: Small Color polish checklist

gt = (
    GT(monthly, rowname_col="Month")

    # Formatting per column (semantic type)
    .fmt_number(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], decimals=1, use_seps=False)
    .sub_missing(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], missing_text="—")

    # Step 3: Big Color — gradient fills for Temp (Blues, primary) and Wind (Greens, secondary)
    .data_color(
        columns=["Avg Temp (°F)"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Avg Wind (mph)"],
        palette="Greens",
        domain=[wind_lo, wind_hi],
        truncate=False,
        na_color="#808080",
    )

    # Step 4: Heading band — light washed-DA tint (pale-blue for Blues table)
    .tab_options(
        column_labels_background_color="#EAF0F6",  # washed Navy tint (from palettes.md §2)
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )

    # Step 5: Small Color polish checklist

    # (a) Cell borders — hairline between all rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )

    # (c) Row striping — ≥10 rows check; this table has 5, so skip striping
    # .opt_row_striping()  # Skipped: <10 body rows

    # (d) Stub tint — light grey (grey-budget default with Big Color present)
    .tab_style(
        style=style.fill(color="#EAF0F6"),  # washed Navy tint to harmonize with band
        locations=loc.stub(),
    )

    # Frame — light border on all four sides
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

    # Titles and annotations
    .tab_header(
        title="Air Quality: Monthly Averages",
        subtitle="Average temperature, wind speed, and ozone levels by month",
    )
    .tab_source_note("Source: Daily air quality measurements aggregated by month")
)

# Render to PNG
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
