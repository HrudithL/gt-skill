import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Load the S&P 500 data
df = pd.read_csv('sp500.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Get the date range
start_date = df['date'].min()
end_date = df['date'].max()

# Calculate 5-year statistics
earliest_close = df.iloc[0]['close']
latest_close = df.iloc[-1]['close']
highest_close = df['close'].max()
lowest_close = df['close'].min()
avg_close = df['close'].mean()
avg_volume = df['volume'].mean()

# Calculate total return percentage
total_return_pct = ((latest_close - earliest_close) / earliest_close) * 100

# Calculate yearly statistics
df['year'] = df['date'].dt.year
yearly_stats = []

for year in sorted(df['year'].unique()):
    year_data = df[df['year'] == year]
    year_start = year_data.iloc[0]['close']
    year_end = year_data.iloc[-1]['close']
    year_high = year_data['close'].max()
    year_low = year_data['close'].min()
    year_return = ((year_end - year_start) / year_start) * 100

    yearly_stats.append({
        'Year': str(year),
        'Year Start': year_start,
        'Year End': year_end,
        'High': year_high,
        'Low': year_low,
        'Return %': year_return,
        'Avg Daily Volume (M)': year_data['volume'].mean() / 1_000_000
    })

# Create summary statistics table
summary_data = {
    'Metric': [
        'Period Start Date',
        'Period End Date',
        'Starting Close',
        'Ending Close',
        '5-Year Total Return %',
        'Highest Close',
        'Lowest Close',
        'Average Close',
        'Avg Daily Volume (M)'
    ],
    'Value': [
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d'),
        f'${earliest_close:,.2f}',
        f'${latest_close:,.2f}',
        f'{total_return_pct:.2f}%',
        f'${highest_close:,.2f}',
        f'${lowest_close:,.2f}',
        f'${avg_close:,.2f}',
        f'{avg_volume / 1_000_000:,.1f}'
    ]
}

summary_df = pd.DataFrame(summary_data)

# Create yearly statistics table
yearly_df = pd.DataFrame(yearly_stats)

# Build the summary table with great_tables
gt_summary = (
    GT(summary_df)
    .tab_header(
        title="S&P 500 Overview",
        subtitle=f"5-Year Summary ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
    )
    .cols_label(
        Metric="Metric",
        Value="Value"
    )
    .tab_options(
        table_font_size="11pt",
        column_labels_font_weight="bold"
    )
)

gt_summary.gtsave('table.png')

print("✓ Summary table created successfully")
print(f"  - Data range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"  - Total return: {total_return_pct:.2f}%")
print(f"  - Starting close: ${earliest_close:,.2f}")
print(f"  - Ending close: ${latest_close:,.2f}")
