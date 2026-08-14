import pandas as pd
from great_tables import GT, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap,
    humanize_labels
)

# Read and prepare data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Group by year-month
df_filtered['year_month'] = df_filtered['date'].dt.to_period('M')

# Calculate monthly statistics
monthly_stats = []
for period, group in df_filtered.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    pct_change = ((closing_price - opening_price) / opening_price) * 100

    # Daily volume average
    avg_daily_volume = group['volume'].mean()

    # Daily price changes
    group['daily_change'] = group['close'] - group['open']
    best_day_gain = group['daily_change'].max()
    worst_day_loss = group['daily_change'].min()

    monthly_stats.append({
        'month': period.strftime('%Y-%m'),
        'opening_price': opening_price,
        'closing_price': closing_price,
        'pct_change': pct_change,
        'avg_daily_volume': avg_daily_volume,
        'best_day_gain': best_day_gain,
        'worst_day_loss': worst_day_loss,
    })

summary_df = pd.DataFrame(monthly_stats)

# Create the GT table
gt = GT(summary_df, rowname_col='month')

# Humanize labels with overrides
gt = humanize_labels(gt, summary_df, overrides={
    'opening_price': 'Opening Price',
    'closing_price': 'Closing Price',
    'pct_change': 'Monthly % Change',
    'avg_daily_volume': 'Avg Daily Volume',
    'best_day_gain': 'Best Day Gain',
    'worst_day_loss': 'Worst Day Loss',
})

# Format currency columns
gt = gt.fmt_currency(columns=['opening_price', 'closing_price', 'best_day_gain', 'worst_day_loss'])

# Format percentage column
gt = gt.fmt_number(columns=['pct_change'], decimals=2)

# Format volume column with thousands separator
gt = gt.fmt_integer(columns=['avg_daily_volume'])

# Add spanner for best/worst day columns
gt = gt.tab_spanner(label='Daily Extremes', columns=['best_day_gain', 'worst_day_loss'])

# Apply band to header
gt = band(gt, shade="dark", hue="forest")

# Apply heatmap to percent change (diverging, signed measure)
gt = heatmap(gt, columns=['pct_change'], kind='diverging', hue='default')

# Apply striping
gt = stripe(gt)

# Apply stub tint
gt = stub_tint(gt, hue="forest")

# Add spanner divider
gt = gt.tab_style(
    style=style.borders(
        sides="right",
        color=PALETTE["neutral"]["vertical_divider"],
        weight="1px"
    ),
    locations=loc.body(columns=['avg_daily_volume'])
)
gt = gt.tab_style(
    style=style.borders(
        sides="right",
        color=PALETTE["neutral"]["vertical_divider"],
        weight="1px"
    ),
    locations=loc.column_labels(columns=['avg_daily_volume'])
)

# Add title and subtitle
gt = gt.tab_header(
    title="S&P 500 Monthly Performance Summary",
    subtitle="2010 through 2015"
)

# Add source notes
gt = gt.tab_source_note(
    source_note="Monthly percent change is calculated as (closing price - opening price) / opening price. Best day gain and worst day loss represent the highest and lowest daily price changes within each month."
)
gt = gt.tab_source_note(
    source_note="Source: S&P 500 historical daily price data."
)

# Apply frame and hairlines
gt = frame(gt)
gt = hairlines(gt)

# Finalize and save
finalize(gt, path="table.png")
