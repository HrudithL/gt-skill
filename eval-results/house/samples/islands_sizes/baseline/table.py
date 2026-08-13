import pandas as pd
from great_tables import GT

df = pd.read_csv("islands.csv")

gt = (
    GT(df)
    .tab_header(title="Islands and Their Sizes", subtitle="Land area in thousands of square miles")
    .cols_label(name="Island", size="Size (1000 sq mi)")
    .fmt_number(columns="size", decimals=0)
    .tab_options(
        heading_title_font_size="large",
        heading_subtitle_font_size="medium"
    )
)

gt.gtsave("table.png")
