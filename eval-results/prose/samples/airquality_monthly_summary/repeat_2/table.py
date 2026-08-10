import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: Read and clean the data
df = pd.read_csv("airquality.csv")

# Aggregate by month: calculate average temperature, wind speed, and ozone
agg_df = df.groupby("Month").agg(
    Avg_Temp=("Temp", "mean"),
    Avg_Wind=("Wind", "mean"),
    Avg_Ozone=("Ozone", "mean"),
).reset_index()

# Create month names for clarity
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
agg_df["Month"] = agg_df["Month"].map(month_names)

# Step 2: Organize columns — Month is the stub (row identifiers)
agg_df = agg_df.rename(columns={"Month": "Month"})

# Step 3: Big Color — Two ordered magnitude measures qualify (≥5 rows each)
# Temperature and Ozone are colored; Wind is bold uncolored
# Temperature: neutral magnitude → Blues
# Ozone: environmental/growth context → Greens

temp_cols = ["Avg_Temp"]
ozone_cols = ["Avg_Ozone"]

# Compute domains for gradients
temp_lo = float(np.nanmin(agg_df[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(agg_df[temp_cols].to_numpy()))
ozone_lo = float(np.nanmin(agg_df[ozone_cols].to_numpy()))
ozone_hi = float(np.nanmax(agg_df[ozone_cols].to_numpy()))

# Build the table
gt = (
    GT(agg_df, rowname_col="Month")
    .tab_header(
        title="Air Quality Summary by Month",
        subtitle="Average temperature, wind speed, and ozone levels across summer 2024",
    )
    .cols_label(
        Avg_Temp="Avg. Temperature (°F)",
        Avg_Wind="Avg. Wind Speed (mph)",
        Avg_Ozone="Avg. Ozone (ppb)",
    )
    # Format the measures
    .fmt_number(columns=["Avg_Temp", "Avg_Wind", "Avg_Ozone"], decimals=1)
    # Step 3: Big Color — gradient fills for two measures
    .data_color(
        columns=["Avg_Temp"],
        palette="Blues",
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color="#808080",
    )
    .data_color(
        columns=["Avg_Ozone"],
        palette="Greens",
        domain=[ozone_lo, ozone_hi],
        truncate=False,
        na_color="#808080",
    )
    # Bold the uncolored secondary measure (Wind)
    .tab_style(
        style=style.text(weight="bold"),
        locations=loc.body(columns=["Avg_Wind"]),
    )
    # Step 4: Heading band — light band with washed tints (Big Color present)
    # Use pale blue as the dominant tint (matching Blues gradient)
    .tab_options(
        column_labels_background_color="#EAF0F6",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # Step 5: Small Color polish
    # (a) Cell borders — hairlines between rows
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
    )
    # (d) Stub tint — no striping, so stub gets light tint
    .tab_style(
        style=style.fill(color="#EAF0F6"),
        locations=loc.stub(),
    )
    # Add footer: two separate notes (analytical caption + source provenance)
    .tab_source_note("Temperature and ozone show clear seasonal patterns, with peaks in July and August.")
    .tab_source_note("Source: Air quality measurements from daily observations.")
)

# Step 7: Render
gt.gtsave("table.png")
print("Table rendered successfully: table.png")
