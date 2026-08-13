import pandas as pd
from great_tables import GT
import great_tables as gt

df = pd.read_csv('gtcars.csv')

top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'ctry_origin', 'msrp', 'drivetrain', 'trsmn']]

top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

gt_table = (
    GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_label(
        mfr="Manufacturer",
        model="Model",
        year="Year",
        ctry_origin="Country",
        msrp="MSRP",
        drivetrain="Drivetrain",
        trsmn="Transmission"
    )
    .fmt_currency(columns=['msrp'], currency='USD')
    .cols_align(align='center', columns=['year', 'drivetrain', 'trsmn'])
    .cols_align(align='right', columns=['msrp'])
)

gt_table.gtsave('table.png')
