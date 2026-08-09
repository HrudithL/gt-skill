import pandas as pd
from great_tables import GT, loc, style
from great_tables.data import exibble

# Load the air quality data
df = pd.read_csv("airquality.csv")

# Calculate monthly averages
monthly_avg = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().reset_index()

# Round to 2 decimal places
monthly_avg = monthly_avg.round(2)

# Map month numbers to month names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly_avg["Month"] = monthly_avg["Month"].map(month_names)

# Rename columns for display
monthly_avg = monthly_avg.rename(columns={
    "Month": "Month",
    "Temp": "Avg Temperature (°F)",
    "Wind": "Avg Wind Speed (mph)",
    "Ozone": "Avg Ozone (ppb)"
})

# Create the GT table
gt = GT(monthly_avg)
gt = gt.tab_header(
    title="Air Quality Monthly Summary",
    subtitle="Average Temperature, Wind Speed, and Ozone Levels"
)

# Format numeric columns
gt = gt.fmt_number(
    columns=["Avg Temperature (°F)", "Avg Wind Speed (mph)", "Avg Ozone (ppb)"],
    decimals=2
)

# Save the table as PNG
gt.gtsave("table.png")
