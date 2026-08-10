import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load and prepare data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df = df[(df['date'] >= '2010-01-01') & (df['date'] <= '2015-12-31')]
df = df.sort_values('date').reset_index(drop=True)

# Calculate daily gains/losses
df['daily_gain_loss'] = df['close'] - df['open']

# Group by year-month
df['year_month'] = df['date'].dt.to_period('M')

# Create monthly summary
monthly_data = []
for period, group in df.groupby('year_month'):
    year, month = period.year, period.month

    open_price = group.iloc[0]['open']
    close_price = group.iloc[-1]['close']
    pct_change = ((close_price - open_price) / open_price) * 100
    avg_volume = group['volume'].mean()

    # Highest single-day gain (max close - open for the day)
    daily_gains = group['close'] - group['open']
    max_gain = daily_gains.max()

    # Highest single-day loss (min close - open for the day, i.e., most negative)
    min_loss = daily_gains.min()

    monthly_data.append({
        'year_month': f"{period}",
        'open': open_price,
        'close': close_price,
        'pct_change': pct_change,
        'avg_volume': avg_volume,
        'max_gain': max_gain,
        'max_loss': min_loss,
    })

summary_df = pd.DataFrame(monthly_data)

# Create GT table
gt = (
    GT(summary_df, rowname_col='year_month')
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle=md('2010–2015: opening/closing prices, percent change, and intra-month volatility')
    )
    .tab_stubhead(label='Month')
    .fmt_number(columns='open', decimals=2)
    .fmt_number(columns='close', decimals=2)
    .fmt_number(columns='pct_change', decimals=2)
    .fmt_number(columns='avg_volume', decimals=0, use_seps=True)
    .fmt_number(columns='max_gain', decimals=2)
    .fmt_number(columns='max_loss', decimals=2)
)

# Label columns
gt = humanize_labels(
    gt,
    summary_df,
    overrides={
        'open': 'Open',
        'close': 'Close',
        'pct_change': '% Change',
        'avg_volume': 'Avg Daily Volume',
        'max_gain': 'Max Daily Gain',
        'max_loss': 'Max Daily Loss',
    }
)

# Apply percent change heatmap (diverging, since it can be positive/negative)
gt = heatmap(gt, 'pct_change', kind='diverging', hue='default')

# Apply band styling with forest hue (finance-appropriate)
gt = band(gt, hue='forest')

# Apply striping (72 rows is well above 10-row threshold)
gt = stripe(gt)

# Apply stub tint to match the forest hue
gt = stub_tint(gt, hue='forest')

# Apply frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Source note
gt = gt.tab_source_note(source_note='Source: S&P 500 daily price and volume data, 2010–2015.')

# Finalize and save
finalize(gt, path='table.png')
