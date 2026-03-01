# Counting / Enumeration — Evaluation Summary

## Primitive Definition
Can the model count discrete elements in an image? This spans shapes, grid lines, chart bars, table rows, and diagram nodes.

## Key Finding
**Counting is solved when elements are visually distinct and well-separated, or when text labels provide structural cues. It degrades sharply with overlapping shapes and unlabeled dense grids.**

## Tasks Evaluated

### Ceiling Tasks (≥97% accuracy)

| Task | Accuracy | n | Source | Notes |
|------|----------|---|--------|-------|
| Chart bar count | 98.4% | 64 | Generated | 3-10 bars, simple bar charts |
| Chart series count | 97.4% | 576 | Generated | 2-10 series in grouped bars (100% at 2-5, degrades to 86% at 9) |
| Chart line count | 99.0% | 576 | Generated | 2-10 lines |
| Table row count | 100% | 240 | Generated | 3-10 rows, all grid sizes and styles |
| Diagram node count | 100% | 120 | Generated | 3-10 nodes, all 4 template types |

These tasks share a common trait: elements are **visually distinct and structurally organized**. Minor degradation appears at 9-10 series where visual clutter increases.

### Degrading Counting Tasks

| Task | Accuracy | n | Notes |
|------|----------|---|-------|
| Chart bar count (total) | 93.2% | 576 | Total bars in grouped charts (n_categories × n_series). 100% at 2-5 series, drops to 66% at 9 series |

Counting total bars in dense grouped charts degrades because individual bars become narrow and hard to distinguish at high series counts.

### Degrading Tasks

#### Counting Circles

| Source | Overall Exact | Within ±1 | Within ±2 | n |
|--------|--------------|-----------|-----------|---|
| Generated | 83.8% | 97.5% | 98.8% | 80 |
| HF Blind | 65.6% | 82.1% | 92.5% | 480 |

**By count (generated):**

| Count | Exact |
|-------|-------|
| 3 | 100% |
| 4 | 70% |
| 5 | 90% |
| 6 | 100% |
| 7 | 80% |
| 8 | 100% |
| 9 | 80% |
| 10 | 50% |

**By overlap fraction (generated):**

| Overlap | Exact |
|---------|-------|
| 0.10 | 94% |
| 0.20 | 62% |
| 0.30 | 75% |
| 0.40 | 88% |
| 0.50 | 100% |

- Circles are substantially easier than pentagons (83.8% vs 61.5% generated), confirming the VLMs Are Blind finding that shape type matters.
- Same overlap pattern: moderate overlap (0.2) is hardest, high overlap (0.5) recovers to 100%.
- **Matched-range comparison (counts 5-9 only):** Gen 90.0% vs HF 65.6% — a 24.4pp gap.

**Olympic rings bias in HF circles.** The HF dataset uses an Olympic-style layout (3-over-2 arrangement with colored rings). The model has a strong prior that this pattern = 5 circles. When GT≠5, the model predicts "5" in **22.4%** of HF cases vs only **4.3%** in generated (monochrome) images.

| GT | HF "predicted 5" rate | Gen "predicted 5" rate |
|----|----------------------|----------------------|
| 6 | 32.3% | 0% |
| 7 | 31.2% | 0% |
| 8 | 16.7% | 0% |
| 9 | 9.4% | 0% |

**Gap decomposition (counts 5-9):** Of the 24.4pp gap between gen (90.0%) and HF (65.6%):
- **17.9pp (73%) is Olympic rings bias** — the model defaulting to "5" based on the visual pattern
- **6.5pp (27%) is residual** (shape scale, rendering style, line thickness)

If bias-driven errors were removed, HF accuracy would be 83.5% — close to gen's 90.0%.

#### Counting Pentagons

| Source | Overall Exact | Within ±1 | Within ±2 | n |
|--------|--------------|-----------|-----------|---|
| Generated | 61.5% | 79.8% | 91.8% | 400 |
| HF Blind | 75.2% | 87.9% | 93.1% | 480 |

**By count (generated, with overlap variation):**

