import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from datetime import datetime

# Load the S&P 500 data
df = pd.read_csv('sp500.csv')

# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort by date ascending
df = df.sort_values('date').reset_index(drop=True)

# Extract year from date
df['year'] = df['date'].dt.year

# Get the last date in the dataset
last_date = df['date'].max()
# Filter for past 5 years (approximately 1825 days)
cutoff_date = last_date - pd.Timedelta(days=5*365)
df_filtered = df[df['date'] >= cutoff_date].copy()

# Get unique years and sort them
years = sorted(df_filtered['year'].unique())

# Create summary table by year
summary_data = []

for year in years:
    year_data = df_filtered[df_filtered['year'] == year]

    # Get first and last close prices for the year
    first_close = year_data['close'].iloc[0]
    last_close = year_data['close'].iloc[-1]

    # Calculate yearly metrics
    yearly_return = ((last_close - first_close) / first_close) * 100
    yearly_high = year_data['high'].max()
    yearly_low = year_data['low'].min()
    avg_volume = year_data['volume'].mean() / 1e9  # Convert to billions

    summary_data.append({
        'Year': year,
        'Opening': first_close,
        'Closing': last_close,
        'High': yearly_high,
        'Low': yearly_low,
        'Return %': yearly_return,
        'Avg Volume (B)': avg_volume
    })

summary_df = pd.DataFrame(summary_data)

# Determine year range for subtitle
year_start = summary_df['Year'].min()
year_end = summary_df['Year'].max()

# Create the GT table
gt = (
    GT(summary_df)
    .tab_header(
        title="S&P 500 Five-Year Overview",
        subtitle=f"Annual Summary Statistics ({year_start}-{year_end})"
    )
    .fmt_number(
        columns=['Opening', 'Closing', 'High', 'Low'],
        decimals=2
    )
    .fmt_number(
        columns=['Return %'],
        decimals=2
    )
    .fmt_number(
        columns=['Avg Volume (B)'],
        decimals=2
    )
)

# Apply conditional styling for positive returns (green)
positive_rows = [i for i, row in enumerate(summary_df['Return %']) if row > 0]
if positive_rows:
    gt = gt.tab_style(
        style=style.fill(color='#e8f5e9'),
        locations=loc.body(rows=positive_rows)
    )
    gt = gt.tab_style(
        style=style.text(color='#1b5e20', weight='bold'),
        locations=loc.body(rows=positive_rows, columns=['Return %'])
    )

# Apply conditional styling for negative returns (red)
negative_rows = [i for i, row in enumerate(summary_df['Return %']) if row < 0]
if negative_rows:
    gt = gt.tab_style(
        style=style.fill(color='#ffebee'),
        locations=loc.body(rows=negative_rows)
    )
    gt = gt.tab_style(
        style=style.text(color='#b71c1c', weight='bold'),
        locations=loc.body(rows=negative_rows, columns=['Return %'])
    )

# Make year column bold
gt = gt.tab_style(
    style=style.text(weight='bold'),
    locations=loc.body(columns=['Year'])
)

# Style the header
gt = gt.tab_options(
    table_font_size='12px'
)

# Save as PNG
gt.gtsave('table.png', zoom=2)

print("Table created and saved as table.png")
print("\nSummary Statistics:")
print(summary_df.to_string(index=False))
