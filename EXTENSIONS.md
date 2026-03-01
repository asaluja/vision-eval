# Extensions & Known Issues

## Patterned Grid: Generator Bug (Fixed, Needs Re-evaluation)

The `generate/patterned_grids.py` generator had a ground-truth bug: `actual_count` was set to `count` after the cell-drawing loop, but `count` is reassigned on every iteration, so it held the value from the last cell drawn (an edge cell, always 1) rather than the anomaly cell's actual shape count.

**Impact**: All patterned grid results in `results/patterned_grid_results.jsonl` have incorrect ground truth (always 1). The reported 15.5% accuracy and 0% add-anomaly accuracy were artifacts of scoring against wrong labels. With corrected ground truth, the model actually achieves ~76% overall — it counts correctly most of the time. The entire narrative about the model being unable to see anomalies was inverted.

**Fix**: Capture `anomaly_count = count` inside the anomaly cell branch before the loop overwrites `count`.

**Action needed**: Re-generate and re-evaluate to produce correct results. Once done, the patterned grid section can be restored to the prior bias override summary. The task is currently excluded from all summaries and figures pending re-evaluation.

---

# Extensions: Synthetic Image Pairs

## Motivation

All current evaluation tasks use **single images**. Image pairs are a fundamentally different evaluation paradigm: show two nearly identical images and ask the model to identify or reason about the difference. This is higher-value than single-image tasks because:

1. **Directly generates finetuning data** — every pair where CLIP can't see the difference and Haiku gets it wrong is a contrastive training example
2. **Start from what matters, verify it's a blind spot** — unlike natural-image approaches (MMVP) where you find blind spots and then figure out why they matter
3. **CLIP embedding analysis adds rigor** — pairs designed so CLIP cosine similarity is high (semantically identical) but the perceptual difference is task-critical

## Status

- [x] **Chart data match** (`generate/chart_comparison.py`) — same data rendered as different chart types, ask if values match. First implementation of this paradigm.
- [ ] Everything below is future work.

## Per-Primitive Pair Types

### 1. Relative Comparison in Charts (HIGHEST PRIORITY)

Most common real-world question, small visual delta, CLIP almost certainly blind to it.

- Two bar charts identical except bar A is slightly taller than bar B in one, and slightly shorter in the other
- Two line charts where the red line crosses above/below the blue line at different points
- "Which is bigger?" with a small delta is exactly where CLIP says "same image"

### 2. Text/Number Changes in Documents (HIGH PRIORITY)

Directly tests whether the model reads or hallucinates values.

- Same form, but the dollar amount is $1,234 vs. $1,284
- Same chart, but the y-axis label says "Revenue ($M)" vs. "Revenue ($K)"
- Same slide, but a bullet point says "increased" vs. "decreased"

### 3. Count Changes in Charts/Diagrams (HIGH PRIORITY)

Fundamental and easy to generate at scale.

- Same chart layout, 5 bars vs. 6 bars
- Same scatter plot, 8 points vs. 9 points
- Same diagram, 4 nodes vs. 5 nodes
- Perfect CLIP traps — overall composition is identical, only the count changes

### 4. Spatial Localization

- Same table, but the highlighted cell is at (2,3) vs. (2,4)
- Same bar chart, but the tallest bar is the 3rd vs. the 4th
- Same UI mockup, but the error icon is next to a different field

### 5. Color Discrimination

- Same chart, but the legend maps blue->Revenue, red->Cost in one and colors are swapped in the other
- Same heatmap, but one cell is slightly darker
- Same dashboard, green status indicator vs. yellow

### 6. Line / Path Following

- Same flowchart structure, but the "Yes" branch goes left in one and right in the other
- Same line chart, but the trend goes up at the end vs. down
- Same network diagram, but one edge is rerouted

### 7. Prior / Bias Override

- Standard 8x8 chessboard vs. 9x8 chessboard
- Standard die face with 6 dots vs. 7 dots
- CLIP will almost certainly conflate these — it's seen millions of chessboards and "knows" what one looks like

---

# Extended Thinking Experiments

## Extended Thinking Results

Ran with `--thinking --thinking-budget 8000` across multiple primitives.

### Results

| Primitive | Task | Baseline | Thinking | Delta |
|-----------|------|----------|----------|-------|
| Prior Bias | Board games | 60.0% | 59.5% | -0.5pp |
| Prior Bias | conflict_annotation | 75.0% | **90.0%** | **+15.0pp** |
| Prior Bias | conflict_value_label | 0% | 0% | — |
| Prior Bias | conflict_title_trend | 100% | 97.5% | -2.5pp |
| Prior Bias | conflict_legend_color | 100% | 97.5% | -2.5pp |
| Rel. Comparison | pie_slice_compare | 73.3% | 75.0% | +1.7pp |
| Rel. Comparison | pie_slice_count | 100% | 98.3% | -1.7pp |
| Rel. Comparison | pie_value_estimate | 76.7% | 72.5% | -4.2pp |
| Color | heatmap_cell_value | 55.9% | 56.3% | +0.4pp |

**Key insight: Extended thinking only helps annotation conflicts (+15pp).** This is the one task where the model sees the correct answer but is swayed by a misleading signal — giving it space to reason helps it resist. All other tasks are perceptual, not reasoning, failures:
- Value labels (0%→0%): OCR-level text reliance is not a reasoning problem
- Board games (-0.5pp): Cannot see the extra row regardless of thinking time
- Pie charts (+1.7pp): Angular estimation doesn't improve with reasoning
- Heatmap (+0.4pp): Color-to-value interpolation is perceptual

*Note: Patterned grid thinking results were removed due to a generator ground-truth bug (see top of this file). Re-evaluation needed before conclusions can be drawn.*

---

## Implementation Notes (Image Pairs)

- Each pair type needs its own generator in `generate/`
- Ground truth is typically Yes/No ("are these the same?") or a specific difference description
- The `chart_comparison.py` generator can serve as a template for the side-by-side composite image pattern
- CLIP/DINOv2 embedding scores can be computed post-hoc on generated pairs to validate that they are indeed "CLIP traps" (high CLIP sim, low DINOv2 sim)
- For finetuning: pairs where Haiku fails become contrastive training examples — show both images, teach the model to articulate the difference
