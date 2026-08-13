import pandas as pd
from great_tables import GT

# Load the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'ctry_origin', 'msrp', 'drivetrain', 'trsmn']].copy()

# Sort by country first, then by price (descending)
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Create the GT table
gt = (
    GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_label(
        mfr="Manufacturer",
        model="Model",
        ctry_origin="Country",
        msrp="Price (USD)",
        drivetrain="Drivetrain",
        trsmn="Transmission"
    )
    .fmt_currency(
        columns='msrp',
        currency='USD'
    )
)

gt.gtsave("table.png")
