import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values('date').reset_index(drop=True)

# Extract year-month for grouping
df_filtered['year_month'] = df_filtered['date'].dt.to_period('M')

# Calculate monthly metrics
monthly_data = []
for period, group in df_filtered.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    avg_volume = group['volume'].mean()

    # Daily gains and losses
    daily_changes = group['close'].diff().dropna()
    highest_gain = daily_changes.max() if len(daily_changes) > 0 else 0
    highest_loss = daily_changes.min() if len(daily_changes) > 0 else 0

    monthly_data.append({
        'Month': period.strftime('%Y-%m'),
        'Open': opening_price,
        'Close': closing_price,
        'Monthly %': pct_change,
        'Avg Daily Vol': avg_volume,
        'Best Day': highest_gain,
        'Worst Day': highest_loss,
    })

summary_df = pd.DataFrame(monthly_data)

# Create the GT table
gt = (
    GT(summary_df)
    .fmt_currency(columns=['Open', 'Close'], currency='USD', decimals=2)
    .fmt_number(columns=['Monthly %'], decimals=2)
    .fmt_currency(columns=['Best Day', 'Worst Day'], currency='USD', decimals=2)
    .fmt_number(columns=['Avg Daily Vol'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010 through 2015'
    )
    .tab_source_note(source_note='Data source: S&P 500 historical prices')
)

# Render the table
gt.gtsave('table.png')
print("Table saved to table.png")
