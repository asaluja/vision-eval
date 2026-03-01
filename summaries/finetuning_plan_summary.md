# Finetuning Plan

## Failure Taxonomy

The evaluation reveals three mechanistically distinct failure regimes, each requiring a different training lever:

1. **OCR-as-crutch** — the model reads text labels instead of perceiving visual content (value-label conflict: 0% accuracy, 100% text-reliant; grid counting: 49% without text → 100% with text). This silently affects every chart/table/document task: when labels are correct, OCR-reliance produces correct answers, masking the underlying blindness.
2. **Perceptual resolution limits** — smooth degradation along psychometric curves as visual complexity increases (path tracing at 52-56% with distractors, intersection detection at 18% for 5-point lines, proximity threshold at distance_ratio ≈ 0.05–0.10, color discrimination collapsing at ΔL≈7, heatmap value reading at 56%, pie angular estimation at 73%). These are all clearly in-distribution for practical VLM tasks.
3. **Memorized priors override vision** — canonical knowledge short-circuits perception (logos: 1.9% accuracy with 99.8% bias alignment; flags: 40% with 83% bias alignment). However, logos and flags are largely out-of-distribution for typical VLM deployments and are deprioritized for training — they serve as evaluation benchmarks for measuring bias override capability.

**Extended thinking experiments sharpen this taxonomy.** Thinking with budget=8000 only helps annotation conflicts (+15pp, 75%→90%) — the one task where the failure is reasoning, not perception. Value labels (0%→0%), pie comparison (+1.7pp), heatmap (+0.4pp), and board games (-0.5pp) are all unchanged, confirming these are perceptual limits that reasoning cannot overcome.

## Three-Stage Training Pipeline

**Stage 1 — SFT: Visual Grounding (~330K examples).** Break the OCR dependency. Train on charts without value labels (or with deliberately wrong labels), grids without coordinate text, and pie charts without percentage annotations. Every SFT target includes chain-of-thought referencing visual landmarks: *"The gridlines are at 0, 20, 40, 60, 80. The Apr bar extends just above 80. My estimate: {82}."* Curriculum: weeks 1-2 all no-label → weeks 3-4 introduce wrong-label conflict detection → weeks 5-6 reintroduce correct labels. The reintroduction is critical: we want a model that *verifies* text against visual evidence, not one that ignores all text. Include 70K solved-task examples for regularization to prevent catastrophic forgetting on table lookups (currently 100%) and diagram navigation (100%).

**Stage 2 — DPO: Grounding Calibration (~40K pairs).** Value-label conflict is the primary DPO target: 0% accuracy with 100% text-reliance means every instance produces a perfectly clean preference pair. Chosen: visual estimation with gridline reasoning. Rejected: the model's actual output reading the wrong label. Extended thinking confirms this is behavioral, not cognitive (0%→0% with thinking) — the model needs retraining, not more reasoning time. Additional DPO sources: touching circles at threshold distances (0% at gap < 12px), color discrimination at low ΔL (weighted toward greens/purples), annotation conflicts at small gaps (gap < 15 only — larger gaps are already solved, and thinking alone improves baseline from 75%→90%), and path following overcounts (97% of errors are overcounts).

**Stage 3 — RL with Verifiable Rewards (~225K episodes).** Sharpen perceptual strategies for tasks with smooth degradation curves — all clearly in-distribution. All tasks have exactly computable ground truth. Curricula start where the model succeeds (~90%+) and push into failure regimes: overlapping shapes (overlap 0.1 → 0.5), path following (2 → 6 connections), pie value estimation (3 → 8 slices, gap 15pp → 3pp), dense chart reading (3 → 10 series), line intersection (3-point → 5-point with anti-false-positive bonus at GT=0), heatmap value reading (4×4 → 6×6, sequential → diverging colormaps), line series comparison (y_max auto → 200, gap 10 → 1), and trend detection at high series counts (n_series 4 → 10). The last two are distinct from dense chart value reading: line comparison at fixed y-axis (65% at gap=1/y=200) requires discriminating small height differences under axis compression, while trend detection at 10 series (81%) is a path-isolation problem where the model must trace a named series through overlapping lines.

