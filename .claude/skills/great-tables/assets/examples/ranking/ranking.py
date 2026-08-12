"""Ranking archetype — distilled reference example.

Data: data/gtcars.csv  (47 high-performance cars)
Story: Top 10 production cars by horsepower, with the leader visually
       called out.
"""
import pandas as pd
from great_tables import GT, loc, style

df = pd.read_csv("data/gtcars.csv")

# Compose a single human label per row. Two separate mfr/model columns force
# the reader to combine them mentally on every row.
df["car"] = df["mfr"] + " " + df["model"]

# Sort by hp descending and take the top 10. The sort IS the message; an
# unsorted dump erases the archetype.
top = df.sort_values("hp", ascending=False).head(10).reset_index(drop=True)
top["rank"] = top.index + 1  # 1-based; leaderboards start at #1, not #0.
top = top[["rank", "car", "year", "ctry_origin", "hp", "trq", "drivetrain", "msrp"]]

leader = top.loc[0, "car"]
leader_hp = int(top.loc[0, "hp"])
runner_up_hp = int(top.loc[1, "hp"])

gt = (
    GT(top, rowname_col="car")
    .tab_header(
        title="Top 10 by Horsepower",
        subtitle="Production cars in the gtcars dataset, ranked by peak HP",
    )
    .cols_label(
        rank="#", year="Year", ctry_origin="Country",
        hp="HP", trq="Torque (lb-ft)", drivetrain="Drive", msrp="MSRP",
    )
    .fmt_currency(columns=["msrp"], currency="USD", decimals=0)
    .fmt_integer(columns=["hp", "trq"])
    # use_seps=False on year — `2,017` is wrong for a year.
    .fmt_integer(columns=["year"], use_seps=False)
    # Full-row highlight on the #1 leader (a Top-N "winner" story) — a solid
    # Dark Academia hex with white text, spanning every body column. Rank and
    # the other measures otherwise render fully plain: no consolation bold.
    .tab_style(
        style=[style.fill(color="#9A7B33"), style.text(color="#ffffff", weight="bold")],
        locations=loc.body(rows=[0]),
    )
    .cols_align(align="left", columns=["ctry_origin", "drivetrain"])
    .cols_align(align="right", columns=["rank", "year", "hp", "trq", "msrp"])
    # Heading band — fixed branding navy, bold labels, white text, every table.
    .tab_options(
        column_labels_background_color="#08306B",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint — fixed branding hex, unconditional whenever a stub exists.
    # Uniform across every row, including the highlighted leader.
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping — default on every table (only one row is highlighted).
    .opt_row_striping()
    .tab_options(
        row_striping_background_color="#F6F6F6",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    .cols_width(cases={
        "car": "210px", "rank": "50px", "year": "70px", "ctry_origin": "110px",
        "hp": "80px", "trq": "110px", "drivetrain": "70px", "msrp": "110px",
    })
    .tab_options(
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_source_note(
        source_note=f"{leader} leads the field with {leader_hp} hp, {leader_hp - runner_up_hp} more than the #2 car."
    )
    .tab_source_note(source_note="Source: gtcars dataset (Posit / great_tables sample data).")
)

gt.gtsave("ranking.png", zoom=2.0, expand=15)
