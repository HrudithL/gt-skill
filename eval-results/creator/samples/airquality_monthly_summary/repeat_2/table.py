import pandas as pd
from great_tables import GT, md
import great_tables.css as css

df = pd.read_csv('airquality.csv')

monthly_avg = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().reset_index()
monthly_avg.columns = ['Month', 'Temperature (°F)', 'Wind Speed (mph)', 'Ozone (ppb)']

month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_avg['Month'] = monthly_avg['Month'].map(month_names)

monthly_avg = monthly_avg.round(2)

gt = (
    GT(monthly_avg)
    .tab_header(
        title="Air Quality Metrics by Month",
        subtitle="Average temperature, wind speed, and ozone levels"
    )
    .tab_source_note("Data source: New York air quality measurements, May-September")
    .data_color(
        columns='Temperature (°F)',
        palette=['lightblue', 'yellow', 'red'],
        domain=[monthly_avg['Temperature (°F)'].min(), monthly_avg['Temperature (°F)'].max()]
    )
    .data_color(
        columns='Ozone (ppb)',
        palette=['lightyellow', 'red'],
        domain=[monthly_avg['Ozone (ppb)'].min(), monthly_avg['Ozone (ppb)'].max()]
    )
)

gt.gtsave('table.png')
