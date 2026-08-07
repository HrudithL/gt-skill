import pandas as pd
from great_tables import GT

df = pd.read_csv('airquality.csv')

monthly_avg = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).reset_index()

month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_avg['Month'] = monthly_avg['Month'].map(month_names)

monthly_avg.columns = ['Month', 'Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

gt = (
    GT(monthly_avg)
    .fmt_number(columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=2)
    .tab_header(title='Air Quality Metrics by Month', subtitle='Average Temperature, Wind Speed, and Ozone Levels')
)

gt.gtsave("table.png")
