import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Read and clean data
df = pd.read_csv("airquality.csv")

# Group by Month and calculate averages
monthly_stats = df.groupby("Month").agg({
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
monthly_stats["Month"] = monthly_stats["Month"].map(month_names)

# Rename columns for display
monthly_stats.rename(columns={
    "Temp": "Avg_Temp",
    "Wind": "Avg_Wind",
    "Ozone": "Avg_Ozone"
}, inplace=True)

# Step 2: Organize columns - month is the stub
# Columns are already in good narrative order

# Step 3: Big Color - compute domains for each measure
temp_cols = ["Avg_Temp"]
wind_cols = ["Avg_Wind"]
ozone_cols = ["Avg_Ozone"]

temp_lo = float(np.nanmin(monthly_stats[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly_stats[temp_cols].to_numpy()))

wind_lo = float(np.nanmin(monthly_stats[wind_cols].to_numpy()))
wind_hi = float(np.nanmax(monthly_stats[wind_cols].to_numpy()))

ozone_lo = float(np.nanmin(monthly_stats[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(monthly_stats[ozone_cols].to_numpy()))

# Build the table
gt = (
    GT(monthly_stats, rowname_col="Month")
    # Formatting
    .fmt_number(columns=["Avg_Temp", "Avg_Wind", "Avg_Ozone"], decimals=1)
    # Step 3: Big Color - Three distinct measures, all qualify
    # Temperature - neutral magnitude -> Blues
    .data_color(
        columns=temp_cols,
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    # Wind Speed - neutral magnitude -> Greens (secondary neutral, per tie-breaker rule)
    .data_color(
        columns=wind_cols,
        palette="Greens",
        domain=[wind_lo, wind_hi],
        truncate=False,
        na_color="#808080",
    )
    # Ozone - neutral magnitude -> Oranges (tertiary neutral, per tie-breaker rule)
    .data_color(
        columns=ozone_cols,
        palette="Oranges",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Step 4: Heading band - fixed navy band with white text
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.text(color="white"),
        locations=loc.column_labels(),
    )
    # Step 5: Small-Color polish
    # (a) Cell borders and column-label bottom rule
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (c) Row striping - apply by default
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # (d) Stub tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # (e) Formatting with sub_missing
    .sub_missing(columns=["Avg_Temp", "Avg_Wind", "Avg_Ozone"], missing_text="—")
    # Step 6: Titles & annotations
    .tab_header(
        title="Air Quality Summary Statistics by Month",
        subtitle="Average temperature, wind speed, and ozone levels"
    )
    .tab_source_note(
        source_note="Measurements aggregated from daily observations across months."
    )
    .tab_source_note(
        source_note="Source: Air quality data (airquality.csv)."
    )
    # Step 2 continued: Compact layout
    .cols_width(cases={
        "Avg_Temp": "120px",
        "Avg_Wind": "120px",
        "Avg_Ozone": "120px"
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    # Frame - boxed enclosing border
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
)

# Step 7: Render & verify
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
