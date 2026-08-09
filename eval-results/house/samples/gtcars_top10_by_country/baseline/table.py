import pandas as pd
from great_tables import GT

# Read the CSV file
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()

# Sort by country and price within country
top_10_sorted = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False])

# Create the GT table
gt_table = (
    GT(top_10_sorted)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin with Drivetrain & Transmission"
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
    .fmt_currency(
        columns=["msrp"],
        currency="USD"
    )
    .cols_width({"mfr": "100px", "model": "100px", "year": "60px", "ctry_origin": "120px", "drivetrain": "90px", "trsmn": "80px", "msrp": "120px"})
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="lightgray"
    )
)

gt_table.gtsave("table.png")
