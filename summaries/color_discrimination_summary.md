# Color Discrimination — Evaluation Summary

## Primitive Definition
Can the model distinguish colors, match legend entries to data series, and detect shade differences? This spans legend-to-bar matching, odd-shade cell detection, and heatmap value reading.

## Key Finding
**Color discrimination is solved for visually distinct colors (100%) but degrades sharply as shades converge. At ΔL≈7 (near-threshold lightness difference), odd-cell detection drops to 60%. At ΔL≈5 (extreme), it collapses to 21% — near random guessing. Heatmap value reading (56%) is the hardest task, requiring color reading and continuous scale interpolation simultaneously.**

## Tasks Evaluated

### Ceiling Tasks (100% accuracy)

| Task | Accuracy | n | Condition |
|------|----------|---|-----------|
| `chart_legend_match` (easy) | 100% | 30 | Maximally distinct colors (red, blue, green, orange, purple) |
| `color_grid_odd` (easy) | 100% | 100 | Darkest vs lightest shade (ΔL≈30-40) |
| `color_grid_odd` (hard) | 100% | 100 | Dark vs medium shade (ΔL≈16-23) |

When colors are visually distinct — either across different hue families or with large lightness differences — performance is perfect regardless of number of bars or grid size.

### Degrading Tasks

#### Legend-to-Bar Matching (`chart_legend_match`)

Overall: **77.8%** (140/180)

| Difficulty | Accuracy | n | Description |
|-----------|----------|---|-------------|
| Easy | 100% | 30 | Bars use maximally distinct hue families |
| Hard | **73.3%** | 150 | Bars use same-family similar shades |

**Hard difficulty by number of bars:**

| n_bars | Accuracy | n |
|--------|----------|---|
| 3 | 90% | 50 |
| 4 | 68% | 50 |
| 5 | **62%** | 50 |

With only 3 similar-shade bars the model correctly identifies the queried color 90% of the time. As bars increase to 5, accuracy drops to 62% — more candidates with similar colors creates confusion between adjacent shades in the legend.

**Hard difficulty by color family:**

| Family | Accuracy | n |
|--------|----------|---|
| blues | 86.7% | 30 |
| reds | 80.0% | 30 |
| greens | 80.0% | 30 |
| oranges | **60.0%** | 30 |
| purples | **60.0%** | 30 |

Oranges and purples are the hardest families — their similar shades are more perceptually ambiguous than blues or reds, possibly because orange/purple occupy narrower regions of the model's color representation.

**Error pattern:** Most errors are adjacent-shade confusions — the model picks the wrong shade within the same family rather than a completely wrong family. The bar heights are read correctly; the failure is in matching the color to the correct legend entry.

#### Odd-Shade Cell Detection (`color_grid_odd`)

Overall: **73.4%** (367/500)

**By grid difficulty (ΔL = lightness delta between odd cell and base):**

| Difficulty | ΔL approx | Accuracy | n |
|-----------|-----------|----------|---|
| easy | ΔL≈30-40 | 100% | 100 |
| hard | ΔL≈16-23 | 100% | 100 |
| very_hard | ΔL≈10 | **86%** | 100 |
| near_threshold | ΔL≈7 | **60%** | 100 |
| extreme | ΔL≈5 | **21%** | 100 |

The perceptual cliff falls between ΔL=10 (86%) and ΔL=7 (60%). At ΔL=5, accuracy is 21% — essentially random for a 4×4 grid (random baseline = 6.25%, so the model retains slight above-chance sensitivity but nearly none).

**Color family × difficulty cross-tab (accuracy %):**

| Difficulty | blues | greens | oranges | purples | reds |
|-----------|-------|--------|---------|---------|------|
| easy | 100% | 100% | 100% | 100% | 100% |
| hard | 100% | 100% | 100% | 100% | 100% |
| very_hard | 90% | 70% | **100%** | 80% | 90% |
| near_threshold | 70% | **25%** | **90%** | 50% | 65% |
| extreme | 5% | 15% | **55%** | 10% | 20% |

Oranges stand out: even at extreme difficulty (ΔL≈5), orange achieves 55% — more than double any other family (next best: greens at 15%). Greens are consistently the hardest family, reaching near-zero at extreme difficulty. This asymmetry likely reflects how the model's visual encoder weights warm vs. cool hues.

**By grid size × difficulty:**

