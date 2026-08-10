import pandas as pd
from great_tables import GT, style, loc

# Step 1: UNDERSTAND & CLEAN DATA
df = pd.read_csv("gtcars.csv")

# Get top 10 most expensive cars overall
df_top10 = df.nlargest(10, "msrp").copy()

# Select and organize columns for the table
df_display = df_top10[["model", "ctry_origin", "drivetrain", "trsmn", "msrp"]].copy()
df_display = df_display.rename(columns={
    "model": "Model",
    "ctry_origin": "Country",
    "drivetrain": "Drivetrain",
    "trsmn": "Transmission",
    "msrp": "MSRP"
})

# Sort by country then by MSRP descending for grouping
df_display = df_display.sort_values(["Country", "MSRP"], ascending=[True, False]).reset_index(drop=True)

# Step 2: ORGANIZE COLUMNS with groupname_col for country grouping
gt = (
    GT(df_display, groupname_col="Country")
    .cols_hide(columns=["Country"])  # Hide since it's the groupname_col
)

# Step 3: BIG COLOR — Price is a neutral magnitude → Blues gradient
gt = gt.data_color(
    columns="MSRP",
    palette="Blues",
    domain=[df_display["MSRP"].min(), df_display["MSRP"].max()],
)

# Step 4: HEADING BAND — Has Big Color → light band (washed-DA tint of Blues)
gt = gt.tab_options(
    column_labels_background_color="#EAF0F6",  # Washed Navy/Blues tint
    column_labels_font_weight="bold",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
)

# Step 5: SMALL-COLOR POLISH CHECKLIST

# (a) Cell borders — hairlines between all body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Frame — light border on all four sides
gt = gt.tab_options(
    table_border_top_style="solid",    table_border_top_color="#CCCCCC",    table_border_top_width="1px",
    table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
    table_border_left_style="solid",   table_border_left_color="#CCCCCC",   table_border_left_width="1px",
    table_border_right_style="solid",  table_border_right_color="#CCCCCC",  table_border_right_width="1px",
)

# (e) Formatting per column
gt = gt.fmt_currency(
    columns="MSRP",
    currency="USD",
    decimals=0,
    use_seps=True,
)

# Row-group emphasis (country headers)
gt = gt.tab_options(
    row_group_background_color="#EAF0F6",  # Washed tint to match heading band
    row_group_font_weight="bold",
    row_group_border_top_color="#BDBDBD",
    row_group_border_bottom_color="#BDBDBD",
    row_group_padding="6px",
)

# Step 6: TITLES & ANNOTATIONS
gt = (
    gt.tab_header(
        title="Top 10 Most Expensive GT Cars",
        subtitle="Grouped by Country of Origin",
    )
    .tab_source_note(
        source_note="Data includes drivetrain (RWD/AWD) and transmission type for each vehicle."
    )
    .tab_source_note(
        source_note="Source: gtcars.csv"
    )
)

# Step 7: RENDER & VERIFY
gt.gtsave("table.png", expand=15, zoom=2.0)
print("✓ Table rendered to table.png")
