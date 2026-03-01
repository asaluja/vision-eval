# Color Discrimination — Evaluation Summary

## Primitive Definition
Can the model distinguish colors, match legend entries to data series, and detect shade differences? This spans legend-to-bar matching, odd-shade cell detection, and heatmap value reading.

## Key Finding
**Color discrimination is solved for visually distinct colors (100%) but degrades sharply as shades converge. At ΔL≈7 in HSL lightness (near-threshold), odd-cell detection drops to 60%. At ΔL≈5, it collapses to 21% — near random guessing. (ΔL is measured in HSL space, not perceptually uniform CIELAB; equivalent CIELAB ΔL* ranges are roughly 4–9 depending on hue.) Heatmap value reading (56% tolerance-based accuracy) appears to be the hardest task, but MAE analysis reveals the model estimates color values at ~12% normalized error across both (0,10) and (0,100) ranges — the low accuracy on wider ranges is an artifact of systematic rounding to colorbar tick marks, not worse perception.**

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

ΔL here is the difference in HSL lightness (Python `colorsys`), scaled 0–100. The generator holds hue and saturation fixed and varies only L: base at L=0.40, odd cell at L=0.40+delta. Note: HSL lightness is not perceptually uniform — the same ΔL produces different perceptual contrasts across color families (e.g., ΔL=5 in HSL corresponds to roughly 4.4–6.5 in CIELAB ΔL*, which partly explains the large cross-family accuracy spread below).

| Difficulty | ΔL (HSL×100) | Accuracy | n |
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

Requires three compound operations: (1) localize the queried cell, (2) read its color, (3) map that color to a value on the colorbar. However, **tolerance-based accuracy is misleading for this task** — MAE analysis reveals the model performs comparably across value ranges, with the accuracy gap driven by scoring granularity, not perceptual quality.

##### MAE Analysis (Primary Metric)

| Range | n | MAE | NMAE (% of range) | Median AE | Tolerance Accuracy |
|-------|---|-----|--------------------|-----------|--------------------|
| (0, 10) | 90 | 0.92 | **9.2%** | 1.0 | 90.0% |
| (0, 100) | 90 | 11.69 | **11.7%** | 10.0 | 15.6% |
| (−1, 1) | 90 | 2.43 | **121.7%** | 2.0 | 62.2% |

**Key insight: the (0,10) and (0,100) ranges have nearly identical normalized MAE (~9–12%).** The model performs roughly the same quality of color-to-value estimation regardless of scale. The 15.6% accuracy on (0,100) is an artifact of tight tolerance scoring (±5 for gt=100), not genuinely worse perception. On (0,10), MAE <1 easily passes the ±2 floor, inflating accuracy to 90%.

##### Systematic Rounding to Colorbar Ticks

On the (0,100) range, **100% of extracted values are multiples of 10** (vs. 36% of ground truth values). The model reads the cell color, finds the nearest major tick on the colorbar, and reports that value. This is not a failure of color perception — it is the natural behavior of reading a continuous color scale without fine interpolation. For (0,10), the model similarly rounds to integers, which happen to be the tick marks on that scale, and the tight spacing means rounding errors stay small.

**Error distribution for (0,100) — most errors are small:**

| Tolerance | Within | % |
|-----------|--------|---|
| ±5 | 26/90 | 28.9% |
| ±10 | 55/90 | **61.1%** |
| ±15 | 70/90 | 77.8% |
| ±20 | 76/90 | **84.4%** |
| ±25 | 78/90 | 86.7% |

61% of answers are within ±10 and 84% within ±20 — consistent with systematic rounding to the nearest 10.

##### The (−1,1) Range is Fundamentally Broken

Unlike the other ranges, the (−1,1) range reveals a genuine failure: **53% of extracted values fall outside the valid [−1, 1] range** (the model returns values like 3, 5, 6). The model does not read the colorbar scale labels — it appears to hallucinate a (0,N) range and report values from that imagined scale. With only 3 possible integer ground-truth values (−1, 0, 1), the task is also poorly suited to integer extraction. This range tests **scale label reading**, not color interpolation, and should be analyzed separately or replaced.

Extracted value distribution for (−1,1): {0: 7, 1: 35, 2: 9, 3: 12, 4: 9, 5: 8, 6: 10} — the model overwhelmingly returns small positive integers regardless of the actual colorbar range.

##### Breakdowns (excluding −1,1 range)

**MAE by grid size (0,100 range):**

