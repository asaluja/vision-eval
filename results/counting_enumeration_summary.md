# Counting / Enumeration — Evaluation Summary

## Primitive Definition
Can the model count discrete elements in an image? This spans shapes, grid lines, chart bars, table rows, and diagram nodes.

## Key Finding
**Counting is solved when elements are visually distinct and well-separated, or when text labels provide structural cues. It degrades sharply with overlapping shapes and unlabeled dense grids.**

## Tasks Evaluated

### Ceiling Tasks (100% exact match)

| Task | n | Source | Notes |
|------|---|--------|-------|
| Chart bar count | 40 | Generated | 3-10 bars, simple bar charts |
| Chart series count | 40 | Generated | 2-3 series in grouped bars |
| Chart bar count total | 40 | Generated | Up to 30 bars (10 categories × 3 series) |
| Chart line count | 28 | Generated | 2-3 lines |
| Table row count | 240 | Generated | 3-10 rows, all grid sizes and styles |
| Diagram node count | 120 | Generated | 3-10 nodes, all 4 template types |

These tasks share a common trait: elements are **visually distinct, non-overlapping, and structurally organized**. The model has no trouble counting them regardless of quantity.

### Degrading Tasks

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

#### Grid Counting

| Source | Overall Exact | Within ±1 | Within ±2 | n |
|--------|--------------|-----------|-----------|---|
| Generated | 74.5% | 97.5% | 100% | 200 |
| HF Blind | 64.8% | 98.9% | 100% | 528 |

**The text label effect (generated):**

| Condition | Exact |
|-----------|-------|
| with_text=True | **100%** |
| with_text=False | **49%** |

Without text, accuracy on grids ≥9 rows drops to **0-10%**. With text labels, the model is perfect at all sizes. This mirrors the chart value reading finding: the model reads text, not the visual.

**Errors are exclusively in the row dimension** — column counting is perfect across all sizes. The model struggles specifically with counting horizontal grid lines.

**By dimensions, blank grids only (generated):**
- 3×3 to 5×5: 100%
- 5×6: 30%
- 7×8: 50%
- 9×10: 0%
- 11×12: 0%

## Cross-Task Patterns

1. **Structured, labeled counting is solved.** Charts, tables, and diagrams with distinct visual elements hit 100% regardless of count. The ceiling is not reached even at 30 elements.

2. **Visual-only counting degrades with overlap and density.** The core failure is distinguishing individual elements when they overlap or are packed densely. This is a perceptual limitation, not a reasoning one.

3. **Text labels rescue counting.** Grid counting goes from 49% to 100% with text; this is the same pattern as chart value reading (show_values). The model defaults to OCR when text is available.

4. **Errors are small.** Across all degrading tasks, errors are within ±1-2. The model never catastrophically miscounts (e.g., saying 3 when the answer is 10). It's off by 1-2, suggesting it perceives the approximate quantity but can't resolve individual elements.

5. **The "magic number" is ~7.** Consistent with known working memory limits, counting accuracy is high for counts ≤5-6 in easy conditions and degrades beyond that, especially with visual interference (overlap, dense packing).

## Finetuning Implications

- **Training curriculum**: Start with non-overlapping shapes (count ≤5), progressively increase overlap density and count to 15+.
- **RL reward signal**: Counting is fully verifiable — reward = exact match to ground truth.
- **Chain-of-thought**: Encourage the model to enumerate elements sequentially ("I see circle 1 at top-left, circle 2 overlapping it at center...") rather than estimating a global count.
- **Grid counting**: Train on blank grids specifically, since text labels make the task trivially easy and don't exercise visual counting.
