import pandas as pd
from great_tables import GT, md
import sys
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Load and aggregate data by month
df = pd.read_csv('./airquality.csv')

month_names = {
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September'
}

# Group by month and calculate averages
monthly_avg = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean'
}).round(1)

# Rename columns for display
monthly_avg.columns = ['avg_temp', 'avg_wind', 'avg_ozone']

# Add month name as a column for the stub
monthly_avg['Month'] = monthly_avg.index.map(month_names)
monthly_avg = monthly_avg[['Month', 'avg_temp', 'avg_wind', 'avg_ozone']]
monthly_avg = monthly_avg.reset_index(drop=True)

# Create GT object with Month as stub
gt = (
    GT(monthly_avg, rowname_col='Month')
    .tab_header(
        title='Air Quality Monthly Summary',
        subtitle=md('Average temperature, wind speed, and ozone levels by month'),
    )
    .fmt_number(columns='avg_temp', decimals=1)
    .fmt_number(columns='avg_wind', decimals=1)
    .fmt_number(columns='avg_ozone', decimals=1)
    .tab_source_note(source_note='Source: provided dataset.')
)

# Apply humanize_labels to convert snake_case to Title Case
gt = humanize_labels(
    gt,
    monthly_avg,
    overrides={
        'avg_temp': 'Avg Temperature (°F)',
        'avg_wind': 'Avg Wind Speed (mph)',
        'avg_ozone': 'Avg Ozone (ppb)'
    }
)

# Apply Big Color: 1 sequential heatmap for temperature (sequential/neutral)
gt = heatmap(gt, 'avg_temp', kind='sequential', hue='neutral')

# Apply heading band
gt = band(gt, hue='navy')

# Apply striping (5 body rows is below 10-row gate, but we can evaluate)
# 5 rows < 10, so skip striping per the gate in stripe()

# Apply stub tint
gt = stub_tint(gt, hue='navy')

# Apply hairlines and frame
gt = hairlines(gt)
gt = frame(gt)

# Finalize and save
finalize(gt, path='table.png')
