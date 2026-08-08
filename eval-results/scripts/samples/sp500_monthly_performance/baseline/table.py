import pandas as pd
import great_tables as gt
from datetime import datetime

df = pd.read_csv('sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df = df.sort_values('date').reset_index(drop=True)
df['year_month'] = df['date'].dt.to_period('M')

monthly_stats = []

for year_month in df['year_month'].unique():
    month_data = df[df['year_month'] == year_month].reset_index(drop=True)

    year = year_month.year
    month = year_month.month

    if year < 2010 or year > 2015:
        continue

    open_price = month_data['open'].iloc[0]
    close_price = month_data['close'].iloc[-1]

    pct_change = ((close_price - open_price) / open_price) * 100

    avg_volume = month_data['volume'].mean()

    daily_changes = month_data['close'].pct_change().dropna() * 100
    month_data_with_change = month_data.copy()
    month_data_with_change['daily_change'] = daily_changes.reset_index(drop=True).reindex(month_data_with_change.index)

    best_day = month_data_with_change['daily_change'].max()
    worst_day = month_data_with_change['daily_change'].min()

    monthly_stats.append({
        'Year': year,
        'Month': month,
        'Month Name': datetime(year, month, 1).strftime('%B'),
        'Open': open_price,
        'Close': close_price,
        'Pct Change': pct_change,
        'Avg Volume': avg_volume,
        'Best Day': best_day,
        'Worst Day': worst_day,
    })

stats_df = pd.DataFrame(monthly_stats)
stats_df = stats_df.sort_values(['Year', 'Month']).reset_index(drop=True)

gt_table = (
    gt.GT(stats_df)
    .cols_move_to_start(columns=['Year', 'Month Name'])
    .cols_hide(columns=['Month'])
    .fmt_number(
        columns=['Open', 'Close'],
        decimals=2
    )
    .fmt_number(
        columns=['Pct Change', 'Best Day', 'Worst Day'],
        decimals=2
    )
    .fmt_number(
        columns=['Avg Volume'],
        decimals=0
    )
    .cols_label(
        Year='Year',
        **{'Month Name': 'Month'},
        Open='Opening Price',
        Close='Closing Price',
        **{'Pct Change': 'Monthly % Change'},
        **{'Avg Volume': 'Avg Daily Volume'},
        **{'Best Day': 'Best Day Gain (%)'},
        **{'Worst Day': 'Worst Day Loss (%)'}
    )
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010-2015'
    )
)

gt_table.gtsave('table.png')
print("Table saved to table.png")
