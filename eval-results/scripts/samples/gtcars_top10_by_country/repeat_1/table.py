import pandas as pd
import numpy as np
from great_tables import GT, style, loc
from gt_consistency import heatmap, band, frame, finalize, stripe, stub_tint

# Step 1: Load and prepare data
df = pd.read_csv('gtcars.csv')

# Filter to top 10 most expensive cars
top10 = df.nlargest(10, 'msrp').copy()

# Create a display label for car identification (mfr + model)
top10['car'] = top10['mfr'] + ' ' + top10['model']

# Select and organize columns for display
# Group by country, so we'll use groupname_col
cols_display = ['car', 'drivetrain', 'trsmn', 'msrp']
display_df = top10[['ctry_origin', 'car', 'drivetrain', 'trsmn', 'msrp']].copy()

# Sort by country, then by price descending (for visual grouping)
display_df = display_df.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Rename columns for display
display_df = display_df.rename(columns={
    'ctry_origin': 'Country',
    'car': 'Car',
    'drivetrain': 'Drivetrain',
    'trsmn': 'Transmission',
    'msrp': 'MSRP'
})

# Reorder columns: Country, Car, Drivetrain, Transmission, MSRP
display_df = display_df[['Country', 'Car', 'Drivetrain', 'Transmission', 'MSRP']]

# Step 2: Create GT with grouping by country
gt = GT(display_df, groupname_col='Country', rowname_col='Car')

# Step 3: Apply big color to MSRP (ordered magnitude with ≥5 rows)
# Neutral magnitude (price) uses Blues, sequential kind
gt = heatmap(gt, columns=['MSRP'], kind='sequential', hue='neutral')

# Step 4: Apply heading band
gt = band(gt)

# Step 5: Apply small color polish
gt = stripe(gt)
gt = stub_tint(gt)

# Format currency column
gt = gt.fmt_currency(columns=['MSRP'], decimals=0, use_seps=True)

# Format drivetrain and transmission as plain text (no special formatting)
# These are categorical, not numeric

# Apply cell borders (hairline between rows)
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color='#E8E8E8',
    table_body_hlines_width='1px',
    column_labels_border_bottom_color='#CCCCCC',
    column_labels_border_bottom_width='2px',
)

# Row group styling (bold + structural rule)
gt = gt.tab_options(
    row_group_font_weight='bold',
    row_group_border_top_color='#BDBDBD',
    row_group_border_bottom_color='#BDBDBD',
    row_group_padding='6px',
)

# Compact layout
gt = gt.cols_width(cases={
    'Car': '180px',
    'Drivetrain': '100px',
    'Transmission': '110px',
    'MSRP': '120px',
})

gt = gt.tab_options(
    heading_padding='6px',
    column_labels_padding='6px',
    column_labels_padding_horizontal='8px',
    data_row_padding='5px',
    data_row_padding_horizontal='8px',
    source_notes_padding='6px',
)

# Step 6: Add titles and annotations
gt = gt.tab_header(
    title='Top 10 Most Expensive GT Cars',
    subtitle='Grouped by Country of Origin'
)

gt = gt.tab_source_note(
    source_note='Price represents manufacturer suggested retail price (MSRP) at the time of listing.'
)

gt = gt.tab_source_note(
    source_note='Source: gtcars.csv'
)

# Step 7: Apply frame and finalize
gt = frame(gt)
gt = finalize(gt)

# Render
gt.gtsave('table.png')
