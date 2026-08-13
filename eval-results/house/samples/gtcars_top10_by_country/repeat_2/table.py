import pandas as pd
import numpy as np
from great_tables import GT, loc, md, style
from house_table import PALETTE, frame, hairlines, finalize, band, \
    stripe, stub_tint, heatmap, status_chip, summary_row, \
    group_emphasis, humanize_labels

# Read data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
df_top10 = df.nlargest(10, 'msrp').copy()

# Create composite identifier for row names
df_top10['car'] = df_top10['mfr'] + ' ' + df_top10['model']

# Select and organize columns
df_table = df_top10[[
    'car',
    'ctry_origin',
    'msrp',
    'drivetrain',
    'trsmn'
]].reset_index(drop=True)

# Prepare for display
df_table = df_table.rename(columns={
    'car': 'car',
    'ctry_origin': 'country',
    'msrp': 'price',
    'drivetrain': 'drivetrain',
    'trsmn': 'transmission'
})

# Build the table
gt = (
    GT(df_table, rowname_col='car', groupname_col='country')
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle=md('By MSRP, grouped by country of origin')
    )
    .tab_stubhead(label='Vehicle')
    .fmt_currency(columns='price', decimals=0)
    .sub_missing(columns=['price', 'drivetrain', 'transmission'], missing_text='—')
)

# Humanize labels with overrides
gt = humanize_labels(
    gt,
    df_table,
    overrides={
        'price': 'Price (MSRP)',
        'drivetrain': 'Drivetrain',
        'transmission': 'Transmission'
    }
)

# Column widths + padding
gt = gt.cols_width(
    cases={
        'car': '180px',
        'country': '140px',
        'price': '130px',
        'drivetrain': '100px',
        'transmission': '100px',
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

# Big Color: price is the hero measure (sequential, neutral/Blues)
gt = heatmap(gt, 'price', kind='sequential', hue='neutral')

# Branding surfaces
gt = band(gt, hue='navy')

# Small-Color polish
gt = stripe(gt)
gt = stub_tint(gt, hue='navy')
gt = group_emphasis(gt)

# Source notes: analytical caption first, then provenance
gt = (
    gt.tab_source_note(
        source_note='Ranked by manufacturer\'s suggested retail price (MSRP) in descending order.'
    )
    .tab_source_note(source_note='Source: provided dataset.')
)

# Finalize
gt = hairlines(gt)
gt = frame(gt)
finalize(gt, path='table.png')
