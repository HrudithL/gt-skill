import pandas as pd
from great_tables import GT, md, loc, style
from house_table import PALETTE, frame, finalize, stripe, stub_tint, heatmap, humanize_labels

df = pd.read_csv("islands.csv")

gt = GT(df, rowname_col="name")
gt = gt.tab_header(
    title="Island Sizes",
    subtitle=md("Geographic area in thousands of square kilometers"),
)
gt = gt.tab_stubhead(label="Island")
gt = gt.fmt_number(columns="size", decimals=1, use_seps=True)
gt = humanize_labels(gt, df)

# Big Color: one sequential heatmap for size (the neutral magnitude hero)
gt = heatmap(gt, "size", kind="sequential", hue="neutral")

# Heading band: light navy accent_tint (default for neutral magnitude)
gt = gt.tab_options(
    column_labels_background_color="#C9E0F0",
    column_labels_border_bottom_color="#CCCCCC",
    column_labels_border_bottom_width="2px",
    column_labels_border_bottom_style="solid",
)

# Small-Color polish: many rows (49) so striping applies; only 1 column is colored
# Stub tint matches the heatmap family (navy)
gt = stripe(gt)
gt = stub_tint(gt, hue="navy")

# Row hairlines between body rows
gt = gt.tab_options(
    table_body_hlines_style="solid",
    table_body_hlines_color="#E8E8E8",
    table_body_hlines_width="1px",
)
gt = frame(gt)

gt.tab_source_note(source_note="Source: provided dataset.")
finalize(gt, path="table.png", zoom=2.0, expand=15)
