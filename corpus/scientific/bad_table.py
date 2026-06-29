"""Scientific archetype — bad example.

Dominant failure mode (one per spec §13 Q2):
    *Full default float precision, no units in headers, no scientific
    notation.* Rate constants like `6.36e-15` get rendered as
    `0.0000` after fmt_number rounding, or as raw `6.36e-15` with no
    units alongside, so the reader cannot tell whether they are
    looking at SI units, CGS, or per-molecule rates.

Same source CSV as good_table.py (../../data/reactions.csv).
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))
import gtskill_chrome  # noqa: F401

import pandas as pd
from great_tables import GT

df = pd.read_csv(_ROOT / "data" / "reactions.csv")
picks = ["methane", "benzene", "ethanol", "methanol", "toluene",
         "formaldehyde", "ethene", "acetaldehyde", "propene", "isoprene"]
sub = df[df["cmpd_name"].isin(picks)][
    ["cmpd_name", "cmpd_formula", "cmpd_mwt", "OH_k298", "OH_uncert"]
]

# BAD: fmt_number on a column whose values are 10⁻¹⁵ — gets rounded to
# 0.0000 and loses every bit of information. Compare to good_table.py which
# uses fmt_scientific with n_sigfig=3. No header, no unit-bearing labels,
# no sort order, no uncertainty handling, no source note.
(
    GT(sub)
    .fmt_number(columns=["cmpd_mwt", "OH_k298", "OH_uncert"], decimals=4)
    .gtsave(str(_HERE / "bad_table.png"), zoom=3.0)
)
