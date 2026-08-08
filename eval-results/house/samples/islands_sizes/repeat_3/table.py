import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, finalize, stripe, stub_tint, heatmap, humanize_labels

# Read the islands data
islands = pd.read_csv("islands.csv")

gt = (
    GT(islands, rowname_col="name")
    .tab_header(
        title="World's Largest Islands",
        subtitle=md("Land area in thousands of square kilometers"),
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

gt = humanize_labels(gt, islands)

# Single heatmap for the magnitude column (size)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Heading band with navy tint
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color=PALETTE["neutral"]["column_label_rule"],
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Small-color polish: stripe + stub tint to harmonize with the navy heatmap
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color=PALETTE["neutral"]["hairline"],
    table_body_hlines_width="1px",
)

# Boxed frame
gt = frame(gt)

# Source note
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Render with house format defaults
finalize(gt, path="table.png", zoom=2.0, expand=15)
