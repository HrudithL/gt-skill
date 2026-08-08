import pandas as pd
from great_tables import GT
from great_tables.data import exibble

# Read the air quality data
df = pd.read_csv("airquality.csv")

# Group by month and calculate averages
monthly_avg = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean().round(2)

# Create month names for better readability
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly_avg.index = monthly_avg.index.map(month_names)
monthly_avg = monthly_avg.reset_index()
monthly_avg.columns = ["Month", "Avg Temperature (°F)", "Avg Wind Speed (mph)", "Avg Ozone (ppb)"]

# Create the great_tables table
gt = (
    GT(monthly_avg)
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .fmt_number(
        columns=["Avg Temperature (°F)", "Avg Wind Speed (mph)", "Avg Ozone (ppb)"],
        decimals=2
    )
    .cols_align(align="center")
)

gt.gtsave("table.png")
print("Table saved to table.png")
