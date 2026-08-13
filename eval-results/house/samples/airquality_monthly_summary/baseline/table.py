import pandas as pd
from great_tables import GT, loc, style

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(2)

# Rename columns for display
monthly_stats.columns = ['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Reset index to make Month a column
monthly_stats = monthly_stats.reset_index()
monthly_stats['Month'] = monthly_stats['Month'].astype(int)

# Map month numbers to names
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Reorder columns
monthly_stats = monthly_stats[['Month', 'Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']]

# Create GT table
gt = (
    GT(monthly_stats)
    .tab_header(
        title='Air Quality Monthly Summary',
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

# Save the table
gt.gtsave('table.png')
