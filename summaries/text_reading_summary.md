# Text Reading — Evaluation Summary

## Primitive Definition
Can the model read text at varying sizes, rotations, and contrast levels? This isolates the OCR capability that all chart, table, and document tasks depend on.

## Key Finding
**Text reading is near-perfect at font ≥14px for words (97–100%) and reliable for upright text, but 45° rotation degrades both words (87% at font=14) and numbers (60% at font=20). Below 10px, accuracy collapses: font=8px drops to 45% for words and 20% for numbers; font=6px is near-zero (13% words, 10% numbers). Numbers degrade faster than words at every size because the model's lexical priors can rescue partial word recognition but provide no fallback for digits. At font=8+rotation, the model hallucinates plausible-looking but completely wrong words.**

## Tasks Evaluated

### Ceiling Tasks (≥95% accuracy)

| Task | Accuracy | n | Condition |
|------|----------|---|-----------|
| `text_word_reading` (font=20) | 100% | 150 | All rotations, all contrasts |
| `text_word_reading` (font=14) | 97.3% | 150 | Aggregate; drops to 87% at rot=45° |
| `text_number_reading` (font=14) | 95.0% | 40 | Aggregate; 100% at 0°/45°/90° but 80% at 30° |

Word reading at font=20 is the only true ceiling across all rotations. At font=14, words drop to 87% at 45° rotation. Numbers are more fragile: font=20 is only 82.5% (n=40) due to 60% accuracy at 45° rotation, and font=14 dips to 80% at 30°.

### Degrading Tasks

#### Isolated Word Reading (`text_word_reading`)

Overall: **67.7%** (508/750) — across font=[20,14,10,8,6] × rotation=[0,15,30,45,90°] × contrast=[high,medium,low]

**By font_size:**

| Font | Accuracy | n |
|------|----------|---|
| 20px | 100.0% | 150 |
| 14px | 97.3% | 150 |
| 10px | 83.3% | 150 |
| 8px | **45.3%** | 150 |
| 6px | **12.7%** | 150 |

The cliff between 10px (83%) and 8px (45%) is the key finding — a 2px reduction causes a ~40pp drop. At 6px, the model is near-random.

**By rotation:**

| Rotation | Accuracy | n |
|----------|----------|---|
| 0° | 91.3% | 150 |
| 15° | 76.7% | 150 |
| 30° | 63.3% | 150 |
| 45° | 51.3% | 150 |
| 90° | 56.0% | 150 |

Rotation has a large effect, though 90° (56%) is slightly easier than 45° (51%) — suggesting the model handles purely vertical text better than diagonal text.

**By contrast:**

