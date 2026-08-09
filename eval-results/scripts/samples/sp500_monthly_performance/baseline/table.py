import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter to 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Sort by date ascending for easier processing
df = df.sort_values('date').reset_index(drop=True)

# Group by year-month
df['year_month'] = df['date'].dt.to_period('M')

# Calculate monthly metrics
monthly_stats = []

for period, group in df.groupby('year_month'):
    # Opening and closing prices
    open_price = group.iloc[0]['open']
    close_price = group.iloc[-1]['close']

    # Percent change
    pct_change = ((close_price - open_price) / open_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Daily returns (close to close)
    group_sorted = group.sort_values('date').reset_index(drop=True)
    daily_returns = group_sorted['close'].pct_change() * 100

    # Highest single-day gain and loss
    highest_gain = daily_returns.max()
    highest_loss = daily_returns.min()

    monthly_stats.append({
        'Month': str(period),
        'Open': open_price,
        'Close': close_price,
        'Change %': pct_change,
        'Avg Volume': avg_volume,
        'Best Day %': highest_gain,
        'Worst Day %': highest_loss
    })

result_df = pd.DataFrame(monthly_stats)

# Create the table
gt = (
    GT(result_df)
    .fmt_number(
        columns=['Open', 'Close'],
        decimals=2
    )
    .fmt_number(
        columns=['Change %', 'Best Day %', 'Worst Day %'],
        decimals=2
    )
    .fmt_number(
        columns=['Avg Volume'],
        decimals=0
    )
    .tab_header(
        title='S&P 500 Monthly Performance (2010-2015)',
        subtitle='Summary statistics: opening price, closing price, monthly change, average daily volume, and best/worst day'
    )
    .cols_label(
        Month='Month',
        Open='Open ($)',
        Close='Close ($)',
        **{'Change %': 'Change (%)', 'Avg Volume': 'Avg Daily Volume', 'Best Day %': 'Best Day (%)', 'Worst Day %': 'Worst Day (%)'}
    )
)

gt.gtsave('table.png')
