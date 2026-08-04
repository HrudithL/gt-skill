"""Ground truth for prompts/medium/gtcars_top10_by_country.json.

Data: data/gtcars.csv  (47 gt-car trims: performance specs, drivetrain,
      transmission, country of origin, and MSRP for each configuration)
Story: The 10 most expensive cars in the dataset, grouped by country of
       origin, with drivetrain and transmission shown for each -- a
       "priciest by nationality" leaderboard.

Selection: "top 10 most expensive" -> nlargest(10, "msrp"). No ties at the
cut line (10th = $287,250 vs. 11th = $263,553), so the row set is
unambiguous.

One colored measure (well under the 2-measure ceiling): msrp is the
literal "most expensive" ranking criterion and the only genuine magnitude
on display, so it gets the sequential Blues heatmap. Drivetrain and
transmission are categorical facts with no inherent good/bad polarity --
plain text, no data_color, no status_chip (status_chip is for an actual
good/bad/neutral meaning, which neither column has).
"""
from pathlib import Path

import pandas as pd
from great_tables import GT

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
# Read directly by scripts/gt_compare.py via module import. Keep these as
# literal dict/list assignments (no computation) so they're both a plain-text
# answer key a human can review and something a script can load without exec
# risk beyond what already happens to render the table.

# Acceptable label synonyms per underlying data column. Wording is free;
# the label just has to name the right concept. Keys are the SOURCE CSV
# column name(s) the label is standing in for. The stub (car) and the
# group (ctry_origin) aren't rendered through cols_label, so they have no
# entry here -- LABEL_SYNONYMS only covers ordinary body columns.
LABEL_SYNONYMS = {
    "msrp": ["msrp", "price", "sticker price", "retail price", "cost"],
    "drivetrain": ["drivetrain", "drive", "drive type", "driveline"],
    "trsmn": ["transmission", "gearbox", "trans."],
}

# Only present when the PROMPT TEXT explicitly demands something structural.
# Absence of a key means "not required" -- never inferred from prose at eval
# time, always decided here by whoever wrote this ground truth.
REQUIRED_INSTRUCTIONS = {
    "row_count": 10,       # "top 10" is an explicit, literal number in the prompt
    "grouping": True,      # "grouped by country of origin" -- checked by VALUE (does
                           # the candidate's actual row grouping match the SAME
                           # partition this ground truth uses, not by group-label
                           # text) via execution_tier.group_partition_match. This
                           # ground truth genuinely groups by ctry_origin, so no
                           # special handling is needed beyond that being true.
    # Deliberately NO "sort" key: with grouping enabled, rows display grouped-
    # by-country, and a later group's top car can legitimately cost more than
    # an earlier group's cars (a well-grouped candidate could order its
    # groups differently than this ground truth does and still be correct).
    # The comparator's "sort" check validates strict GLOBAL monotonicity,
    # which grouped display order is not required to satisfy -- adding this
    # key would risk penalizing a genuinely correct, well-grouped candidate.
}

# Keyword-presence check for the caption/subtitle overlap rule (see §9).
CAPTION_KEYWORDS = {
    "caption_should_mention": ["most expensive", "msrp", "country of origin"],
    "subtitle_should_not_duplicate": ["ordered by their priciest car", "sorted by price"],
}

# Underlying SOURCE CSV column(s) that are the canonical colored measure(s),
# used for value-based matching -- NOT the rendered column name/label.
# drivetrain/trsmn are plain categorical display columns, not numeric
# measures, so they don't belong in either list here.
CANONICAL_MEASURES = {
    "colored": ["msrp"],
    "hero_uncolored": [],
}

# Semantic type per rendered column, for the fmt_* correctness check.
# drivetrain/trsmn are text with no fmt_* call, so they're absent here too.
SEMANTIC_TYPES = {
    "msrp": "currency",
}

# ---- Data prep -----------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "gtcars.csv")

# "Top 10 most expensive" -- the literal ranking criterion is MSRP.
top = df.nlargest(10, "msrp").copy()

# Human-readable transmission code -> full description. The raw `trsmn`
# codes ("7a", "8am", ...) are car-enthusiast shorthand (speed count plus
# a/m/am/dd for automatic/manual/automated-manual/direct-drive); decoding
# them to full text is a display-only relabeling of the SAME underlying
# value -- it doesn't change which column answers "transmission details."
TRANSMISSION_LABELS = {
    "6m": "6-speed manual", "7m": "7-speed manual",
    "6a": "6-speed automatic", "7a": "7-speed automatic",
    "8a": "8-speed automatic", "9a": "9-speed automatic",
    "6am": "6-speed automated-manual", "7am": "7-speed automated-manual",
    "8am": "8-speed automated-manual",
    "1dd": "Direct-drive (electric)",
}
top["trsmn"] = top["trsmn"].map(TRANSMISSION_LABELS).fillna(top["trsmn"])
top["drivetrain"] = top["drivetrain"].str.upper()
top["car"] = top["mfr"] + " " + top["model"]

