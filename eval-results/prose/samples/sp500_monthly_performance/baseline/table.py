import pandas as pd
import numpy as np
from great_tables import GT, md
from great_tables.data import exibble

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['daily_gain'] = df['high'] - df['open']
df['daily_loss'] = df['open'] - df['low']

filtered = df[(df['year'] >= 2010) & (df['year'] <= 2015)]

monthly_data = []
for (year, month), group in filtered.groupby(['year', 'month']):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    pct_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = group['volume'].mean()

    highest_gain = group['daily_gain'].max()
    highest_loss = group['daily_loss'].max()

    month_label = pd.Timestamp(year=year, month=month, day=1).strftime('%B %Y')

    monthly_data.append({
        'Month': month_label,
        'Opening_Price': opening_price,
        'Closing_Price': closing_price,
        'Percent_Change': pct_change,
        'Avg_Daily_Volume': avg_volume,
        'Highest_Single_Day_Gain': highest_gain,
        'Highest_Single_Day_Loss': highest_loss,
    })

summary_df = pd.DataFrame(monthly_data)

gt = (
    GT(summary_df)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010 - 2015"
    )
    .fmt_currency(
        columns=['Opening_Price', 'Closing_Price', 'Highest_Single_Day_Gain', 'Highest_Single_Day_Loss'],
        currency='USD'
    )
    .fmt_number(
        columns=['Percent_Change'],
        decimals=2
    )
    .fmt_number(
        columns=['Avg_Daily_Volume'],
        decimals=0
    )
    .cols_label(
        Month="Month",
        Opening_Price="Opening Price",
        Closing_Price="Closing Price",
        Percent_Change="% Change",
        Avg_Daily_Volume="Avg Daily Volume",
        Highest_Single_Day_Gain="Highest Single-Day Gain",
        Highest_Single_Day_Loss="Highest Single-Day Loss"
    )
    .opt_align_table_header('center')
)

gt.gtsave('table.png')
