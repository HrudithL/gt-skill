import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from datetime import datetime

# Step 1: Read and clean data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values('date')

# Calculate daily gains and losses
df_filtered['daily_gain'] = df_filtered['high'] - df_filtered['low']
df_filtered['daily_pct_change'] = ((df_filtered['close'] - df_filtered['open']) / df_filtered['open']) * 100

# Group by year-month
df_filtered['year_month'] = df_filtered['date'].dt.to_period('M')

# Aggregate monthly data
monthly = df_filtered.groupby('year_month').agg(
    opening_price=('open', 'first'),
    closing_price=('close', 'last'),
    avg_daily_volume=('volume', 'mean'),
    highest_single_day_gain=('daily_gain', 'max'),
    highest_single_day_loss=('daily_pct_change', 'min'),
).reset_index()

# Calculate percent change from open to close
monthly['pct_change'] = ((monthly['closing_price'] - monthly['opening_price']) / monthly['opening_price']) * 100

# Reorder columns
monthly = monthly[['year_month', 'opening_price', 'closing_price', 'pct_change', 'avg_daily_volume', 'highest_single_day_gain', 'highest_single_day_loss']]

# Format year_month as string for display
monthly['year_month'] = monthly['year_month'].astype(str)

# Step 2: Organize columns
# Set year_month as the stub (rowname_col)
df_table = monthly.copy()
df_table = df_table.rename(columns={
    'year_month': 'Period',
    'opening_price': 'Open',
    'closing_price': 'Close',
    'pct_change': 'Percent Change',
    'avg_daily_volume': 'Avg Daily Volume',
    'highest_single_day_gain': 'Highest Single-Day Gain',
    'highest_single_day_loss': 'Highest Single-Day Loss'
})

# Step 3: Big Color - Signed measure (pct_change) uses diverging palette
# Calculate symmetric domain for percent change
cols_colored = ['Percent Change']
lo = float(np.nanmin(df_table[cols_colored].to_numpy()))
hi = float(np.nanmax(df_table[cols_colored].to_numpy()))
M = max(abs(lo), abs(hi))

# Step 4 & 5: Build the table with formatting and styling
gt = (
    GT(df_table, rowname_col='Period')
    # Format numeric columns
    .fmt_number(columns=['Open', 'Close'], decimals=2, use_seps=True)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0, use_seps=True)
    .fmt_number(columns=['Highest Single-Day Gain'], decimals=2, use_seps=True)
    .fmt_percent(columns=['Percent Change'], decimals=2, scale_values=False, force_sign=True)
    .fmt_number(columns=['Highest Single-Day Loss'], decimals=2)
    # Step 3: Data color for signed measure
    .data_color(
        columns=['Percent Change'],
        palette='RdYlGn',
        domain=[-M, M],
        truncate=False,
    )
    # Step 5a: Cell borders
    .tab_options(
        table_body_hlines_style='solid',
        table_body_hlines_color='#E8E8E8',
        table_body_hlines_width='1px',
        column_labels_border_bottom_color='#CCCCCC',
        column_labels_border_bottom_width='2px',
    )
    # Step 5d: Stub tint (light blue-tinted for Navy/Blues palette)
    .tab_style(
        style=style.fill(color='#EAF0F6'),
        locations=loc.stub(),
    )
    # Step 5c: Row striping (≥10 rows and not heavily colored)
    .opt_row_striping()
    .tab_options(row_striping_background_color='#F6F6F6')
    # Step 4: Heading band (light tint for Big Color presence)
    .tab_options(
        column_labels_background_color='#EAF0F6',
        heading_background_color='#EAF0F6',
    )
    # Step 5: Frame border
    .tab_options(
        table_border_top_style='solid',
        table_border_top_color='#CCCCCC',
        table_border_top_width='1px',
        table_border_bottom_style='solid',
        table_border_bottom_color='#CCCCCC',
        table_border_bottom_width='1px',
        table_border_left_style='solid',
        table_border_left_color='#CCCCCC',
        table_border_left_width='1px',
        table_border_right_style='solid',
        table_border_right_color='#CCCCCC',
        table_border_right_width='1px',
    )
    # Step 6: Titles and footer notes
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Opening/closing prices, percent change, volume, and daily extremes by month'
    )
    .tab_source_note(source_note='Percent change calculated from monthly open to close. Highest single-day gain is the maximum intraday range (high - low); highest single-day loss is the minimum daily percent change.')
    .tab_source_note(source_note='Source: S&P 500 historical data')
)

# Step 7: Render
gt.gtsave('table.png', expand=15)
