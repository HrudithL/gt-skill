import pandas as pd
from great_tables import GT
from datetime import datetime

# Read the CSV file
df = pd.read_csv('sp500.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
start_date = pd.to_datetime('2010-01-01')
end_date = pd.to_datetime('2015-12-31')
df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()

# Sort by date (ascending)
df = df.sort_values('date').reset_index(drop=True)

# Group by year and month
df['year_month'] = df['date'].dt.to_period('M')

# Create monthly summary
monthly_data = []

for period, group in df.groupby('year_month'):
    year_month_str = str(period)  # YYYY-MM format

    # Get opening and closing prices
    opening = group.iloc[0]['open']
    closing = group.iloc[-1]['close']

    # Calculate percent change
    pct_change = ((closing - opening) / opening) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Highest single-day gain (high - low) and loss within the month
    daily_change = group['high'] - group['low']
    max_daily_gain = daily_change.max()
    min_daily_loss = -daily_change.max()  # Negative to show as loss

    monthly_data.append({
        'Month': year_month_str,
        'Opening': opening,
        'Closing': closing,
        'Pct Change': pct_change,
        'Avg Daily Volume': avg_volume,
        'Max Daily Gain': max_daily_gain,
        'Max Daily Loss': -max_daily_gain
    })

summary_df = pd.DataFrame(monthly_data)

# Create the GT table
gt = (
    GT(summary_df)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010 - 2015"
    )
    .fmt_number(
        columns=['Opening', 'Closing', 'Max Daily Gain', 'Max Daily Loss'],
        decimals=2
    )
    .fmt_number(
        columns=['Pct Change'],
        decimals=2
    )
    .fmt_integer(
        columns=['Avg Daily Volume']
    )
    .tab_options(
        container_width='100%'
    )
)

gt.gtsave('table.png')
print("Table saved to table.png")
