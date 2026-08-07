import pandas as pd
from datetime import datetime
import great_tables as gt

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]
df = df.sort_values('date').reset_index(drop=True)

# Calculate daily gain/loss
df['daily_change'] = df['close'] - df['open']

# Group by year-month
df['year_month'] = df['date'].dt.to_period('M')

monthly_data = []
for period, group in df.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    pct_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = group['volume'].mean()

    # Highest single-day gain and loss
    highest_gain = group['daily_change'].max()
    highest_loss = group['daily_change'].min()

    monthly_data.append({
        'Month': str(period),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Percent Change (%)': pct_change,
        'Avg Daily Volume': avg_volume,
        'Highest Single-Day Gain': highest_gain,
        'Highest Single-Day Loss': highest_loss,
    })

result_df = pd.DataFrame(monthly_data)

# Create the table
gt_table = (
    gt.GT(result_df)
    .tab_header(
        title="S&P 500 Monthly Performance Summary",
        subtitle="2010 – 2015"
    )
    .fmt_number(
        columns=['Opening Price', 'Closing Price'],
        decimals=2
    )
    .fmt_number(
        columns=['Percent Change (%)'],
        decimals=2
    )
    .fmt_number(
        columns=['Avg Daily Volume'],
        decimals=0
    )
    .fmt_number(
        columns=['Highest Single-Day Gain', 'Highest Single-Day Loss'],
        decimals=2
    )
    .data_color(
        columns=['Percent Change (%)'],
        palette=['#d7191c', '#ffffbf', '#2b83ba'],
        domain=[-15, 15]
    )
    .tab_source_note("Data source: S&P 500 historical prices")
    .opt_align_table_header('center')
)

gt_table.gtsave('table.png')
print("Table saved to table.png")