## Deep Dive: The OCR-as-Crutch Problem

This is the highest-leverage failure because it's an *architectural behavior*, not an isolated task. The evidence chain:

| Finding | What It Proves |
|---|---|
| Value-label conflict: 0% accuracy, 100% text-reliant | Model reads the number label, never estimates bar height |
| Value-label with thinking: still 0% | Reasoning cannot override — behavioral retraining needed |
| Grid counting: 100% with text vs 49% without | Model reads coordinates, doesn't count lines |
| Line chart: show_values hurts (72% vs 80%) | Labels from adjacent series cause confusion — model grabs nearest text |
| Pie chart: 100% with % labels vs 53% without | Same pattern extends to angular estimation |
| Annotation conflict: 75% → 90% with thinking | Partially reasoning — annotations are persuasive only when visual evidence is weak |

**Sample training data.** The images below (generated by `figures/make_finetuning_samples.py`) illustrate two training instance types:

*Image 1 — No-label bar chart (SFT target):*
`figures/ft_sample_no_label.png`
- **Prompt**: "What is the value for Apr?"
- **Target response**: "The gridlines are at 0, 20, 40, 60, 80, 100. The Apr bar extends just above the 80 gridline. My estimate: {82}"
- **Scoring**: Tolerance-based — within 5% of GT or ±2, whichever is larger. For GT=82: accepts 78-86.

*Image 2 — Wrong-label bar chart (DPO pair):*
`figures/ft_sample_wrong_label.png`
- **Prompt**: "What is the value for Apr?" (bar height is ~82, label says "55")
- **Chosen response**: "I see a label '55' above the Apr bar, but comparing bar height to the y-axis — it clearly extends just above 80. The label appears incorrect. Based on bar height: {82}"
- **Rejected response**: "{55}" — the model's actual output, reading the label directly.
- **Why this scoring**: We use tolerance-based matching (not exact) because visual interpolation between gridlines has irreducible noise. A model that correctly reads the bar as "about 80" and answers {80} should receive positive reward even though GT is 82. The ±5% tolerance is calibrated against human estimation error on similar charts.

**Why this data, specifically.** The SFT no-label examples force the model to develop a visual estimation strategy — referencing gridlines, comparing relative heights — because there is no text to fall back on. The DPO wrong-label examples then teach the model to *detect and override* incorrect text, which is the real-world failure mode (stale labels in recycled slide decks, wrong annotations in edited reports). The curriculum reintroduces correct labels in weeks 5-6 to restore normal text+visual integration, preventing a model that blindly ignores all text.

## Expected Outcomes

| Metric | Before | After |
|---|---|---|
| Value-label conflict accuracy | 0% | 75-85% |
| Grid counting (blank) | 49% | 80-90% |
| Pie value estimate (no labels) | 53% | 70-80% |
| Pie slice comparison (no labels) | 73% | 85-90% |
| Heatmap value reading | 56% | 65-75% |
| Overlapping shape counting | 62% | 75-85% |
| Chart value (dense, 8-10 series) | ~50% | 65-75% |
| Line comparison (gap=1, y=200) | 65% | 80-90% |
| Trend detection (10 series) | 81% | 90-95% |
| Path following (distractor, 4-6 conn.) | ~35% | 55-65% |
| Intersection counting (5-pt lines) | 18% | 35-50% |
| Annotation conflict | 75% | 90-95% |

Residual gaps reflect genuine perceptual limits (angular estimation noise, encoder resolution, visual clutter in path tracing) rather than training failures. The annotation conflict ceiling is high (90% already achievable with thinking alone) — DPO on hard cases should push the remaining 10%. Logos (1.9%) and flags (40%) are not targeted for training but may improve as a side effect of general bias override capability — they serve as held-out evaluation benchmarks.
