import pandas as pd
import numpy as np
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)
from great_tables import GT, loc

# Read and prepare data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]
df = df.sort_values('date').reset_index(drop=True)

# Group by year-month and calculate monthly metrics
df['year_month'] = df['date'].dt.to_period('M')
monthly = df.groupby('year_month').agg(
    open_price=('open', 'first'),
    close_price=('close', 'last'),
    high=('high', 'max'),
    low=('low', 'min'),
    volume=('volume', 'mean'),
).reset_index()

# Calculate percent change and daily gains/losses
monthly['pct_change'] = ((monthly['close_price'] - monthly['open_price']) /
                         monthly['open_price'])

# For each month, get the highest single-day gain and loss
def get_daily_extremes(group):
    group = group.sort_values('date')
    group['daily_change'] = group['close'].diff()
    daily_gain = group['daily_change'].max()
    daily_loss = group['daily_change'].min()
    return pd.Series({
        'highest_daily_gain': daily_gain if pd.notna(daily_gain) else 0,
        'largest_daily_loss': daily_loss if pd.notna(daily_loss) else 0,
    })

daily_extremes = df.groupby('year_month').apply(get_daily_extremes).reset_index()
monthly = monthly.merge(daily_extremes, on='year_month')

# Create display columns
monthly['month_label'] = monthly['year_month'].astype(str)
monthly['avg_daily_volume'] = monthly['volume']

# Reorder and select columns
display_cols = ['month_label', 'open_price', 'close_price', 'pct_change',
                'avg_daily_volume', 'highest_daily_gain', 'largest_daily_loss']
monthly = monthly[display_cols].copy()

# Create GT table
gt = GT(
    monthly,
    rowname_col='month_label'
).tab_header(
    title='S&P 500 Monthly Performance',
    subtitle='Opening price, closing price, monthly return, and daily extremes (2010–2015)'
).tab_stubhead(label='Month').fmt_number(
    columns='open_price',
    decimals=2
).fmt_number(
    columns='close_price',
    decimals=2
).fmt_percent(
    columns='pct_change',
    decimals=2,
    force_sign=True
).fmt_number(
    columns='avg_daily_volume',
    decimals=0,
    use_seps=True
).fmt_number(
    columns='highest_daily_gain',
    decimals=2
).fmt_number(
    columns='largest_daily_loss',
    decimals=2
)

gt = humanize_labels(
    gt,
    monthly,
    overrides={
        'open_price': 'Opening Price',
        'close_price': 'Closing Price',
        'pct_change': 'Monthly Return',
        'avg_daily_volume': 'Avg Daily Volume',
        'highest_daily_gain': 'Highest Daily Gain',
        'largest_daily_loss': 'Largest Daily Loss',
    }
)

gt = gt.cols_width(
    cases={
        'month_label': '100px',
        'open_price': '110px',
        'close_price': '110px',
        'pct_change': '110px',
        'avg_daily_volume': '130px',
        'highest_daily_gain': '130px',
        'largest_daily_loss': '130px',
    }
).tab_options(
    heading_padding='6px',
    column_labels_padding='6px',
    column_labels_padding_horizontal='8px',
    data_row_padding='5px',
    data_row_padding_horizontal='8px',
    source_notes_padding='6px',
)

# Heatmap the monthly return as the primary measure (diverging, positive=good)
gt = heatmap(gt, 'pct_change', kind='diverging', hue='default')

# Add polish: striping, stub tint, band, frame, hairlines
gt = stripe(gt)
gt = stub_tint(gt, hue='navy')
gt = band(gt, hue='navy')

# Source notes
gt = gt.tab_source_note(
    source_note='Monthly Return is the percent change from opening to closing price for each month.'
).tab_source_note(
    source_note='Source: S&P 500 daily price and volume data.'
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path='table.png')
