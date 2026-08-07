import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

# Load and clean data
df = pd.read_csv('airquality.csv')

# Aggregate by month: calculate mean for each numeric column
monthly_stats = df.groupby('Month')[['Ozone', 'Wind', 'Temp']].mean()

# Reset index to make Month a column
monthly_stats = monthly_stats.reset_index()

# Map month numbers to names
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_stats['Month'] = monthly_stats['Month'].map(month_names)

# Rename columns for display
monthly_stats.columns = ['Month', 'Ozone (ppb)', 'Wind (mph)', 'Temperature (°F)']

# Compute domains for the two colored measures: Temperature and Wind
# These are the top 2 by prompt priority
temp_cols = ['Temperature (°F)']
wind_cols = ['Wind (mph)']

temp_lo = float(np.nanmin(monthly_stats[temp_cols].to_numpy()))
temp_hi = float(np.nanmax(monthly_stats[temp_cols].to_numpy()))
wind_lo = float(np.nanmin(monthly_stats[wind_cols].to_numpy()))
wind_hi = float(np.nanmax(monthly_stats[wind_cols].to_numpy()))

# Build the table
gt = (
    GT(monthly_stats, rowname_col='Month')
    .fmt_number(columns=['Ozone (ppb)', 'Wind (mph)', 'Temperature (°F)'], decimals=1, use_seps=False)
    .sub_missing(columns=['Ozone (ppb)', 'Wind (mph)', 'Temperature (°F)'], missing_text='—')
    # Color Temperature (top priority)
    .data_color(
        columns='Temperature (°F)',
        palette='Blues',
        domain=[temp_lo, temp_hi],
        truncate=False,
        na_color='#808080',
    )
    # Color Wind (second priority)
    .data_color(
        columns='Wind (mph)',
        palette='Greens',
        domain=[wind_lo, wind_hi],
        truncate=False,
        na_color='#808080',
    )
    # Apply heading band with light tint (has Big Color, so light band)
    .tab_options(
        table_font_size='14px',
        column_labels_background_color='#EAF0F6',  # light tint for Blues dominant hue
        column_labels_border_bottom_color='#CCCCCC',
        column_labels_border_bottom_width='2px',
        table_body_hlines_style='solid',
        table_body_hlines_color='#E8E8E8',
        table_body_hlines_width='1px',
        row_striping_background_color='#F6F6F6',
    )
    # Apply row striping (≥5 rows, not fully filled by Big Color)
    .opt_row_striping()
    # Apply stub tint
    .tab_style(
        style=style.fill(color='#EAF0F6'),  # harmonize to Blues tint
        locations=loc.stub(),
    )
    # Apply frame border
    .tab_options(
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
    # Add title and subtitle
    .tab_header(
        title='Air Quality by Month',
        subtitle=md('Average temperature, wind speed, and ozone levels')
    )
)

# Render
gt.gtsave('table.png', expand=15, zoom=2.0)
