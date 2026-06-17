import pandas as pd
from great_tables import GT, md, style, loc

# Load the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Sort by date to ensure proper ordering (oldest to newest)
df = df.sort_values('date')

# Get the last 5 years of data (from 2010-12-31 to 2015-12-31)
# The data goes up to 2015-12-31, so we'll take the last ~5 years
end_date = df['date'].max()
start_date = end_date - pd.DateOffset(years=5)
df_recent = df[df['date'] >= start_date].copy()

# Calculate yearly statistics
df_recent['year'] = df_recent['date'].dt.year
yearly_stats = df_recent.groupby('year').agg({
    'close': ['first', 'last', 'min', 'max', 'mean'],
    'volume': 'mean'
}).reset_index()

# Flatten column names
yearly_stats.columns = ['year', 'open_price', 'close_price', 'low', 'high', 'avg_price', 'avg_volume']

# Calculate year-over-year change
yearly_stats['yoy_change'] = yearly_stats['close_price'].pct_change() * 100
yearly_stats['price_range'] = yearly_stats['high'] - yearly_stats['low']
yearly_stats['return_pct'] = ((yearly_stats['close_price'] - yearly_stats['open_price']) / yearly_stats['open_price']) * 100

# Reorder columns for better presentation
yearly_stats = yearly_stats[['year', 'open_price', 'close_price', 'return_pct', 'yoy_change',
                             'low', 'high', 'price_range', 'avg_price', 'avg_volume']]

# Create the Great Table
gt = (
    GT(yearly_stats)
    .tab_header(
        title=md("**S&P 500 Performance Overview**"),
        subtitle="Five-Year Summary (2011-2015)"
    )
    .cols_label(
        year="Year",
        open_price="Open",
        close_price="Close",
        return_pct="Annual Return",
        yoy_change="YoY Change",
        low="Low",
        high="High",
        price_range="Range",
        avg_price="Avg Price",
        avg_volume="Avg Volume"
    )
    .tab_spanner(
        label="Price Points",
        columns=["open_price", "close_price"]
    )
    .tab_spanner(
        label="Performance",
        columns=["return_pct", "yoy_change"]
    )
    .tab_spanner(
        label="Price Range",
        columns=["low", "high", "price_range"]
    )
    .tab_spanner(
        label="Averages",
        columns=["avg_price", "avg_volume"]
    )
    .fmt_number(
        columns=["open_price", "close_price", "low", "high", "price_range", "avg_price"],
        decimals=2
    )
    .fmt_percent(
        columns=["return_pct", "yoy_change"],
        decimals=2,
        scale_values=False
    )
    .fmt_number(
        columns=["avg_volume"],
        decimals=0,
        compact=True
    )
    .cols_align(
        align="center",
        columns=["year"]
    )
    .cols_align(
        align="right",
        columns=["open_price", "close_price", "return_pct", "yoy_change",
                "low", "high", "price_range", "avg_price", "avg_volume"]
    )
    .data_color(
        columns=["return_pct"],
        palette=["#d73027", "#fee08b", "#1a9850"],
        domain=[-10, 20]
    )
    .data_color(
        columns=["yoy_change"],
        palette=["#d73027", "#fee08b", "#1a9850"],
        domain=[-10, 20]
    )
    .tab_source_note(
        source_note="Data: S&P 500 historical daily data from Yahoo Finance"
    )
    .tab_source_note(
        source_note="Annual Return = (Close - Open) / Open; YoY Change = year-over-year change in closing price"
    )
)

# Save the table as PNG
gt.gtsave("table.png")

print("Table saved as table.png")
print("\nYearly Summary:")
print(yearly_stats.to_string(index=False))
