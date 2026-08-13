import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_stats = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().reset_index()

# Map month numbers to names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Rename columns for display
monthly_stats.columns = ['Month', 'Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Create the table
gt = (
    GT(monthly_stats)
    .fmt_number(columns=['Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=2)
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average temperature, wind speed, and ozone levels by month"
    )
)

gt.gtsave("table.png")
