import pandas as pd
from great_tables import GT, md, loc
from house_table import PALETTE, frame, hairlines, finalize, band, stripe, stub_tint, heatmap, humanize_labels


def build_gtcars_table():
    """Build and render a table of GT cars with horsepower and price."""
    df = pd.read_csv("gtcars.csv")

    # Create composite identifier: manufacturer + model
    df["car"] = df["mfr"] + " " + df["model"]

    # Select relevant columns and sort by horsepower
    display_df = df[["car", "hp", "msrp"]].copy()
    display_df = display_df.sort_values("hp", ascending=False).reset_index(drop=True)

    gt = (
        GT(display_df, rowname_col="car")
        .tab_header(
            title="GT Cars Performance",
            subtitle=md("Horsepower and price across selected sports cars"),
        )
        .fmt_number(columns="hp", decimals=0)
        .fmt_currency(columns="msrp", decimals=0)
    )

    gt = humanize_labels(gt, display_df, overrides={"hp": "Horsepower", "msrp": "Price"})

    # Column widths and padding
    gt = gt.cols_width(
        cases={
            "car": "200px",
            "hp": "120px",
            "msrp": "140px",
        }
    )
    gt = gt.tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )

    # Big Color: horsepower is the hero measure (sequential, neutral/Blues)
    gt = heatmap(gt, "hp", kind="sequential", hue="neutral")

    # Heading band
    gt = band(gt, hue="navy")

    # Small-Color polish: striping, stub tint
    gt = stripe(gt)
    gt = stub_tint(gt, hue="navy")

    # Source notes and finishing
    gt = gt.tab_source_note(
        source_note="Horsepower measured at maximum rated RPM."
    )
    gt = gt.tab_source_note(
        source_note="Source: GT cars dataset."
    )

    gt = hairlines(gt)
    gt = frame(gt)
    finalize(gt)
    return gt


if __name__ == "__main__":
    build_gtcars_table()
