import pandas as pd
from great_tables import GT, loc, md
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the data
df = pd.read_csv('gtcars.csv')

# Create composite row identifier: manufacturer + model
df['car'] = df['mfr'] + ' ' + df['model']

# Select relevant columns and order them
df_table = df[['car', 'hp', 'msrp']].copy()

# Sort by horsepower descending for visual interest
df_table = df_table.sort_values('hp', ascending=False).reset_index(drop=True)

# Create the GT table
gt = GT(df_table, rowname_col='car')

# Title and subtitle
gt = gt.tab_header(
    title='GT Cars Performance',
    subtitle='Horsepower and pricing across leading performance vehicles'
)

# Column labels
gt = humanize_labels(gt, df_table, overrides={'msrp': 'Price'})

# Format columns
gt = gt.fmt_integer(columns='hp')
gt = gt.fmt_currency(columns='msrp', decimals=0)

# Apply striping (no heatmap fills the whole table, so striping applies)
gt = stripe(gt)

# Stub tint for row labels
gt = stub_tint(gt, hue='navy')

# Horsepower heatmap (sequential, neutral for magnitude)
gt = heatmap(gt, 'hp', kind='sequential', hue='neutral')

# Column label band
gt = band(gt, hue='navy')

# Frame and hairlines
gt = frame(gt)
gt = hairlines(gt)

# Source notes
gt = gt.tab_source_note(
    source_note='Horsepower represents maximum output at peak RPM; vehicles ranked by horsepower in descending order.'
)
gt = gt.tab_source_note(
    source_note='Source: provided dataset.'
)

# Finalize and save
finalize(gt, path='table.png')
