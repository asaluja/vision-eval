# Color Discrimination — Evaluation Summary

## Primitive Definition
Can the model distinguish visually similar colors, match legend entries to data series by shade, and detect subtle shade differences in a uniform field?

## Key Finding
**Color shade detection in grids follows a clean sigmoid: 100% at ΔL≥16, 88% at ΔL≈10, 52% at ΔL≈7, and 18% at ΔL≈5. Legend-to-bar color matching degrades to 58% with 5 same-family bars, where roughly half the errors are color confusion (reading the wrong bar) and half are value misreading. Color family matters: oranges are most discriminable, greens least.**

## Tasks Evaluated

### Ceiling Tasks (100% exact match)

| Task | n | Source | Notes |
|------|---|--------|-------|
| Color grid (easy, ΔL≈30-40) | 50 | Generated | Darkest vs lightest shade, 4×4 and 6×6 grids, all 5 families |
| Color grid (hard, ΔL≈16-23) | 50 | Generated | Dark vs medium shade, 4×4 and 6×6 grids, all 5 families |
| Bar chart (easy, distinct colors) | 36 | Generated | 3-5 bars with maximally distinct colors (blue/red/green/orange/purple) |

When shade differences are large (ΔL≥16 in HSL space), the model perfectly identifies the odd cell in a grid regardless of grid size or color family. Similarly, matching a color name to a bar is trivial when bars use maximally distinct hues.

### Degrading Tasks

#### Color Grid — Odd Shade Detection

**Accuracy by lightness delta (ΔL):**

| Difficulty | ΔL (HSL) | 4×4 | 6×6 | Overall |
|-----------|----------|-----|-----|---------|
| easy | ~30-40 | 100% | 100% | **100%** |
| hard | ~16-23 | 100% | 100% | **100%** |
| very_hard | ~10 | 88% | 88% | **88%** |
| near_threshold | ~7 | 56% | 48% | **52%** |
| extreme | ~5 | 24% | 12% | **18%** |

The degradation follows a clean sigmoid curve from 100% to 18% as ΔL drops from 16 to 5.

**Grid size effect:** Minimal at easy/hard (both 100%). At near_threshold and extreme, 4×4 slightly outperforms 6×6 (56% vs 48%, 24% vs 12%), likely because smaller grids produce larger cells that are easier to compare visually.

**Accuracy by color family:**

| Difficulty | Blues | Reds | Greens | Purples | Oranges |
|-----------|-------|------|--------|---------|---------|
| easy | 100% | 100% | 100% | 100% | 100% |
| hard | 100% | 100% | 100% | 100% | 100% |
| very_hard | 90% | 80% | 70% | 100% | 100% |
| near_threshold | 80% | 50% | 10% | 50% | 70% |
| extreme | 10% | 0% | 20% | 10% | 50% |

Color families have dramatically different discriminability:
- **Oranges** are most discriminable (50% even at extreme ΔL≈5), likely because the orange hue range spans warm yellow to deep brown, providing additional hue cues beyond pure lightness.
- **Greens** are least discriminable (10% at near_threshold), consistent with human color perception — green is the widest band in the visible spectrum, making lightness-only differences harder to detect.
- **Reds** are hardest at extreme (0%), possibly because the red family straddles the hue boundary near 0°/360°, compressing perceptual distance.
- **Blues** and **purples** show intermediate performance, tracking roughly with their saturation ranges.

**Error pattern:** At extreme difficulty, the model systematically examines each cell row by row but cannot identify the odd cell. It picks a cell that "looks slightly different" — but it's guessing. The responses show careful reasoning structure applied to perceptually indistinguishable input.

#### Bar Chart — Color Legend Matching

**Accuracy by difficulty × number of bars:**

| Difficulty | n=3 | n=4 | n=5 | Overall |
|-----------|-----|-----|-----|---------|
| easy (distinct colors) | 100% | 100% | 90% | **97%** |
| hard (same-family shades) | 90% | 71% | 58% | **73%** |

