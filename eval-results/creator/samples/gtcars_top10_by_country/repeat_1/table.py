import pandas as pd
from great_tables import GT, md
from gt_house_style import apply_house_style, humanize_labels

df = pd.read_csv("gtcars.csv")

# Clean the data: drop rows with missing MSRP
df = df.dropna(subset=["msrp"])

# Sort by MSRP descending and get top 10
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "drivetrain", "trsmn", "ctry_origin", "msrp"]].copy()

# Rename columns for readability
top_10 = top_10.rename(columns={
    "mfr": "Manufacturer",
    "model": "Model",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "ctry_origin": "Country",
    "msrp": "Price"
})

# Sort by Country and then by Price (descending) for better grouping
top_10 = top_10.sort_values(["Country", "Price"], ascending=[True, False]).reset_index(drop=True)

# Create the GT table
tbl = (
    GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle=md("Grouped by country of origin, with drivetrain and transmission details"),
    )
    .fmt_currency(columns="Price", currency="USD", decimals=0)
    .sub_missing(missing_text="—")
    .tab_source_note(source_note="Source: gtcars.csv dataset")
)

# Apply house style
tbl = apply_house_style(tbl)

# Save the table
tbl.gtsave("table.png", zoom=2, expand=10)
print("Table saved to table.png")
