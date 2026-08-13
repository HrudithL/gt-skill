import pandas as pd
from great_tables import GT

df = pd.read_csv('airquality.csv')

monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).reset_index()

monthly_stats.columns = ['Month', 'Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

gt = (
    GT(monthly_stats)
    .tab_header(
        title='Monthly Air Quality Summary',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels'
    )
    .fmt_number(columns=['Avg Temp (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=2)
)

gt.gtsave('table.png')
