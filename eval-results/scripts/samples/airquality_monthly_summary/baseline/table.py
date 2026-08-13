import pandas as pd
from great_tables import GT

df = pd.read_csv('./airquality.csv')

monthly_avg = df.groupby('Month')[['Ozone', 'Wind', 'Temp']].mean()

month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}

monthly_avg['Month'] = monthly_avg.index.map(month_names)
monthly_avg = monthly_avg[['Month', 'Ozone', 'Wind', 'Temp']].reset_index(drop=True)

gt = (
    GT(monthly_avg)
    .fmt_number(columns=['Ozone', 'Wind', 'Temp'], decimals=2)
    .tab_header(
        title='Monthly Air Quality Summary',
        subtitle='Average Temperature, Wind Speed, and Ozone Levels'
    )
    .cols_label(
        Month='Month',
        Ozone='Ozone (ppb)',
        Wind='Wind Speed (mph)',
        Temp='Temperature (°F)'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
