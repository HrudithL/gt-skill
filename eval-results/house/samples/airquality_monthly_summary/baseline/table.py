import pandas as pd
from great_tables import GT

df = pd.read_csv('airquality.csv')

monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(2)

monthly_stats.columns = ['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']
monthly_stats.index.name = 'Month'
monthly_stats = monthly_stats.reset_index()

month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

gt = (
    GT(monthly_stats)
    .tab_header(
        title='Air Quality Summary by Month',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels'
    )
)

gt.gtsave('table.png')
