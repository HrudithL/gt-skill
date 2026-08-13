import pandas as pd
import numpy as np
from great_tables import GT

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df = df.sort_values('date').reset_index(drop=True)

df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

df['year_month'] = df['date'].dt.to_period('M')

monthly_data = []

for period in sorted(df['year_month'].unique()):
    month_df = df[df['year_month'] == period].reset_index(drop=True)

    if len(month_df) == 0:
        continue

    opening_price = month_df.iloc[0]['open']
    closing_price = month_df.iloc[-1]['close']
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    avg_volume = month_df['volume'].mean()

    daily_change = month_df['high'] - month_df['low']
    highest_gain = daily_change.max()
    highest_loss = -daily_change.min()

    monthly_data.append({
        'Month': str(period),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': pct_change,
        'Avg Daily Volume': avg_volume,
        'Highest Single-Day Gain': highest_gain,
        'Highest Single-Day Loss': highest_loss,
    })

result_df = pd.DataFrame(monthly_data)

gt = (
    GT(result_df)
    .fmt_currency(columns=['Opening Price', 'Closing Price'], currency='USD')
    .fmt_number(columns=['Percent Change'], decimals=2)
    .fmt_integer(columns=['Avg Daily Volume'])
    .fmt_currency(columns=['Highest Single-Day Gain', 'Highest Single-Day Loss'], currency='USD')
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010 through 2015'
    )
)

gt.gtsave('table.png')
