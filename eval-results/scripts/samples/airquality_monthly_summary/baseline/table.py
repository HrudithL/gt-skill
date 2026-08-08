import pandas as pd
import great_tables as gt

# Load the air quality data
df = pd.read_csv("airquality.csv")

# Calculate monthly averages
monthly_avg = df.groupby("Month")[["Temp", "Wind", "Ozone"]].mean()

# Round to 2 decimal places for cleaner display
monthly_avg = monthly_avg.round(2)

# Reset index to make Month a column
monthly_avg = monthly_avg.reset_index()

# Rename columns for better display
monthly_avg.columns = ["Month", "Avg Temperature (°F)", "Avg Wind Speed (mph)", "Avg Ozone (ppb)"]

# Map month numbers to month names
month_names = {
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September"
}
monthly_avg["Month"] = monthly_avg["Month"].map(month_names)

# Create the table
gt_table = (
    gt.GT(monthly_avg)
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .cols_align(align="center")
    .tab_options(
        table_width="600px"
    )
)

# Save the table as PNG
gt_table.gtsave("table.png")
print("Table saved to table.png")
