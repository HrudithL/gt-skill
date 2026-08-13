"""Air quality monthly summary — temperature, wind speed, and ozone levels by month."""
import pandas as pd
import numpy as np
from great_tables import GT, loc, style

# Step 1: Load and clean data
df = pd.read_csv("airquality.csv")

# Coerce numeric columns (handle missing values)
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Step 2: Aggregate by month
agg = df.groupby("Month").agg(
    avg_temp=("Temp", "mean"),
    avg_wind=("Wind", "mean"),
    avg_ozone=("Ozone", "mean"),
).reset_index()

# Map month numbers to names for readability
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
}
agg["Month"] = agg["Month"].map(month_names)

# Step 3: Compute domains for colored measures
# Temperature and Ozone are the key measures per the request
temp_lo = float(np.nanmin(agg[["avg_temp"]].to_numpy()))
temp_hi = float(np.nanmax(agg[["avg_temp"]].to_numpy()))
ozone_lo = float(np.nanmin(agg[["avg_ozone"]].to_numpy()))
ozone_hi = float(np.nanmax(agg[["avg_ozone"]].to_numpy()))

# Step 4: Build the table with all styling
gt = (
    GT(agg, rowname_col="Month")
    .tab_header(
        title="Air Quality Summary by Month",
        subtitle="Average temperature, wind speed, and ozone levels",
    )
    .cols_label(
        avg_temp="Avg. Temperature (°F)",
        avg_wind="Avg. Wind Speed (mph)",
        avg_ozone="Avg. Ozone (ppb)",
    )
    .fmt_number(columns=["avg_temp", "avg_wind", "avg_ozone"], decimals=1)
    # Temperature is a key physical measurement and primary hero
    .data_color(
        columns=["avg_temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Ozone is a distinct air quality measure, also important
    .data_color(
        columns=["avg_ozone"],
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    # Wind speed stays plain (it's contextual, not the main narrative)
    .cols_align(align="right", columns=["avg_temp", "avg_wind", "avg_ozone"])
    # Heading band — fixed branding navy, bold labels, white text
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex, unconditional when stub exists
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    # Compact layout — size columns to content
    .cols_width(cases={
        "Month": "100px",
        "avg_temp": "140px",
        "avg_wind": "140px",
        "avg_ozone": "140px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Footer — analytical caption and source note (two calls, not one)
    .tab_source_note(source_note="Temperature in Fahrenheit, wind speed in mph, ozone in ppb (parts per billion).")
    .tab_source_note(source_note="Source: Air quality dataset (New York, May–September 1973).")
)

gt.gtsave("table.png", zoom=2.0, expand=15)
