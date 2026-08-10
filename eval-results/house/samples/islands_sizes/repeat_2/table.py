import pandas as pd
from great_tables import GT, md

# Import helpers from the house-format skill
import sys
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, hairlines, finalize, band, heatmap

# Load data
df = pd.read_csv('islands.csv')

# Sort by size descending for better readability
df = df.sort_values('size', ascending=False).reset_index(drop=True)

# Build the table
gt = GT(df, rowname_col='name')
gt = gt.tab_header(
    title='World Islands by Size',
    subtitle=md('Total area in thousands of square kilometers'),
)
gt = gt.tab_stubhead(label='Island')

# Format the size column as thousands with no decimals
gt = gt.fmt_number(columns='size', decimals=0, use_seps=True)

# Relabel the size column
gt = gt.cols_label(size='Size (1000 km²)')

# Apply the sequential heatmap for the size magnitude (Blues is neutral for a plain magnitude)
gt = heatmap(gt, 'size', kind='sequential', hue='neutral')

# Apply the house-format styling
gt = band(gt, hue='navy')
gt = hairlines(gt)
gt = frame(gt)

# Source note
gt = gt.tab_source_note(source_note='Source: provided dataset.')

# Save with the mandatory renderer
finalize(gt, path='table.png')