# "Grouped by country of origin" -- countries are ordered by their OWN
# priciest car (Italy's LaFerrari > the US's Ford GT > the UK's Rolls-Royce
# Dawn), and cars within each country are sorted by price, so the "most
# expensive first" reading survives being grouped without requiring strict
# global monotonicity across group boundaries (see REQUIRED_INSTRUCTIONS's
# comment above for why "sort" isn't asserted as a separate requirement).
group_rank = top.groupby("ctry_origin")["msrp"].transform("max")
top = (
    top.assign(_group_rank=group_rank)
       .sort_values(["_group_rank", "msrp"], ascending=[False, False])
       .drop(columns="_group_rank")
       .loc[:, ["car", "ctry_origin", "msrp", "drivetrain", "trsmn"]]
       .reset_index(drop=True)
)

msrp_lo = float(top["msrp"].min())
msrp_hi = float(top["msrp"].max())

# ---- Table -----------------------------------------------------------------
gt = (
    GT(top, rowname_col="car", groupname_col="ctry_origin")
    .tab_header(
        title="The 10 Priciest GT Cars, by Country of Origin",
        subtitle="MSRP, drivetrain, and transmission for the ten most expensive cars in the gtcars dataset",
    )
    .tab_stubhead(label="Car")
    .cols_label(msrp="MSRP", drivetrain="Drivetrain", trsmn="Transmission")
    .fmt_currency(columns=["msrp"], decimals=0)
    # Big Color 1/1 (well under the 2-measure ceiling): msrp is the literal
    # "most expensive" ranking criterion and the only real magnitude here,
    # so it's the sequential Blues hero. Drivetrain/transmission stay plain
    # text -- categorical facts with no good/bad polarity, so neither
    # data_color nor status_chip applies.
    .data_color(
        columns=["msrp"],
        palette="Blues",
        domain=[msrp_lo, msrp_hi],
        na_color="#808080",
        truncate=False,
        autocolor_text=True,
    )
    .cols_align(align="right", columns=["msrp"])
    .cols_align(align="left", columns=["drivetrain", "trsmn"])
    # Heading band: accent_tint navy, matching the Blues heatmap's family
    # (the DA hue-selection rule: match an existing heatmap's hue first).
    .tab_options(
        column_labels_background_color="#C9E0F0",
        column_labels_font_weight="bold",
        column_labels_border_bottom_color="#CCCCCC",
        column_labels_border_bottom_width="2px",
        table_body_hlines_style="solid",
        table_body_hlines_color="#E8E8E8",
        table_body_hlines_width="1px",
        table_border_top_style="solid", table_border_top_color="#CCCCCC", table_border_top_width="1px",
        table_border_bottom_style="solid", table_border_bottom_color="#CCCCCC", table_border_bottom_width="1px",
        table_border_left_style="solid", table_border_left_color="#CCCCCC", table_border_left_width="1px",
        table_border_right_style="solid", table_border_right_color="#CCCCCC", table_border_right_width="1px",
    )
    # Row striping: exactly 10 body rows clears the >=10-row gate, and only
    # 1 of the 3 visible non-stub/non-group columns (msrp) carries color --
    # nowhere near "essentially fully covered" -- so striping helps here
    # rather than fighting the layout. Because striping is on, the stub does
    # NOT also get a solid tint fill: a flat stub fill and alternating
    # stripes are two competing "separate the rows" mechanisms, and with 10
    # rows right at the striping floor, striping is the one that actually
    # helps distinguish a 6-row country group from a 1-row one.
    .opt_row_striping()
    .tab_options(row_striping_background_color="#F6F6F6")
    # Group headers: bold + the #BDBDBD structural rule only, deliberately
    # no background fill -- that's reserved for a summary/total row, which
    # this table doesn't have (no meaningful total across MSRPs of 10
    # different specific cars).
    .tab_options(
        row_group_font_weight="bold",
        row_group_border_top_color="#BDBDBD",
        row_group_border_bottom_color="#BDBDBD",
    )
    .tab_source_note(
        source_note=(
            "“Most expensive” = manufacturer's suggested retail price (MSRP). "
            "Countries are ordered by their priciest car, and cars within each country are "
            "sorted by price, so the table reads ‘most expensive first’ even after "
            "grouping by country of origin."
        )
    )
    .tab_source_note(
        source_note="Source: gtcars dataset (Posit / great_tables sample data), 2014–2017 model years."
    )
)

gt.gtsave(str(_HERE / "gtcars_top10_by_country.png"), zoom=2.0, expand=15)
