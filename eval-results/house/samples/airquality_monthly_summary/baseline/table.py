import pandas as pd
from great_tables import GT

df = pd.read_csv('airquality.csv')

monthly_summary = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().reset_index()

month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_summary['Month'] = monthly_summary['Month'].map(month_names)

monthly_summary = monthly_summary.rename(columns={
    'Month': 'Month',
    'Temp': 'Avg Temperature (°F)',
    'Wind': 'Avg Wind Speed',
    'Ozone': 'Avg Ozone Level'
})

gt = GT(monthly_summary)
gt = gt.fmt_number(columns=['Avg Temperature (°F)', 'Avg Wind Speed', 'Avg Ozone Level'], decimals=1)

gt.gtsave('table.png')
