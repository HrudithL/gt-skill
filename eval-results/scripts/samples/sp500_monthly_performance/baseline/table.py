import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]
df = df.sort_values('date')

monthly_data = []

for year in range(2010, 2016):
    for month in range(1, 13):
        month_df = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]

        if len(month_df) == 0:
            continue

        month_df_sorted = month_df.sort_values('date')

        opening_price = month_df_sorted.iloc[0]['open']
        closing_price = month_df_sorted.iloc[-1]['close']
        percent_change = ((closing_price - opening_price) / opening_price) * 100

        avg_daily_volume = month_df['volume'].mean()

        daily_changes = month_df_sorted['close'].diff()
        highest_gain = daily_changes.max()
        highest_loss = daily_changes.min()

        month_name = datetime(year, month, 1).strftime('%B %Y')

        monthly_data.append({
            'Month': month_name,
            'Opening Price': opening_price,
            'Closing Price': closing_price,
            'Percent Change': percent_change,
            'Avg Daily Volume': avg_daily_volume,
            'Highest Daily Gain': highest_gain,
            'Highest Daily Loss': highest_loss
        })

summary_df = pd.DataFrame(monthly_data)

gt = (
    GT(summary_df)
    .fmt_currency(columns=['Opening Price', 'Closing Price', 'Highest Daily Gain', 'Highest Daily Loss'], currency='USD')
    .fmt_number(columns=['Percent Change'], decimals=2, pattern='{x}%')
    .fmt_integer(columns=['Avg Daily Volume'])
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Opening & closing prices, monthly percent change, average daily volume, and extreme daily movements'
    )
    .tab_options(
        table_font_size='14px',
        heading_title_font_size='18px'
    )
)

gt.gtsave('table.png')
