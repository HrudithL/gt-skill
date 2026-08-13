import pandas as pd
import numpy as np
from great_tables import GT
from datetime import datetime

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]
df = df.sort_values('date')

# Group by year-month
df['year_month'] = df['date'].dt.to_period('M')

# Calculate monthly statistics
monthly_stats = []

for period in sorted(df['year_month'].unique()):
    month_data = df[df['year_month'] == period]

    opening_price = month_data.iloc[0]['open']
    closing_price = month_data.iloc[-1]['close']
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = month_data['volume'].mean()

    # Daily changes
    month_data_sorted = month_data.sort_values('date')
    daily_gains = (month_data_sorted['close'].values[1:] - month_data_sorted['close'].values[:-1]) / month_data_sorted['close'].values[:-1] * 100

    if len(daily_gains) > 0:
        highest_gain = daily_gains.max()
        highest_loss = daily_gains.min()
    else:
        highest_gain = 0
        highest_loss = 0

    monthly_stats.append({
        'Month': str(period),
        'Open': opening_price,
        'Close': closing_price,
        'Change %': percent_change,
        'Avg Daily Vol': avg_volume,
        'Highest Gain %': highest_gain,
        'Highest Loss %': highest_loss
    })

# Create dataframe
results_df = pd.DataFrame(monthly_stats)

# Format the data for display
gt_table = (
    GT(results_df)
    .fmt_currency(columns=['Open', 'Close'], currency='USD')
    .fmt_number(columns=['Change %', 'Highest Gain %', 'Highest Loss %'], decimals=2)
    .fmt_number(columns=['Avg Daily Vol'], decimals=0)
    .cols_label(
        Month='Month',
        Open='Opening Price',
        Close='Closing Price',
        **{'Change %': 'Monthly Change %', 'Avg Daily Vol': 'Avg Daily Volume', 'Highest Gain %': 'Highest Daily Gain %', 'Highest Loss %': 'Highest Daily Loss %'}
    )
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010-2015'
    )
)

gt_table.gtsave('table.png')
print("Table saved to table.png")
