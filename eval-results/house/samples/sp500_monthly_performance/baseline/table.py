import pandas as pd
from great_tables import GT
from datetime import datetime

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df = df.sort_values('date')
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

monthly_data = []

for year_month, group in df.groupby(df['date'].dt.to_period('M')):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = group['volume'].mean()

    daily_changes = group['close'] - group['open']
    highest_gain = daily_changes.max()
    highest_loss = daily_changes.min()

    monthly_data.append({
        'Month': str(year_month),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_volume,
        'Highest Daily Gain': highest_gain,
        'Highest Daily Loss': highest_loss,
    })

summary_df = pd.DataFrame(monthly_data)

gt = GT(summary_df)

gt = gt.fmt_currency(
    columns=['Opening Price', 'Closing Price', 'Highest Daily Gain', 'Highest Daily Loss'],
    currency='USD'
)

gt = gt.fmt_number(
    columns=['Percent Change'],
    decimals=2
)

gt = gt.fmt_integer(
    columns=['Avg Daily Volume']
)

gt = gt.tab_header(
    title='S&P 500 Monthly Performance Summary',
    subtitle='2010–2015'
)

gt = gt.cols_label(
    **{
        'Month': 'Month',
        'Opening Price': 'Open',
        'Closing Price': 'Close',
        'Percent Change': 'Change %',
        'Avg Daily Volume': 'Avg Volume',
        'Highest Daily Gain': 'Best Day',
        'Highest Daily Loss': 'Worst Day',
    }
)

gt.gtsave('table.png')
