import pandas as pd
import numpy as np
from great_tables import GT, loc, style

# Load and clean data
df = pd.read_csv("airquality.csv")

# Convert numeric columns to float (handle empty values)
df["Ozone"] = pd.to_numeric(df["Ozone"], errors="coerce")
df["Wind"] = pd.to_numeric(df["Wind"], errors="coerce")
df["Temp"] = pd.to_numeric(df["Temp"], errors="coerce")

# Create month name mapping
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}

# Calculate monthly averages
monthly_agg = (
    df.groupby("Month")
    .agg(
        Temperature=("Temp", "mean"),
        Wind=("Wind", "mean"),
        Ozone=("Ozone", "mean")
    )
    .reset_index()
)

# Add month name and sort
monthly_agg["Month_Name"] = monthly_agg["Month"].map(month_names)
monthly_agg = monthly_agg[["Month_Name", "Temperature", "Wind", "Ozone"]].reset_index(drop=True)

# Round to 1 decimal place
monthly_agg["Temperature"] = monthly_agg["Temperature"].round(1)
monthly_agg["Wind"] = monthly_agg["Wind"].round(1)
monthly_agg["Ozone"] = monthly_agg["Ozone"].round(1)

# Create table with month as stub
gt = (
    GT(monthly_agg, rowname_col="Month_Name")
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average temperature (°F), wind speed (mph), and ozone (ppb) by month"
    )
    .cols_label(Temperature="Temperature (°F)", Wind="Wind (mph)", Ozone="Ozone (ppb)")
    .fmt_number(columns=["Temperature", "Wind", "Ozone"], decimals=1)
    .tab_options(
        column_labels_background_color="#22384F",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px"
    )
    .cols_align(align="right", columns=["Temperature", "Wind", "Ozone"])
)

gt.gtsave("table.png")