The hard bar chart task degrades monotonically with n_bars. At n=5 with same-family shades, accuracy is 58% — barely above chance for a task with 5 options.

**Hard bar accuracy by color family:**

| Family | Accuracy | n |
|--------|----------|---|
| Reds | 78% | 32 |
| Oranges | 77% | 30 |
| Greens | 76% | 29 |
| Blues | 69% | 29 |
| Purples | 67% | 33 |

The family ranking for bars differs from grids — purples are hardest for bars (67%) while greens were hardest for grids. This suggests the legend-matching task involves different perceptual demands than the odd-one-out task.

**Error analysis (41 hard bar errors):**
- **Color confusion (49%):** The model correctly reads a bar's value but reads the **wrong bar** — it maps the queried color name (e.g., "dark purple") to a different bar with a similar shade. These errors read a value that exactly matches another bar in the chart.
- **Value misreading (51%):** The model identifies the correct bar but misreads its height. Mean absolute error: 25.7 units on a 15-90 scale.

The roughly equal split between color confusion and value misreading suggests two independent failure modes compound: the model must both (1) match a color name to the correct bar among similar shades, and (2) accurately read that bar's value. Both tasks have ~75-85% individual success rates, and their errors are approximately independent.

**Queried color type matters:**
- "Dark" shades account for 27/41 errors (66% of errors but ~33% of queries) — dark shades are harder to distinguish in legends because they appear more similar on screen.
- "Light" shades have only 1 error — the lightest shade in each family is visually distinctive.

## Cross-Task Patterns

1. **Lightness delta is the primary difficulty axis for shade detection.** The grid task provides a clean psychometric curve: 100% at ΔL≥16, sigmoid degradation through ΔL=10 (88%), ΔL=7 (52%), and ΔL=5 (18%). This is a perceptual resolution limit, not a reasoning failure.

2. **Color family creates a 5× accuracy range at threshold difficulties.** At near_threshold (ΔL≈7), accuracy ranges from 10% (greens) to 80% (blues). This means the ΔL threshold depends on which hue family is being tested — a single ΔL number is insufficient to characterize the model's color discrimination.

3. **Grid size has minimal effect compared to shade distance.** 4×4 vs 6×6 shows only ~5-10% difference at threshold difficulties. The bottleneck is perceiving the shade difference, not the cell size or search space.

4. **Legend-to-bar matching compounds two failure modes.** Color confusion (wrong bar) and value misreading (wrong value) contribute roughly equally. With n=5 same-family bars, both tasks are individually unreliable, and their errors multiply: ~75% per-task accuracy yields ~58% joint accuracy (0.75 × 0.75 ≈ 0.56).

5. **Dark shades are disproportionately confusable.** In both grids and bar charts, darker shades within a family are harder to distinguish. This is consistent with Weber's law — the same absolute lightness difference (ΔL=5) is a larger relative change at L=80 (light) than at L=40 (dark).

6. **The model's reasoning is intact even when perception fails.** Grid extreme errors show systematic row-by-row examination — the model uses the correct strategy but simply cannot perceive the shade difference. This distinguishes color discrimination from tasks like counting where both perception and reasoning may fail.

## Finetuning Implications

- **Color grid detection at ΔL=5-10 is the primary finetuning target.** The clean sigmoid provides natural curriculum design: start at ΔL=15 (already perfect), progressively decrease to ΔL=5.
- **Per-family calibration is needed.** Training should include examples from all 5 color families at threshold difficulties, with potentially family-specific difficulty schedules (oranges can start harder, greens need more training at easier levels).
- **Bar chart color matching needs dual training:** (1) Legend-to-bar color mapping with same-family shades, and (2) value reading accuracy under color uncertainty. These are separable skills that both need improvement.
- **DPO pairs:** Grid images at near_threshold (52%) and extreme (18%) provide high-quality preference pairs — the model is uncertain and frequently wrong, making both correct and incorrect responses readily available for contrastive training.
- **Dark shade emphasis:** Training data should oversample "dark" shade queries since these account for disproportionate errors in both tasks.
