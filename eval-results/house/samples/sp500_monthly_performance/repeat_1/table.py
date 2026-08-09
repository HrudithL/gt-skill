import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
import sys
sys.path.insert(0, '.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, finalize, heatmap

# Read and parse data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Create year-month column for grouping
df['year_month'] = df['date'].dt.to_period('M')

# Calculate daily return percentage for each row
df['daily_return_pct'] = ((df['close'] - df['open']) / df['open']) * 100

# Group by month and calculate metrics
monthly_stats = []
for period, group in df.groupby('year_month'):
    year_month = period.to_timestamp()
    year = year_month.year
    month = year_month.month

    # Skip if not in 2010-2015
    if year < 2010 or year > 2015:
        continue

    # Find first and last trading days
    first_day = group.iloc[0]
    last_day = group.iloc[-1]

    # Opening and closing prices
    open_price = first_day['open']
    close_price = last_day['close']

    # Monthly percent change
    monthly_return = ((close_price - open_price) / open_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Highest single-day gain and loss
    daily_returns = group['daily_return_pct']
    highest_gain = daily_returns.max()
    highest_loss = daily_returns.min()

    monthly_stats.append({
        'Year_Month': year_month.strftime('%B %Y'),
        'Open': open_price,
        'Close': close_price,
        'Monthly_Return_%': monthly_return,
        'Avg_Daily_Volume': avg_volume,
        'Highest_Gain_%': highest_gain,
        'Highest_Loss_%': highest_loss,
    })

# Create DataFrame
summary_df = pd.DataFrame(monthly_stats)

# Create GT table
gt = (
    GT(summary_df, rowname_col='Year_Month')
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010 – 2015'
    )
    .cols_label(
        Year_Month='Month',
        Open='Opening Price',
        Close='Closing Price',
        **{'Monthly_Return_%': 'Monthly Return (%)',
           'Avg_Daily_Volume': 'Avg Daily Volume',
           'Highest_Gain_%': 'Highest Daily Gain (%)',
           'Highest_Loss_%': 'Highest Daily Loss (%)'}
    )
    .fmt_number(
        columns=['Open', 'Close'],
        decimals=2,
    )
    .fmt_number(
        columns=['Monthly_Return_%', 'Highest_Gain_%', 'Highest_Loss_%'],
        decimals=2,
    )
    .fmt_number(
        columns=['Avg_Daily_Volume'],
        decimals=0,
    )
    .tab_options(
        table_body_hlines_style='solid',
    )
)

# Color the monthly return (diverging) and highest daily gain (sequential)
gt = heatmap(
    gt,
    columns=['Monthly_Return_%'],
    kind='diverging',
    hue='default',
)

gt = heatmap(
    gt,
    columns=['Highest_Gain_%'],
    kind='sequential',
    hue='positive',
)

# Add source notes
gt = (
    gt
    .tab_source_note('Source: S&P 500 daily price data.')
    .tab_source_note('Daily gain/loss: percentage change from opening to closing price within each trading day.')
)

# Finalize with frame and save
frame(gt)
finalize(gt, path='table.png', zoom=2.0, expand=15)
