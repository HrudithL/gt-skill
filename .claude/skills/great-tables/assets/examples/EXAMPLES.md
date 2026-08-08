# Examples

Concrete reference tables. Each archetype lives in its own subfolder
with source code and rendered output. Load the matching `.py` for the
archetype you need.

| Archetype | Use when... | Files |
|---|---|---|
| Financial | Money, prices, signed deltas, percentages | `financial/financial.py` · `financial/financial.png` |
| Time series | Dates, trends, monthly/yearly aggregation | `time_series/time_series.py` · `time_series/time_series.png` |
| Ranking | Top-N lists, ordered results | `ranking/ranking.py` · `ranking/ranking.png` |
| Summary stats | Aggregations, totals, subtotals | `summary_stats/summary_stats.py` · `summary_stats/summary_stats.png` |
| Scientific | Measurements with units, sig figs | `scientific/scientific.py` · `scientific/scientific.png` |
| Heatmap | Color-encoded data cells | `heatmap/heatmap.py` · `heatmap/heatmap.png` |

Every archetype assigns its final chained expression to a top-level `gt = (...)` —
copy that assignment into your own script too, then add your own `gt.gtsave(
"table.png")` as a separate final line (Step 7's mandatory render, which these
distilled examples deliberately leave out to keep the archetype itself
data-shape-agnostic). Don't leave the final chain as a bare, unassigned expression
— nothing downstream (your own render call, any later `tab_style` targeting the
same table, a reviewer's own script) has a name to refer back to it by.
