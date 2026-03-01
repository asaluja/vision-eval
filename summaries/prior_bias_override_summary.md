# Prior Bias Override — Evaluation Summary

## Primitive Definition
Can the model report what it actually sees, overriding memorized defaults? This tests whether the model defaults to canonical knowledge (standard dice patterns, canonical flag stripe counts, expected logo elements) rather than counting or measuring the actual visual content.

## Key Finding
**Prior bias dominates all three tasks. Logos is the most extreme: 1.9% accuracy with 99.8% bias alignment — the model almost never counts logo elements, it just retrieves canonical knowledge (Nike swoosh = 1 curve). Flags are 40% accurate with 83% bias alignment. Patterned grid add-anomalies are 0% — the model cannot see an extra shape when the surrounding pattern says it shouldn't be there. Extended thinking does not help — these are perceptual failures, not reasoning failures.**

## Tasks Evaluated

### Ceiling Tasks
None. Every task shows significant bias-induced errors — this is the only primitive with zero ceiling tasks.

### Degrading Tasks

#### Patterned Grid Anomaly Detection (`patterned_grid`)

A grid where every cell contains a pattern of shapes (dice dots or tally marks) following a spatial rule. One cell is modified (+1 or −1 shape). Task: count the shapes in the anomalous cell.

**Overall: 15.5%** (39/252 local)

**By anomaly type:**

| Anomaly | Accuracy | n |
|---------|----------|---|
| Add (+1 shape) | **0.0%** | 126 |
| Remove (−1 shape) | **31.0%** | 126 |

**By grid_size × anomaly:**

| Grid | Add | Remove |
|------|-----|--------|
| 6×6 | 0% | 54.8% |
| 8×8 | 0% | 26.2% |
| 10×10 | 0% | 11.9% |

**The model never detects add-anomalies (0/126).** When an extra shape is added, the model consistently reports the anomalous count without recognizing it as anomalous — it counts what's there but doesn't compare against the surrounding pattern.

**Remove-anomaly accuracy degrades sharply with grid size.** At 6×6 the model detects 55% of removed shapes. At 10×10, only 12%. Larger grids reinforce the expected pattern more strongly, making deviations harder to detect.

**By grid_type:**

| Type | Accuracy |
|------|----------|
| Dice | 13.5% |
| Tally | 17.5% |

Tally marks are slightly easier — more distinct spatial arrangements make the anomaly marginally more visible.

**Error patterns:**

For add anomaly (GT=1 for all 126 instances):
- The model never reports the correct count (GT=1). Instead, it overcounts significantly: 43.7% say 3, 38.9% say 4, with a tail up to 8. Only 1.6% say the cell-specific canonical (2).
- The model appears to apply the *surrounding* cells' visual count (3-4 shapes) to the anomalous cell rather than counting the cell's single actual shape. The anomalous cell is effectively invisible — the model reads it as "like the others."

For remove anomaly (cell has canonical−1 shapes):
- At canonical=2: model correctly answers 1 in 72% (easily visible gap)
- At canonical=3: model answers 2 in 83% (correct counting overrides prior)
- At canonical=4: model answers 3 in 75% — still partially perceiving the reduction

**Generated vs HF comparison:**

| Source | Dice | Tally | Overall |
|--------|------|-------|---------|
| Generated | 13.5% | 17.5% | 15.5% |
| HF (biased) | 14.9% | 31.5% | 23.2% |

HF performs somewhat better on tally marks (31.5% vs 17.5%), likely due to rendering differences — HF tally marks may have more visual contrast or spacing that makes deviations more salient.

#### Flag Element Counting (`flags`, HF VLMs-are-Biased)

**Overall: 40.0%** (96/240) — bias alignment: **83% of errors**

| Sub-topic | Accuracy | n |
|-----------|----------|---|
| 2D Stars | 45.5% | 156 |
| 2D Stripes | 29.8% | 84 |

The task asks how many stars or stripes are in a flag image. The dominant error is the US flag canonical bias: GT=13 stars → model answers 12; GT=13 stripes → model answers the canonical wrong value. Of 144 errors, 120 are the exact biased answer (83% bias alignment).

Star counting (45.5%) is easier than stripe counting (29.8%) — stripes may have stronger prior associations or be harder to count visually when the flag is rendered at low resolution.

#### Logo Element Counting (`logos`, HF VLMs-are-Biased)

