import pandas as pd
import numpy as np
from great_tables import GT
from great_tables.data import exibble

df = pd.read_csv('./sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df = df.sort_values('date').reset_index(drop=True)

df['daily_gain'] = df['high'] - df['low']
df['daily_loss'] = df['open'] - df['close']

monthly_data = []

for year in range(2010, 2016):
    for month in range(1, 13):
        month_df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]

        if len(month_df) == 0:
            continue

        opening = month_df.iloc[0]['open']
        closing = month_df.iloc[-1]['close']
        percent_change = ((closing - opening) / opening) * 100
        avg_volume = month_df['volume'].mean()
        max_daily_gain = month_df['daily_gain'].max()
        max_daily_loss = month_df['daily_loss'].max()

        monthly_data.append({
            'Date': f"{year}-{month:02d}",
            'Open': opening,
            'Close': closing,
            'Percent Change': percent_change,
            'Avg Daily Volume': avg_volume,
            'Max Daily Gain': max_daily_gain,
            'Max Daily Loss': max_daily_loss
        })

monthly_df = pd.DataFrame(monthly_data)

gt = (
    GT(monthly_df)
    .fmt_number(
        columns=['Open', 'Close'],
        decimals=2
    )
    .fmt_number(
        columns=['Percent Change'],
        decimals=2,
        pattern='{x}%'
    )
    .fmt_number(
        columns=['Avg Daily Volume'],
        decimals=0
    )
    .fmt_number(
        columns=['Max Daily Gain', 'Max Daily Loss'],
        decimals=2
    )
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)'
    )
)

gt.gtsave("table.png")
