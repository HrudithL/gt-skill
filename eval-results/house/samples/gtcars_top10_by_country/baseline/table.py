import pandas as pd
from great_tables import GT

df = pd.read_csv('gtcars.csv')

top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'drivetrain', 'trsmn', 'ctry_origin', 'msrp']].copy()
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])
top_10['msrp'] = top_10['msrp'].astype('int64')

gt = (
    GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_label(
        mfr="Manufacturer",
        model="Model",
        year="Year",
        drivetrain="Drivetrain",
        trsmn="Transmission",
        ctry_origin="Country",
        msrp="MSRP"
    )
    .fmt_currency(
        columns='msrp',
        currency='USD'
    )
    .cols_move(
        after='ctry_origin',
        columns=['mfr', 'model', 'year', 'drivetrain', 'trsmn', 'msrp']
    )
)

gt.gtsave('table.png')
