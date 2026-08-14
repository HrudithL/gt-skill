import pandas as pd
import numpy as np
from great_tables import GT, md, style, loc
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap

df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().round(2)

# Map month numbers to names
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
monthly['month_label'] = monthly.index.map(month_names)

# Reorder columns: month first, then measures
monthly = monthly[['month_label', 'Temp', 'Wind', 'Ozone']]
monthly = monthly.reset_index(drop=True)

# Create GT table
gt = (
    GT(monthly, rowname_col='month_label')
    .tab_header(
        title='Air Quality Monthly Summary',
        subtitle=md('Average temperature, wind speed, and ozone levels by month'),
    )
    .tab_stubhead(label='Month')
    .fmt_number(columns=['Temp', 'Wind', 'Ozone'], decimals=2)
)

# Humanize labels
gt = gt.cols_label(
    month_label='Month',
    Temp='Temperature (°F)',
    Wind='Wind Speed (mph)',
    Ozone='Ozone (ppb)',
)

# Set column widths and padding
gt = gt.cols_width(
    cases={
        'month_label': '100px',
        'Temp': '140px',
        'Wind': '140px',
        'Ozone': '140px',
    }
)
gt = gt.tab_options(
    heading_padding='6px',
    column_labels_padding='6px',
    column_labels_padding_horizontal='8px',
    data_row_padding='5px',
    data_row_padding_horizontal='8px',
    source_notes_padding='6px',
)

# Apply heatmaps: temperature and ozone are the main measures
# Temperature: sequential (neutral/Blues, higher is more interesting)
# Ozone: sequential (positive/Greens, higher pollution is notable)
# Wind stays plain text
gt = heatmap(gt, 'Temp', kind='sequential', hue='neutral')
gt = heatmap(gt, 'Ozone', kind='sequential', hue='positive')

# Branding: band, stripe, stub tint
gt = band(gt, hue='navy')
gt = stripe(gt)
gt = stub_tint(gt, hue='navy')

# Source notes
gt = (
    gt.tab_source_note(
        source_note='Wind speed is displayed as plain text. Temperature and Ozone levels are color-coded by magnitude.'
    )
    .tab_source_note(source_note='Source: New York air quality data, May–September 1973.')
)

# Frame and hairlines
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path='table.png')
