# Examples

Load the matching `.py` for your archetype.

| Archetype | Use when... | Files |
|---|---|---|
| Financial | Money, prices, signed deltas, percentages | `financial/financial.py` · `financial/financial.png` |
| Time series | Dates, trends, monthly/yearly aggregation | `time_series/time_series.py` · `time_series/time_series.png` |
| Ranking | Top-N lists, ordered results | `ranking/ranking.py` · `ranking/ranking.png` |
| Summary stats | Aggregations, totals, subtotals | `summary_stats/summary_stats.py` · `summary_stats/summary_stats.png` |
| Scientific | Measurements with units, sig figs | `scientific/scientific.py` · `scientific/scientific.png` |
| Heatmap | Color-encoded data cells | `heatmap/heatmap.py` · `heatmap/heatmap.png` |

Every archetype assigns its final chain to a top-level `gt = (...)` — copy that
into your own script, then add your own `gt.gtsave("table.png")` as a separate
final line (these distilled examples deliberately leave the render call out).
Don't leave the final chain as a bare, unassigned expression.