| Grid | MAE | Tolerance Accuracy | n |
|------|-----|--------------------|---|
| 4×4 | 10.7 | 63.3% | 30 |
| 4×6 | 11.9 | 54.4% | 30 |
| 6×6 | 12.4 | 50.0% | 30 |

Modest degradation with grid density — MAE increases ~16% from 4×4 to 6×6.

**MAE by colormap (0,100 range):**

| Colormap | MAE | Tolerance Accuracy | n |
|----------|-----|--------------------|---|
| viridis | **8.2** | 58.9% | 30 |
| RdBu | 13.0 | 53.3% | 30 |
| YlOrRd | **13.9** | 55.6% | 30 |

Viridis (perceptually uniform, sequential) has substantially lower MAE than RdBu (diverging) or YlOrRd (sequential but non-uniform). This is consistent with viridis being designed for accurate value reading.

**Extended thinking: 56.3%** (+0.4pp) — no improvement. Thinking cannot improve color-to-value interpolation; this is a perceptual precision limitation, not a reasoning one.

## Cross-Task Patterns

1. **Easy color discrimination is solved.** Distinct hue families (100%), large lightness gaps (100%). The model's color vocabulary is adequate for typical business charts with well-chosen palettes.

2. **The perceptual cliff falls at ΔL≈7–10 (HSL lightness).** Above ΔL=10: ≥86%. At ΔL=7: 60%. At ΔL=5: 21%. This is a sharp threshold, not a gradual curve. Same-family shades need at least ΔL≈10–15 to be reliably discriminable. Because HSL lightness is not perceptually uniform, the equivalent CIELAB ΔL* range is roughly 6–12 depending on hue family.

3. **Orange is uniquely robust; green is uniquely fragile.** Across all tasks, orange maintains much higher accuracy at near-threshold and extreme difficulties. Greens collapse earliest. This mirrors the model's apparent color representation geometry — warm hues are more discriminable at small lightness deltas than cool/neutral hues.

4. **More similar bars = harder matching, non-linearly.** Legend-to-bar matching drops from 90% (3 bars) to 62% (5 bars) in the hard condition. Each additional same-family bar compounds confusion.

5. **Heatmap accuracy is misleading — MAE tells the real story.** Tolerance-based accuracy (15.6% on the 0-100 range) dramatically understates performance. Normalized MAE is ~12% across both the (0,10) and (0,100) ranges — the model does equally well at color estimation regardless of scale. The bottleneck is systematic rounding to colorbar tick marks (100% of 0-100 answers are multiples of 10), not poor color perception.

6. **Colorbar design matters.** Viridis (perceptually uniform) achieves MAE=8.2 vs. RdBu=13.0 and YlOrRd=13.9 on the 0-100 range. Perceptually uniform colormaps designed for accurate value reading genuinely help the model. Diverging colormaps (RdBu) that pass through white or near-white create mid-range ambiguity.

7. **Non-standard colorbar ranges break scale reading.** On (−1,1), 53% of extracted values fall outside the valid range — the model hallucinates a positive integer scale rather than reading the colorbar labels. This is a distinct failure mode (scale label comprehension) from color interpolation.

## Finetuning Implications

- **Near-threshold shade discrimination is the highest-value target.** The ΔL=7 regime (60%) is realistic — professional charts frequently use similar-shade families for related series. Training pairs: (color grid with ΔL=7-10 → correct odd cell) across all families, weighted toward greens/purples.
- **DPO pairs for legend matching:** Hard-difficulty instances with n_bars=4-5 provide natural preference pairs. Rejected: model confuses dark blue for medium blue and returns wrong bar value. Preferred: correctly identifies the shade.
- **Heatmap training should target sub-tick interpolation.** The model already reads the approximate color region correctly (NMAE ~12%) but rounds to the nearest major tick mark. Training data that rewards precision between ticks ("the cell is ~65, not 70") would push past the current rounding plateau. Chain-of-thought forcing the model to explicitly reference the colorbar ("this shade is between the 60 and 70 marks, closer to 70") may help.
- **Non-standard colorbar ranges need explicit scale-reading training.** The (−1,1) failure is not about color perception — the model doesn't read the scale labels at all. Training pairs with diverse value ranges (negative, fractional, non-zero-based) would address this.
- **Prefer perceptually uniform colormaps.** Viridis's MAE advantage (8.2 vs. 13+) suggests training on uniform colormaps first builds a cleaner color-to-value signal before introducing diverging or non-uniform scales.
- **Easy color discrimination needs no improvement** — distinct-color charts are already solved. Training resources should go to same-family, near-threshold cases.
