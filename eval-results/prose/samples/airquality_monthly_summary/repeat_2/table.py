import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Data Cleaning
df = pd.read_csv("airquality.csv")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce")

# Aggregate by month: compute averages
monthly = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Create month names for display
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["month_label"] = monthly["Month"].map(month_names)

# Reorder columns and set month label as index column
monthly = monthly[["month_label", "Temp", "Wind", "Ozone"]]
monthly.columns = ["Month", "Temperature (°F)", "Wind (mph)", "Ozone (ppb)"]

# Step 2: Organize Columns
# Month is the stub (row identifier)
# Three numeric measures: Temperature, Wind, Ozone
# All qualify for column gradient fill (≥5 months, ordered magnitude)

# Step 3: Big Color — Determine domains for each measure
temp_cols = ["Temperature (°F)"]
wind_cols = ["Wind (mph)"]
ozone_cols = ["Ozone (ppb)"]

temp_lo = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly[temp_cols].to_numpy()))

wind_lo = float(np.nanmin(monthly[wind_cols].to_numpy()))
wind_hi = float(np.nanmax(monthly[wind_cols].to_numpy()))

ozone_lo = float(np.nanmin(monthly[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(monthly[ozone_cols].to_numpy()))

# Step 4: Heading band (unconditional)
# Fixed navy band: #08306B

# Step 5: Small Color polish + Step 6: Titles
# Step 7: Render

gt = (
    GT(monthly, rowname_col="Month")
    # Formatting
    .fmt_number(columns="Temperature (°F)", decimals=1)
    .fmt_number(columns="Wind (mph)", decimals=1)
    .fmt_number(columns="Ozone (ppb)", decimals=1)
    # Big Color: data_color for each measure with appropriate palette
    # Temperature: neutral magnitude → Blues
    .data_color(
        columns="Temperature (°F)",
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Wind: neutral magnitude → Blues (but secondary, so use Greens per neutral tie-breaker)
    .data_color(
        columns="Wind (mph)",
        palette="Greens",
        domain=[wind_lo, wind_hi],
        truncate=False,
        na_color="#808080",
    )
    # Ozone: neutral magnitude → Oranges (tertiary per the fallback ladder)
    .data_color(
        columns="Ozone (ppb)",
        palette="Oranges",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Titles
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    # Small Color checklist
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        # (Step 4) Heading band: fixed navy branding
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        # Frame (all four sides)
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
        heading_padding="8px",
        heading_padding_horizontal="8px",
        data_row_padding="8px",
        data_row_padding_horizontal="8px",
    )
    # Column-label text color (explicit pin)
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # (c) Row striping
    .opt_row_striping()
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (f) Titles & annotations - caption and source
    .tab_source_note(
        "Averages computed from daily observations across the 5-month period."
    )
    .tab_source_note(
        "Source: R datasets::airquality"
    )
    # Column widths
    .cols_width(cases={
        "Month": "120px",
        "Temperature (°F)": "140px",
        "Wind (mph)": "120px",
        "Ozone (ppb)": "120px",
    })
)

# Step 7: Render
gt.gtsave("table.png", expand=15)
