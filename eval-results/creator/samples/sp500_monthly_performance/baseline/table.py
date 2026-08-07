import pandas as pd
from great_tables import GT
from datetime import datetime

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for years 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df = df.sort_values('date').reset_index(drop=True)

# Create monthly grouping
df['year_month'] = df['date'].dt.to_period('M')

# Calculate monthly metrics
monthly_data = []

for period, group in df.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_daily_volume = group['volume'].mean()

    # Calculate daily returns to find highest gain and loss
    group['daily_return'] = ((group['close'] - group['open']) / group['open']) * 100
    highest_gain = group['daily_return'].max()
    highest_loss = group['daily_return'].min()

    monthly_data.append({
        'Month': str(period),
        'Open': opening_price,
        'Close': closing_price,
        'Pct Change': percent_change,
        'Avg Daily Volume': avg_daily_volume,
        'Highest Daily Gain': highest_gain,
        'Highest Daily Loss': highest_loss
    })

summary_df = pd.DataFrame(monthly_data)

# Create the table
gt = (
    GT(summary_df)
    .fmt_number(columns=['Open', 'Close'], decimals=2)
    .fmt_number(columns=['Pct Change', 'Highest Daily Gain', 'Highest Daily Loss'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010-2015 Monthly Metrics'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