| Contrast | Accuracy | n |
|----------|----------|---|
| high (#000 / #FFF) | 70.4% | 250 |
| medium (#555 / #DDD) | 70.0% | 250 |
| low (#888 / #BBB) | 62.8% | 250 |

Contrast is the weakest axis — ~7pp gap between high and low contrast, far smaller than the font and rotation effects.

**Font × rotation cross-tab (word accuracy %):**

| Font | rot=0° | rot=15° | rot=30° | rot=45° | rot=90° |
|------|--------|---------|---------|---------|---------|
| 20px | 100% | 100% | 100% | 100% | 100% |
| 14px | 100% | 100% | 100% | 87% | 100% |
| 10px | 100% | 100% | 80% | 63% | 73% |
| 8px | 100% | 80% | 33% | 7% | 7% |
| 6px | 57% | 3% | 3% | 0% | 0% |

The interaction is strongly multiplicative: font=8 at rot=0° is 100%, but font=8 at rot=45° collapses to 7%. Font=6 reaches 0% at all rotations except straight-on.

**Word error pattern — lexical hallucination:**
Below font=8, the model doesn't fail silently — it hallucinates plausible English words with no connection to the target:
- GT="Compliance" → "Suitcase" (font=6, rot=90°)
- GT="Marketing" → "Explore" (font=6, rot=90°)
- GT="Quarterly" → "Socks" (font=6, rot=90°)
- GT="Analysis" → "Analyze" (font=10, rot=30°)
- GT="Revenue" → "Revisions" / "Reversals" (font=10, rot=90°)

At tiny sizes and high rotations, the model sees a word-shape blob and generates whatever word its prior suggests. Errors are not random character substitutions — they're coherent words that share approximate visual features with the target.

#### Isolated Number Reading (`text_number_reading`)

Overall: **52.5%** (105/200) — across font=[20,14,10,8,6] × rotation=[0,30,45,90°]

**By font_size:**

| Font | Accuracy | n |
|------|----------|---|
| 20px | 82.5% | 40 |
| 14px | **95.0%** | 40 |
| 10px | 55.0% | 40 |
| 8px | **20.0%** | 40 |
| 6px | **10.0%** | 40 |

Number reading is harder than word reading at every font size. Even font=20 only reaches 82.5% (vs 100% for words) because rotation affects numbers more at large sizes.

**By rotation:**

| Rotation | Accuracy | n |
|----------|----------|---|
| 0° | 84.0% | 50 |
| 30° | 46.0% | 50 |
| 45° | 36.0% | 50 |
| 90° | 44.0% | 50 |

**Font × rotation cross-tab (number accuracy %):**

| Font | rot=0° | rot=30° | rot=45° | rot=90° |
|------|--------|---------|---------|---------|
| 20px | 100% | 90% | 60% | 80% |
| 14px | 100% | 80% | 100% | 100% |
| 10px | 100% | 60% | 20% | 40% |
| 8px | 80% | 0% | 0% | 0% |
| 6px | 40% | 0% | 0% | 0% |

Font=8 with any rotation is essentially 0%. Font=10 with rotation ≥45° drops to 20-40%.

**Number error patterns — digit-level failures:**
Unlike word errors (lexical hallucination), number errors show raw OCR failure at the digit level:
- "73" → "13" (7→1 confusion at angle)
- "518" → "528" (single digit substitution)
- "256" → "254" (single digit substitution)
- "365" → "55" (digit dropping)
- "2048" → "2024" (year prior substitution)
- "89" → "88" (single-digit confusion)
- At font=6-8: "I can only see a small icon / symbol" — model stops perceiving text entirely

Numbers lack lexical rescue. With words, partial letter recognition enables language-prior completion ("Exp..." → "Expenses"). With numbers, each digit must be independently resolved with no analogous fallback.

## Cross-Task Patterns

1. **Font=14px is the practical floor for reliable reading — at 0° and 90°.** At 14px and upright/vertical orientation, both words (100%) and numbers (100%) are at ceiling. Aggregate accuracy (97.3% words, 95.0% numbers) masks 45° degradation: words drop to 87%, and numbers at font=20 drop to 60% at this angle. Most chart text is upright or 90°-rotated, so typical business content falls in the reliable zone, but oblique labels (e.g., angled axis tick labels) are at risk.

2. **The 8px cliff is steep and unexpected.** Word accuracy drops 38pp (83%→45%) and number accuracy drops 35pp (55%→20%) from 10px to 8px. Small icon labels, footnotes, and footnote annotations commonly fall in the 6-9px range and will be largely unreadable.

3. **Rotation degrades multiplicatively with small font.** At font=8, rotation collapses accuracy from 100% (0°) to 7% (45°). At font=14, the same rotation causes negligible degradation. Font and rotation are not independent — they interact severely at small sizes.

4. **Lexical priors rescue words but expose model dependency.** The 15pp accuracy gap between words (67.7%) and numbers (52.5%) reflects the language model rescuing degraded word signals via vocabulary. The hallucination at font=6 ("Suitcase" for "Compliance") is the dark side of this: when the visual signal is too degraded, the prior generates fluent but completely wrong text.

5. **90° rotation is not the hardest angle.** Across both tasks, 45° rotation is consistently harder than 90°. Pure vertical text appears to be easier for the vision encoder than diagonal text — possibly because vertical text is encountered in training data (rotated labels, signage) more than diagonal.

6. **Contrast has minimal effect compared to font size.** The 7-8pp gap between high and low contrast is dwarfed by font size effects (87pp gap between 20px and 6px). Contrast optimization is low-priority for training.

## Finetuning Implications

- **The 8-10px regime is the highest-value target.** Font=8 (words: 45%, numbers: 20%) is the practical failure boundary for real-world text. Training with synthetic small-text data (font=8-10, all rotations) would cover the most relevant failure mode.
- **Numbers need dedicated training.** They cannot benefit from lexical priors — each digit must be learned independently. Training curriculum: start with single digits at small sizes, build to multi-digit numbers with rotation.
- **Include vertical text explicitly.** 90° rotation is a qualitatively distinct pattern. Dedicated exposure to vertically oriented text (axis labels rotated 90°, vertical signage) would help.
- **Lexical hallucination at tiny sizes is a safety concern.** At font=6 the model confidently outputs plausible but wrong words. Applications relying on OCR of small text need explicit uncertainty calibration, not just accuracy improvement.
- **Font ≥14px at 0°/90° needs no improvement** — already at ceiling. Oblique angles (30–45°) at font=14–20 still show 80–87% for words and 60–90% for numbers, presenting a smaller but real training opportunity.
