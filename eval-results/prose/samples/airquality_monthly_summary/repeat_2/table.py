import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: UNDERSTAND DATA & CLEAN
df = pd.read_csv("airquality.csv")

# Ensure numeric columns are correctly typed (data.md checklist)
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")
df["Month"] = df["Month"].astype(int)

# Aggregate by month: mean of Temperature, Wind, and Ozone
monthly = df.groupby("Month").agg({
    "Temp": "mean",
    "Wind": "mean",
    "Ozone": "mean"
}).reset_index()

# Map month numbers to month names (stub formatting: "Mon YYYY" pattern, but we only have months)
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly["Month"] = monthly["Month"].map(month_names)

# Rename for clarity
monthly = monthly.rename(columns={
    "Month": "Month",
    "Temp": "Avg Temp (°F)",
    "Wind": "Avg Wind (mph)",
    "Ozone": "Avg Ozone (ppb)"
})

# Step 2: ORGANIZE COLUMNS
# Month is the stub (rowname_col), three numeric measures as value columns

# Step 3: BIG COLOR
# One colored measure: Temperature (Avg Temp). Use Greens palette (warmth/growth concept).
# Domain: covers full range of data
temp_min = monthly["Avg Temp (°F)"].min()
temp_max = monthly["Avg Temp (°F)"].max()

# Step 4: HEADING BAND
# Big Color present → LIGHT washed band. Temperature uses Greens → use Forest green tint: #EAF1EC

# Step 5: SMALL COLOR CHECKLIST
gt = (
    GT(monthly, rowname_col="Month")
    # (a) Cell borders
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    # (d) Stub tint - Forest green washed tint since Big Color uses Greens
    .tab_style(
        style=style.fill(color="#EAF1EC"),
        locations=loc.stub(),
    )
    # (e) Formatting per column
    .fmt_number(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], decimals=1, use_seps=True)
    .sub_missing(columns=["Avg Temp (°F)", "Avg Wind (mph)", "Avg Ozone (ppb)"], missing_text="—")
    # Step 3: Big Color - data_color on Temperature
    .data_color(
        columns=["Avg Temp (°F)"],
        palette="Greens",
        domain=[temp_min, temp_max]
    )
    # Frame - light border all sides + margin
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
    # Step 4: Heading band - light Forest green tint (Big Color present)
    .tab_options(
        column_labels_background_color="#EAF1EC"
    )
)

# Step 6: TITLES & ANNOTATIONS
gt = (
    gt.tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average temperature, wind speed, and ozone levels (May–September)"
    )
    .tab_source_note(source_note="Source: provided air quality dataset.")
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15)
print("Table rendered successfully to table.png")
