# Relative Comparison — Evaluation Summary

## Primitive Definition
Can the model compare two visual elements and determine which is larger/higher/closer/more? This spans bar height comparison, line series comparison, pie slice comparison, table max identification, and proximity/touching detection.

## Key Finding
**Comparison is solved for discrete, labeled elements (bars, table cells) down to value differences of 2. At diff=1 (~1% relative difference), accuracy drops to 89%. Proximity detection reveals a sharp perceptual threshold: the model cannot distinguish "separated" from "touching" below ~12-15 pixels of visible gap. Pie slice comparison (73%) is substantially harder than bar comparison (98%) for the same proportional differences, confirming angular estimation is a weaker perceptual channel.**

## Tasks Evaluated

### Ceiling Tasks (≥95% accuracy)

| Task | Accuracy | n | Source | Notes |
|------|----------|---|--------|-------|
| Table max value | 100% | 240 | Local | 3-10 rows × 2-5 cols, plain and shaded styles |
| Bar comparison (diff≥2) | 100% | 500 | Local | value_diff=[2,5,10,20,40], all n_bars and grid configs |
| Line comparison (gap≥1) | 100% | 38 | Local | 2-line charts, all non-zero gaps correct |
| Highest bar (chart) | 98.4% | 64 | Local | 3-10 category charts, natural data |
| Relative bar compare (overall) | 98.2% | 600 | Local | Across all diffs, including diff=1 |

**Table max** is perfect across all 24 configurations (4 row counts × 3 column counts × 2 styles). The model reads numeric values from table cells flawlessly and compares them correctly.

**Bar comparison** is perfect at diff≥2 regardless of distractor count (tested up to 12 bars), grid presence, or base value magnitude.

### Degrading Tasks

#### Bar Height Comparison (Controlled Diffs)

| value_diff | Accuracy | n |
|-----------|----------|---|
| 1 | **89.0%** | 100 |
| 2 | 100% | 100 |
| 5 | 100% | 100 |
| 10 | 100% | 100 |
| 20 | 100% | 100 |
| 40 | 100% | 100 |

**diff=1 breakdown by n_bars × grid:**

| n_bars | grid=False | grid=True |
|--------|-----------|-----------|
| 4 | 100% | 70% |
| 6 | 80% | 100% |
| 8 | 80% | 100% |
| 10 | 80% | 100% |
| 12 | 100% | 80% |

- The threshold is sharp at diff=1 (absolute difference of 1 unit on a ~60-95 scale, i.e., ~1-1.7% relative difference).
- At diff=2 (~2-3% relative), accuracy is already 100%. No gradual degradation — the cliff is between 1% and 2% relative difference.
- Number of distractor bars (4-12) has **no significant effect** — accuracy is 97.5-98.3% across all n_bars values.
- Grid lines show **no consistent directional effect** — errors at diff=1 are scattered across grid/no-grid conditions.
- **Error pattern**: All 11 errors at diff=1 follow the same failure mode — the model picks the wrong bar of the highlighted pair. Base values range from 60-91, confirming the model struggles with sub-2% relative differences regardless of absolute magnitude.

#### Line Series Comparison

Overall: **90.3%** (271/300) across gap=[1,2,5,10,20] × y_max=[auto,100,200].

The y-axis range is the critical variable — it controls how much visual space the gap occupies:

| value_gap | y=auto (easy) | y=100 (moderate) | y=200 (compressed) |
|-----------|--------------|------------------|-------------------|
| 1 | 95% | **60%** | **65%** |
| 2 | 100% | 85% | **70%** |
| 5 | 100% | 100% | 80% |
| 10 | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% |