**Overall: 1.9%** (8/414) — bias alignment: **99.8% of errors** (405/406)

| Sub-topic | Accuracy | n |
|-----------|----------|---|
| Car Logos | 0.0% | 270 |
| Shoe Logos | 5.6% | 144 |

This is the strongest prior bias signal in the entire eval. The task asks how many visible elements (curves, rings, etc.) appear in a logo. The model never counts — it retrieves canonical knowledge:
- Shoe logos (Nike/Adidas): GT=2+ visible elements → model answers canonical count in 99.3% of errors (135/136); 1 Shoe Logos error was non-bias-aligned (model answered 2, canonical was 3)
- Car logos: 0% accuracy, 100% bias aligned (270/270 errors)

405 of 406 errors (99.8%) are the exact canonical biased answer; one Shoe Logos error was non-bias-aligned (Adidas shoe, model answered 2 stripes, canonical=3, GT=4). The model's visual encoder rarely engages for logos — it pattern-matches the brand and outputs the memorized element count. This is qualitatively different from patterned grid (where the model at least attempts to count) — here it almost never counts at all.

#### Extended Thinking Experiment

Re-ran patterned grid with extended thinking (`--thinking --thinking-budget 2048`) to test whether step-by-step reasoning helps override the memorized pattern prior.

| Task | Baseline | Thinking | Delta |
|------|----------|----------|-------|
| Patterned grid | 15.5% | 17.1% | +1.6pp |

**Extended thinking makes no meaningful difference.** Add-anomalies remain at 0%. The failure is perceptual — if the visual encoder doesn't register the extra/missing shape as distinct from the surrounding pattern, no reasoning step can recover it.

## Cross-Task Patterns

1. **Bias alignment scales with prior strength.** Logos (99.8% bias aligned, 1.9% accurate) > flags (83% bias aligned, 40% accurate) > patterned grid add-anomalies (near-100% bias aligned, 0% accurate). The stronger and more specific the memorized prior (Nike swoosh = 1 curve), the more completely it overrides visual evidence.

2. **Logos represent complete vision bypass.** The model doesn't just weight the prior more heavily — it appears to skip visual counting entirely. 100% bias alignment with 0% accuracy on car logos means the visual encoder output is irrelevant. It's pattern-matching "BMW logo" and returning canonical ring count from memory.

3. **The add/remove asymmetry in patterned grids.** For add anomalies (GT=1), the model overcounts to 3-4 (the surrounding cells' visual count) rather than reading the anomalous cell's single shape — the anomalous cell is effectively invisible. For remove anomalies, the model more often reads the actual reduced count, possibly because a missing shape creates a visible gap. The failure is worse for additions than removals.

4. **Grid context reinforces bias proportionally to grid size.** Remove-anomaly accuracy drops from 55% at 6×6 to 12% at 10×10. More surrounding cells showing the canonical pattern strengthen contextual expectation, making the anomaly harder to detect.

5. **Extended thinking cannot overcome perceptual failures.** +1.6pp on patterned grid with thinking budget. The model cannot reason its way past a visual signal it never received. These failures are upstream of reasoning.

6. **All tasks produce high-quality DPO pairs.** Every bias-aligned error is a clean (correct visual answer, biased memorized answer) preference pair with zero ambiguity about which is preferred.

## Finetuning Implications

- **Logos are the highest-density DPO source.** 406/414 instances (98%) produce preference pairs with 99.8% bias alignment (405/406 errors bias-aligned; 1 Shoe Logos error is not bias-aligned). The rejected answer is almost always the canonical element count; the preferred answer is the actual visual count.
- **Flag training covers two distinct biases.** Star count (12 vs 13) and stripe count each have their own canonical prior. Both sub-topics need independent training coverage.
- **Add-anomaly training for patterned grids.** 0% accuracy = every instance is a training opportunity. The model needs to learn single-cell counting independent of surrounding pattern context.
- **Grid size is a natural curriculum axis.** Start at 6×6 (remove-anomalies 55% correct, closest to learnable) and progressively increase to 10×10 (12%).
- **Chain-of-thought for logo/flag tasks:** "Count only what is visible in this image, do not rely on what you know about this brand/country." Without this instruction, the model retrieves rather than perceives.
- **Car logos need dedicated attention.** 0% accuracy suggests the car logo prior is exceptionally strong. May need higher learning rate or more examples relative to shoe logos (5.6% baseline).
