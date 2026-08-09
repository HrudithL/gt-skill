import pandas as pd
import numpy as np
from great_tables import GT, md, loc, style
from great_tables import html
import sys
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint,
    heatmap, humanize_labels
)

# Load the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Sort by date
df = df.sort_values('date')

# Create year-month column for grouping
df['year_month'] = df['date'].dt.to_period('M')

# Aggregate by month
monthly_stats = []
for period, group in df.groupby('year_month'):
    group = group.sort_values('date')

    # Opening and closing prices (first and last trading days)
    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']

    # Percent change
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Single-day gains and losses (based on high-low within each day)
    group['daily_gain'] = group['high'] - group['open']
    group['daily_loss'] = group['open'] - group['low']

    highest_gain = group['daily_gain'].max()
    highest_loss = group['daily_loss'].max()

    monthly_stats.append({
        'month': period.strftime('%b %Y'),
        'open': opening_price,
        'close': closing_price,
        'pct_change': pct_change,
        'avg_volume': avg_volume,
        'highest_gain': highest_gain,
        'highest_loss': highest_loss,
    })

# Create DataFrame
stats_df = pd.DataFrame(monthly_stats)

# Create the GT table
gt = GT(stats_df, rowname_col='month')
gt = gt.tab_header(
    title='S&P 500 Monthly Performance Summary',
    subtitle=md('Opening, closing, and daily gains/losses from 2010–2015'),
)

# Format columns
gt = gt.fmt_currency(columns=['open', 'close'], decimals=2)
gt = gt.fmt_percent(columns='pct_change', decimals=2, scale_values=False)
gt = gt.fmt_number(columns='avg_volume', decimals=0, use_seps=True)
gt = gt.fmt_currency(columns=['highest_gain', 'highest_loss'], decimals=2)

# Apply labels
gt = humanize_labels(
    gt,
    stats_df,
    overrides={
        'open': 'Opening Price',
        'close': 'Closing Price',
        'pct_change': 'Monthly Change',
        'avg_volume': 'Avg Daily Volume',
        'highest_gain': 'Highest Daily Gain',
        'highest_loss': 'Highest Daily Loss',
    }
)

# Apply heatmap to percent change (diverging, signed measure)
gt = heatmap(gt, 'pct_change', kind='diverging', hue='default')

# Apply sequential heatmap to average volume
gt = heatmap(gt, 'avg_volume', kind='sequential', hue='neutral')

# Structural formatting
gt = band(gt, hue='navy')
if len(stats_df) >= 10:
    gt = stripe(gt)
gt = stub_tint(gt, hue='navy')
gt = hairlines(gt)
gt = frame(gt)

# Add source note
gt = gt.tab_source_note(source_note='Source: S&P 500 historical data (sp500.csv), 2010–2015.')

# Finalize and save
finalize(gt, path='table.png')
