import pandas as pd
import numpy as np
from great_tables import GT, style, loc

# Step 1: UNDERSTAND & CLEAN DATA
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars globally
df_top10 = df.nlargest(10, 'msrp').copy()

# Create composite car identifier for stub
df_top10['car'] = df_top10['mfr'] + ' ' + df_top10['model']

# Prepare display data: select and order columns
df_display = df_top10[['car', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()
df_display = df_display.rename(columns={
    'car': 'Car',
    'ctry_origin': 'Country',
    'drivetrain': 'Drivetrain',
    'trsmn': 'Transmission',
    'msrp': 'MSRP ($)'
})

# Sort by country then by MSRP descending for better grouping
df_display = df_display.sort_values(['Country', 'MSRP ($)'], ascending=[True, False])

# Step 2: ORGANIZE COLUMNS
# Set up stub and groups
gt = GT(
    df_display,
    rowname_col='Car',
    groupname_col='Country'
)

# Step 3: BIG COLOR - MSRP is ordered magnitude, 10 rows ≥ 5
# Sequential fill: price is neutral magnitude → Blues palette
# Compute domain from data
lo = float(np.nanmin(df_display[['MSRP ($)']].to_numpy()))
hi = float(np.nanmax(df_display[['MSRP ($)']].to_numpy()))

gt = (
    gt
    .fmt_currency(columns='MSRP ($)', currency='USD', decimals=0)
    .data_color(
        columns='MSRP ($)',
        palette='Blues',
        domain=[lo, hi],
        truncate=False,
        na_color='#808080',
    )
)

# Step 4: HEADING BAND - fixed navy band with white text
gt = gt.tab_options(
    heading_background_color='#08306B',
    heading_align='center',
    heading_title_font_weight='bold',
    heading_subtitle_font_weight='normal',
)

# Pin white column-label text explicitly
gt = gt.tab_style(
    style=style.text(color='white'),
    locations=loc.column_labels()
)

# Step 5: SMALL COLOR CHECKLIST
# (a) Cell borders - hairlines between rows
gt = gt.tab_options(
    table_body_hlines_style='solid',
    table_body_hlines_color='#E8E8E8',
    table_body_hlines_width='1px',
)

# Column-label bottom rule
gt = gt.tab_options(
    column_labels_border_bottom_color='#CCCCCC',
    column_labels_border_bottom_width='2px',
)

# (c) Row striping - apply by default
gt = gt.opt_row_striping()
gt = gt.tab_options(row_striping_background_color='#F6F6F6')

# (d) Stub tint - fixed pale blue
gt = gt.tab_style(
    style=style.fill(color='#EAF0F6'),
    locations=loc.stub(),
)

# (e) Format missing values
gt = gt.sub_missing(columns=['Drivetrain', 'Transmission'], missing_text='—')

# Step 6: TITLES & ANNOTATIONS
gt = (
    gt
    .tab_header(
        title='Top 10 Most Expensive GT Cars',
        subtitle='Grouped by Country of Origin'
    )
    .tab_source_note(
        source_note='Price in USD (Manufacturer Suggested Retail Price). Cars ranked by MSRP in descending order.'
    )
    .tab_source_note(
        source_note='Source: gtcars.csv'
    )
)

# Global frame and layout options
gt = gt.tab_options(
    table_layout='auto',
)

# Step 7: RENDER & VERIFY
gt.gtsave('table.png')
print("Table rendered successfully to table.png")
