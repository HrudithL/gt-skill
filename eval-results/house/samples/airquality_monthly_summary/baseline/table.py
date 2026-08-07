import pandas as pd
from great_tables import GT, style, loc

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(2).reset_index()

# Map month numbers to month names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Rename columns for display
monthly_stats.columns = ['Month', 'Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Create the GT table
gt = (
    GT(monthly_stats)
    .tab_header(
        title='Monthly Air Quality Statistics',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels'
    )
    .fmt_number(
        columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'],
        decimals=2
    )
    .tab_options(
        container_width='600px'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
