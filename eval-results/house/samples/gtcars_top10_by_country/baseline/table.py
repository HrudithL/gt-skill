import pandas as pd
import great_tables as gt

# Read the data
df = pd.read_csv('gtcars.csv')

# Get top 10 most expensive cars
top_10 = df.nlargest(10, 'msrp')[['mfr', 'model', 'year', 'ctry_origin', 'drivetrain', 'trsmn', 'msrp']].copy()

# Sort by country then by price descending
top_10 = top_10.sort_values(['ctry_origin', 'msrp'], ascending=[True, False]).reset_index(drop=True)

# Create a clean table
table = (
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
    .fmt_currency(
        columns="msrp",
        currency="USD"
    )
    .cols_align(
        align="left",
        columns=["mfr", "model", "year", "ctry_origin", "drivetrain", "trsmn"]
    )
    .cols_align(
        align="right",
        columns=["msrp"]
    )
    .tab_options(
        table_font_size="11pt"
    )
)

table.gtsave("table.png")
print("Table saved to table.png")
