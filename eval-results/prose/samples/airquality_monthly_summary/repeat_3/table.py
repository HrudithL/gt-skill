import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Aggregate by month
monthly = df.groupby("Month").agg({
    "Ozone": "mean",
    "Wind": "mean",
    "Temp": "mean",
}).reset_index()

# Map month numbers to names for the stub
month_names = {5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
monthly["Month_Name"] = monthly["Month"].map(month_names)
monthly = monthly.drop(columns=["Month"])

# Reorder columns: Month as stub, then Ozone, Wind, Temp
monthly = monthly[["Month_Name", "Ozone", "Wind", "Temp"]]

# Step 2: Organize columns
# Month_Name is the stub, Ozone and Temp are measures (colored), Wind is a supporting measure

# Step 3: Big Color — Temperature and Ozone both qualify
# Ozone: neutral magnitude → Blues
# Temperature: neutral magnitude → Blues (but two blues would violate distinctness)
# For two neutral measures: primary (mentioned first in prompt) → Blues, secondary → Greens
# Prompt mentions: "temperature, wind speed, and ozone" — temperature first, ozone second
# So: Temperature → Blues (primary), Ozone → Greens (secondary)

ozone_cols = ["Ozone"]
temp_cols = ["Temp"]
wind_cols = ["Wind"]

# Compute domains
ozone_lo = float(np.nanmin(monthly[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(monthly[ozone_cols].to_numpy()))
temp_lo = float(np.nanmin(monthly[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly[temp_cols].to_numpy()))

# Step 4 & 5: Build table with heading band and all styling
gt = (
    GT(monthly, rowname_col="Month_Name")
    # Formatting (Step 5.e)
    .fmt_number(columns=["Ozone", "Temp", "Wind"], decimals=1, use_seps=False)
    .sub_missing(columns=["Ozone", "Wind", "Temp"], missing_text="—")
    # Big Color (Step 3) — gradient fills for Ozone and Temperature
    .data_color(
        columns=["Temp"],
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
    # Column labels
    .cols_label(
        Ozone="Ozone (ppb)",
        Wind="Wind Speed (mph)",
        Temp="Temperature (°F)",
    )
    # Column widths (Step 5 compact layout)
    .cols_width(cases={
        "Month_Name": "120px",
        "Ozone": "110px",
        "Wind": "120px",
        "Temp": "120px",
    })
    # Heading band (Step 4) — fixed navy
    .tab_header(
        title="Air Quality Summary by Month",
        subtitle="Average ozone levels, wind speed, and temperature",
    )
    # Step 5: Small-Color checklist
    # (a) Cell borders — hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # (c) Row striping — apply by default
    .opt_row_striping()
    # (d) Stub tint — fixed pale blue
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (f) Titles & annotations — footer notes
    .tab_source_note(source_note="Temperature and ozone displayed as averages across available observations for each month.")
    .tab_source_note(source_note="Source: airquality.csv")
    # Frame and padding (Step 5 & global constants)
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
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
        # Heading band styling (Step 4) — fixed navy branding
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
    )
)

gt.gtsave("table.png", expand=15)
