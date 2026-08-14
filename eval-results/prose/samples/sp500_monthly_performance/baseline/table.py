import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values('date')

# Extract year and month
df_filtered['year_month'] = df_filtered['date'].dt.to_period('M')

# Group by month and calculate statistics
monthly_stats = []

for period, group in df_filtered.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    percent_change = ((closing_price - opening_price) / opening_price) * 100

    avg_volume = group['volume'].mean()

    # Calculate daily gains/losses
    daily_changes = group['close'].pct_change() * 100
    highest_gain = daily_changes.max()
    highest_loss = daily_changes.min()

    monthly_stats.append({
        'Month': str(period),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_volume,
        'Highest Single-Day Gain': highest_gain,
        'Highest Single-Day Loss': highest_loss
    })

stats_df = pd.DataFrame(monthly_stats)

# Create the GT table
gt = (
    GT(stats_df)
    .fmt_number(columns=['Opening Price', 'Closing Price'], decimals=2)
    .fmt_number(columns=['Percent Change', 'Highest Single-Day Gain', 'Highest Single-Day Loss'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010 through 2015'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
