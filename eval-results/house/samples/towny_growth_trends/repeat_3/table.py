import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap

# Read the data
df = pd.read_csv("towny.csv")

# Calculate overall growth rate (1996 to 2021)
df["overall_growth"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth")[["name", "population_1996", "density_1996",
                                              "population_2001", "density_2001",
                                              "population_2006", "density_2006",
                                              "population_2011", "density_2011",
                                              "population_2016", "density_2016",
                                              "population_2021", "density_2021",
                                              "pop_change_1996_2001_pct",
                                              "pop_change_2001_2006_pct",
                                              "pop_change_2006_2011_pct",
                                              "pop_change_2011_2016_pct",
                                              "pop_change_2016_2021_pct"]].reset_index(drop=True)

# Create a display table with selected columns
# Reshape to show Population and Density for each census year
display_data = []
for idx, row in top_15.iterrows():
    display_data.append({
        "Town": row["name"],
        "Pop 1996": int(row["population_1996"]),
        "Density 1996": round(row["density_1996"], 1),
        "Pop 2001": int(row["population_2001"]),
        "Density 2001": round(row["density_2001"], 1),
        "Chg 96-01 %": row["pop_change_1996_2001_pct"],
        "Pop 2006": int(row["population_2006"]),
        "Density 2006": round(row["density_2006"], 1),
        "Chg 01-06 %": row["pop_change_2001_2006_pct"],
        "Pop 2011": int(row["population_2011"]),
        "Density 2011": round(row["density_2011"], 1),
        "Chg 06-11 %": row["pop_change_2006_2011_pct"],
        "Pop 2016": int(row["population_2016"]),
        "Density 2016": round(row["density_2016"], 1),
        "Chg 11-16 %": row["pop_change_2011_2016_pct"],
        "Pop 2021": int(row["population_2021"]),
        "Density 2021": round(row["density_2021"], 1),
        "Chg 16-21 %": row["pop_change_2016_2021_pct"],
    })

table_df = pd.DataFrame(display_data)

# Build the GT table
gt = (
    GT(table_df, rowname_col="Town")
    .tab_header(
        title="Ontario's Top 15 Fastest-Growing Towns",
        subtitle=md("Population growth and density trends across census years (1996–2021)")
    )
    .tab_spanner(label="1996", columns=["Pop 1996", "Density 1996"])
    .tab_spanner(label="2001", columns=["Pop 2001", "Density 2001", "Chg 96-01 %"])
    .tab_spanner(label="2006", columns=["Pop 2006", "Density 2006", "Chg 01-06 %"])
    .tab_spanner(label="2011", columns=["Pop 2011", "Density 2011", "Chg 06-11 %"])
    .tab_spanner(label="2016", columns=["Pop 2016", "Density 2016", "Chg 11-16 %"])
    .tab_spanner(label="2021", columns=["Pop 2021", "Density 2021", "Chg 16-21 %"])
    # Format population columns
    .fmt_number(columns=["Pop 1996", "Pop 2001", "Pop 2006", "Pop 2011", "Pop 2016", "Pop 2021"],
                decimals=0, use_seps=True)
    # Format density columns
    .fmt_number(columns=["Density 1996", "Density 2001", "Density 2006", "Density 2011", "Density 2016", "Density 2021"],
                decimals=1, use_seps=False)
    # Format percentage change columns
    .fmt_percent(columns=["Chg 96-01 %", "Chg 01-06 %", "Chg 06-11 %", "Chg 11-16 %", "Chg 16-21 %"],
                 decimals=1)
    .tab_source_note("Source: Statistics Canada Census data, 1996–2021. Density in persons per km². Ranked by overall population growth 1996–2021.")
)

# Apply big color: heatmap the percentage changes with diverging palette
gt = heatmap(gt, ["Chg 96-01 %", "Chg 01-06 %", "Chg 06-11 %", "Chg 11-16 %", "Chg 16-21 %"],
             kind="diverging", hue="default")

# Apply styling
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Row hairlines
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

gt = frame(gt)
finalize(gt, path="table.png", zoom=2.0, expand=15)
