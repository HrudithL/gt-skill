"""Ground truth for prompts/medium/gtcars_top10_by_country.json.

Data: data/gtcars.csv  (47 gt-car trims: performance specs, drivetrain,
      transmission, country of origin, and MSRP for each configuration)
Story: The 10 most expensive cars in the dataset, grouped by country of
       origin, with drivetrain and transmission shown for each -- a
       "priciest by nationality" leaderboard.

Design decisions (author-directed; see the 2026-08-12 interview that
settled these against the previous draft's assumptions):

Selection: "top 10 most expensive" -> nlargest(10, "msrp"). No ties at the
cut line (10th = $287,250 vs. 11th = $263,553), so the row set is
unambiguous.

Stub: mfr + model (e.g. "Ford GT", "Ferrari 458 Speciale") -- NOT bare
model. "GT" alone is not a known car; "Ford GT" is. The manufacturer is a
critical identifying detail, not disambiguation noise, even in a slice
where the bare model happens to already be unique. This matches
gtcars_hp_price.py's own stub choice -- the two gtcars ground truths must
agree on this, and a prior draft of this file didn't.

Column order (after stub + country group): MSRP, Drivetrain, Transmission.
Price -- the literal ranking criterion the prompt names ("most expensive")
-- leads immediately after the stub/group, ahead of the two spec-detail
columns.

Group order: country groups are ordered by each group's OWN priciest car
(Italy's LaFerrari > the US's Ford GT > the UK's Rolls-Royce Dawn), not
alphabetically -- keeps the "most expensive first" reading intact even
after grouping. Cars within each country are sorted by price descending.

One colored measure (well under the 2-measure ceiling): msrp is the
literal "most expensive" ranking criterion and the only genuine magnitude
on display, so it gets the sequential Blues heatmap. Drivetrain and
transmission are categorical facts with no inherent good/bad polarity --
plain text, no data_color, no status_chip.

Value formatting, by author direction: Drivetrain is rendered ALL CAPS
(RWD/AWD/FWD -- these are already acronyms, so caps is the natural
reading). Transmission is rendered in Title Case, every word capitalized
("7-Speed Automated-Manual", not "7-speed automated-manual") -- it's
prose, not an acronym, so word-initial caps read as a label rather than
shouting.

Column-label band: DEEP navy (#08306B, sampled directly from the dark end
of the msrp Blues heatmap -- not an arbitrary separate navy), bold, white
text (not the house-default light tint) -- an explicit, louder header
treatment than the skill's own default, by author direction. Group
(country) labels are bolded too, via the same row_group_font_weight option
the base house style already uses.

Compact layout, by author direction: every column has an explicit
`cols_width` sized to its own content plus a small buffer (not left to
auto-layout, which was stretching the narrow Drivetrain/Transmission
columns into visible dead space), and cell padding is tightened throughout
(`data_row_padding`, `column_labels_padding`, `heading_padding`,
`source_notes_padding`) along with a smaller `gtsave(expand=...)` margin.

Row striping AND stub tint together: by author direction, this table
combines a light navy stub tint with grey zebra striping across the other
columns -- a deliberate departure from the house skill's usual
striping-vs-stub-tint mutual exclusivity (that rule optimizes for a
generic default; here the two are wanted together, and since MSRP's own
heatmap and the stub's own tint are cell-level fills that sit on top of
the row-level stripe, the grey stripe only actually shows through on the
uncolored Drivetrain/Transmission cells anyway).
"""
from pathlib import Path

import pandas as pd
from great_tables import GT, loc, md, style

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent

# ---- Ground-truth comparator metadata --------------------------------------
# Read directly by scripts/gt_compare.py via module import. Keep these as
# literal dict/list assignments (no computation) so they're both a plain-text
# answer key a human can review and something a script can load without exec
# risk beyond what already happens to render the table.

# Acceptable label synonyms per underlying data column. Wording is free;
# the label just has to name the right concept. The stub (car = mfr+model)
# and the group (ctry_origin) aren't rendered through cols_label, so they
# have no entry here -- LABEL_SYNONYMS only covers ordinary body columns.
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
    # "sort" with the "within_group" scope (not the default global scope):
    # a plain global sort check would false-fail a well-grouped candidate
    # whose LATER group's top car costs more than an EARLIER group's cars
    # (grouped display legitimately breaks strict cross-group ordering).
    # But omitting a sort check entirely would let a candidate shuffle cars
    # WITHIN a country with no penalty, losing the "most expensive first"
    # reading the prompt implies. "within_group" verifies each candidate
    # row-group's own segment is independently descending, without
    # requiring cross-group monotonicity.
    "sort": ("msrp", "desc", "within_group"),
}

