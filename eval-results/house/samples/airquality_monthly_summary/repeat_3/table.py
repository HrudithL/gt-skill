import pandas as pd
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, finalize, humanize_labels, heatmap, stripe, stub_tint

# Load and aggregate data
df = pd.read_csv('airquality.csv')

# Create monthly aggregates
monthly_data = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean',
}).reset_index()

# Map month numbers to names
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly_data['Month'] = monthly_data['Month'].map(month_names)

# Rename columns for display
monthly_data.columns = ['month', 'temperature', 'wind_speed', 'ozone']

# Build the table
gt = (
    GT(monthly_data, rowname_col='month')
    .tab_header(
        title='Air Quality Summary by Month',
        subtitle=md('Average temperature (°F), wind speed (mph), and ozone levels (ppb)')
    )
    .tab_stubhead(label='Month')
    .fmt_number(columns='temperature', decimals=1)
    .fmt_number(columns='wind_speed', decimals=2)
    .fmt_number(columns='ozone', decimals=1)
)

gt = humanize_labels(
    gt,
    monthly_data,
    overrides={
        'temperature': 'Temperature (°F)',
        'wind_speed': 'Wind Speed (mph)',
        'ozone': 'Ozone (ppb)'
    }
)

# Color heatmaps: temperature (sequential, positive/warm) and ozone (sequential, warning)
gt = heatmap(gt, 'temperature', kind='sequential', hue='positive')
gt = heatmap(gt, 'ozone', kind='sequential', hue='warning')

# Heading band with forest hue (environment/air quality theme)
gt = gt.tab_options(
    column_labels_background_color='#CFEAD9',
    column_labels_border_bottom_color='#CCCCCC',
    column_labels_border_bottom_width='2px',
    column_labels_border_bottom_style='solid',
)

# Small-color polish
gt = stub_tint(gt, hue='forest')

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color='#E8E8E8',
    table_body_hlines_width='1px',
)

# Source note
gt = gt.tab_source_note(source_note='Source: airquality.csv — monthly averages computed from daily observations.')

# Frame and finalize
gt = frame(gt)
finalize(gt, path='table.png', zoom=2.0, expand=15)
