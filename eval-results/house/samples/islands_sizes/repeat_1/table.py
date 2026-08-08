import pandas as pd
from great_tables import GT, md
from great_tables import loc, style

# Import helpers from the house-table reference
import sys
sys.path.insert(0, './.claude/skills/great-tables-house/scripts')
from house_table import PALETTE, frame, finalize, stripe, stub_tint, heatmap, humanize_labels

# Load the data
df = pd.read_csv('./islands.csv')

# Create the GT table with island name as the stub
gt = GT(df, rowname_col='name')

# Add title and subtitle
gt = gt.tab_header(
    title='World Islands by Size',
    subtitle=md('Land area in thousands of square kilometers')
)

# Format the size column
gt = gt.fmt_number(columns='size', decimals=0, use_seps=True)

# Humanize labels
gt = humanize_labels(gt, df, overrides={'size': 'Size (1000s km²)'})

# Apply the sequential heatmap for the size measure (neutral/Blues)
gt = heatmap(gt, 'size', kind='sequential', hue='neutral')

# Heading band - navy accent tint (default for neutral/Blues heatmap)
gt = gt.tab_options(
    column_labels_background_color='#C9E0F0',
    column_labels_border_bottom_color=PALETTE['neutral']['column_label_rule'],
    column_labels_border_bottom_width='2px',
    column_labels_border_bottom_style='solid',
)

# Striping and stub tint for visual clarity (>= 10 rows and not fully colored)
gt = stripe(gt)
gt = stub_tint(gt, hue='navy')

# Row hairlines between body rows (non-negotiable base)
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color=PALETTE['neutral']['hairline'],
    table_body_hlines_width='1px',
)

# Add frame border (non-negotiable base)
gt = frame(gt)

# Add source note (non-negotiable base)
gt = gt.tab_source_note(source_note='Source: provided dataset.')

# Finalize with render (non-negotiable base)
finalize(gt, path='table.png', zoom=2.0, expand=15)