# Keyword-presence check for the caption/subtitle overlap rule (see §9).
# `caption_should_mention` is an ALL-of-these match (see comparator.py's
# check_caption_not_restating_subtitle) -- unlike towny's genuinely
# ambiguous "which growth definition" question (where all 3 keywords
# jointly make up one unavoidable disambiguation the caption MUST state),
# "most expensive" here has only one real candidate metric (msrp): there
# is no genuine definitional ambiguity to force a caption to restate.
# Left empty rather than picking phrases a good, distinctive, non-
# duplicative caption might reasonably NOT use (e.g. one about country
# mix or a standout car) -- an empty list is vacuously satisfied, leaving
# only the (still-enforced) "doesn't just restate the subtitle" check.
CAPTION_KEYWORDS = {
    "caption_should_mention": [],
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

# Stub = mfr + model (see module docstring: "GT" alone isn't a known car,
# "Ford GT" is). Confirmed unique across all 10 selected cars.
top["car"] = top["mfr"] + " " + top["model"]

# Human-readable transmission code -> full description. The raw `trsmn`
# codes ("7a", "8am", ...) are car-enthusiast shorthand (speed count plus
# a/m/am/dd for automatic/manual/automated-manual/direct-drive); decoding
# them to full text is a display-only relabeling of the SAME underlying
# value -- it doesn't change which column answers "transmission details."
TRANSMISSION_LABELS = {
    "6m": "6-Speed Manual", "7m": "7-Speed Manual",
    "6a": "6-Speed Automatic", "7a": "7-Speed Automatic",
    "8a": "8-Speed Automatic", "9a": "9-Speed Automatic",
    "6am": "6-Speed Automated-Manual", "7am": "7-Speed Automated-Manual",
    "8am": "8-Speed Automated-Manual",
    "1dd": "Direct-Drive (Electric)",
}
top["trsmn"] = top["trsmn"].map(TRANSMISSION_LABELS).fillna(top["trsmn"])
# Drivetrain: all caps (RWD/AWD/FWD) -- author-directed, see module docstring.
top["drivetrain"] = top["drivetrain"].str.upper()

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
    # Columns sized to their own content (+ a small buffer), not left to
    # auto-stretch across the render viewport -- author-directed, to kill
    # the excess whitespace auto-layout was leaving in the narrow columns.
    .cols_width(cases={"car": "210px", "msrp": "120px", "drivetrain": "110px", "trsmn": "235px"})
    # Column-label band: DEEP navy -- the same #08306B that sits at the dark
    # end of the msrp Blues heatmap itself (sampled directly from that
    # gradient), not a lighter, disconnected navy -- bold, white text.
    # Author-directed louder header treatment, not the house skill's usual
    # light-tint default.
    .tab_options(
        column_labels_background_color="#08306B",
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
        # Tighter padding throughout -- less whitespace per cell, by author
        # direction, applied everywhere (heading, header, body, source notes).
        heading_padding="6px",
        column_labels_padding="6px",
        column_labels_padding_horizontal="8px",
        data_row_padding="5px",
        data_row_padding_horizontal="8px",
        source_notes_padding="6px",
    )
    .tab_style(style=style.text(color="white"), locations=loc.column_labels())
    # Stub tint -- washed navy, applied TOGETHER with row striping below by
    # author direction (see module docstring for why this deviates from the
    # house skill's usual either/or rule).
    .tab_style(style=style.fill(color="#EAF0F6"), locations=loc.stub())
    # Row striping: grey zebra across the body. Combined with the msrp
    # heatmap and stub tint above -- both of those are cell-level fills that
    # sit on top of this row-level stripe, so the grey only actually shows
    # through on the uncolored Drivetrain/Transmission cells.
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
            "Italy claims 6 of the 10 spots, led by the Ferrari LaFerrari at $1,416,362 — more "
            "than triple the price of the next car, the Ford GT."
        )
    )
    .tab_source_note(
        source_note="Source: gtcars dataset (Posit / great_tables sample data), 2014–2017 model years."
    )
)

gt.gtsave(str(_HERE / "gtcars_top10_by_country.png"), zoom=2.0, expand=8)
