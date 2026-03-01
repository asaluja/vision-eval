# Task Inventory

Master mapping of all eval task types to primitives, sources, and result status.
Auto-counts last updated from results/ directory. See `docs/` for other reference material.

| Task type | Source | Results? | Count | Primitive |
|---|---|---|---|---|
| `counting_circles` | Local | ✓ | 80 | Counting/Enumeration |
| `counting_circles` | HF | ✓ | 480 | Counting/Enumeration |
| `counting_pentagons` | Local | ✓ | 440 | Counting/Enumeration |
| `counting_pentagons` | HF | ✓ | 480 | Counting/Enumeration |
| `nested_squares` | Local | ✓ | 66 | Counting/Enumeration |
| `nested_squares` | HF | ✓ | 240 | Counting/Enumeration |
| `grid_counting` | Local | ✓ | 220 | Counting/Enumeration |
| `grid_counting` | HF | ✓ | 528 | Counting/Enumeration |
| `chart_bar_count` | Local | ✓ | 64 | Counting/Enumeration |
| `chart_bar_count_total` | Local | ✓ | 576 | Counting/Enumeration |
| `chart_series_count` | Local | ✓ | 576 | Counting/Enumeration |
| `chart_line_count` | Local | ✓ | 576 | Counting/Enumeration |
| `diagram_node_count` | Local | ✓ | 120 | Counting/Enumeration |
| `pie_slice_count` | Local | ✓ | 60 | Counting/Enumeration |
| `table_row_count` | Local | ✓ | 240 | Counting/Enumeration |
| `circled_letter` | Local | ✓ | 40 | Spatial Localization |
| `circled_letter` | HF | ✓ | 624 | Spatial Localization |
| `chart_bar_value` | Local | ✓ | 64 | Spatial Localization |
| `chart_grouped_value` | Local | ✓ | 576 | Spatial Localization |
| `chart_line_value` | Local | ✓ | 576 | Spatial Localization |
| `table_cell_lookup` | Local | ✓ | 480 | Spatial Localization |
| `line_intersection` | Local | ✓ | 150 | Line/Path Following |
| `line_intersection` | HF | ✓ | 3600 | Line/Path Following |
| `path_following` | Local | ✓ | 140 | Line/Path Following |
| `path_following` | HF | ✓ | 720 | Line/Path Following |
| `chart_line_trend` | Local | ✓ | 576 | Line/Path Following |
| `diagram_next_step` | Local | ✓ | 180 | Line/Path Following |
| `diagram_decision` | Local | ✓ | 300 | Line/Path Following |
| `touching_circles` | Local | ✓ | 850 | Relative Comparison |
| `touching_circles` | HF | ✓ | 1344 | Relative Comparison |
| `chart_bar_compare` | Local | ✓ | 64 | Relative Comparison |
| `table_max` | Local | ✓ | 240 | Relative Comparison |
| `pie_slice_compare` | Local | ✓ | 60 | Relative Comparison |
| `relative_bar_compare` | Local | ✓ | 600 | Relative Comparison |
| `relative_line_compare` | Local | ✓ | 300 | Relative Comparison |
| `chart_data_match` | Local | ✓ | 240 | Relative Comparison |
| `chart_legend_match` | Local | ✓ | 180 | Color Discrimination |
| `color_grid_odd` | Local | ✓ | 500 | Color Discrimination |
| `heatmap_cell_value` | Local | ✓ | 270 | Color Discrimination |
| `text_word_reading` | Local | ✓ | 750 | Text Reading |
| `text_number_reading` | Local | ✓ | 200 | Text Reading |
| `patterned_grid` | Local | ✓ | 252 | Prior/Bias Override |
| `patterned_grid` | HF | ✓ | 336 | Prior/Bias Override |
| `flags` | HF | ❌ | 0 | Prior/Bias Override |
| `logos` | HF | ❌ | 0 | Prior/Bias Override |
| `conflict_value_label` | Local | ✓ | 40 | Visual-Textual Consistency |
| `conflict_title_trend` | Local | ✓ | 40 | Visual-Textual Consistency |
| `conflict_legend_color` | Local | ✓ | 40 | Visual-Textual Consistency |
| `conflict_annotation` | Local | ✓ | 40 | Visual-Textual Consistency |

## Notes

- Counts reflect instances in `results/*_results.jsonl` as of last update
- HF sources: VLMs-are-Blind (blind) and VLMs-are-Biased (biased) benchmarks
- `flags` and `logos` available via `--dataset biased --topics Flags Logos` but not yet run
- `chart_data_match` instances exist (from `chart_comparison` generator) but not yet evaluated
- Excluded from analysis (results exist but not in scope): `board_game_rows`, `board_game_cols`, `optical_illusion`
