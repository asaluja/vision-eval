# Visual-Textual Consistency (Grounding) — Evaluation Summary

## Primitive Definition
When text annotations in a chart contradict the visual content, does the model ground its answer in what it sees or what it reads?

## Key Finding
**The model completely trusts explicit numeric labels (0% accuracy, 100% text-reliant) but correctly ignores misleading titles and legends. Annotations partially fool it, especially when the visual evidence is ambiguous.**

## Tasks Evaluated

All tasks are synthetically generated. Each plants a specific text-visual contradiction in a chart and asks a question whose correct answer requires reading the visual, not the text. The `text_reliant` metric tracks whether the model's answer matched the wrong text.

Note: `chart_data_match` (cross-representation data equivalence) was initially categorized here but moved to Relative Comparison — it has no text-visual conflict, only cross-visual comparison.

### Overall Results

| Conflict Type | Accuracy | Text-Reliant Rate | n |
|---|---|---|---|
| Value label (wrong number on bar) | **0%** | **100%** | 40 |
| Annotation ("Highest" on wrong bar) | 75% | 25% | 40 |
| Title trend (title contradicts trend) | 100% | 0% | 40 |
| Legend color (swapped series names) | 100% | 0% | 40 |

### Conflict Type Deep-Dives

#### 1. Value Label Conflict (0% accuracy)

The model **always** reads the text label above the bar, never the actual bar height. Even when the prompt explicitly says "based on the bar heights shown," the response is the wrong label value with no visual reasoning.

Example: Bar visually at height 52, labeled "36". Prompt: "Based on the bar heights shown, read the value of Product B." Response: `{36}`.

| n_categories | Accuracy | Text-Reliant |
|---|---|---|
| 3 | 0% | 100% |
| 4 | 0% | 100% |
| 5 | 0% | 100% |
| 6 | 0% | 100% |

No variation by number of categories — the failure is absolute.

#### 2. Annotation Conflict (75% accuracy)

A red "Highest" arrow and label points to a non-max bar. The model is fooled 25% of the time, and errors strongly correlate with the **value gap** between the true max and the annotated bar:

| Condition | Mean gap (true max − annotated) |
|---|---|
| Correct responses | 29.7 |
| Error responses | 11.3 |

When the true max is clearly taller (gap ≥ 20), the model ignores the annotation. When bars are similar in height (gap < 15), the annotation tips the model toward the wrong answer.

| n_categories | Accuracy |
|---|---|
| 3 | 60% |
| 4 | 70% |
| 5 | 100% |
| 6 | 70% |

The n=5 result (100%) appears to be a lucky draw with large gaps rather than a systematic effect.

#### 3. Title Trend Conflict (100% accuracy)

The model consistently reads the visual trend and ignores the contradictory title. Responses often explicitly acknowledge the contradiction:

> "Looking at the chart titled 'Rising Sales Over Time,' I can see three data points: January: 33, February: 27, March: 21. The values are clearly going down..."

The model reads the data points, reasons about the direction, and answers correctly — the title has zero influence.

#### 4. Legend Color Conflict (100% accuracy)

The legend maps colors to the wrong series names (e.g., blue bars labeled "Cost" when they are actually "Revenue"). The model reads bar values by spatial position and color, answering correctly regardless of legend labels.

This suggests the model resolves "what is the value of X for Y?" by: (1) finding the series via the legend label → color mapping, (2) locating the bar at the correct position, (3) reading its height or label. Since the bar values are labeled with correct numbers, the model gets the right answer even though it may be identifying the wrong series.

## Cross-Task Patterns

1. **Text-reliance hierarchy: labels > annotations > titles/legends.** Explicit numeric labels placed directly on visual elements are trusted absolutely. Spatial annotations (arrows) are partially trusted, especially when the visual evidence is ambiguous. High-level text (titles, legends) is ignored in favor of visual data.

2. **The model does not read bar heights — it reads value labels.** The 0% accuracy on `conflict_value_label` combined with 100% on `conflict_legend_color` (which also has value labels, but correct ones) confirms that the model's "value reading" is actually OCR of the label text, not visual estimation of bar height.

3. **Annotations are persuasive when visual evidence is weak.** The annotation conflict error pattern (mean gap 11 for errors vs 30 for correct) shows the model uses annotations as tiebreakers when it can't easily determine the answer visually. This is arguably rational behavior — but it means the model can be misled by wrong annotations on close-call comparisons.

4. **The model can reason past contradictions at the semantic level.** Title trend responses show the model explicitly noting the title, reading the data points, and reasoning about direction. This higher-order reasoning overrides the title — but the same reasoning does not override value labels.

5. **The critical vulnerability is at the character level, not the semantic level.** The model fails when wrong information is placed exactly where it looks for the answer (number above a bar). It succeeds when wrong information is elsewhere (title, legend, arrow on a different bar).

## Real-World Likelihood of Each Conflict Type

Not all conflict types are equally likely in practice. In real-world charts (slide decks, reports, dashboards), legends and axis labels are auto-generated by plotting libraries and almost never wrong. Errors arise from human editing — updating data without updating surrounding text.

| Conflict Type | Real-World Likelihood | How It Happens | Model Accuracy |
|---|---|---|---|
| Wrong title | Most common | Data updated, title not refreshed; editorial spin ("Revenue Growing" on flat data) | 100% (solved) |
| Wrong value labels | Common | Hardcoded text annotations in PowerPoint/infographics not refreshed after data update | 0% (total failure) |
| Wrong annotations | Moderate | Callout arrows ("peak quarter") left pointing at old element after data changes | 75% (partial) |
| Swapped legend | Rare | Auto-generated by plotting libraries; almost never wrong in practice | 100% (solved) |

The model's worst failure (value labels, 0%) is the second most common real-world error. Its best performance (titles, 100%) is on the most common error. This mismatch makes value-label grounding a high-priority finetuning target.

## Finetuning Implications

- **Highest priority: value-label grounding.** Train on charts where the model must estimate bar/line values from the visual rendering, with no text labels or with deliberately wrong labels. This is the single clearest grounding failure.
- **RL reward signal**: Exact match to the true visual value (bar height), not the displayed label.
- **Curriculum for annotations**: Start with large value gaps (easy to override the annotation), progressively decrease the gap. The model already resists annotations at gap ≥ 20; train it to resist at gap < 10.
- **Title/legend conflicts are solved** — no finetuning needed for these.
- **Connection to prior findings**: Grid counting (100% with text, 49% without) showed the model defaults to OCR. This primitive confirms and quantifies the pattern: when a numeric label is present, the model reads it and does not verify it against the visual.
