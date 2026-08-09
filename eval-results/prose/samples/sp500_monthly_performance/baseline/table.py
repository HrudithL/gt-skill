import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Read the data
df = pd.read_csv('sp500.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Sort by date ascending
df = df.sort_values('date').reset_index(drop=True)

# Group by year-month
df['year_month'] = df['date'].dt.to_period('M')

# Calculate monthly metrics
monthly_data = []

for period, group in df.groupby('year_month'):
    year, month = period.year, period.month

    # Opening price (first day of month)
    opening_price = group.iloc[0]['open']

    # Closing price (last day of month)
    closing_price = group.iloc[-1]['close']

    # Percent change
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Daily percent changes
    group['daily_pct_change'] = ((group['close'] - group['open']) / group['open']) * 100

    # Highest single-day gain
    max_gain = group['daily_pct_change'].max()

    # Highest single-day loss (most negative)
    max_loss = group['daily_pct_change'].min()

    monthly_data.append({
        'Month': str(period),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': pct_change,
        'Avg Daily Volume': avg_volume,
        'Highest Single-Day Gain': max_gain,
        'Highest Single-Day Loss': max_loss,
    })

result_df = pd.DataFrame(monthly_data)

# Create the GT table
gt = (
    GT(result_df)
    .fmt_currency(columns=['Opening Price', 'Closing Price'], currency='USD')
    .fmt_number(columns=['Percent Change', 'Highest Single-Day Gain', 'Highest Single-Day Loss'], decimals=2)
    .fmt_integer(columns=['Avg Daily Volume'])
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Monthly OHLC data with daily volume and intra-month extremes'
    )
)

gt.gtsave('table.png')
