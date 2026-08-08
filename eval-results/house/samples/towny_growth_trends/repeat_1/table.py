import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, band, stripe, stub_tint, heatmap, humanize_labels

# Read the data
df = pd.read_csv("./towny.csv")

# Calculate overall growth rate (1996 to 2021) to identify fastest-growing towns
df["overall_growth_rate"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_rate")[
    [
        "name",
        "density_1996",
        "density_2001",
        "density_2006",
        "density_2011",
        "density_2016",
        "density_2021",
        "pop_change_1996_2001_pct",
        "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct",
        "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ]
].reset_index(drop=True)

# Create GT table
gt = GT(top_15, rowname_col="name")

# Add title and subtitle
gt = gt.tab_header(
    title="Population Growth Trends: Ontario's Fastest-Growing Towns",
    subtitle=md("Top 15 towns ranked by overall growth 1996–2021, with density changes across all census years and percentage changes between periods"),
)

# Add spanners for logical grouping
gt = gt.tab_spanner(
    label="Population Density (persons/km²)",
    columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"],
)
gt = gt.tab_spanner(
    label="Population Change (%)",
    columns=[
        "pop_change_1996_2001_pct",
        "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct",
        "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ],
)

# Format columns
gt = gt.fmt_number(columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"], decimals=1)
gt = gt.fmt_percent(
    columns=[
        "pop_change_1996_2001_pct",
        "pop_change_2001_2006_pct",
        "pop_change_2006_2011_pct",
        "pop_change_2011_2016_pct",
        "pop_change_2016_2021_pct",
    ],
    decimals=1,
)

# Humanize labels
gt = humanize_labels(
    gt,
    top_15,
    overrides={
        "density_1996": "1996",
        "density_2001": "2001",
        "density_2006": "2006",
        "density_2011": "2011",
        "density_2016": "2016",
        "density_2021": "2021",
        "pop_change_1996_2001_pct": "1996–2001",
        "pop_change_2001_2006_pct": "2001–2006",
        "pop_change_2006_2011_pct": "2006–2011",
        "pop_change_2011_2016_pct": "2011–2016",
        "pop_change_2016_2021_pct": "2016–2021",
    },
)

# Apply heatmap to density columns (sequential, positive growth -> Greens)
gt = heatmap(
    gt,
    columns=["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"],
    kind="sequential",
    hue="positive",
)

# Apply formatting and styling
gt = stripe(gt)
gt = stub_tint(gt, hue="forest")
gt = gt.tab_options(
    column_labels_background_color="#CFEAD9",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Add vertical dividers between the two spanner groups
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.body(columns="density_2021"),
)
gt = gt.tab_style(
    style=style.borders(sides="right", color=PALETTE["neutral"]["vertical_divider"], weight="1px"),
    locations=loc.column_labels(columns="density_2021"),
)

# Add row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# Add frame
gt = frame(gt)

# Add source notes
gt = gt.tab_source_note(source_note="Source: Statistics Canada Census of Population (1996–2021).")
gt = gt.tab_source_note(
    source_note="Fastest-growing: towns ranked by overall population change from 1996 to 2021. Density: persons per km². Population change: period-over-period percentage growth rates."
)

# Finalize and render
finalize(gt, path="table.png", zoom=2.0, expand=15)
