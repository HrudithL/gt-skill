import pandas as pd
from great_tables import GT, md, html, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Load the data
df_raw = pd.read_csv('sp500.csv')

# Convert date to datetime
df_raw['date'] = pd.to_datetime(df_raw['date'])

# Extract year and month
df_raw['year_month'] = df_raw['date'].dt.to_period('M')

# Filter for 2010-2015
df_raw = df_raw[(df_raw['date'].dt.year >= 2010) & (df_raw['date'].dt.year <= 2015)]

# Group by month and calculate summary statistics
monthly_data = []

for year_month, group in df_raw.groupby('year_month'):
    year, month = year_month.year, year_month.month

    # Opening price (first trading day of month)
    opening_price = group.iloc[0]['open']

    # Closing price (last trading day of month)
    closing_price = group.iloc[-1]['close']

    # Percent change
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Daily gains and losses
    group['daily_change'] = group['close'] - group['open']
    highest_gain = group['daily_change'].max()
    highest_loss = group['daily_change'].min()

    monthly_data.append({
        'Month': year_month.strftime('%Y-%m'),
        'Opening Price': opening_price,
        'Closing Price': closing_price,
        'Monthly % Change': pct_change,
        'Avg Daily Volume': avg_volume,
        'Highest Daily Gain': highest_gain,
        'Highest Daily Loss': highest_loss,
    })

df = pd.DataFrame(monthly_data)

# Convert date string to datetime for proper sorting
df['Month_dt'] = pd.to_datetime(df['Month'])
df = df.sort_values('Month_dt').reset_index(drop=True)
df['Month'] = df['Month_dt'].dt.strftime('%b %Y')
df = df.drop('Month_dt', axis=1)

# Create the GT table
gt = (
    GT(df)
    .cols_label(
        Month='Month',
        **{'Opening Price': 'Open', 'Closing Price': 'Close',
           'Monthly % Change': 'Monthly %', 'Avg Daily Volume': 'Avg Vol',
           'Highest Daily Gain': 'High Gain', 'Highest Daily Loss': 'High Loss'}
    )
    .fmt_number(columns=['Opening Price', 'Closing Price'], decimals=2)
    .fmt_number(columns=['Monthly % Change'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .fmt_number(columns=['Highest Daily Gain', 'Highest Daily Loss'], decimals=2)
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010–2015'
    )
)

# Apply styling
gt = band(gt, shade='light', hue='navy')
gt = stripe(gt)
gt = stub_tint(gt, hue='navy')
gt = frame(gt)
finalize(gt)

# Render
gt.gtsave('table.png')
