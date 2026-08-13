import pandas as pd
import great_tables as gt
from nokap import webshot
import tempfile
import os

# Read the air quality data
df = pd.read_csv('airquality.csv')

# Calculate monthly averages
monthly_avg = df.groupby('Month')[['Temp', 'Wind', 'Ozone']].mean().reset_index()

# Create a mapping for month names
month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}

monthly_avg['Month'] = monthly_avg['Month'].map(month_names)

# Rename columns for display
monthly_avg.columns = ['Month', 'Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)']

# Create the table
gt_table = (
    gt.GT(monthly_avg)
    .fmt_number(columns=['Avg Temperature (°F)', 'Avg Wind Speed (mph)', 'Avg Ozone (ppb)'], decimals=1)
    .tab_header(
        title='Air Quality Data: Monthly Averages',
        subtitle='Temperature, Wind Speed, and Ozone Levels'
    )
    .tab_options(
        table_width='600px'
    )
)

# Save as HTML temporarily and then capture with webshot
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
    html_path = f.name
    f.write(gt_table.as_raw_html())

try:
    webshot(html_path, 'table.png')
finally:
    os.unlink(html_path)
