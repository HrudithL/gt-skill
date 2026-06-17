import pandas as pd
from datetime import timedelta
from great_tables import GT, md

# Load the S&P 500 data
df = pd.read_csv('/Users/hrudithl/Documents/posit-dev/gtskill/runs/20260617-120902/sp500.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Get the last 5 years of data
five_years_ago = df['date'].max() - timedelta(days=365*5)
df_5y = df[df['date'] >= five_years_ago].copy()
df_5y['year'] = df_5y['date'].dt.year

# Build yearly summary
summary_data = []
for year in sorted(df_5y['year'].unique()):
    year_data = df_5y[df_5y['year'] == year]
    year_open = year_data[year_data['date'] == year_data['date'].min()]['open'].values[0]
    year_close = year_data[year_data['date'] == year_data['date'].max()]['close'].values[0]
    year_high = year_data['high'].max()
    year_low = year_data['low'].min()
    year_return = ((year_close - year_open) / year_open) * 100
    
    summary_data.append({
        'Year': int(year),
        'Open': round(year_open, 2),
        'High': round(year_high, 2),
        'Low': round(year_low, 2),
        'Close': round(year_close, 2),
        'Return %': round(year_return, 2)
    })

summary_df = pd.DataFrame(summary_data)

# Create the polished table with Great Tables
gt_table = (
    GT(summary_df)
    .tab_header(
        title=md("**S&P 500 Index Overview**"),
        subtitle=md("5-Year Historical Perfo        subtitle=md("5-Year Historical Perfo         table_font_size="14px",
        column_labels_font_weight="bold"
    )
    .fmt_number(
        columns=['Open', 'High', 'Low', 'Close'],
        decimals=2,
        use_seps=True,
        sep_mark=","
    )
    .fmt_number(
        columns=['Return %'],
        decimals=2,
        suffix="%"
    )
)

# Save as PNG
output_path = '/Users/hrudithl/Documents/posit-dev/gtskill/runs/20260617-120902/sp500_overview.png'
gt_table.gtsave(output_path)

print(f"S&P 500 Overview table saved to: {output_path}")
print(f"\nSummary Data:")
print(summary_df)
