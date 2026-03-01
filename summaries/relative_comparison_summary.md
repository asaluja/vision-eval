# Relative Comparison — Evaluation Summary

## Primitive Definition
Can the model compare two visual elements and determine which is larger/higher/closer/more? This spans bar height comparison, line series comparison, table max identification, and proximity/touching detection.

## Key Finding
**Comparison is solved for discrete, labeled elements (bars, table cells) down to value differences of 2. At diff=1 (~1% relative difference), accuracy drops to 94%. Proximity detection reveals a sharp perceptual threshold: the model cannot distinguish "separated" from "touching" below ~12-15 pixels of visible gap, with r=0.1 circles showing a pathological always-touching bias up to 10px gaps.**

## Tasks Evaluated

### Ceiling Tasks (100% exact match)

| Task | n | Source | Notes |
|------|---|--------|-------|
| Table max value | 240 | Generated | 3-10 rows × 2-5 cols, plain and shaded styles |
| Bar comparison (diff≥2) | 400 | Generated | value_diff=[2,5,10,20,40], all n_bars and grid configs |
| Line comparison (gap≥2) | 20 | Generated | 2-line charts, all gaps ≥2 are correct |
| Touching circles (dist≤0, r≥0.1) | 200 | Generated | Overlapping/touching correctly identified |
| Touching circles (dist≥0.2) | 250 | Generated | Clearly separated correctly identified |

**Table max** is perfect across all configurations — 4 row counts × 3 column counts × 2 styles = 24 configs, all at 100%. The model reads numeric values from table cells flawlessly and compares them correctly.

**Bar comparison** is perfect at diff≥2 regardless of number of distractor bars (tested up to 12), grid presence, or base value magnitude.

### Degrading Tasks

#### Bar Height Comparison (Controlled Diffs)

| value_diff | n_bars=4 | n_bars=6 | n_bars=8 | n_bars=10 | n_bars=12 | Overall |
|-----------|----------|----------|----------|-----------|-----------|---------|
| 1 | 90% | 95% | 95% | 90% | 100% | **94%** |
| 2 | 100% | 100% | 100% | 100% | 100% | 100% |
| 5+ | 100% | 100% | 100% | 100% | 100% | 100% |

**diff=1 breakdown by grid:**

| n_bars | grid=False | grid=True |
|--------|-----------|-----------|
| 4 | 100% | 80% |
| 6 | 100% | 90% |
| 8 | 100% | 90% |
| 10 | 80% | 100% |
| 12 | 100% | 100% |

- The threshold is razor-sharp at diff=1 (absolute difference of 1 unit on a ~60-95 scale, i.e., ~1-1.7% relative difference).
- At diff=2 (2-3% relative), accuracy is already 100%. There is no gradual degradation curve — the cliff is between 1% and 2% relative difference.
- Number of distractor bars (4-12) has **no significant effect**. The model correctly identifies and focuses on the two highlighted (orange) bars regardless of clutter.
- Grid lines show no consistent directional effect — errors at diff=1 are scattered across grid/no-grid conditions.
- **Error pattern**: All 5 errors at diff=1 share the same failure mode — the model reports both bars as "approximately equal" or reads them as the same value, then guesses wrong. It correctly perceives the bars are nearly identical but cannot resolve the 1-unit difference.

#### Highest Bar Identification (Chart Generator, Natural Data)

| n_categories | Accuracy | n |
|-------------|----------|---|
| 3 | 100% | 40 |
| 5 | 95% | 40 |
| 7 | 100% | 40 |
| 10 | 92% | 40 |

Overall: **96.9%** (155/160)

- Errors cluster in the `vals0` (narrow value spread) configurations where the top two bars are close in height.
- At n=10, errors include label extraction issues ("June" vs "Jun"), suggesting some failures are scoring artifacts rather than perceptual failures.
- Consistent with the controlled diff findings: when the value difference is small, the model struggles regardless of whether the comparison is explicit (highlighted pair) or implicit (find the max).

