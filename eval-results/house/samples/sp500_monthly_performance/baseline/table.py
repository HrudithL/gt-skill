import pandas as pd
from great_tables import GT
from datetime import datetime

# Read the S&P 500 data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Extract year and month
df['year_month'] = df['date'].dt.to_period('M')

# Group by month and calculate metrics
monthly_data = []

for period, group in df.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']

    # Percent change from open to close
    percent_change = ((closing_price - opening_price) / opening_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Daily gains/losses
    group['daily_change'] = group['close'].diff()

    # Highest single-day gain
    max_gain = group['daily_change'].max()

    # Highest single-day loss (most negative)
    max_loss = group['daily_change'].min()

    monthly_data.append({
        'Month': period.strftime('%B %Y'),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_volume,
        'Highest Single-Day Gain': max_gain,
        'Highest Single-Day Loss': max_loss
    })

result_df = pd.DataFrame(monthly_data)

# Create the GT table
gt = (
    GT(result_df)
    .fmt_currency(columns=['Opening Price', 'Closing Price'], currency='USD')
    .fmt_currency(columns=['Highest Single-Day Gain', 'Highest Single-Day Loss'], currency='USD')
    .fmt_number(columns=['Percent Change'], decimals=2, pattern='{x}%')
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance (2010-2015)',
        subtitle='Opening/closing prices, monthly percent change, average daily volume, and daily extremes'
    )
)

gt.gtsave('table.png')