Key findings:
- **y=auto (matplotlib default)** zooms in on the data range, making even a gap of 1 visually large — 95% accuracy. This explains why the earlier 40-instance eval showed 100% at gap≥1: all instances used auto-zoom.
- **y=100 or y=200** (fixed range) compresses the visual gap. At gap=1 with y=200, two lines at 45 and 46 are nearly indistinguishable on a 0-200 scale — accuracy drops to 60-65%.
- **Gap=2 with y=200 is the most informative cell** (70%) — a visible but ambiguous difference that the model resolves correctly only 70% of the time when the axis is compressed.
- At gap≥10, y_max has no effect — all 100%.
- **The cliff between line and bar comparison disappears once y-axis is controlled.** Bar comparison at diff=1 is 91%; line comparison at gap=1/y=auto is 95%. But at gap=1/y=200, line comparison drops to 65% — worse than bar comparison. The apparent ease of line comparison in the first eval was an artifact of auto-scaling.

#### Touching/Proximity Detection

**Overall: Local 59.6% (507/850), HF 94.3% (1267/1344)**

The large gap between Local and HF reflects different difficulty distributions. Local sweeps fine-grained near-threshold distances (0.01-0.10) that dominate the dataset and drive accuracy down. HF uses more varied scenarios with larger separations.

**Local accuracy by distance_ratio:**

| distance_ratio | Accuracy | n | Interpretation |
|---------------|----------|---|----------------|
| ≤-0.1 (overlap) | 100% | 150 | Overlapping — trivially correct |
| 0.0 (touching) | 96% | 50 | Edge contact — near-perfect |
| 0.01-0.04 | 2-8% | 200 | Near-threshold gap — model says "touching" |
| 0.05-0.07 | 20-44% | 150 | Transition zone |
| 0.08-0.10 | 64-70% | 150 | Model beginning to see the gap |
| ≥0.20 | 100% | 150 | Clearly separated — trivially correct |

**By radius:**

| Radius | Accuracy | n |
|--------|----------|---|
| 0.05 | 61.8% | 170 |
| 0.10 | **41.2%** | 170 |
| 0.15 | 59.4% | 170 |
| 0.20 | 68.2% | 170 |
| 0.25 | 67.6% | 170 |

r=0.10 (small circles, ~100px diameter) is the worst performer. The model has a pathological "always touching" bias at this scale, consistent with previous analysis showing 0% accuracy across all near-threshold distances.

**False positive bias:** In the near-threshold zone, errors are almost exclusively false positives — the model says "touching" when circles are separated. It rarely makes the opposite error.

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

Errors correlate with the gap between the largest and second-largest slice. Most errors occur when the top two slices differ by ≤5 percentage points. At 8 slices accuracy drops to 50% (more candidates at similar sizes).

This is notably harder than bar comparison, where diff≥2 is 100%. Angular estimation (pie wedges) is perceptually harder than height estimation (bars) for the same proportional difference — consistent with psychophysics research showing humans are also worse at angle vs. length judgments.

#### Cross-Representation Data Matching (`chart_data_match`)

Overall: **93.3%** (224/240) — two charts shown side-by-side, ask if the underlying data is identical.

| Chart pair | Accuracy | n |
|-----------|----------|---|
| bar_v vs bar_h | 97.5% | 80 |
| bar_v vs line | 97.5% | 80 |
| bar_v vs pie | **85.0%** | 80 |

**By match/perturbation (bar_v vs pie only):**

| Condition | Accuracy | n |
|-----------|----------|---|
| Same data (GT=Yes) | **75.0%** | 40 |
| Different: replace | 100% | 10 |
| Different: swap | 95.8% | 24 |
| Different: shift | 83.3% | 6 |

The asymmetry is striking: the model correctly detects that data is *different* (97%+) but struggles to confirm data is *the same* when one chart is a pie (75%). This is consistent with the pie slice value estimation finding (53% without % labels) — the model cannot read exact pie proportions precisely enough to verify equality. When the data is the same, it needs to confirm every value matches; one imprecise pie reading causes a false "No." When data is different, any one mismatch is sufficient to say "No," which is easier.