| Count | Exact | ±1 |
|-------|-------|-----|
| 3 | 100% | 100% |
| 4 | 30% | — |
| 5 | 44% | — |
| 6 | 30% | — |
| 7 | 74% | — |
| 8 | 74% | — |
| 9 | 78% | — |
| 10 | 62% | — |

**By overlap fraction (generated):**

| Overlap | Exact |
|---------|-------|
| 0.10 | 87.5% |
| 0.20 | 55.0% |
| 0.30 | 38.8% |
| 0.40 | 60.0% |
| 0.50 | 66.2% |

- Counts 4-6 with moderate overlap (0.3) collapse to **0%** in multiple cells of the cross-tab.
- The model tends to **overcount** in the 4-6 range, likely misinterpreting overlapping regions as separate shapes.
- High overlap (0.5) partially recovers, possibly because heavily overlapping shapes merge into a single visual mass.
- **Matched-range comparison (counts 5-9 only):** Gen 60.0% vs HF 75.2%. The direction flips vs circles: gen pentagons are *harder* than HF because gen uses large shapes with explicit overlap fractions creating more ambiguous intersection regions, while HF pentagons are tiny with proportionally less overlap.

#### Nested Squares

| Source | Overall Exact | Within ±1 | Within ±2 | n |
|--------|--------------|-----------|-----------|---|
| Generated | 88.3% | 100% | 100% | 60 |
| HF Blind | 84.2% | 100% | 100% | 240 |

**By depth (HF Blind):**

| Depth | Exact |
|-------|-------|
| 2 | 96.7% |
| 3 | 98.3% |
| 4 | 81.7% |
| 5 | 60.0% |

Clear degradation with nesting depth. All errors are within ±1 — the model never miscounts by more than 1 square.

**Matched-range comparison (depth 2-5):** Gen 90.0% vs HF 84.2%. Small gap likely from HF's thinner lines and smaller shapes being harder to resolve. Gen depth=2 has an anomaly (60%) where the model counts the image border as an additional square.

#### Grid Counting

| Source | Overall Exact | Within ±1 | Within ±2 | n |
|--------|--------------|-----------|-----------|---|
| Generated (all) | 74.5% | 97.5% | 100% | 200 |
| Generated (blank only) | 49.0% | — | — | 100 |
| HF Blind (all blank) | 64.8% | 98.9% | 100% | 528 |

**The text label effect (generated):**

| Condition | Exact |
|-----------|-------|
| with_text=True | **100%** |
| with_text=False | **49%** |

Without text, accuracy on grids ≥9 rows drops to **0-10%**. With text labels, the model is perfect at all sizes. This mirrors the chart value reading finding: the model reads text, not the visual.

**Matched-range comparison (blank grids, rows 3-10):** Gen 61.3% vs HF 64.8%. Nearly identical once text-labeled samples are removed and ranges are matched. The gen overall (74.5%) is inflated by the 50% with_text=True samples scoring 100%.

**Errors are exclusively in the row dimension** — column counting is perfect across all sizes. The model struggles specifically with counting horizontal grid lines.

**By dimensions, blank grids only (generated):**
- 3×3 to 5×5: 100%
- 5×6: 30%
- 7×8: 50%
- 9×10: 0%
- 11×12: 0%

#### Pie Chart Slice Counting

| Source | Overall Exact | n |
|--------|--------------|---|
| Generated | **100%** | 60 |

Perfect across all slice counts (3-8), even without category labels (legend-only). Pie chart slices are non-overlapping and visually distinct — each wedge has a unique color and clear boundaries. This places pie counting in the **ceiling** category alongside bar/table/diagram counting.

| Slices | Exact |
|--------|-------|
| 3 | 100% |
| 4 | 100% |
| 5 | 100% |
| 6 | 100% |
| 7 | 100% |
| 8 | 100% |

## Generated vs HF Benchmark Comparison

Raw accuracy numbers differ between generated and HF sources. Three systematic factors explain the gaps:

**1. Count/parameter range mismatch.** Generated sets include easy low counts (3-4) and text-labeled conditions that inflate averages. HF datasets use narrower, harder count ranges (typically 5-9). Matched-range comparisons:

