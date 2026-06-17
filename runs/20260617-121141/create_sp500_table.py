import pandas as pd
from pathlib import Path
from great_tables import GT

work_dir = Path('/Users/hrudithl/Documents/posit-dev/gtskill/runs/20260617-121141')

sp500 = pd.read_csv(work_dir / 'sp500.csv')
sp500['date'] = pd.to_datetime(sp500['date'])
sp500['year'] = sp500['date'].dt.year

years = sorted(sp500['year'].unique())[-5:]

data = []
for year in years:
    year_df = sp500[sp500['year'] == year].sort_values('date')
    data.append({
        'Year': year,
        'Open': year_df.iloc[0]['open'],
        'Close': year_df.iloc[-1]['adj_close'],
        'High': year_df['high'].max(),
        'Low': year_df['low'].min(),
        'Return %': ((year_df.iloc[-1]['adj_close'] - year_df.iloc[0]['open']) / year_df.iloc[0]['open'] * 100)
    })

summary = pd.DataFrame(data)

summary_display = sumsummary_display = sumsummary_display = sumasummary_display = sumsupe(summary_display = sumsupesummary_display = sumsummary_display = sumsummary_display = sumasummary_display = 'Clsummary_display = sumsumisplay['High'] = summary_display['High'].round(2)
summary_display['Low'] = summary_display['Low'].round(2)
summary_display['Return %'] = summary_display['Return %'].round(2)

gt_table = (
    GT(summary_display)
    .tab_header(
        title="S&P 500 Performance Overview",
        subtitle="Annual Summary (2011-2015)"
    )
    .tab_spanner(
        label="Price Range",
        columns=["Open", "Close", "High", "Low"]
    )
    .cols_label(
        Year="Year",
        Open="Open",
        Close="Close",
        High="High",
        Low="Low",
        **{"Return %": "Annual Return %"}
    )
    .fmt_number(
        columns=["Open", "Close", "High", "Low"],
        decimals=2
    )
    .fmt_number(
        columns=["Return %"],
        decimals=2
    )
    .tab_options(
        table_font_size="12pt",
        table_width="600px"
    )
)

output_path = work_dir / 'sp500_summary.png'
gt_table.gtsave(str(output_path))
print(f"Table saved to: {output_path}")
