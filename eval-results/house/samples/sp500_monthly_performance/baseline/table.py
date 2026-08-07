import pandas as pd
from datetime import datetime
import great_tables as gt

# Read the CSV file
df = pd.read_csv('sp500.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Sort by date ascending (since the CSV appears to be in reverse chronological order)
df = df.sort_values('date').reset_index(drop=True)

# Calculate daily gain/loss
df['daily_change'] = df['close'] - df['open']
df['daily_gain_pct'] = (df['daily_change'] / df['open']) * 100

# Group by year and month
df['year_month'] = df['date'].dt.to_period('M')

# Aggregate monthly statistics
monthly_stats = []

for period, group in df.groupby('year_month'):
    year_month_str = str(period)

    # Opening price (first trading day of month)
    open_price = group.iloc[0]['open']

    # Closing price (last trading day of month)
    close_price = group.iloc[-1]['close']

    # Percent change
    pct_change = ((close_price - open_price) / open_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Highest daily gain (in absolute price terms)
    max_daily_gain = group['daily_change'].max()

    # Highest daily loss (in absolute price terms, shown as negative)
    min_daily_loss = group['daily_change'].min()

    monthly_stats.append({
        'Month': year_month_str,
        'Open': open_price,
        'Close': close_price,
        'Month % Change': pct_change,
        'Avg Daily Volume': avg_volume,
        'Max Daily Gain': max_daily_gain,
        'Max Daily Loss': min_daily_loss
    })

# Create DataFrame
result_df = pd.DataFrame(monthly_stats)

# Create the table
gt_table = (
    gt.GT(result_df)
    .fmt_number(columns=['Open', 'Close'], decimals=2)
    .fmt_number(columns=['Month % Change'], decimals=2)
    .fmt_number(columns=['Max Daily Gain', 'Max Daily Loss'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010-2015'
    )
    .tab_options(
        table_width='100%'
    )
)

# Save as PNG
gt_table.gtsave('table.png')
print("Table saved to table.png")
