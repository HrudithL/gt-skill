import pandas as pd
from great_tables import GT
import polars as pl

df = pd.read_csv('./sp500.csv')
df['date'] = pd.to_datetime(df['date'])

df_filtered = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)].copy()
df_filtered = df_filtered.sort_values('date')

monthly_data = []

for year in range(2010, 2016):
    for month in range(1, 13):
        month_df = df_filtered[(df_filtered['date'].dt.year == year) &
                               (df_filtered['date'].dt.month == month)]

        if len(month_df) == 0:
            continue

        opening = month_df.iloc[0]['open']
        closing = month_df.iloc[-1]['close']
        percent_change = ((closing - opening) / opening) * 100
        avg_volume = month_df['volume'].mean()

        month_df_sorted_high = month_df.sort_values('high', ascending=False)
        month_df_sorted_low = month_df.sort_values('low')

        highest_gain = month_df_sorted_high.iloc[0]['high'] - month_df_sorted_high.iloc[0]['open']
        highest_loss = month_df_sorted_low.iloc[0]['low'] - month_df_sorted_low.iloc[0]['open']

        month_name = pd.Timestamp(year, month, 1).strftime('%B %Y')

        monthly_data.append({
            'Month': month_name,
            'Open': opening,
            'Close': closing,
            'Percent Change': percent_change,
            'Avg Daily Volume': avg_volume,
            'Highest Single-Day Gain': highest_gain,
            'Highest Single-Day Loss': highest_loss
        })

summary_df = pd.DataFrame(monthly_data)

gt = (
    GT(summary_df)
    .fmt_currency(columns=['Open', 'Close'], currency='USD')
    .fmt_number(columns=['Percent Change'], decimals=2, pattern='{x}%')
    .fmt_number(columns=['Avg Daily Volume'], decimals=0)
    .fmt_currency(columns=['Highest Single-Day Gain', 'Highest Single-Day Loss'], currency='USD')
    .tab_header(
        title='S&P 500 Monthly Performance Summary',
        subtitle='2010 - 2015'
    )
    .opt_align_table_header('center')
)

gt.gtsave('table.png')
