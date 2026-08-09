import pandas as pd
from great_tables import GT

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Group by month and calculate averages
monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(2).reset_index()

# Rename columns for clarity
monthly_stats.columns = ['Month', 'Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Create month names
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Create the GT table
gt = (
    GT(monthly_stats)
    .tab_header(
        title='Air Quality Monthly Summary',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels by Month'
    )
    .fmt_number(columns=['Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=2)
)

# Save to PNG
gt.gtsave('table.png')
print("Table saved to table.png")
