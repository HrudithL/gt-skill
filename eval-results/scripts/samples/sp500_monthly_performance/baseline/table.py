import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Load the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Sort by date ascending
df_filtered = df_filtered.sort_values('date').reset_index(drop=True)

# Calculate daily gains/losses
df_filtered['daily_gain_loss'] = df_filtered['close'] - df_filtered['open']

# Group by year-month
df_filtered['year_month'] = df_filtered['date'].dt.to_period('M')

# Create monthly summary
monthly_summary = []

for period, group in df_filtered.groupby('year_month'):
    year, month = period.year, period.month

    opening_price = group['open'].iloc[0]
    closing_price = group['close'].iloc[-1]
    percent_change = ((closing_price - opening_price) / opening_price) * 100

    avg_daily_volume = group['volume'].mean()

    # Find highest daily gain and loss
    highest_gain = group['daily_gain_loss'].max()
    highest_loss = group['daily_gain_loss'].min()

    monthly_summary.append({
        'Month': period.strftime('%Y-%m'),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_daily_volume,
        'Highest Daily Gain': highest_gain,
        'Highest Daily Loss': highest_loss
    })

# Convert to DataFrame
summary_df = pd.DataFrame(monthly_summary)

# Create the GT table
gt = (GT(summary_df)
    .fmt_number(
        columns=['Opening Price', 'Closing Price'],
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
        columns=['Highest Daily Gain', 'Highest Daily Loss'],
        decimals=2
    )
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010-2015'
    )
)

gt.gtsave('table.png')
