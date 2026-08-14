import pandas as pd
from great_tables import GT
from datetime import datetime

# Read the CSV file
df = pd.read_csv('sp500.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()

# Add daily change calculation
df_filtered['daily_change'] = df_filtered['high'] - df_filtered['low']

# Sort by date ascending for grouping
df_filtered = df_filtered.sort_values('date')

# Group by year-month
monthly_data = []
for year_month, group in df_filtered.groupby(df_filtered['date'].dt.to_period('M')):
    opening = group.iloc[-1]['open']  # Last row (earliest date) is the opening
    closing = group.iloc[0]['close']  # First row (latest date) is the closing
    pct_change = ((closing - opening) / opening) * 100
    avg_volume = group['volume'].mean()

    # Find highest daily gain and loss in the month
    max_daily_gain = group['daily_change'].max()
    min_daily_loss = -(group['daily_change'].max())  # Make it negative

    # Actually, we need to find the largest single-day move
    # Create daily returns
    group_sorted = group.sort_values('date')
    group_sorted['daily_return'] = group_sorted['close'].diff() / group_sorted['open'].shift()
    max_gain_pct = group_sorted['daily_return'].max() * 100
    max_loss_pct = group_sorted['daily_return'].min() * 100

    monthly_data.append({
        'Month': year_month.strftime('%B %Y'),
        'Open': opening,
        'Close': closing,
        'Change %': pct_change,
        'Avg Volume': avg_volume,
        'Max Daily Gain %': max_gain_pct,
        'Max Daily Loss %': max_loss_pct,
    })

# Create DataFrame
summary_df = pd.DataFrame(monthly_data)

# Create GT table
gt = (
    GT(summary_df)
    .fmt_currency(columns=['Open', 'Close'], currency='USD')
    .fmt_number(columns=['Change %', 'Max Daily Gain %', 'Max Daily Loss %'], decimals=2)
    .fmt_number(columns=['Avg Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010–2015'
    )
)

# Save to PNG
gt.gtsave('table.png')
print("Table saved to table.png")
