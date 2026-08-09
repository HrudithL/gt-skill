import pandas as pd
from great_tables import GT, md
import sys
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap

# Load and aggregate data
df = pd.read_csv('airquality.csv')

# Map month numbers to names
month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}

# Calculate monthly averages
monthly_stats = df.groupby('Month').agg({
    'Temp': 'mean',
    'Wind': 'mean',
    'Ozone': 'mean',
}).reset_index()

# Add month names
monthly_stats['Month_Name'] = monthly_stats['Month'].map(month_names)

# Reorder columns and round values
monthly_stats = monthly_stats[['Month_Name', 'Temp', 'Wind', 'Ozone']].copy()
monthly_stats = monthly_stats.round(1)

# Create GT table
gt = GT(monthly_stats, rowname_col='Month_Name')
gt = gt.tab_header(
    title='Air Quality Monthly Summary',
    subtitle=md('Average temperature, wind speed, and ozone levels by month')
)
gt = gt.tab_stubhead(label='Month')

# Format columns
gt = gt.fmt_number(columns='Temp', decimals=1)
gt = gt.fmt_number(columns='Wind', decimals=1)
gt = gt.fmt_number(columns='Ozone', decimals=1)

# Add column labels
from great_tables import loc, style
gt = gt.cols_label(
    Temp='Avg Temp (°F)',
    Wind='Avg Wind (mph)',
    Ozone='Avg Ozone (ppb)'
)

# Apply the two heatmaps (max allowed): Temperature (sequential) and Wind (sequential)
# Temperature uses Greens hue since it represents heat/intensity
gt = heatmap(gt, 'Temp', kind='sequential', hue='warning')
# Wind uses Blues hue for a neutral magnitude
gt = heatmap(gt, 'Wind', kind='sequential', hue='neutral')

# Apply house styling
gt = band(gt, hue='forest')
gt = stub_tint(gt, hue='forest')

# Add source note
gt = gt.tab_source_note('Source: provided dataset.')

# Apply frame and finalize
gt = frame(gt)
finalize(gt, path='table.png')
