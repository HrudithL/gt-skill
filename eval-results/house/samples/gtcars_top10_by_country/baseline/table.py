import pandas as pd
import great_tables as gt

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']]

# Sort by country origin, then by price descending
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Create the table
gt_table = (
    gt.GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_label(
        mfr="Manufacturer",
        model="Model",
        year="Year",
        ctry_origin="Country",
        drivetrain="Drivetrain",
        trsmn="Transmission",
        msrp="MSRP"
    )
    .fmt_currency(columns="msrp", currency="USD")
    .cols_width({
        'mfr': '120px',
        'model': '150px',
        'year': '60px',
        'ctry_origin': '130px',
        'drivetrain': '100px',
        'trsmn': '110px',
        'msrp': '130px'
    })
    .tab_options(
        container_width='100%',
        table_font_size='11px'
    )
)

gt_table.gtsave('table.png')