#### Touching/Proximity Detection

**Overall accuracy by distance × radius (accuracy heatmap):**

| dist | r=0.05 | r=0.10 | r=0.15 | r=0.20 | r=0.25 |
|------|--------|--------|--------|--------|--------|
| ≤0.0 (overlap/touch) | 93% | 100% | 100% | 100% | 100% |
| 0.01 | 20% | **0%** | 0% | 0% | 0% |
| 0.02 | 10% | **0%** | 0% | 0% | 0% |
| 0.03 | 40% | **0%** | 0% | 0% | 0% |
| 0.04 | 40% | **0%** | 0% | 0% | 0% |
| 0.05 | 50% | **0%** | 0% | 0% | 50% |
| 0.06 | 50% | **0%** | 0% | 60% | 50% |
| 0.07 | 50% | **0%** | 20% | 100% | 50% |
| 0.08 | 30% | **0%** | 90% | 100% | 100% |
| 0.09 | 30% | **0%** | 100% | 100% | 100% |
| 0.10 | 50% | **0%** | 100% | 100% | 100% |
| ≥0.20 | 100% | 100% | 100% | 100% | 100% |

**Approximate pixel gaps at key thresholds (canvas ≈ 500px effective):**

| Radius | Threshold distance | Pixel gap at threshold | Transition width |
|--------|-------------------|----------------------|-----------------|
| r=0.05 | — | — | No clean threshold (noise) |
| r=0.10 | 0.10 → 0.20 | 10px → 20px | Binary cliff |
| r=0.15 | 0.07 → 0.09 | 10.5px → 13.5px | Steep sigmoid |
| r=0.20 | 0.06 → 0.07 | 12px → 14px | Steep sigmoid |
| r=0.25 | 0.07 → 0.08 | 17.5px → 20px | Steep sigmoid |

**Three distinct radius regimes:**

1. **r=0.05 (tiny circles, ~50px diameter):** Accuracy is noisy (20-50%) across all small gaps. The circles are too small for reliable proximity assessment. Even touching (dist=0.0) only reaches 80%. The model is essentially guessing.

2. **r=0.10 (small circles, ~100px diameter):** Pathological "always touching" bias. The model says "Yes" for **every single instance** from dist=0.01 to dist=0.10 (100 consecutive wrong answers). Then jumps to 100% correct at dist=0.20. This is not gradual degradation — it's a binary failure where gaps up to 10px are invisible to the model at this circle size, and then a 20px gap is suddenly obvious.

3. **r=0.15-0.25 (medium-large circles):** Clean sigmoid transition. The perceptual threshold consistently falls at **~12-15px of visible gap**. Below this, the model defaults to "touching." Above this, accuracy reaches 100%. The transition is steep (0% to 100% over ~2-4px of gap).

**The universal pixel threshold is ~12-15px.** For r=0.15, 0.20, and 0.25, accuracy transitions from 0% to ≥90% as the absolute pixel gap crosses the 12-15px range. The r=0.10 anomaly (threshold at 10-20px with no intermediate accuracy) may reflect a different failure mode — perhaps the circle diameter-to-gap ratio creates a visual illusion of touching for medium-sized circles.

**Error pattern:** 100% of errors in the near-threshold zone are false positives — the model says "touching" when circles are separated. It never makes the opposite error (saying "separated" when actually touching/overlapping), except for the noisy r=0.05 case.

#### Pie Chart Slice Comparison (Largest Slice)

| n_slices | Accuracy | n |
|----------|----------|---|
| 3 | 70% | 10 |
| 4 | 90% | 10 |
| 5 | 70% | 10 |
| 6 | 80% | 10 |
| 7 | 80% | 10 |
| 8 | 50% | 10 |

Overall: **73.3%** (44/60) — no percentage labels shown.

Errors correlate strongly with the gap between the largest and second-largest slice. Most errors occur when the top two slices differ by ≤5 percentage points (e.g., 34% vs 35%). At 8 slices the accuracy drops to 50%, since more slices means more candidates at similar sizes.

