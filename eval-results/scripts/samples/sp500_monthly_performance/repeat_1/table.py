import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc

df = pd.read_csv("sp500.csv")
df['date'] = pd.to_datetime(df['date'])

df['year_month'] = df['date'].dt.to_period('M')
df['daily_change'] = df['close'] - df['open']

monthly_data = []
for ym, group in df.groupby('year_month'):
    group = group.sort_values('date')

    opening_price = group.iloc[0]['open']
    closing_price = group.iloc[-1]['close']
    percent_change = ((closing_price - opening_price) / opening_price) * 100
    avg_volume = group['volume'].mean()

    group['intraday_gain'] = group['high'] - group['low']
    group['daily_gain'] = group['close'] - group['open']

    highest_gain = group['daily_gain'].max()
    highest_loss = group['daily_gain'].min()

    monthly_data.append({
        'Month': str(ym),
        'Open': opening_price,
        'Close': closing_price,
        'Percent Change': percent_change,
        'Avg Daily Volume': avg_volume,
        'Highest Daily Gain': highest_gain,
        'Highest Daily Loss': highest_loss,
    })

summary_df = pd.DataFrame(monthly_data)

summary_df = summary_df.sort_values('Month').reset_index(drop=True)

summary_df = summary_df[(summary_df['Month'] >= '2010-01') & (summary_df['Month'] <= '2015-12')]

cols_numeric = ['Open', 'Close', 'Avg Daily Volume', 'Highest Daily Gain', 'Highest Daily Loss']
for col in cols_numeric:
    summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')

lo = float(np.nanmin(summary_df[['Percent Change']].to_numpy()))
hi = float(np.nanmax(summary_df[['Percent Change']].to_numpy()))
M = max(abs(lo), abs(hi))

gt = (
    GT(summary_df, rowname_col='Month')
    .fmt_currency(columns=['Open', 'Close'], decimals=2)
    .fmt_number(columns=['Highest Daily Gain', 'Highest Daily Loss'], decimals=2)
    .fmt_number(columns=['Avg Daily Volume'], decimals=0, use_seps=True)
    .fmt_percent(columns=['Percent Change'], decimals=2, force_sign=True)
    .data_color(
        columns=['Percent Change'],
        palette='RdYlGn',
        domain=[-M, M],
        truncate=False,
    )
    .tab_header(
        title='S&P 500 Monthly Performance Summary (2010–2015)',
        subtitle='Opening price, closing price, percent change, average daily volume, and daily gains/losses'
    )
    .cols_label(
        Open='Opening Price',
        Close='Closing Price',
        **{'Percent Change': 'Monthly %Δ', 'Avg Daily Volume': 'Avg Daily Volume',
           'Highest Daily Gain': 'Highest Daily Gain', 'Highest Daily Loss': 'Highest Daily Loss'}
    )
    .tab_options(
        table_body_hlines_style='solid',
        table_body_hlines_color='#E8E8E8',
        table_body_hlines_width='1px',
        column_labels_border_bottom_color='#CCCCCC',
        column_labels_border_bottom_width='2px',
        column_labels_background_color='#EAF0F6',
        column_labels_font_weight='bold',
        table_border_top_style='solid',
        table_border_top_color='#CCCCCC',
        table_border_top_width='1px',
        table_border_bottom_style='solid',
        table_border_bottom_color='#CCCCCC',
        table_border_bottom_width='1px',
        table_border_left_style='solid',
        table_border_left_color='#CCCCCC',
        table_border_left_width='1px',
        table_border_right_style='solid',
        table_border_right_color='#CCCCCC',
        table_border_right_width='1px',
    )
    .tab_style(
        style=style.fill(color='#F0F0F0'),
        locations=loc.stub(),
    )
    .opt_row_striping()
    .sub_missing(columns=cols_numeric, missing_text='—')
    .tab_source_note(
        md('**Canonical definitions:** Percent change = (close − open) / open. Highest daily gain/loss = close − open per trading day.')
    )
)

gt.gtsave('table.png', expand=15)
