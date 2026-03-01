# Text Reading — Evaluation Summary

## Primitive Definition
Can the model read text at varying sizes, rotations, and contrast levels? This isolates the OCR capability that all chart, table, and document tasks depend on.

## Key Finding
**Text reading is near-solved for words (96.3%) and chart labels (100%) but degrades for isolated numbers at small sizes with rotation (81%). The model leverages lexical priors for words — guessing plausible words from partial visual information — but numbers lack this cue, exposing raw OCR limitations. At font=10 + 90° rotation, word accuracy drops to 47% and number accuracy to 0%.**

## Tasks Evaluated

### Ceiling Tasks (100% exact match)

| Task | n | Source | Notes |
|------|---|--------|-------|
| Chart axis label reading | 60 | Generated | Font 7-12px, rotation 0-60°, all configs 100% |
| Word reading (font ≥20px) | 225 | Generated | All rotations, all contrasts, perfect |
| Number reading (font ≥32px) | 40 | Generated | All rotations perfect |

Chart axis labels are perfectly readable even at the smallest tested font (7px) with 60° rotation. This is likely because matplotlib renders labels at higher effective resolution than our isolated text images, and the chart context provides structural cues.

Word reading is robust down to font=20px across all rotations (0-90°) and all contrast levels (high/medium/low). The model's vocabulary knowledge compensates for visual degradation.

### Degrading Tasks

#### Isolated Word Reading

**Overall: 96.3%** (361/375)

**By font_size × rotation (all contrasts):**

| Font | rot=0 | rot=15 | rot=30 | rot=45 | rot=90 |
|------|-------|--------|--------|--------|--------|
| 48 | 100% | 100% | 100% | 100% | 100% |
| 32 | 100% | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% | 100% | 100% |
| 14 | 100% | 100% | 100% | 87% | 100% |
| **10** | **100%** | **100%** | **87%** | **87%** | **47%** |

Errors are concentrated exclusively at font=10 (the smallest size), and primarily at 90° rotation. At font=14, only 2 errors appear (both at 45° rotation).

**Font=10, rotation × contrast:**

| Rotation | High | Medium | Low |
|----------|------|--------|-----|
| 0° | 100% | 100% | 100% |
| 15° | 100% | 100% | 100% |
| 30° | 100% | 80% | 80% |
| 45° | 100% | 80% | 80% |
| 90° | 80% | **0%** | 60% |

