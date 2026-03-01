# Prior Bias Override — Evaluation Summary

## Primitive Definition
Can the model report what it actually sees, overriding memorized defaults? This tests whether the model defaults to canonical knowledge (8×8 chess, standard dice patterns, illusion-expected percepts) rather than counting or measuring the actual visual content.

## Key Finding
**The model's memorized priors completely override visual evidence. Board game dimension counting has 100% bias alignment — the model always outputs the canonical dimension (8 for chess, 19 for Go) regardless of actual size, yielding 0%/100% accuracy in a perfectly binary pattern. Patterned grid anomaly detection is at 15.5% overall with 0% on add-anomalies, and optical illusions are near-chance (57%) across all six illusion types.**

## Tasks Evaluated

### Ceiling Tasks (100% exact match)

None. Every task in this primitive shows significant bias-induced errors. This is the only primitive with no ceiling tasks — prior bias is a universal failure mode.

### Degrading Tasks

---

#### 1. Board Game Dimension Counting

**Overall: 60.0%** (240/400)

| Condition | Accuracy | n | Bias Alignment |
|-----------|----------|---|----------------|
| Canonical dims (8×8, 19×19) | 100% | 80 | 100% |
| Non-canonical dims | 50.0% | 320 | 100% |
| **Overall** | **60.0%** | **400** | **100%** |

**Bias alignment is 100%.** The model answers the canonical dimension in every single response (400/400). It is correct only when the actual dimension happens to coincide with the canonical one.

**Per-config breakdown (18 evals each, zero variance):**

| Board | Dim asked | GT | Model | Correct? |
|-------|-----------|-----|-------|----------|
| Chess 7×8 | rows | 7 | **8** | 0% |
| Chess 7×8 | cols | 8 | **8** | 100% |
| Chess 9×8 | rows | 9 | **8** | 0% |
| Chess 9×8 | cols | 8 | **8** | 100% |
| Chess 8×7 | rows | 8 | **8** | 100% |
| Chess 8×7 | cols | 7 | **8** | 0% |
| Chess 8×9 | rows | 8 | **8** | 100% |
| Chess 8×9 | cols | 9 | **8** | 0% |
| Chess 8×8 | rows | 8 | **8** | 100% |
| Chess 8×8 | cols | 8 | **8** | 100% |
| Go 18×19 | rows | 18 | **19** | 0% |
| Go 18×19 | cols | 19 | **19** | 100% |
| Go 20×19 | rows | 20 | **19** | 0% |
| Go 20×19 | cols | 19 | **19** | 100% |
| Go 19×18 | rows | 19 | **19** | 100% |
| Go 19×18 | cols | 18 | **19** | 0% |
| Go 19×20 | rows | 19 | **19** | 100% |
| Go 19×20 | cols | 20 | **19** | 0% |
| Go 19×19 | rows | 19 | **19** | 100% |
| Go 19×19 | cols | 19 | **19** | 100% |

Every config is either 0% or 100% with no variance across 18 evaluations per config. The model does not look at the board — it recalls "chess = 8×8" and "go = 19×19" and outputs accordingly. The ±1 dimension modification is completely invisible to it.

**Why 60% overall?** Of the 10 configs per game, 3 have both dimensions matching canonical (canonical + the two where the non-asked dimension is modified). This gives 6/10 = 60% by pure coincidence, not perception.

---

#### 2. Patterned Grid Anomaly Detection

**Overall: 15.5%** (39/252)

**By anomaly type:**

| Anomaly | Accuracy | n |
|---------|----------|---|
| Add (+1 shape) | **0.0%** | 126 |
| Remove (-1 shape) | **31.0%** | 126 |

**By grid_size × anomaly:**

| Grid | Add | Remove |
|------|-----|--------|
| 6×6 | 0% | 54.8% |
| 8×8 | 0% | 26.2% |
| 10×10 | 0% | 11.9% |

**The model never detects add-anomalies (0/126).** When an extra shape is added to a cell, the model consistently reports a count higher than the ground truth — it sees more shapes than the anomaly introduced, suggesting it counts the pattern-expected shapes and adds the visible extra without distinguishing the anomaly from the pattern.

**Remove-anomaly accuracy degrades sharply with grid size.** At 6×6, the model detects 55% of removed shapes. At 10×10, only 12%. Larger grids reinforce the pattern more strongly, making deviations harder to detect — consistent with the hypothesis that surrounding context biases the model toward the expected count.

**By grid_type:**

| Type | Accuracy |
|------|----------|
| Dice | 13.5% |
| Tally | 17.5% |

Tally marks are slightly easier to count accurately than dice dots, possibly because tally marks have more distinct spatial arrangements.

**Error patterns — model answers cluster around canonical±1:**

For add anomaly (canonical count + 1 shapes present):
- When canonical=2: model answers 3 in 89% of errors (counts the actual shapes but misses that this is the anomaly)
- When canonical=3: model answers 4 in 84% of errors
- When canonical=4: model answers 4-6

For remove anomaly (canonical count - 1 shapes present):
- When canonical=2: model correctly answers 1 in 72% (remove is more detectable at low counts)
- When canonical=3: model answers 2 in 83% of errors (reports canonical-1, which is actually correct counting)
- When canonical=4: model answers 3 in 75%