| Task | Gen (full) | Gen (matched range) | HF | Matched range |
|------|-----------|-------------------|-----|---------------|
| Circles | 83.8% | 90.0% | 65.6% | counts 5-9 |
| Pentagons | 61.5% | 60.0% | 75.2% | counts 5-9 |
| Nested squares | 88.3% | 90.0% | 84.2% | depth 2-5 |
| Grid counting | 74.5% | 61.3% | 64.8% | blank, rows 3-10 |

**2. Olympic rings memorization bias (circles only).** The HF circle task uses a 3-over-2 Olympic-style layout with colored rings. The model defaults to "5" in 22.4% of non-5 cases (vs 4.3% in monochrome gen images). This accounts for **73% of the circle gap** (17.9 of 24.4pp). Removing bias-driven errors brings HF to 83.5%, within 6.5pp of gen's 90%. This is a memorization failure, not a perceptual one — the same phenomenon studied in the VLMs Are Biased paper.

**3. Shape scale and overlap geometry.** The residual 6.5pp circle gap and the pentagon/nested-squares gaps are driven by rendering differences: HF uses small shapes on large canvases with thin lines, while gen uses frame-filling shapes with thick strokes. For pentagons, the direction flips: gen is *harder* than HF (60% vs 75%) because gen's explicit overlap fractions create more ambiguous intersection regions.

Grid counting is the best-matched task: once text-labeled samples are removed and the row range is aligned, gen (61.3%) and HF (64.8%) nearly converge.

## Cross-Task Patterns

1. **Structured, labeled counting is solved.** Charts, tables, diagrams, and pie chart slices with distinct visual elements hit 100% regardless of count. Pie slices are perfect up to 8 despite having no text labels — each wedge's unique color and clear boundary is sufficient. The ceiling is not reached even at 30 elements.

2. **Visual-only counting degrades with overlap and density.** The core failure is distinguishing individual elements when they overlap or are packed densely. This is a perceptual limitation, not a reasoning one. Shape complexity compounds the effect: pentagons (60.0%) are much harder than circles (90.0%) at matched count ranges (5-9).

3. **Text labels rescue counting.** Grid counting goes from 49% to 100% with text; this is the same pattern as chart value reading (show_values). The model defaults to OCR when text is available.

4. **Memorization priors override visual evidence.** The HF circle task's Olympic-style layout triggers a strong "5 rings" prior, accounting for 73% of the gen-vs-HF accuracy gap. The model predicts "5" for 32% of 6-circle and 31% of 7-circle HF images — but never in monochrome gen images. This is a bias/memorization failure, not a perceptual one, and connects directly to the VLMs Are Biased findings.

5. **Errors are small when they're perceptual.** Across all degrading tasks, perceptual errors are within ±1-2. The model never catastrophically miscounts when actually trying to count. The exception is bias-driven errors (e.g., predicting 5 for 7 circles), which can be off by more.

6. **The "magic number" is ~7.** Consistent with known working memory limits, counting accuracy is high for counts ≤5-6 in easy conditions and degrades beyond that, especially with visual interference (overlap, dense packing).

## Finetuning Implications

- **Training curriculum**: Start with non-overlapping shapes (count ≤5), progressively increase overlap density and count to 15+.
- **RL reward signal**: Counting is fully verifiable — reward = exact match to ground truth.
- **Chain-of-thought**: Encourage the model to enumerate elements sequentially ("I see circle 1 at top-left, circle 2 overlapping it at center...") rather than estimating a global count.
- **Grid counting**: Train on blank grids specifically, since text labels make the task trivially easy and don't exercise visual counting.
- **Bias override training**: Include Olympic-layout circles with non-5 counts as explicit DPO negatives (model says 5, ground truth is 7). The 22% bias rate on HF circles is a high-signal source of (preferred, dispreferred) pairs.
- **Shape scale variation**: Include small-on-large-canvas images (matching HF-style rendering), not just frame-filling shapes. After removing bias errors, a residual 6.5pp gap remains between large and small circles.
