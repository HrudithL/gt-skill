import pandas as pd
from great_tables import GT, md
from house_table import PALETTE, frame, hairlines, finalize, band, heatmap, humanize_labels


def build_table():
    """Build monthly air quality summary table."""
    df = pd.read_csv("airquality.csv")

    # Compute monthly averages
    monthly = df.groupby("Month").agg({
        "Temp": "mean",
        "Wind": "mean",
        "Ozone": "mean",
    }).reset_index()

    # Map month numbers to names
    month_names = {
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
    }
    monthly["Month"] = monthly["Month"].map(month_names)

    # Rename columns for display
    monthly.rename(columns={
        "Month": "month",
        "Temp": "avg_temperature",
        "Wind": "avg_wind_speed",
        "Ozone": "avg_ozone",
    }, inplace=True)

    gt = GT(monthly, rowname_col="month")

    gt = gt.tab_header(
        title="Monthly Air Quality Summary",
        subtitle=md("Average temperature, wind speed, and ozone levels by month"),
    )

    # Format columns
    gt = gt.fmt_number(columns="avg_temperature", decimals=1)
    gt = gt.fmt_number(columns="avg_wind_speed", decimals=1)
    gt = gt.fmt_number(columns="avg_ozone", decimals=1)

    # Apply humanized labels with overrides
    gt = humanize_labels(gt, monthly, overrides={
        "avg_temperature": "Avg Temperature (°F)",
        "avg_wind_speed": "Avg Wind Speed (mph)",
        "avg_ozone": "Avg Ozone (ppb)",
    })

    # Apply heatmap to the ozone measure (the primary focus)
    gt = heatmap(gt, "avg_ozone", kind="sequential", hue="neutral")

    # Column widths and padding
    gt = gt.cols_width(cases={
        "month": "100px",
        "avg_temperature": "130px",
        "avg_wind_speed": "130px",
        "avg_ozone": "130px",
    })
    gt = gt.tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )

    # Apply branding and polish
    gt = band(gt, hue="navy")
    gt = hairlines(gt)
    gt = frame(gt)

    # Source notes
    gt = gt.tab_source_note(
        source_note="Ozone is colored to highlight seasonal patterns; temperature and wind speed are shown as plain text for context."
    )
    gt = gt.tab_source_note(
        source_note="Source: airquality.csv — New York air quality data, May–September 1973."
    )

    finalize(gt, path="table.png")


if __name__ == "__main__":
    build_table()