| | grid=4 | grid=6 |
|---|---|---|
| easy | 100% | 100% |
| hard | 100% | 100% |
| very_hard | 90% | 82% |
| near_threshold | 64% | 56% |
| extreme | 22% | 20% |

A modest ~8pp penalty for the larger grid at near-threshold, but negligible at extreme. Cell size is not the primary failure mode — colorimetric similarity dominates.

#### Heatmap Value Reading (`heatmap_cell_value`)

Overall: **55.9%** (151/270) within tolerance (max(2, gt×5%))

Requires three compound operations: (1) localize the queried cell, (2) read its color, (3) map that color to a value on the colorbar.

**By grid size:**

| Grid | Accuracy | n |
|------|----------|---|
| 4×4 | **63.3%** | 90 |
| 4×6 | 54.4% | 90 |
| 6×6 | **50.0%** | 90 |

Smaller grids are easier — fewer cells, larger cell area, less crowded colorbar navigation.

**By colormap:**

| Colormap | Accuracy | n |
|----------|----------|---|
| viridis | 58.9% | 90 |
| YlOrRd | 55.6% | 90 |
| RdBu | **53.3%** | 90 |

RdBu (diverging, passes through white at center) is hardest — near-neutral midrange colors are ambiguous about sign and magnitude.

**Error magnitude distribution:**

| Tolerance | Within | % |
|-----------|--------|---|
| Exact (±0) | 69/270 | 25.6% |
| ±2 | 150/270 | 55.6% |
| ±5 | 194/270 | 71.9% |
| ±10 | 235/270 | 87.0% |
| ±20 | 256/270 | 94.8% |

The model is rarely wildly wrong (94.8% within ±20) but rarely precise (25.9% exact). Errors cluster in the ±5-10 range — the model reads the approximate color region correctly but cannot interpolate the colorbar precisely.

## Cross-Task Patterns

1. **Easy color discrimination is solved.** Distinct hue families (100%), large lightness gaps (100%). The model's color vocabulary is adequate for typical business charts with well-chosen palettes.

2. **The perceptual cliff falls at ΔL≈7-10.** Above ΔL=10: ≥86%. At ΔL=7: 60%. At ΔL=5: 21%. This is a sharp threshold, not a gradual curve. Same-family shades need at least ΔL≈10-15 to be reliably discriminable.

3. **Orange is uniquely robust; green is uniquely fragile.** Across all tasks, orange maintains much higher accuracy at near-threshold and extreme difficulties. Greens collapse earliest. This mirrors the model's apparent color representation geometry — warm hues are more discriminable at small lightness deltas than cool/neutral hues.

4. **More similar bars = harder matching, non-linearly.** Legend-to-bar matching drops from 90% (3 bars) to 62% (5 bars) in the hard condition. Each additional same-family bar compounds confusion.

5. **Heatmap combines three failure modes.** Cell localization, color reading, and colorbar interpolation errors all compound. The gap between 25.9% exact and 87.0% within-±10 suggests the model can identify the approximate color region but lacks precision in continuous scale reading.

6. **Colorbar design matters.** Diverging colormaps (RdBu) that pass through white or near-white are harder than sequential colormaps (viridis, YlOrRd). Mid-range ambiguity is a design failure, not just a model failure.

## Finetuning Implications

- **Near-threshold shade discrimination is the highest-value target.** The ΔL=7 regime (60%) is realistic — professional charts frequently use similar-shade families for related series. Training pairs: (color grid with ΔL=7-10 → correct odd cell) across all families, weighted toward greens/purples.
- **DPO pairs for legend matching:** Hard-difficulty instances with n_bars=4-5 provide natural preference pairs. Rejected: model confuses dark blue for medium blue and returns wrong bar value. Preferred: correctly identifies the shade.
- **Heatmap training should emphasize colorbar interpolation.** The main failure mode is scale reading precision, not cell localization. Training data where the model explicitly reads the colorbar ("the cell color corresponds to ≈60 on the scale") would build the color-to-value mapping.
- **Easy color discrimination needs no improvement** — distinct-color charts are already solved. Training resources should go to same-family, near-threshold cases.
- **Avoid diverging colormaps in training eval.** RdBu's white midpoint creates genuine ambiguity. Training on sequential colormaps (viridis, YlOrRd) first builds a cleaner color-to-value signal before introducing the complexity of diverging scales.
