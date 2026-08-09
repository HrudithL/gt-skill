import pandas as pd
from great_tables import GT
from great_tables.data import exibble

# Load the air quality data
df = pd.read_csv('airquality.csv')

# Group by month and calculate averages
monthly_stats = df.groupby('Month')[['Ozone', 'Wind', 'Temp']].mean().reset_index()

# Rename columns for clarity
monthly_stats.columns = ['Month', 'Avg Ozone', 'Avg Wind', 'Avg Temperature']

# Map month numbers to names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Create the table
gt = (
    GT(monthly_stats)
    .tab_header(title='Air Quality Monthly Summary', subtitle='Average Temperature, Wind Speed, and Ozone Levels')
    .fmt_number(columns=['Avg Ozone', 'Avg Wind', 'Avg Temperature'], decimals=2)
    .cols_label(
        Month='Month',
        **{'Avg Ozone': 'Avg Ozone (ppb)', 'Avg Wind': 'Avg Wind (mph)', 'Avg Temperature': 'Avg Temperature (°F)'}
    )
)

gt.gtsave('table.png')
