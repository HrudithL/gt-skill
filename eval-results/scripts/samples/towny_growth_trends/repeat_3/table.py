import pandas as pd
import numpy as np
from great_tables import GT, md, html, style, loc
from gt_consistency import PALETTE, frame, finalize, heatmap, band, stripe, stub_tint

df = pd.read_csv("towny.csv")

# Calculate overall growth 1996-2021
df["overall_growth_pct"] = (df["population_2021"] - df["population_1996"]) / df["population_1996"]

# Get top 15 fastest-growing towns
top_15 = df.nlargest(15, "overall_growth_pct").copy()

# Select and rename columns for display
display_cols = [
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

table_df = top_15[display_cols].copy()
table_df = table_df.reset_index(drop=True)

# Create column groups for density and changes
density_cols = ["density_1996", "density_2001", "density_2006", "density_2011", "density_2016", "density_2021"]
change_cols = ["pop_change_1996_2001_pct", "pop_change_2001_2006_pct", "pop_change_2006_2011_pct",
               "pop_change_2011_2016_pct", "pop_change_2016_2021_pct"]

# Compute domain for density gradient
lo_density = float(np.nanmin(table_df[density_cols].to_numpy()))
hi_density = float(np.nanmax(table_df[density_cols].to_numpy()))

gt = (
    GT(table_df, rowname_col="name")
    .cols_label(
        density_1996="1996",
        density_2001="2001",
        density_2006="2006",
        density_2011="2011",
        density_2016="2016",
        density_2021="2021",
        pop_change_1996_2001_pct="1996-2001",
        pop_change_2001_2006_pct="2001-2006",
        pop_change_2006_2011_pct="2006-2011",
        pop_change_2011_2016_pct="2011-2016",
        pop_change_2016_2021_pct="2016-2021",
    )
    .tab_spanner(label="Density (persons/km²)", columns=density_cols)
    .tab_spanner(label="Population Change (%)", columns=change_cols)
    .fmt_number(columns=density_cols, decimals=1)
    .fmt_percent(columns=change_cols, decimals=1, scale_values=False)
    .data_color(
        columns=density_cols,
        palette="Blues",
        domain=[lo_density, hi_density],
        truncate=False,
        na_color="#808080",
    )
    .sub_missing(columns=density_cols + change_cols, missing_text="—")
    .tab_options(
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.body(columns="density_2021"),
    )
    .tab_style(
        style=style.borders(sides="right", color="#D0D0D0", weight="1px"),
        locations=loc.column_labels(columns="density_2021"),
    )
    .tab_style(
        style=style.fill(color="#F0F0F0"),
        locations=loc.stub(),
    )
)

gt = stripe(gt)

gt = (
    gt
    .tab_options(
        column_labels_background_color=PALETTE["washed"]["navy"],
    )
    .tab_header(
        title="Population Growth Trends for Ontario's Top 15 Fastest-Growing Towns",
        subtitle="Density changes across census years (1996-2021) with decade-to-decade growth rates",
    )
    .tab_source_note(
        source_note="Ranking metric: overall population growth 1996-2021. "
                    "Percentage changes computed from population counts (continuous series, not reset per period)."
    )
    .tab_source_note(source_note="Source: provided Ontario census dataset.")
)

gt = stub_tint(gt, hue="navy")
gt = frame(gt)
gt = finalize(gt)
