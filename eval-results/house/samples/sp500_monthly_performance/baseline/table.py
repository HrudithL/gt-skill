import pandas as pd
from great_tables import GT
import re

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]

# Add year and month columns
df_filtered['year'] = df_filtered['date'].dt.year
df_filtered['month'] = df_filtered['date'].dt.month

# Group by year and month, then calculate summaries
def calculate_monthly_stats(group):
    intra_day_gain = (group['high'] - group['open']) * 100 / group['open']
    intra_day_loss = (group['low'] - group['open']) * 100 / group['open']

    return pd.Series({
        'open_price': group['open'].iloc[0],
        'close_price': group['close'].iloc[-1],
        'pct_change': ((group['close'].iloc[-1] - group['open'].iloc[0]) / group['open'].iloc[0]) * 100,
        'avg_volume': group['volume'].mean(),
        'highest_daily_gain': intra_day_gain.max(),
        'highest_daily_loss': intra_day_loss.min(),
    })

monthly_stats = df_filtered.groupby(['year', 'month']).apply(calculate_monthly_stats, include_groups=False).reset_index()
monthly_stats.columns = ['Year', 'Month', 'open_price', 'close_price', 'pct_change', 'avg_volume', 'highest_daily_gain', 'highest_daily_loss']

# Add month name
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
monthly_stats['Month_Name'] = monthly_stats['Month'].apply(lambda x: month_names[x - 1])

# Reorder columns
display_df = monthly_stats[['Year', 'Month_Name', 'open_price', 'close_price', 'pct_change', 'avg_volume', 'highest_daily_gain', 'highest_daily_loss']].copy()

# Round numeric columns
display_df['open_price'] = display_df['open_price'].round(2)
display_df['close_price'] = display_df['close_price'].round(2)
display_df['pct_change'] = display_df['pct_change'].round(2)
display_df['avg_volume'] = display_df['avg_volume'].round(0).astype(int)
display_df['highest_daily_gain'] = display_df['highest_daily_gain'].round(2)
display_df['highest_daily_loss'] = display_df['highest_daily_loss'].round(2)

# Rename columns for display
display_df.columns = ['Year', 'Month', 'Opening Price', 'Closing Price', 'Monthly % Change', 'Avg Daily Volume', 'Highest Single-Day Gain %', 'Highest Single-Day Loss %']

gt = (
    GT(display_df)
    .tab_header(title="S&P 500 Monthly Performance Summary", subtitle="2010–2015")
    .cols_align(align="center")
    .tab_options(
        table_font_size="11px",
        heading_background_color="#f0f0f0",
    )
)

gt.gtsave("table.png")
print("Table saved to table.png")
