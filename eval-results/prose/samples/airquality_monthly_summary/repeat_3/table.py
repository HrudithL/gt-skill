import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Compute monthly averages, grouping by Month
monthly = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Create month names for better readability
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}
monthly["Month_Name"] = monthly["Month"].map(month_names)

# Drop the numeric month column and reorder
monthly = monthly[["Month_Name", "Temp", "Wind", "Ozone"]]
monthly.columns = ["Month", "Temperature", "Wind", "Ozone"]

# Set Month as the index for the stub
monthly_display = monthly.set_index("Month").reset_index()

# Step 2: Organize columns - Month is the stub, Temperature and Ozone are our measured values
# Step 3: Big Color - Both Temperature (as primary) and Ozone are distinct air quality dimensions
# Compute domains for the colored measures
temp_cols = ["Temperature"]
ozone_cols = ["Ozone"]
temp_lo = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly[temp_cols].to_numpy()))
ozone_lo = float(np.nanmin(monthly[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(monthly[ozone_cols].to_numpy()))

# Step 4 & 5: Build the table with all styling
gt = (
    GT(monthly, rowname_col="Month")
    # Column labels
    .cols_label(
        Temperature="Temperature (°F)",
        Wind="Wind Speed (mph)",
        Ozone="Ozone (ppb)",
    )
    # Format numbers
    .fmt_number(columns=["Temperature", "Wind", "Ozone"], decimals=1, use_seps=False)
    .sub_missing(columns=["Temperature", "Wind", "Ozone"], missing_text="—")
    # Big Color - Temperature (Blues - neutral magnitude)
    .data_color(
        columns="Temperature",
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Big Color - Ozone (Greens - distinct air quality indicator)
    .data_color(
        columns="Ozone",
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band (fixed branding)
    .tab_header(
        title="Air Quality by Month",
        subtitle="Average temperature, wind speed, and ozone levels",
    )
    .tab_style(
        style=style.fill(color="#08306B"),
        locations=loc.column_labels(),
    )
    .tab_style(
        style=style.text(color="white", weight="bold"),
        locations=loc.column_labels(),
    )
    .tab_options(
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        row_striping_background_color="#F6F6F6",
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Step 6: Titles & annotations (footer notes)
    .tab_source_note(
        source_note="Temperature and Ozone are colored to highlight their magnitudes across months; Wind speed is shown as reference data.",
    )
    .tab_source_note(
        source_note="Source: Air quality dataset (airquality.csv).",
    )
)

# Render to PNG
gt.gtsave("table.png")
