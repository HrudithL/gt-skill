import pandas as pd
from great_tables import GT

df = pd.read_csv("gtcars.csv")

df_sorted = df.nlargest(10, "msrp")

df_sorted = df_sorted.sort_values("ctry_origin")

df_display = df_sorted[["mfr", "model", "year", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
df_display.columns = ["Manufacturer", "Model", "Year", "Country", "Drivetrain", "Transmission", "MSRP"]

df_display["MSRP"] = df_display["MSRP"].apply(lambda x: f"${x:,.0f}")

gt = (
    GT(df_display)
    .tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin"
    )
    .tab_stubhead(label="")
)

gt.gtsave("table.png")