The model appears to count shapes in the anomalous cell reasonably well but struggles to determine the correct ground truth when the task requires comparing against the pattern.

**HF VLMs-are-Biased comparison:**

| Source | Dice | Tally | Overall |
|--------|------|-------|---------|
| Generated | 13.5% | 17.5% | 15.5% |
| HF | 14.9% | 31.5% | 23.2% |

Generated results are slightly lower than HF, possibly due to denser grids and more varied anomaly positions in our generator.

---

#### 3. Optical Illusions (HF VLMs-are-Biased)

**Overall: 57.2%** (453/792) — near binary-choice chance (50%).

| Illusion | Accuracy | n |
|----------|----------|---|
| Zöllner | 72.9% | 144 |
| Müller-Lyer | 56.9% | 144 |
| Vertical-Horizontal | 56.9% | 72 |
| Poggendorff | 54.2% | 144 |
| Ponzo | 52.1% | 144 |
| Ebbinghaus | 50.0% | 144 |

**Bias alignment: 42.8%** — the model answers the illusion-expected (incorrect) percept 43% of the time, which combined with 57% accuracy means it's roughly splitting between the biased answer and the correct answer.

**Ebbinghaus is at exact chance (50.0%)** — the model cannot determine whether two circles are the same size when surrounded by different-sized circles. The illusion completely overrides size comparison.

**Zöllner is the easiest (72.9%)** — determining whether lines are parallel despite diagonal hatch marks is somewhat easier, possibly because parallelism is a more robust visual feature than relative size.

---

## Extended Thinking Experiment

Re-ran both board games and patterned grid with extended thinking (`--thinking --thinking-budget 2048`) to test whether step-by-step reasoning helps override memorized priors.

| Task | Baseline | Thinking | Delta |
|------|----------|----------|-------|
| Patterned grid | 15.5% | 17.1% | +1.6pp |
| Board games | 60.0% | 59.5% | -0.5pp |

**Extended thinking makes no difference.** Add-anomalies remain at 0%, canonical dimensions remain at 100%, and off-by-one board dimensions remain at 50%. The model cannot think its way out of a perception failure — if the visual representation doesn't encode the deviation from the memorized default, no amount of reasoning will recover it. This confirms the bias override failure is **perceptual, not reasoning-based**.

## Cross-Task Patterns

1. **Memorized priors completely dominate visual evidence for board games.** 100% bias alignment with zero variance across 400 evaluations means the model doesn't engage its vision system at all for this task — it pattern-matches "chess board" → 8×8 and "go board" → 19×19 without counting.

2. **Grid context reinforces bias proportionally to grid size.** Patterned grid accuracy drops from 55% at 6×6 to 12% at 10×10 (remove anomaly). More cells showing the canonical pattern create stronger contextual bias, making the single anomalous cell harder to detect. This is analogous to how more distractor paths hurt path-following.

3. **Add vs remove asymmetry: additions are invisible, removals are partially detectable.** Add-anomalies are 0% while remove-anomalies are 31%. Adding a shape to a cell creates a count that is "one more than expected" — but the model often reports the actual count rather than the expected one, suggesting it partially perceives the shapes but fails the comparison task. Removing a shape creates an obvious visual gap at low canonical counts (1 shape where 2 are expected).

4. **Optical illusions affect the model similarly to humans.** The near-chance accuracy across 5 of 6 illusion types suggests the model's visual representations encode the same biased percepts that humans experience. This is consistent with training on human-generated image descriptions.

5. **The 60% board game accuracy is a trap metric.** It looks moderately good but conceals 100% bias alignment — the model is right only when the answer happens to match its prior. This makes board games an ideal DPO data source: every non-canonical instance generates a clear (correct, biased) preference pair.

## Finetuning Implications

- **Board games are the highest-quality DPO data source in the entire eval.** 100% bias alignment with zero variance means every non-canonical instance (320 of 400) produces a clean preference pair where the correct answer is always the non-canonical dimension and the biased answer is always the canonical one. No noise, no ambiguity.
- **Patterned grid training should focus on add-anomalies.** 0% accuracy on add means every instance is a training opportunity. Remove-anomalies at small grid sizes (55% at 6×6) are partially solved and less valuable.
- **Grid size is a natural curriculum axis.** Start training at small grids (6×6, where remove-anomalies are 55% correct) and progressively increase to 10×10 (12%), forcing the model to resist stronger contextual bias.
- **Optical illusion training requires careful framing.** Unlike board games and grids where the correct answer is objectively verifiable, optical illusions involve subjective size/angle comparisons where the "correct" answer is the physically measured value. Training the model to override illusions means training it to distrust its visual representations — which may conflict with other visual tasks.
- **Chain-of-thought for board games:** Encourage explicit counting: "I see rows 1, 2, 3, 4, 5, 6, 7 — that's 7 rows" rather than pattern-matching "this is a chess board, chess boards have 8 rows." The model has the counting ability (it counts other things correctly) but never applies it here because the prior short-circuits reasoning.
