import pandas as pd
from great_tables import GT
from great_tables.data import exibble

df = pd.read_csv('./gtcars.csv')

# Sort by MSRP and get top 10
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()

# Format transmission codes for readability
trans_map = {
    '7a': '7-Speed Auto',
    '6a': '6-Speed Auto',
    '8am': '8-Speed Auto',
    '6m': '6-Speed Manual',
    '7m': '7-Speed Manual',
    '9a': '9-Speed Auto',
    '1dd': '1-Speed Direct Drive',
    '8a': '8-Speed Auto'
}
top_10['trsmn'] = top_10['trsmn'].map(trans_map).fillna(top_10['trsmn'])

# Format drivetrain for readability
drivetrain_map = {
    'rwd': 'RWD',
    'awd': 'AWD',
    'fwd': 'FWD'
}
top_10['drivetrain'] = top_10['drivetrain'].map(drivetrain_map).fillna(top_10['drivetrain'])

# Rename columns for display
top_10 = top_10.rename(columns={
    'mfr': 'Manufacturer',
    'model': 'Model',
    'year': 'Year',
    'ctry_origin': 'Country',
    'drivetrain': 'Drivetrain',
    'trsmn': 'Transmission',
    'msrp': 'MSRP'
})

# Sort by Country then MSRP descending for better grouping visualization
top_10 = top_10.sort_values(['Country', 'MSRP'], ascending=[True, False]).reset_index(drop=True)

# Create GT table
gt = (GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Grouped by country of origin with drivetrain and transmission details"
    )
    .fmt_currency(columns='MSRP', currency='USD')
    .cols_width({
        'Manufacturer': '100px',
        'Model': '120px',
        'Year': '60px',
        'Country': '110px',
        'Drivetrain': '100px',
        'Transmission': '130px',
        'MSRP': '140px'
    })
)

gt.gtsave('table.png')
