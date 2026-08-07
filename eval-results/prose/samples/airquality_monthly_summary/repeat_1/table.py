import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Aggregate by month: calculate means
monthly = df.groupby("Month")[["Ozone", "Wind", "Temp"]].mean().reset_index()

# Map month numbers to names for display
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October"
}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Organize columns: stub first, then the three measures
monthly_display = monthly[["Month_Name", "Temp", "Wind", "Ozone"]].copy()
monthly_display.columns = ["Month", "Temperature", "Wind", "Ozone"]

# Step 2: Organize columns - Month is the stub (row identifier)
# We have 6 months of data (≥5 rows), so all three measures qualify for coloring
# Priority by prompt: Temperature, Wind, Ozone (in order mentioned)
# We can color up to 2, so we color Temperature (primary) and Wind (secondary)
# Ozone will be uncolored

# Step 3: Determine Big Color - we have 3 qualifying measures, cap at 2
# Primary measure: Temp (temperature, neutral magnitude → Blues)
# Secondary measure: Wind (wind speed, neutral magnitude → use Greens per tie-breaker rule)
temp_cols = ["Temperature"]
wind_cols = ["Wind"]
ozone_cols = ["Ozone"]

# Compute domains
temp_lo = float(np.nanmin(monthly_display[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly_display[temp_cols].to_numpy()))
wind_lo = float(np.nanmin(monthly_display[wind_cols].to_numpy()))
wind_hi = float(np.nanmax(monthly_display[wind_cols].to_numpy()))

# Step 4: Heading band - we have Big Color, so use LIGHT band
# Hue: neutral magnitudes (money/price/volume) default to Blues per palettes.md §3
# But we have two neutral measures, so primary=Blues, secondary=Greens (fallback ladder)
band_hex = "#EAF0F6"  # washed Navy tint (Blues family)

# Step 5: Small Color polish - build the table with formatting
gt = (
    GT(monthly_display, rowname_col="Month")
    # Format all numeric columns
    .fmt_number(columns=["Temperature", "Wind", "Ozone"], decimals=1, use_seps=True)
    # Handle missing values
    .sub_missing(columns=["Temperature", "Wind", "Ozone"], missing_text="—")
    # Big Color: Temperature (Blues, primary neutral magnitude)
    .data_color(
        columns=["Temperature"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color: Wind (Greens, secondary neutral magnitude per tie-breaker)
    .data_color(
        columns=["Wind"],
        palette="Greens",
        domain=[wind_lo, wind_hi],
        truncate=False,
        na_color="#808080",
    )
    # Heading band - light Navy tint (Big Color present → light band)
    .tab_options(
        column_labels_background_color="#EAF0F6",
    )
    # Stub tint - harmonize to the washed Navy tint (Big Color matches)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Column label bottom rule (constant in small_color.md)
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Cell hairline borders (every table)
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Row striping (≥10 rows gate: we have 6, so skip striping per rule)
    # (Skipped: < 10 rows)
    # Frame border (every table)
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
    # Titles (both required)
    .tab_header(
        title="Air Quality: Monthly Averages",
        subtitle="Temperature, Wind Speed, and Ozone Levels"
    )
    # Caption and source (≥5 rows → caption required)
    .tab_source_note("Data source: US EPA air quality measurements, May–October")
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
