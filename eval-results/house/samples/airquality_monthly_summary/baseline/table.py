import pandas as pd
from great_tables import GT

df = pd.read_csv('airquality.csv')

monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(2)

monthly_stats = monthly_stats.reset_index()
monthly_stats.columns = ['Month', 'Avg Temperature', 'Avg Wind Speed', 'Avg Ozone Level']

month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

gt = (
    GT(monthly_stats)
    .tab_header(
        title="Monthly Air Quality Summary",
        subtitle="Average Temperature, Wind Speed, and Ozone Levels"
    )
)

gt.gtsave('table.png')
