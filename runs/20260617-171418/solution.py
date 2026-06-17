import pandas as pd
import numpy as np
from datetime import datetime
from great_tables import GT, loc
from great_tables.style import fill, text

# Load the data
df = pd.read_csv('sp500.csv')

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Get the last 5 years of data
max_year = df['date'].dt.year.max()
min_year_for_5yr = max_year - 4  # Last 5 years
df_5yr = df[df['date'].dt.year >= min_year_for_5yr].copy()

# Extract year from date
df_5yr['year'] = df_5yr['date'].dt.year

# Get the start and end dates
start_date = df_5yr['date'].min()
end_date = df_5yr['date'].max()

# Calculate yearly summary statistics
yearly_stats = []

for year in sorted(df_5yr['year'].unique()):
    year_data = df_5yr[df_5yr['year'] == year]

    # Get first and last closing price of the year
    first_close = year_data.iloc[0]['close']
    last_close = year_data.iloc[-1]['close']

    # Calculate the change and percentage change
    year_change = last_close - first_close
    year_pct_change = (year_change / first_close) * 100

    # Get high and low for the year
    year_high = year_data['high'].max()
    year_low = year_data['low'].min()

    # Get opening price for the year
    opening = year_data.iloc[0]['open']

    # Get total volume for the year
    total_volume = year_data['volume'].sum()

    yearly_stats.append({
        'Year': int(year),
        'Opening': opening,
        'Closing': last_close,
        'High': year_high,
        'Low': year_low,
        'Change': year_change,
        'Change %': year_pct_change,
        'Avg Volume': total_volume / len(year_data),
        'Trading Days': len(year_data)
    })

# Create DataFrame from yearly stats
summary_df = pd.DataFrame(yearly_stats)

# Calculate overall 5-year statistics
overall_first_close = df_5yr.iloc[0]['close']
overall_last_close = df_5yr.iloc[-1]['close']
overall_change = overall_last_close - overall_first_close
overall_pct_change = (overall_change / overall_first_close) * 100
overall_high = df_5yr['high'].max()
overall_low = df_5yr['low'].min()

# Add a row for 5-Year Overview at the top
overview_row = pd.DataFrame([{
    'Year': '5-Yr Overview',
    'Opening': overall_first_close,
    'Closing': overall_last_close,
    'High': overall_high,
    'Low': overall_low,
    'Change': overall_change,
    'Change %': overall_pct_change,
    'Avg Volume': df_5yr['volume'].mean(),
    'Trading Days': len(df_5yr)
}])

# Combine overview with yearly data
display_df = pd.concat([overview_row, summary_df], ignore_index=True)

# Format the dataframe for display
display_df['Opening'] = display_df['Opening'].round(2)
display_df['Closing'] = display_df['Closing'].round(2)
display_df['High'] = display_df['High'].round(2)
display_df['Low'] = display_df['Low'].round(2)
display_df['Change'] = display_df['Change'].round(2)
display_df['Change %'] = display_df['Change %'].round(2)
display_df['Avg Volume'] = display_df['Avg Volume'].round(0).astype(int)
display_df['Trading Days'] = display_df['Trading Days'].astype(int)

# Create the GT table
gt = GT(display_df)

# Format columns
gt = (gt
      .fmt_number(columns=['Opening', 'Closing', 'High', 'Low', 'Change'], decimals=2)
      .fmt_number(columns=['Change %'], decimals=2)
      .fmt_integer(columns=['Avg Volume', 'Trading Days'])
)

# Add title and subtitle
gt = (gt
      .tab_header(
          title="S&P 500: 5-Year Performance Overview",
          subtitle=f"Daily data from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
      )
)

# Style the title
gt = (gt
      .tab_style(
          style=[
              fill(color="#1f77b4"),
              text(color="white", weight="bold", size="16px")
          ],
          locations=loc.title()
      )
      .tab_style(
          style=[
              text(color="#555555", size="13px")
          ],
          locations=loc.subtitle()
      )
)

# Format column headers with better styling
gt = (gt
      .tab_style(
          style=[
              fill(color="#e9ecef"),
              text(weight="bold", align="center")
          ],
          locations=loc.column_labels()
      )
)

# Style the first row (Overview) differently - with bold text and light gray background
gt = (gt
      .tab_style(
          style=[
              fill(color="#f0f0f0"),
              text(weight="bold")
          ],
          locations=loc.body(rows=[0])
      )
)

# Apply conditional formatting to rows based on positive/negative change
# Green for positive years, red for negative years
for i in range(1, len(display_df)):
    change_val = display_df.loc[i, 'Change %']
    if change_val > 0:
        # Green for positive
        gt = gt.tab_style(
            style=[
                fill(color="#d4edda"),
                text(color="#155724", weight="bold")
            ],
            locations=loc.body(rows=[i], columns=['Change', 'Change %'])
        )
    elif change_val < 0:
        # Red for negative
        gt = gt.tab_style(
            style=[
                fill(color="#f8d7da"),
                text(color="#721c24", weight="bold")
            ],
            locations=loc.body(rows=[i], columns=['Change', 'Change %'])
        )

# Save as PNG using gtsave (newer approach)
gt.gtsave('table.png')

print("✓ Table created successfully: table.png")
print(f"\nS&P 500 Summary (5-Year Overview):")
print(f"Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
print(f"Start: {overall_first_close:.2f}")
print(f"End: {overall_last_close:.2f}")
print(f"5-Year Change: {overall_change:+.2f} ({overall_pct_change:+.2f}%)")
print(f"5-Year High: {overall_high:.2f}")
print(f"5-Year Low: {overall_low:.2f}")
print(f"\nYearly Breakdown:")
for _, row in summary_df.iterrows():
    print(f"  {int(row['Year'])}: {row['Change %']:+.2f}%")
