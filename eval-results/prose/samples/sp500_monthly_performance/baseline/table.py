import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Read the S&P 500 data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Sort by date ascending for processing
df = df.sort_values('date').reset_index(drop=True)

# Group by year-month
df['year_month'] = df['date'].dt.to_period('M')

# Calculate monthly summaries
monthly_data = []

for period, group in df.groupby('year_month'):
    group = group.sort_values('date').reset_index(drop=True)

    # Get opening price (first day of month) and closing price (last day of month)
    open_price = group.iloc[0]['open']
    close_price = group.iloc[-1]['close']

    # Calculate percent change
    percent_change = ((close_price - open_price) / open_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Highest single-day gain (high - low)
    group['daily_gain'] = group['high'] - group['low']
    max_daily_gain = group['daily_gain'].max()

    # Highest single-day loss (as negative value, store as positive)
    # We'll calculate as the largest intraday drop
    group['daily_loss'] = group['high'] - group['low']
    max_daily_loss = group['daily_loss'].max()

    monthly_data.append({
        'Month': str(period),
        'Opening Price': open_price,
        'Closing Price': close_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_volume,
        'Highest Daily Gain': max_daily_gain,
        'Highest Daily Loss': max_daily_loss
    })

# Create dataframe from monthly summaries
summary_df = pd.DataFrame(monthly_data)

# Create the table with great_tables
gt = (
    GT(summary_df)
    .fmt_currency(columns=['Opening Price', 'Closing Price', 'Highest Daily Gain', 'Highest Daily Loss'], currency='USD')
    .fmt_number(columns=['Percent Change'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010 through 2015'
    )
)

# Save the table
gt.gtsave('table.png')
print("Table saved to table.png")
