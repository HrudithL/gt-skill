import pandas as pd
import great_tables as gt

# Load the data
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars
top_10 = df.nlargest(10, "msrp")

# Sort by country and then by price
top_10_sorted = top_10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Prepare the table data
table_data = top_10_sorted[["ctry_origin", "mfr", "model", "year", "drivetrain", "trsmn", "msrp"]].copy()
table_data.columns = ["Country", "Manufacturer", "Model", "Year", "Drivetrain", "Transmission", "MSRP"]

# Create the great_tables table with grouping by Country
gt_table = (
    gt.GT(table_data, groupname_col="Country")
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .fmt_currency(columns=["MSRP"], currency="USD")
    .cols_label(
        Drivetrain="Drivetrain",
        Transmission="Transmission",
        MSRP="Price (USD)"
    )
    .tab_options(
        container_width="900px"
    )
)

# Render to PNG
gt_table.gtsave("table.png")
print("Table rendered successfully to table.png")