By n_categories: accuracy is 90-97% across all sizes (3-6), with slight degradation at n=4 (91.7%) and n=6 (90.0%) — more categories means more values to cross-check.

## Cross-Task Patterns

1. **Discrete labeled comparison is solved.** Table max (100%), bar comparison at diff≥2 (100%), line comparison at gap≥1 (100%), and cross-representation matching with non-pie charts (97.5%) are all ceiling tasks. When elements have distinct labels and measurable values, the model compares correctly.

2. **The 1% relative difference threshold for bars.** At diff=1 on a base of 60-95, the model cannot reliably distinguish heights that differ by ~1-1.7%. At diff=2 (~2-3%), it's perfect. The cliff is razor-sharp with no gradual degradation curve.

3. **No distractor effect for comparison.** Increasing bars from 4 to 12 has no impact on comparison accuracy (97.5-98.3% across all n_bars). The model successfully attends to highlighted elements and ignores irrelevant context, contrasting with counting tasks where more elements degrade performance.

4. **Pixel-level proximity detection has a hard ~12-15px floor.** Below ~12px of visible gap between circle edges, the model defaults to "touching." This is a fundamental resolution limit, not a reasoning failure.

5. **Circle size creates distinct failure regimes.** r=0.10 shows pathological "always touching" bias (41.2% overall). r=0.05 is noisy (61.8%). r=0.15-0.25 show cleaner sigmoid transitions. The model processes proximity differently depending on object scale.

6. **False positive bias in proximity.** Near the threshold, errors are exclusively "touching" when actually separated. The model has a systematic bias toward reporting contact — a reasonable real-world prior that fails for precisely separated geometric shapes.

7. **Angular comparison (pie) is harder than height comparison (bars).** Bar comparison is 100% at diff≥2; pie slice comparison is 73% overall. Estimating angles/areas is perceptually harder than comparing aligned bar heights for the same proportional difference.

9. **Pie chart imprecision propagates to cross-representation matching.** The bar-vs-pie `chart_data_match` task (85%) fails predominantly on the "same data" case (75%), where the model must confirm every pie proportion matches the bar values exactly. A single imprecise angle read causes a false "No." Detecting differences (97%+) is easy — confirming equality requires all reads to be precise.

8. **Line comparison difficulty is entirely determined by y-axis scale.** With auto-zoom, line comparison at gap=1 is 95%. With a fixed y=200 axis, the same gap=1 drops to 65% — worse than bar comparison at diff=1 (91%). The apparent ease of line comparison in naive evals is an artifact of matplotlib's default auto-scaling making small differences look large. When the axis is fixed to reflect a realistic data range, line and bar comparison have similar thresholds.

## Finetuning Implications

- **Proximity calibration is the highest-value target.** The 12-15px threshold and the r=0.10 pathological bias represent clear, systematic errors. Training pairs: (nearly-touching circles with visible gap → "No") at various scales.
- **DPO pairs for touching circles:** The sharp 0% → 100% transitions provide ideal hard negative mining. Pairs at dist=0.05 (wrong) vs dist=0.20 (right) for the same radius create high-quality preference pairs.
- **Diff=1 bar comparison is near the noise floor.** At 89%, the absolute value difference (1 pixel of bar height) is genuinely at visual resolution limits. Chain-of-thought reasoning may help more than visual finetuning.
- **Pie slice comparison needs angular reasoning training.** At 73%, this is the weakest structured comparison task. Training with explicit angular estimation ("slice A spans ~120°, slice B spans ~115°") could help.
- **Line comparison training should use fixed y-axis ranges.** Training on auto-zoomed charts gives a misleading ~95% accuracy. Real charts use fixed scales — train on y_max=100/200 with small gaps to build genuine comparison ability rather than auto-scale exploitation.
- **Scale-aware proximity training:** The r=0.10 pathological behavior suggests the model needs proximity training specifically at the small-circle regime.
- **Table max needs no improvement** — already 100% across all configurations.
