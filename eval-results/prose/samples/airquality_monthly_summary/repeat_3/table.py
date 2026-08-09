import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Compute monthly averages
monthly = df.groupby("Month")[["Ozone", "Wind", "Temp"]].mean().reset_index()

# Map month numbers to names
month_names = {
    5: "May", 6: "June", 7: "July", 8: "August", 9: "September"
}
monthly["Month"] = monthly["Month"].map(month_names)

# Rename columns for display
monthly = monthly.rename(columns={
    "Month": "month",
    "Temp": "Temperature",
    "Wind": "Wind Speed",
    "Ozone": "Ozone"
})

# Step 2: Organize columns — month is the stub
# Step 3: Compute domains for gradient coloring
# Temperature and Ozone are the 2 colored measures (neutral magnitudes → Blues for both, but use secondary Greens for second)
cols_temp = ["Temperature"]
cols_ozone = ["Ozone"]

temp_lo = float(np.nanmin(monthly[cols_temp].to_numpy()))
temp_hi = float(np.nanmax(monthly[cols_temp].to_numpy()))
ozone_lo = float(np.nanmin(monthly[cols_ozone].to_numpy()))
ozone_hi = float(np.nanmax(monthly[cols_ozone].to_numpy()))

# Step 4 & 5: Build the table with Big Color (light band) + Small Color polish
gt = (
    GT(monthly, rowname_col="month")
    # Format columns
    .fmt_number(columns=["Temperature", "Wind Speed", "Ozone"], decimals=1, use_seps=False)
    .sub_missing(columns=["Temperature", "Wind Speed", "Ozone"], missing_text="—")
    # Big Color: gradient fills on Temperature (primary, Blues) and Ozone (secondary, Greens)
    .data_color(
        columns=["Temperature"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Ozone"],
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Light heading band (washed-DA tint of Blues → pale blue)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5 (a): Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # Step 5 (c): Row striping (≥10 rows)
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Step 5 (d): Stub tint (harmonized to Blues washed tint)
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Frame border (all four sides)
    .tab_options(
        table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
        table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
    )
    # Titles
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels (May–September)",
    )
)

# Render
gt.gtsave("table.png", expand=15, zoom=2.0)
print("✓ table.png created successfully")
