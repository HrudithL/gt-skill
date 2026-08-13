import pandas as pd
from great_tables import GT

# Read the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")[["mfr", "model", "year", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()

# Sort by country, then by price descending
top_10 = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Format the data for display
top_10["price"] = "$" + (top_10["msrp"] / 1000).round(1).astype(str) + "K"
top_10["car"] = top_10["mfr"] + " " + top_10["model"] + " (" + top_10["year"].astype(str) + ")"
top_10["drivetrain_label"] = top_10["drivetrain"].str.upper()
top_10["transmission"] = top_10["trsmn"]

# Select columns for display
display_df = top_10[["ctry_origin", "car", "drivetrain_label", "transmission", "price"]]
display_df.columns = ["Country", "Vehicle", "Drivetrain", "Transmission", "MSRP"]

# Create the GT table
gt = (
    GT(display_df)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .cols_width({
        "Country": "120px",
        "Vehicle": "250px",
        "Drivetrain": "100px",
        "Transmission": "110px",
        "MSRP": "100px"
    })
)

# Save the table
gt.gtsave("table.png")
print("Table created and saved to table.png")
