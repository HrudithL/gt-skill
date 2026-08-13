import pandas as pd
from great_tables import GT

# Load the air quality data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).reset_index()

# Round to 2 decimal places
monthly_stats = monthly_stats.round(2)

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
monthly_stats = monthly_stats.rename(columns={
    'Month': 'Month',
    'Temp': 'Avg Temperature (°F)',
    'Wind': 'Avg Wind Speed (mph)',
    'Ozone': 'Avg Ozone (ppb)'
})

# Create the table
gt = GT(monthly_stats).tab_header(
    title='Air Quality Statistics by Month',
    subtitle='Average Temperature, Wind Speed, and Ozone Levels'
).fmt_number(
    columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'],
    decimals=2
)

# Save as PNG
gt.gtsave('table.png')

print("Table created and saved to table.png")
