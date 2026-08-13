import pandas as pd
import numpy as np
from datetime import datetime
from great_tables import GT, md, loc, style
from house_table import (
    PALETTE, frame, hairlines, finalize, band, stripe,
    stub_tint, heatmap, humanize_labels
)

# Read the S&P 500 data
df = pd.read_csv("sp500.csv")
df['date'] = pd.to_datetime(df['date'])

# Filter to 2010-2015 range
df = df[(df['date'].dt.year >= 2010) & (df['date'].dt.year <= 2015)]
df = df.sort_values('date')

# Group by year-month and calculate monthly summaries
df['year_month'] = df['date'].dt.to_period('M')

monthly_data = []
for period, group in df.groupby('year_month'):
    month_str = period.strftime('%Y-%m')
    year = int(month_str[:4])
    month = int(month_str[5:])

    # Get opening (first trading day of month) and closing (last trading day)
    opening = group.iloc[0]['open']
    closing = group.iloc[-1]['close']

    # Calculate percent change
    pct_change = (closing - opening) / opening

    # Average daily volume
    avg_volume = group['volume'].mean()

    # Find highest single-day gain and loss within month
    group['daily_gain_loss'] = ((group['close'] - group['open']) / group['open']) * 100
    highest_gain = group['daily_gain_loss'].max()
    highest_loss = group['daily_gain_loss'].min()

    monthly_data.append({
        'month': period.strftime('%b %Y'),
        'opening': opening,
        'closing': closing,
        'pct_change': pct_change,
        'avg_volume': avg_volume,
        'highest_gain': highest_gain,
        'highest_loss': highest_loss,
    })

monthly_df = pd.DataFrame(monthly_data)

# Build the GT table
gt = (
    GT(monthly_df, rowname_col="month")
    .tab_header(
        title="S&P 500 Monthly Performance",
        subtitle=md("Monthly summary showing opening/closing prices, percent change, volume, and daily extremes (2010–2015)"),
    )
    .tab_stubhead(label="Month")
    .fmt_number(columns="opening", decimals=2, use_seps=False)
    .fmt_number(columns="closing", decimals=2, use_seps=False)
    .fmt_percent(columns="pct_change", decimals=2, force_sign=True)
    .fmt_number(columns="avg_volume", decimals=0, use_seps=True)
    .fmt_number(columns="highest_gain", decimals=2, force_sign=True, pattern="{x}%")
    .fmt_number(columns="highest_loss", decimals=2, force_sign=True, pattern="{x}%")
)

# Humanize labels
gt = humanize_labels(
    gt,
    monthly_df,
    overrides={
        "opening": "Opening Price",
        "closing": "Closing Price",
        "pct_change": "% Change",
        "avg_volume": "Avg Daily Volume",
        "highest_gain": "Highest Daily Gain",
        "highest_loss": "Highest Daily Loss",
    }
)

# Column widths and padding
gt = gt.cols_width(
    cases={
        "month": "90px",
        "opening": "110px",
        "closing": "110px",
        "pct_change": "100px",
        "avg_volume": "135px",
        "highest_gain": "130px",
        "highest_loss": "130px",
    }
)
gt = gt.tab_options(
    heading_padding="6px",
    column_labels_padding="6px",
    column_labels_padding_horizontal="8px",
    data_row_padding="5px",
    data_row_padding_horizontal="8px",
    source_notes_padding="6px",
)

# Apply heatmap to percent change (diverging, signed measure)
gt = heatmap(gt, "pct_change", kind="diverging", hue="default")

# Apply heatmap to highest gain/loss separately (both diverging measures)
# Highest gain uses Greens, highest loss uses Reds
gt = heatmap(gt, "highest_gain", kind="sequential", hue="positive")
gt = heatmap(gt, "highest_loss", kind="sequential", hue="warning")

# Heading band and other styling
gt = band(gt, hue="navy")
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Source notes and finalize
gt = (
    gt.tab_source_note(
        source_note="% Change is the percent change from opening to closing price within the month. Highest Daily Gain/Loss are the maximum single-day gains and losses (percent change from open to close) within each month."
    )
    .tab_source_note(source_note="Source: S&P 500 historical price data.")
)

gt = hairlines(gt)
gt = frame(gt)
finalize(gt)
