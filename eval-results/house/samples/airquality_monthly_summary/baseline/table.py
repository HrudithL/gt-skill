import pandas as pd
from great_tables import GT

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Group by month and calculate averages
monthly_summary = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(2)

# Rename columns for clarity
monthly_summary.columns = ['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']
monthly_summary.index.name = 'Month'

# Map month numbers to names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_summary.index = monthly_summary.index.map(month_names)

# Create the great_tables table
gt = (
    GT(monthly_summary.reset_index())
    .tab_header(
        title="Air Quality Monthly Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
    .fmt_number(
        columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'],
        decimals=2
    )
    .tab_options(
        container_width="600px"
    )
)

gt.gtsave('table.png')
