import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]
df = df.sort_values('date')

# Create a year-month column
df['year_month'] = df['date'].dt.to_period('M')

# Group by month to compute summary statistics
monthly_data = []

for period, group in df.groupby('year_month'):
    group = group.sort_values('date').reset_index(drop=True)

    opening_price = group['open'].iloc[0]
    closing_price = group['close'].iloc[-1]
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_daily_volume = group['volume'].mean()

    # Calculate daily gains and losses
    group['daily_gain'] = group['close'] - group['open']

    highest_gain = group['daily_gain'].max()
    highest_loss = group['daily_gain'].min()

    monthly_data.append({
        'Month': str(period),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_daily_volume,
        'Highest Daily Gain': highest_gain,
        'Highest Daily Loss': highest_loss
    })

summary_df = pd.DataFrame(monthly_data)

# Create the GT table
gt = (
    GT(summary_df)
    .fmt_number(columns=['Opening Price', 'Closing Price', 'Highest Daily Gain', 'Highest Daily Loss'], decimals=2)
    .fmt_number(columns=['Percent Change'], decimals=2, pattern='{x}%')
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Daily trading metrics aggregated by month'
    )
)

# Render to PNG
gt.gtsave('table.png')
print("Table saved to table.png")
