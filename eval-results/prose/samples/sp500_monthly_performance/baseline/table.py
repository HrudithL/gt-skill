import pandas as pd
from great_tables import GT
from datetime import datetime
import os

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values('date')

monthly_stats = []

for year_month, group in df_filtered.groupby(df_filtered['date'].dt.to_period('M')):
    group = group.sort_values('date')

    open_price = group.iloc[0]['open']
    close_price = group.iloc[-1]['close']
    pct_change = ((close_price - open_price) / open_price) * 100

    avg_volume = group['volume'].mean()

    daily_changes = group['close'].diff()
    highest_gain = daily_changes.max()
    highest_loss = daily_changes.min()

    monthly_stats.append({
        'Month': year_month.strftime('%Y-%m'),
        'Opening Price': open_price,
        'Closing Price': close_price,
        'Percent Change (%)': pct_change,
        'Avg Daily Volume': avg_volume,
        'Highest Single-Day Gain': highest_gain,
        'Highest Single-Day Loss': highest_loss,
    })

monthly_df = pd.DataFrame(monthly_stats)

gt = (
    GT(monthly_df)
    .fmt_number(columns=['Opening Price', 'Closing Price'], decimals=2)
    .fmt_number(columns=['Percent Change (%)'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .fmt_number(columns=['Highest Single-Day Gain', 'Highest Single-Day Loss'], decimals=2)
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Showing opening/closing prices, monthly percent change, average daily volume, and highest single-day gains/losses'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
