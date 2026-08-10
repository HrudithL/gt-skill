import pandas as pd
from great_tables import GT

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Group by month and calculate means
monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).reset_index()

# Map month numbers to month names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Rename columns for clarity
monthly_stats.columns = ['Month', 'Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Create the great_tables GT object
gt = (
    GT(monthly_stats)
    .tab_header(
        title='Monthly Air Quality Summary',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels'
    )
    .fmt_number(columns=['Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=2)
)

# Save the table as PNG
gt.gtsave('table.png')
print("Table saved to table.png")
