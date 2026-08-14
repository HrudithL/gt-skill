import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages for Temperature, Wind, and Ozone
monthly_stats = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().round(2)

# Rename columns for clarity
monthly_stats.columns = ['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Reset index to make Month a column
monthly_stats = monthly_stats.reset_index()

# Map month numbers to month names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Create the GT table
gt = GT(monthly_stats)
gt = gt.tab_header(
    title='Air Quality Monthly Summary',
    subtitle='Average Temperature, Wind Speed, and Ozone Levels'
)

# Render and save
gt.gtsave('table.png')
print("Table saved to table.png")