At font=10 + rot=90°, medium contrast collapses to **0%** (0/5) while high contrast maintains 80% and low contrast 60%. The medium contrast anomaly (#555 on #DDD) may create a specific gray-on-gray combination that is harder to resolve than the low contrast (#888 on #BBB) at this extreme rotation.

**Word error pattern — lexical hallucination:**
The model doesn't fail silently — it produces plausible English words that share visual features with the target:
- "Expenses" → "Experiences" (font=14, rot=45)
- "Analysis" → "Analyze" (font=10, rot=30/45)
- "Forecast" → "Forrest" (font=10, rot=90)
- "Margin" → "bargain" (font=10, rot=90)
- "Marketing" → "hardcoding" (font=10, rot=90)
- "Revenue" → "Revisions" / "Reversals" (font=10, rot=90)

These are not random character errors — they're the model's language prior filling in visual ambiguity with the most likely word given partial letter recognition. At 90° rotation with low resolution, the model sees a word-length shape and generates a contextually plausible completion.

#### Isolated Number Reading

**Overall: 81.0%** (81/100)

**By font_size × rotation:**

| Font | rot=0 | rot=30 | rot=45 | rot=90 |
|------|-------|--------|--------|--------|
| 48 | 100% | 100% | 100% | 100% |
| 32 | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 60% | 80% |
| 14 | 100% | 40% | 100% | 100% |
| **10** | **100%** | **20%** | **20%** | **0%** |

Numbers degrade much more severely than words at the same font size and rotation. At font=10 + rot=90°, accuracy is **0%** (vs 47% for words). At font=10 + rot=30°, accuracy is 20% (vs 87% for words).

The font=14 pattern is irregular — rot=30° drops to 40% while rot=45° and rot=90° are 100%. This is driven by a single number ("73") that was misread as "13" in 3/5 instances at rot=30°, suggesting a specific digit confusion (7→1) at this angle.

**Number error patterns — digit-level confusion:**
Unlike word errors (lexical hallucination), number errors show raw OCR failures:
- "73" → "13" (font=14, rot=30) — the "7" becomes a "1" at this angle
- "518" → "5128" (font=20, rot=45) — phantom digit insertion
- "256" → "325" (font=10, rot=90) — digit transposition and substitution
- "365" → "55" (font=10, rot=90) — digit dropping
- "2048" → "2548" (font=10, rot=90) — digit substitution
- "89" → "88" (font=20, rot=90) — single-digit confusion
- Several font=10 errors: "I can only see a small icon" — the model doesn't even see text, interpreting the tiny rotated number as a cursor/icon

Numbers lack the lexical rescue that words enjoy. With words, even partial letter recognition can be completed by language priors ("Exp..." → "Expenses"). With numbers, each digit must be independently resolved — there's no prior for "what 3-digit number starts with 5 and ends with 8."

#### HF Circled Letter

| Source | Accuracy | n |
|--------|----------|---|
| Generated | 80.0% | 40 |
| HF Blind | 82.4% | 624 |

The circled letter task asks the model to identify which letter in a word has a circle drawn around it. At 82.4%, this represents a different kind of text reading challenge — the text itself is readable, but the model must additionally determine which specific character the circle encloses, requiring spatial precision overlaid on OCR.

## Cross-Task Patterns

1. **Text reading is near-solved above 14px.** At font sizes ≥14px, word reading is ≥96% and number reading is ≥90% across all rotations and contrasts. The model's OCR capability is strong for typical document and chart text sizes.

2. **Lexical priors rescue words but not numbers.** The 15-point accuracy gap between words (96.3%) and numbers (81.0%) reflects the model's language model coming to the rescue: partial visual information from degraded text can be completed by vocabulary knowledge for words, but numbers must be read digit-by-digit with no such fallback.

3. **Rotation is harder than small font size or low contrast.** At font=10, unrotated text is 100% for both words and numbers. Rotation at the same font size drops accuracy dramatically (words: 47% at 90°, numbers: 0% at 90°). Contrast reduction alone has a smaller effect — font=10 + rot=0° is 100% at all contrasts.

4. **Chart labels are easier than isolated text at the same nominal font size.** Chart labels at font=7px are 100%, while isolated words at font=10px with rotation are <90%. Chart rendering via matplotlib produces higher-quality anti-aliased text at effective DPI, and the bar-chart context provides structural cues for label identification.

5. **The 90° rotation failure is not symmetric.** At font=10, performance at rot=45° (~87% words, ~20% numbers) is substantially better than rot=90° (~47% words, ~0% numbers). Vertical text appears to be a qualitatively harder visual pattern than diagonal text for the vision encoder.

6. **Medium contrast can be harder than low contrast.** At font=10 + rot=90°, medium contrast (#555/#DDD) yields 0% word accuracy while low contrast (#888/#BBB) yields 60%. This counterintuitive result suggests the specific gray values of medium contrast fall in a perceptual dead zone for the model.

## Finetuning Implications

- **Small rotated numbers are the highest-value target.** Font=10 numbers at 30-90° rotation (20-0% accuracy) represent a clear, systematic failure that training could address. The failure is at the character recognition level, not reasoning.
- **Training should include vertical text (90° rotation).** This is a qualitatively distinct failure mode from diagonal text. The model may need specific exposure to vertically oriented characters.
- **Curriculum design:** Start with large rotated text (font=32, where everything is 100%), progressively decrease size. Numbers should be trained separately from words since they can't benefit from language model priors.
- **Don't train on chart labels.** They're already 100% — the chart rendering pipeline produces high-quality text that doesn't exercise the model's OCR limits.
- **Circled letter training for spatial precision.** The 82% accuracy on circled letters represents a spatial overlay challenge distinct from pure OCR — training should include character-level localization within words.