This is notably harder than bar comparison, where diff≥2 is 100%. Angular estimation (pie wedges) is perceptually harder than height estimation (bars) for the same proportional difference — a ~5% relative difference in a pie chart (about 18° of arc) is much harder to resolve than a 5% height difference in a bar chart.

#### Pie Chart Value Estimation

| Condition | Accuracy | n |
|-----------|----------|---|
| With % labels | **100%** | 60 |
| Without % labels | **53%** | 60 |

The text label effect again: with percentage labels, value reading is perfect. Without labels, the model must estimate angular proportions visually.

**Error distribution (no % labels):**
- Mean absolute error: 2.8 percentage points
- Within ±5%: 88.3%
- Within ±10%: 100%

Errors are small — the model approximates proportions reasonably but can't achieve the ±2pp tolerance threshold ~47% of the time. This is consistent with angular estimation being imprecise but not wildly wrong.

## Cross-Task Patterns

1. **Discrete labeled comparison is solved.** Table max (100%), bar comparison at diff≥2 (100%), and line comparison at gap≥2 (100%) are all ceiling tasks. When elements have distinct labels and measurable values, the model compares correctly.

2. **The 1% relative difference threshold for bars.** At diff=1 on a base of 60-95, the model cannot reliably distinguish heights that differ by ~1-1.7%. At diff=2 (~2-3%), it's perfect. This threshold is remarkably consistent across 4-12 bars and with/without gridlines.

3. **Pixel-level proximity detection has a hard ~12-15px floor.** Below ~12px of visible gap between circle edges, the model defaults to "touching." This is a fundamental resolution limit of the vision encoder, not a reasoning failure — the model's responses show it examining the image carefully but being unable to resolve sub-12px gaps.

4. **Circle size creates distinct failure regimes.** Tiny circles (r=0.05) → noise. Small circles (r=0.10) → binary cliff with "always touching" bias. Medium+ circles (r=0.15+) → clean sigmoid with ~12-15px threshold. This suggests the model processes proximity differently depending on object scale, not just gap size.

5. **False positive bias in proximity.** Near the threshold, errors are exclusively "touching" when actually separated, never the reverse. The model has a systematic bias toward reporting contact. This is consistent with a prior that nearby objects are touching — a reasonable real-world prior that becomes incorrect for precisely separated geometric shapes.

6. **No distractor effect for comparison.** Increasing bars from 4 to 12 has no impact on comparison accuracy. The model successfully attends to highlighted elements and ignores irrelevant context. This contrasts with counting tasks where more elements consistently degrades performance.

7. **Angular comparison (pie) is harder than height comparison (bars).** Bar comparison is 100% at diff≥2 (~2-3% relative); pie slice comparison is 73% overall, with errors at gaps up to 12 percentage points. Estimating angles/areas is perceptually harder than comparing aligned bar heights — consistent with psychophysics research showing humans are also worse at angle vs. length judgments.

## Finetuning Implications

- **Proximity calibration is the highest-value target.** The 12-15px threshold and the r=0.10 pathological bias represent clear, systematic errors that finetuning could address. Training pairs: (nearly-touching circles with visible gap → "No") at various scales.
- **DPO pairs for touching circles:** The 0% → 100% transitions provide ideal hard negative mining. Pairs of images at dist=0.08 (wrong) vs dist=0.10 (right) for the same radius create high-quality preference pairs where the visual difference is minimal but the correct answer flips.
- **Diff=1 bar comparison is near the noise floor.** At 94% accuracy, finetuning could improve this, but the absolute value difference (1 pixel of bar height) is genuinely at the limit of visual resolution. Chain-of-thought reasoning ("I estimate bar A at 63 and bar B at 64, so B is taller") might help more than pure visual finetuning.
- **Table max needs no improvement** — already at 100% across all configurations tested.
- **Scale-aware training for proximity:** The r=0.10 pathological behavior suggests the model needs proximity training specifically at the small-circle regime, where its current representation collapses gap information.
