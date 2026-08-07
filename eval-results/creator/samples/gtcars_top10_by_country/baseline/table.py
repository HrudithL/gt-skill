import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars overall
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "year", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Format the data for display
top_10["Country"] = top_10["ctry_origin"]
top_10["Make"] = top_10["mfr"]
top_10["Model"] = top_10["model"]
top_10["Year"] = top_10["year"].astype(int)
top_10["Drivetrain"] = top_10["drivetrain"].str.upper()
top_10["Transmission"] = top_10["trsmn"]
top_10["Price"] = top_10["msrp"]

# Sort by country, then by price descending for display
display_df = top_10[["Country", "Make", "Model", "Year", "Drivetrain", "Transmission", "Price"]].sort_values(
    by=["Country", "Price"], ascending=[True, False]
).reset_index(drop=True)

# Create the GT table
gt_table = (
    GT(display_df)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .fmt_currency(columns=["Price"], currency="USD")
    .cols_label(
        Country="Country",
        Make="Make",
        Model="Model",
        Year="Year",
        Drivetrain="Drivetrain",
        Transmission="Transmission",
        Price="MSRP"
    )
)

gt_table.gtsave("table.png")
