"""S&P 500 Monthly Performance Summary (2010–2015)"""

import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
import sys

# Add skill helpers to path
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, finalize, humanize_labels, heatmap, stripe, stub_tint

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Filter to 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Create monthly summary
df['year_month'] = df['date'].dt.to_period('M')
grouped = df.groupby('year_month')

monthly_data = []
for period, group in grouped:
    group = group.sort_values('date')
    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_daily_volume = group['volume'].mean()

    # Calculate daily changes (day-over-day)
    daily_changes = group['close'].pct_change() * 100
    highest_single_day_gain = daily_changes.max()
    highest_single_day_loss = daily_changes.min()

    monthly_data.append({
        'month': period.strftime('%b %Y'),
        'opening_price': opening_price,
        'closing_price': closing_price,
        'percent_change': percent_change,
        'avg_daily_volume': avg_daily_volume,
        'highest_daily_gain': highest_single_day_gain,
        'highest_daily_loss': highest_single_day_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Build the table
gt = (
    GT(monthly_df, rowname_col='month')
    .tab_header(
        title='S&P 500 Monthly Performance',
        subtitle=md('Monthly summary statistics from 2010 through 2015'),
    )
    .tab_stubhead(label='Month')
    .fmt_currency(columns=['opening_price', 'closing_price'], decimals=2)
    .fmt_number(columns='percent_change', decimals=2)
    .fmt_number(columns='avg_daily_volume', decimals=0, use_seps=True)
    .fmt_number(columns=['highest_daily_gain', 'highest_daily_loss'], decimals=2)
    .sub_missing(columns=['highest_daily_gain', 'highest_daily_loss'], missing_text='—')
)

gt = humanize_labels(
    gt,
    monthly_df,
    overrides={
        'opening_price': 'Opening Price',
        'closing_price': 'Closing Price',
        'percent_change': 'Monthly Change',
        'avg_daily_volume': 'Avg Daily Volume',
        'highest_daily_gain': 'Highest Daily Gain',
        'highest_daily_loss': 'Highest Daily Loss',
    },
)

# Color percent change (diverging measure: positive=good)
gt = heatmap(gt, 'percent_change', kind='diverging', hue='default')

# Row hairlines
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color=PALETTE['neutral']['hairline'],
    table_body_hlines_width='1px',
)

# Heading band with navy tint (matching the Blue heatmap)
gt = gt.tab_options(
    column_labels_background_color='#C9E0F0',
    column_labels_border_bottom_color=PALETTE['neutral']['column_label_rule'],
    column_labels_border_bottom_width='2px',
    column_labels_border_bottom_style='solid',
)

# Stub tint
gt = stub_tint(gt, hue='navy')

# Row striping
gt = stripe(gt)

# Frame
gt = frame(gt)

# Source note
gt = gt.tab_source_note(
    source_note='Source: S&P 500 daily price data. Percent change is calculated as (closing - opening) / opening. Daily gains/losses represent the highest single-day percentage changes within each month.'
)

# Render
finalize(gt, path='table.png', zoom=2.0, expand=15)
