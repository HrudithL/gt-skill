import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, stripe, heatmap, humanize_labels

# Read the data
df = pd.read_csv("islands.csv")

# Create the GT object
gt = (
    GT(df, rowname_col="name")
    .tab_header(
        title="World Islands by Size",
        subtitle=md("Land area in thousands of square kilometers"),
    )
    .tab_stubhead(label="Island")
    .fmt_number(columns="size", decimals=0, use_seps=True)
)

# Apply humanize_labels to the remaining columns
gt = humanize_labels(gt, df, overrides={"size": "Area (1000 km²)"})

# Apply heatmap coloring to the size column (the hero measure)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Apply the column label band with accent_tint navy
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Row striping and stub tint for visual clarity
gt = stripe(gt)
gt = gt.tab_style(
    style=style.fill(color=PALETTE["washed"]["navy"]),
    locations=loc.stub(),
)

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)

# Add frame and source note
gt = frame(gt)
gt = gt.tab_source_note(source_note="Source: provided dataset.")

# Finalize and save
finalize(gt, path="table.png", zoom=2.0, expand=15)
