# Prior Bias Override — Evaluation Summary

## Primitive Definition
Can the model report what it actually sees, overriding both memorized defaults and misleading text annotations? This tests two failure modes: (1) the model defaults to canonical knowledge (logo element counts, flag stripe counts) rather than counting the actual visual content, and (2) the model defers to text annotations (value labels, chart annotations) rather than grounding in the visual rendering.

## Key Finding
**The model fails to ground in visual content in two distinct ways. For logos, prior bias is near-total: 1.9% accuracy with 99.8% bias alignment — the model retrieves canonical knowledge instead of counting. For chart value labels, text-reliance is absolute: 0% accuracy when wrong numbers are placed on bars — the model reads the label, never the bar height. Both are "trusting something other than the image" failures, but the prior path (logos/flags) and the text path (value labels) are independent mechanisms.**

## Tasks Evaluated

### Ceiling Tasks

#### Title Trend Conflict (`conflict_title_trend`, Local)

**Overall: 100%** (40/40) — text-reliant: **0%**

The model consistently reads the visual trend and ignores the contradictory title. Responses often explicitly acknowledge the contradiction ("Looking at the chart titled 'Rising Sales Over Time,' I can see three data points going down..."). The title has zero influence.

#### Legend Color Conflict (`conflict_legend_color`, Local)

**Overall: 100%** (40/40) — text-reliant: **0%**

The legend maps colors to the wrong series names. The model reads bar values by spatial position and color, answering correctly regardless of legend labels. This suggests the model resolves series identity via color + position, not legend text.

### Degrading Tasks

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

405 of 406 errors (99.8%) are the exact canonical biased answer; one Shoe Logos error was non-bias-aligned (Adidas shoe, model answered 2 stripes, canonical=3, GT=4). The model's visual encoder rarely engages for logos — it pattern-matches the brand and outputs the memorized element count.

#### Value Label Conflict (`conflict_value_label`, Local)

**Overall: 0%** (0/40) — text-reliant: **100%**

The model **always** reads the text label above the bar, never the actual bar height. Even when the prompt explicitly says "based on the bar heights shown," the response is the wrong label value with no visual reasoning.

Example: Bar visually at height 52, labeled "36". Prompt: "Based on the bar heights shown, read the value of Product B." Response: `{36}`.

| n_categories | Accuracy | Text-Reliant |
|---|---|---|
| 3 | 0% | 100% |
| 4 | 0% | 100% |
| 5 | 0% | 100% |
| 6 | 0% | 100% |

No variation by number of categories — the failure is absolute. **Extended thinking (budget=2048): still 0%** — thinking cannot override OCR-level text reliance. Larger thinking budgets do not help.

#### Annotation Conflict (`conflict_annotation`, Local)

**Overall: 75%** (30/40) — text-reliant: **25%**

A red "Highest" arrow and label points to a non-max bar. The model is fooled 25% of the time, and errors strongly correlate with the **value gap** between the true max and the annotated bar:

| Condition | Mean gap (true max − annotated) |
|---|---|
| Correct responses | 29.7 |
| Error responses | 11.3 |

When the true max is clearly taller (gap >= 20), the model usually resists the annotation (88.5% accuracy). When bars are similar in height (gap < 15), the annotation tips the model toward the wrong answer (25% accuracy).

**Extended thinking (budget=2048): 90%** (+15pp). Thinking gives the model space to reason past the misleading annotation — the largest improvement of any thinking experiment in this eval. The remaining 10% errors likely occur at very small gaps where the visual evidence is genuinely ambiguous. Larger thinking budgets do not improve further.

## Cross-Task Patterns

1. **Two independent "trust something other than the image" mechanisms.** Logos/flags fail via memorized priors (the model recognizes the brand/country and retrieves canonical element counts). Value labels fail via text-reliance (the model reads the number placed on the bar instead of estimating bar height). These are distinct pathways — prior bias doesn't involve any text in the image, and value-label reliance doesn't involve any memorized knowledge.

2. **Bias/text-reliance scales with signal specificity.** Logos (99.8% bias aligned) > flags (83%) > annotations (25% text-reliant) > titles/legends (0%). The more specific and directly positioned the misleading signal (number on a bar, brand name on a logo), the more completely it overrides visual evidence. Diffuse signals (chart title, legend position) are ignored.

3. **Logos represent complete vision bypass.** The model doesn't weight the prior more heavily — it appears to skip visual counting entirely. 100% bias alignment with 0% accuracy on car logos means the visual encoder output is irrelevant.

4. **Value labels represent complete text bypass of visual estimation.** The model's "value reading" is OCR of label text, not visual estimation of bar height. This is confirmed by the 0% value-label accuracy combined with 100% legend-color accuracy (which also has labels, but correct ones).

5. **The model can reason past contradictions at the semantic level.** Title trend responses show the model explicitly noting the title, reading the data points, and reasoning about direction. But this same reasoning does not override value labels — the failure is at the character level (reading the number), not the semantic level.

6. **Annotations are persuasive only when visual evidence is weak.** The annotation error pattern (mean gap 11 for errors vs 30 for correct) shows the model uses annotations as tiebreakers when it can't easily determine the answer visually. This is arguably rational behavior that degrades when annotations are wrong.

7. **Extended thinking helps only annotation conflicts (+15pp), not value labels or priors.** Thinking improves annotation resistance (75%→90%) by giving the model space to reason past the misleading arrow. But it cannot break the value-label wall (0%→0%) or the logo/flag prior — these failures are perceptual (OCR, pattern-matching), not reasoning deficits. This confirms the distinction: annotations are a reasoning problem (the model sees the right answer but is swayed), while value labels and priors are perception problems (the model never sees the right answer).

## Real-World Likelihood of Text-Visual Conflicts

| Conflict Type | Real-World Likelihood | How It Happens | Model Accuracy |
|---|---|---|---|
| Wrong title | Most common | Data updated, title not refreshed; editorial spin | 100% (solved) |
| Wrong value labels | Common | Hardcoded text annotations in PowerPoint not refreshed after data update | 0% (total failure) |
| Wrong annotations | Moderate | Callout arrows left pointing at old element after data changes | 75% (partial) |
| Swapped legend | Rare | Auto-generated by plotting libraries; almost never wrong | 100% (solved) |

The model's worst failure (value labels, 0%) is the second most common real-world error.

## Finetuning Implications

- **Logos are the highest-density DPO source for prior bias.** 406/414 instances (98%) produce preference pairs with 99.8% bias alignment. The rejected answer is almost always the canonical element count; the preferred answer is the actual visual count.
- **Value-label grounding is the highest-priority text-reliance target.** Train on charts where the model must estimate bar/line values from the visual rendering, with no text labels or with deliberately wrong labels.
- **Flag training covers two distinct biases.** Star count (12 vs 13) and stripe count each have their own canonical prior. Both sub-topics need independent training coverage.
- **Car logos need dedicated attention.** 0% accuracy suggests the car logo prior is exceptionally strong. May need higher learning rate or more examples relative to shoe logos (5.6% baseline).
- **RL reward signal for value labels**: Exact match to the true visual value (bar height), not the displayed label.
- **Curriculum for annotations**: Start with large value gaps (easy to override the annotation), progressively decrease the gap. The model already resists annotations at gap >= 20; train it to resist at gap < 10.
- **Title/legend conflicts are solved** — no finetuning needed for these.
- **Chain-of-thought prompting may help both failure modes:** "Count only what is visible" for logos/flags; "Estimate the value from the bar height, ignoring any text labels" for value labels. Without explicit instructions, the model retrieves/reads rather than perceives.
