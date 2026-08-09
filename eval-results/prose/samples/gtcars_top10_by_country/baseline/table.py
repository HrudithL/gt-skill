import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "ctry_origin", "drivetrain", "trsmn", "msrp"]].reset_index(drop=True)

# Sort by country and then by price (descending) for better grouping
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False]).reset_index(drop=True)

# Rename columns for clarity
top_10 = top_10.rename(columns={
    "mfr": "Manufacturer",
    "model": "Model",
    "ctry_origin": "Country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "MSRP"
})

# Format MSRP as currency
top_10["MSRP"] = top_10["MSRP"].apply(lambda x: f"${x:,.0f}")

# Create the GT table
gt = (
    GT(top_10)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin with Drivetrain & Transmission Details"
    )
)

gt.gtsave("table.png")
