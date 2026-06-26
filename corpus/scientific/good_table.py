"""Scientific archetype — good example.

Source: ../../data/reactions.csv  (1,683 atmospheric reactions; rate
        constants of trace gases with the OH radical and three other
        oxidants, with uncertainties)
Story:  Rate constants of ten common atmospheric trace gases reacting
        with the hydroxyl radical (OH) at 298 K. The audience is an
        atmospheric chemist who needs to read tiny numbers correctly:
        the values span four orders of magnitude (10⁻¹⁵ → 10⁻¹⁰) and
        must be reported with explicit units, scientific notation, and
        an uncertainty so the reader knows when two rows are
        statistically indistinguishable.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))
import gtskill_chrome  # noqa: F401

import pandas as pd
from great_tables import GT, html

# ---- Data prep ---------------------------------------------------------------
df = pd.read_csv(_ROOT / "data" / "reactions.csv")

# Curated subset: a handful of textbook atmospheric trace gases that span the
# full reactivity range in this dataset. Sorted by rate constant ascending so
# the eye walks from slow to fast — a chemist's natural reading order for
# this kind of table.
picks = [
    "methane", "benzene", "ethanol", "methanol",
    "toluene", "formaldehyde", "ethene",
    "acetaldehyde", "propene", "isoprene",
]
sub = (
    df[df["cmpd_name"].isin(picks)]
      .loc[:, ["cmpd_name", "cmpd_formula", "cmpd_mwt",
               "OH_k298", "OH_uncert"]]
      .sort_values("OH_k298")
      .reset_index(drop=True)
)
sub["cmpd_name"] = sub["cmpd_name"].str.capitalize()

# ---- Table -------------------------------------------------------------------
gt = (
    GT(sub)
    .tab_header(
        title="OH reaction rate constants at 298 K",
        subtitle=html(
            "Selected trace gases. k in cm<sup>3</sup>&nbsp;molecule<sup>&minus;1</sup>&nbsp;s<sup>&minus;1</sup>."
        ),
    )
    # Column labels carry the unit. Embedding units in the header rather than
    # in every cell is the standard convention for scientific tables; doing
    # the opposite is what makes data-dump CSVs hard to read.
    .cols_label(
        cmpd_name="Compound",
        cmpd_formula="Formula",
        cmpd_mwt=html("M<sub>w</sub> (g mol<sup>&minus;1</sup>)"),
        OH_k298=html("k(298 K)"),
        OH_uncert="Rel. uncert.",
    )
    # Scientific notation on the rate constant: with values spanning 10⁻¹⁵ →
    # 10⁻¹⁰, fixed-decimal notation would show either a forest of leading
    # zeros or rounded-to-zero garbage. n_sigfig=3 reports three significant
    # figures, which matches the precision of the underlying measurements.
    .fmt_scientific(columns=["OH_k298"], n_sigfig=3)
    # Molecular weight to two decimals (g/mol) — typical for atmospheric
    # chemistry tables; one decimal would lose meaningful precision for the
    # lighter compounds.
    .fmt_number(columns=["cmpd_mwt"], decimals=2)
    # Uncertainty as a percent. The raw column is fractional (e.g. 0.10 =
    # ±10%). decimals=0 because uncertainties here are quoted to whole
    # percent in the source compilation.
    .fmt_percent(columns=["OH_uncert"], decimals=0)
    .sub_missing(columns=["OH_uncert"], missing_text="—")
    .cols_align(align="left", columns=["cmpd_name", "cmpd_formula"])
    .cols_align(align="right", columns=["cmpd_mwt", "OH_k298", "OH_uncert"])
    .tab_source_note(
        source_note=html(
            "Source: IUPAC Task Group on Atmospheric Chemical Kinetic Data Evaluation, "
            "compiled in the <code>reactions</code> dataset (Posit / great_tables sample data)."
        )
    )
)

gt.gtsave(str(_HERE / "good_table.png"), zoom=3.0)
