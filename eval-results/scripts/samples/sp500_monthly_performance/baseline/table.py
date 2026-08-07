import pandas as pd
from great_tables import GT
from datetime import datetime
import numpy as np

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'] >= '2010-01-01') & (df['date'] <= '2015-12-31')].copy()
df = df.sort_values('date').reset_index(drop=True)

# Group by year-month and calculate monthly statistics
df['year_month'] = df['date'].dt.to_period('M')
monthly_data = []

for period, group in df.groupby('year_month'):
    group = group.sort_values('date')

    # Opening price (first day of month)
    opening = group.iloc[0]['open']

    # Closing price (last day of month)
    closing = group.iloc[-1]['close']

    # Percent change
    pct_change = ((closing - opening) / opening) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Daily gains and losses
    group['daily_change'] = group['close'] - group['open']
    max_gain = group['daily_change'].max()
    max_loss = group['daily_change'].min()

    monthly_data.append({
        'Month': str(period),
        'Open': opening,
        'Close': closing,
        'Change %': pct_change,
        'Avg Daily Volume': avg_volume,
        'Max Gain': max_gain,
        'Max Loss': max_loss,
    })

result_df = pd.DataFrame(monthly_data)

# Create GT table
gt = (
    GT(result_df)
    .fmt_number(columns=['Open', 'Close', 'Max Gain', 'Max Loss'], decimals=2)
    .fmt_number(columns=['Change %'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Opening price, closing price, percent change, average daily volume, and daily extremes by month'
    )
    .tab_stubhead(label='Month')
)

# Save the table
gt.gtsave('table.png')
print("Table saved to table.png")
