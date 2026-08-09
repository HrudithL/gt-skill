import pandas as pd
from great_tables import GT, md, style, loc
from gt_consistency import frame, finalize, band, stripe, PALETTE

df = pd.read_csv("gtcars.csv")

# Step 1: Clean and prepare data
# Get top 10 most expensive cars
df_top10 = df.nlargest(10, "msrp").copy()

# Sort by country, then price descending for better grouping
df_top10 = df_top10.sort_values(["ctry_origin", "msrp"], ascending=[True, False])

# Select and rename columns for display
df_display = df_top10[["ctry_origin", "mfr", "model", "year", "msrp", "drivetrain", "trsmn"]].copy()
df_display.columns = ["Country", "Manufacturer", "Model", "Year", "Price", "Drivetrain", "Transmission"]

# Step 2: Organize columns with grouping by country and manufacturer as stub
gt = (
    GT(df_display, groupname_col="Country", rowname_col="Manufacturer")
    .fmt_currency(columns="Price", currency="USD")
)

# Step 3: No Big Color (categorical table with no magnitude fills)

# Step 4: Dark band (no Big Color)
gt = band(gt, shade="dark", hue="navy")

# Step 5: Small Color polish
gt = stripe(gt)
gt = frame(gt)

# Step 6: Titles and finalize
gt = (
    gt
    .tab_header(
        title="Top 10 Most Expensive GT Cars by Country",
        subtitle="Includes drivetrain and transmission details"
    )
)

finalize(gt)
