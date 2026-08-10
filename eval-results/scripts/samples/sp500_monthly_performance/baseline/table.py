import pandas as pd
import great_tables as gt
from great_tables import loc

# Read the data
df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

# Filter for 2010-2015
df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values('date')

# Group by year and month
df_filtered['year_month'] = df_filtered['date'].dt.to_period('M')

# Calculate monthly metrics
monthly_data = []
for period, group in df_filtered.groupby('year_month'):
    group = group.sort_values('date')

    open_price = group.iloc[0]['open']
    close_price = group.iloc[-1]['close']
    percent_change = ((close_price - open_price) / open_price) * 100

    avg_daily_volume = group['volume'].mean()

    # Calculate daily changes
    group['daily_change'] = group['high'] - group['low']
    highest_gain = group['daily_change'].max()
    highest_loss = -group['daily_change'].min()

    monthly_data.append({
        'Month': period,
        'Opening Price': open_price,
        'Closing Price': close_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_daily_volume,
        'Highest Single-Day Gain': highest_gain,
        'Highest Single-Day Loss': highest_loss
    })

result_df = pd.DataFrame(monthly_data)

# Create the table with great_tables
gt_table = (
    gt.GT(result_df)
    .fmt_currency(
        columns=['Opening Price', 'Closing Price', 'Highest Single-Day Gain', 'Highest Single-Day Loss'],
        currency='USD',
        decimals=2
    )
    .fmt_number(columns=['Percent Change'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .cols_label(
        Month='Month',
        **{col: col for col in result_df.columns if col != 'Month'}
    )
    .cols_width(cases={
        'Month': '100px',
        'Opening Price': '130px',
        'Closing Price': '130px',
        'Percent Change': '120px',
        'Avg Daily Volume': '150px',
        'Highest Single-Day Gain': '150px',
        'Highest Single-Day Loss': '150px'
    })
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010-2015)',
        subtitle='Opening/Closing Prices, Monthly Returns, and Daily Volume/Range Data'
    )
    .tab_options(
        table_font_size='11px',
        table_width='100%',
        container_width='1150px',
        table_layout='fixed',
        data_row_padding='8px'
    )
)

gt_table.gtsave('table.png')
print("Table saved to table.png")
