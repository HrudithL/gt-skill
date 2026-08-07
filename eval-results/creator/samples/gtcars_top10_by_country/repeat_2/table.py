import pandas as pd
from great_tables import GT, md
import sys
sys.path.insert(0, '/Users/hrudithl/Documents/posit-dev/gtskill/.claude/skills/great-tables')
from gt_house_style import apply_house_style, humanize_labels

# Load and prepare data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'msrp', 'ctry_origin', 'drivetrain', 'trsmn']].reset_index(drop=True)

# Create a clean label for transmission
transmission_map = {
    '7a': '7-Speed Automatic',
    '6a': '6-Speed Automatic',
    '8a': '8-Speed Automatic',
    '9a': '9-Speed Automatic',
    '7m': '7-Speed Manual',
    '6m': '6-Speed Manual',
    '1dd': '1-Speed Direct Drive',
    '6am': '6-Speed Automatic/Manual',
    '7am': '7-Speed Automatic/Manual',
    '8am': '8-Speed Automatic/Manual',
}
top_10['transmission'] = top_10['trsmn'].map(transmission_map)

# Clean drivetrain labels
drivetrain_map = {
    'rwd': 'RWD',
    'awd': 'AWD',
    'fwd': 'FWD'
}
top_10['drivetrain_label'] = top_10['drivetrain'].map(drivetrain_map)

# Sort by country then by price descending
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Select final columns for display
display_df = top_10[['mfr', 'model', 'year', 'ctry_origin', 'drivetrain_label', 'transmission', 'msrp']].copy()
display_df.columns = ['Manufacturer', 'Model', 'Year', 'Country', 'Drivetrain', 'Transmission', 'MSRP']

# Create the table
tbl = (
    GT(display_df)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin, with drivetrain and transmission details"),
    )
    .fmt_currency(columns='MSRP', currency='USD', decimals=0)
    .fmt_integer(columns='Year')
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: gtcars.csv dataset")
)

# Apply house style
tbl = apply_house_style(tbl)

# Save to PNG
tbl.gtsave('table.png', zoom=2, expand=10)
print("Table saved to table.png")
