# Spatial Localization — Evaluation Summary

## Primitive Definition

Can the model find a specific element in an image and report what's there? This includes reading a value from a specific cell, identifying a circled letter, reading a bar's value, or tracing which step follows another in a flowchart.

## Overall Performance

| Task | Accuracy | n | Notes |
|------|----------|---|-------|
| Table cell lookup | **100%** | 480 | 12 grid sizes × 2 styles × 2 prompt phrasings × 2 query sets |
| Diagram decision (Yes/No) | **100%** | 240 | Across all template complexities |
| Diagram next step | **94.2%** | 120 | All 7 errors in multi_decision template |
| Bar chart value | **100%** | 64 | Simple bar charts (tolerance ±5% or ±2) |
| Grouped bar value | **74.0%** | 576 | 2-10 series. 97% at 2 series, degrades to 50-53% at 9-10 series |
| Line chart value | **75.7%** | 576 | 2-10 series. 100% at 2-3 series, degrades to 47% at 10 series |
| Circled letter | **82.4%** | 624 | HuggingFace VLMs-are-Blind benchmark |
| Pie value (with % labels) | **100%** | 60 | Reads percentage text |
| Pie value (no % labels) | **53%** | 60 | Must estimate angular proportion visually |

**Bottom line**: Spatial localization is solved for structured, low-clutter layouts (tables, simple charts, diagrams). It degrades sharply with visual density: grouped bar and line chart value reading drop from ~100% at 2-3 series to ~50% at 9-10 series. Failures come from series attribution confusion in dense charts, arrow tracing in complex DAGs, and fine-grained character localization under overlay.

**Note on chart scoring**: Chart value-reading tasks now use tolerance-based scoring (within 5% of GT or ±2, whichever is larger) rather than exact match, reflecting that models must estimate from visual position.

---

## 1. Table Cell Lookup (100%, 480/480)

**Source**: Generated (PIL tables)
**Axes**: Grid size (3×2 to 10×5), header style (plain/shaded), prompt style (explicit vs. natural)

| Grid size | Plain | Shaded |
|-----------|-------|--------|
| 3×2 | 100% | 100% |
| 3×3 | 100% | 100% |
| 3×5 | 100% | 100% |
| 5×2 | 100% | 100% |
| 5×3 | 100% | 100% |
| 5×5 | 100% | 100% |
| 7×2 | 100% | 100% |
| 7×3 | 100% | 100% |
| 7×5 | 100% | 100% |
| 10×2 | 100% | 100% |
| 10×3 | 100% | 100% |
| 10×5 | 100% | 100% |

Two independent query sets (v1 and v2) hit different cells in the same 120 table images, both at 100%. Explicit prompts ("value in row X, column Y") and natural prompts ("What is Japan's Revenue?") perform identically.

**Conclusion**: Solved. Structured grid localization is not a blind spot, even at 10×5 with 50 cells.

---

## 2. Diagram Navigation (98.1%, 353/360)

**Source**: Generated (matplotlib flowcharts)
**Axes**: Template complexity (linear, single_branch, asymmetric, multi_decision), n_steps (3, 5, 7)

| Template | diagram_decision | diagram_next_step |
|----------|-----------------|-------------------|
| linear | — | 100% (30/30) |
| single_branch | 100% (60/60) | 100% (30/30) |
| asymmetric | 100% (60/60) | 100% (30/30) |
| multi_decision | 100% (120/120) | **76.7%** (23/30) |

Decision-following (Yes/No branches) is perfect across all templates. The only failures are in next-step tracing on multi_decision DAGs.

### Deep Dive: Arrow Tracing Failures in Multi-Decision DAGs

All 7 errors come from `diagram_next_step` on `multi_decision` templates. Inspecting each case individually reveals a tight pattern:

**6 of 7 errors share the same root cause**: the model misidentifies which node a leaf-branch arrow points to when it converges on the "End" node. Multi-decision diagrams have 3+ leaf branches whose arrows all converge on a single "End" node at the bottom-left, creating overlapping diagonal arrows. The model consistently picks a nearby process node instead of "End":

| Image | Source node | Ground truth | Model answer | Error type |
|-------|------------|--------------|--------------|------------|
| `flow_multi_decision_n5_1` | Check Inventory | End | Update Database | Arrow crosses other paths |
| `flow_multi_decision_n5_3` | Review Data | End | Update Database | Arrow crosses other paths |
| `flow_multi_decision_n7_4` | Notify Team | End | Validate Input | Arrow crosses other paths |

Each image has two prompt variants; both fail identically, confirming the errors are perceptual, not prompt-sensitive. Looking at the images, the "End" node sits at the bottom-left while leaf nodes sit on the right side. The arrows travel diagonally across the diagram, crossing over or running near other arrows and nodes — making it ambiguous which destination an arrow reaches.

**The remaining error is actually an extraction bug**: on `flow_multi_decision_n3_4`, the model correctly identifies "Complete?" as the next step after "Run Tests", but it also mentions alternative branch outcomes in braces (`{Notify Team}`, `{Assign Task}`) earlier in its reasoning. The regex extractor grabs the *first* `{...}` match instead of the last, picking up "Notify Team" from the reasoning rather than "Complete?" from the final answer.

**Takeaway**: The true model error rate on diagrams is 6/360 (98.3%). The failure mode is specifically *arrow tracing through visual clutter* — long diagonal arrows converging on a shared terminal node. Decision-following and node identification are effectively perfect.

---

## 3. Chart Value Reading

**Source**: Generated (matplotlib bar, grouped bar, line charts)
**Axes**: Chart type, show_values (True/False), show_grid (True/False), n_categories (3, 5, 7, 10), n_series (2–10)
**Scoring**: Tolerance-based (within 5% of GT or ±2, whichever is larger)

### Overall by task type

| Task | Accuracy | n |
|------|----------|---|
| Bar value (simple) | 100% | 64 |
| Grouped bar value | 74.0% | 576 |
| Line value | 75.7% | 576 |

### Series count is the primary difficulty axis

**Grouped bar value by n_series:**

| n_series | Accuracy |
|----------|----------|
| 2 | 97% |
| 3 | 98% |
| 4 | 89% |
| 5 | 83% |
| 6 | 69% |
| 7 | 66% |
| 8 | 61% |
| 9 | 50% |
| 10 | 53% |

**Line value by n_series:**

| n_series | Accuracy |
|----------|----------|
| 2 | 100% |
| 3 | 100% |
| 4 | 95% |
| 5 | 73% |
| 6 | 83% |
| 7 | 66% |
| 8 | 55% |
| 9 | 62% |
| 10 | 47% |

Both tasks show the same pattern: near-perfect at 2-3 series, steady degradation to ~50% at 9-10. The model correctly localizes the queried position (right x-axis point, right row) but increasingly confuses which series the value belongs to as visual density increases.

### Show values effect (line charts)

| Condition | Accuracy |
|-----------|----------|
| show_values=False | 80% |
| show_values=True | 72% |

**Annotations still hurt for line charts** — with many overlapping series, value labels from adjacent lines create confusion. The model grabs a nearby label from the wrong series. Without labels, it estimates from gridlines and performs better overall.

### Pie chart value estimation

| Condition | Accuracy | n |
|-----------|----------|---|
| With % labels | **100%** | 60 |
| Without % labels | **53%** | 60 |

The text label effect is consistent with bar/line charts: percentage labels give perfect accuracy, without them the model must estimate angular proportions. Error distribution without labels: mean absolute error of 2.8 percentage points, 88% within ±5pp, 100% within ±10pp. The model approximates angular proportions reasonably but with less precision than bar height estimation.

---

## 4. Circled Letter Identification (82.4%, 514/624)

**Source**: HuggingFace VLMs-are-Blind benchmark
**Axes**: Word (3 words), circle position (0 to 19), font (Helvetica, OpenSans), circle thickness

### Performance by Word

| Word | Accuracy | n |
|------|----------|---|
| Acknowledgement | 89.4% (161/180) | 180 |
| Subdermatoglyphic | 86.8% (177/204) | 204 |
| tHyUiKaRbNqWeOpXcZvM (random-case) | 73.3% (176/240) | 240 |

### Accuracy by Position (12 trials per cell)

| Pos | Acknowledgement | Subdermatoglyphic | tHyUi**K**aRb... |
|-----|:-:|:-:|:-:|
| 0 | 100% | 100% | **0%** |
| 1 | 100% | 67% | 42% |
| 2 | 100% | 100% | 100% |
| 3 | 100% | 100% | 100% |
| 4 | 100% | 100% | 50% |
| 5 | 100% | 100% | **0%** |
| 6 | 83% | 100% | 100% |
| 7 | 100% | 100% | 50% |
| 8 | 92% | 75% | 100% |
| 9 | 100% | 100% | 67% |
| 10 | 100% | 100% | 67% |
| 11 | 83% | **8%** | 75% |
| 12 | 100% | 100% | 100% |
| 13 | 50% | 100% | 100% |
| 14 | 33% | 83% | 100% |
| 15 | — | 75% | 83% |
| 16 | — | 67% | 100% |
| 17 | — | — | 100% |
| 18 | — | — | 33% |
| 19 | — | — | 100% |

Three cells drop to near-zero: random word positions 0 and 5 (0% each) and Subdermatoglyphic position 11 (8%). These are where the deep-dive analysis is most revealing.

### Deep Dive: Adjacent-Letter Errors Dominate

Of 110 total errors, **70% (74/106 with valid extraction) are off by exactly one position** — the model localizes the circle to the right general region but picks an adjacent character. Only 25% of errors are truly non-local. This is the dominant failure mode across all three words.

**Directional bias differs by word type:**
- Real words: strong **leftward** bias (24 left-neighbor vs 3 right-neighbor errors)
- Random mixed-case word: strong **rightward** bias (16 left vs 31 right-neighbor errors)

The direction flip is explained by visual saliency: in the random word, lowercase targets flanked by uppercase neighbors cause attention to drift toward the larger, more visually prominent glyph.

### Deep Dive: Lowercase Letters Between Uppercase Are Nearly Invisible

The two 0% cells in the random word both involve lowercase letters between uppercase neighbors:

**Position 0 (`t` before `H`)**: 12/12 wrong. The model literally cannot see the lowercase `t` at the start of the string. Multiple responses begin: *"I can see a red circle around the first letter of the string 'HyUiKaRbNqWeOpXcZvM'"* — the model reads the string as starting with `H`, completely missing the `t`. 7 of 12 responses answer `H`; the other 5 fail to extract any letter at all.

**Position 5 (`K` between `i` and `a`)**: 12/12 wrong. Despite `K` being uppercase, the circle is small and positioned at the boundary between characters. 10/12 responses answer `a` (the right neighbor). The model identifies the full string correctly but consistently mislocates the circle one position rightward.

**Position 18 (`v` between `Z` and `M`)**: 8/12 wrong. Font determines error direction — Helvetica errors toward `M` (rightward), OpenSans errors toward `Z` (leftward) — suggesting letter spacing/kerning affects which adjacent character the circle appears to overlap.

### Deep Dive: Word-Level Priors Override Visual Perception

The most striking evidence of language priors interfering with vision comes from **Acknowledgement position 14** (the final `t`):

All 8 errors answer **`S`** — a letter that *doesn't appear anywhere in "Acknowledgement"*. The model is completing the word to its more common plural form, "Acknowledgement**s**", and reporting the expected next letter rather than the circled one. This is pure hallucination from language priors.

Similarly, at **position 13** (`n` near the end), all 6 errors pick `e` (the left neighbor). The model's response often says something like *"the circle is positioned around the 'e' near the end of the word, before the 'nt'"* — demonstrating correct word knowledge but off-by-one localization, with the error direction consistent with reading from memory rather than from pixels.

### Deep Dive: Narrow Characters Are Systematically Misread

**Subdermatoglyphic position 11** (the `l` in "og**l**yphic") is the single worst cell for real words: 11/12 wrong (8% accuracy). The lowercase `l` is extremely narrow and flanked by `g` and `y`. The red circle, drawn to fit the character's bounding box, is correspondingly narrow — almost a vertical line. 9 of 11 errors pick `g` (the left neighbor), suggesting the circle visually bleeds into or is parsed as covering the wider adjacent glyph.

This generalizes: visually narrow characters (`l`, `i`, `t`) in contexts where the circle becomes correspondingly thin are systematically harder to localize than wider characters.

---

## Synthesis

### What's Solved

Spatial localization in **structured, low-density layouts** is effectively solved:
- Grid/table lookup: 100% up to 10×5
- Diagram decision-following: 100% across all complexity levels
- Simple bar chart value reading: 100%
- Multi-series charts at 2-3 series: 97-100%

### Where It Breaks Down

Failures cluster around three mechanisms, all driven by visual density:

1. **Series confusion in dense charts** — Grouped bar and line chart value reading degrade from ~100% at 2-3 series to ~50% at 9-10 series. The model correctly localizes the x position but attributes the value to the wrong series. Annotations make this worse for line charts (80% without labels vs 72% with) because the model grabs a nearby label from the wrong series.

2. **Arrow tracing through visual clutter** — In complex DAGs where multiple arrows converge on a shared terminal node, the model follows the wrong arrow. This is specific to the topology — cascaded decision nodes where 3+ leaf-branch arrows cross each other on the way to "End".

3. **Fine-grained character localization under overlay** — When a circle overlays text, the model localizes to the right general region but is off by one character ~70% of the time an error occurs. This is exacerbated by: (a) narrow characters whose circles become ambiguously thin, (b) lowercase characters flanked by visually dominant uppercase neighbors, and (c) word-level language priors that can override what the model actually sees in the image.

### Implications for Fine-Tuning

- **Multi-series chart training should sweep series count from 2 to 10+.** The 2-3 series case is solved; training signal comes from 5+ series where series attribution breaks down. Chain-of-thought grounding ("I see the green line labeled 'Wholesale'; at Apr it passes through 78") could force explicit label-line verification.
- **Diagram training should emphasize complex topologies** with converging arrows, not just linear/single-branch layouts where the model already excels.
- **Character-level localization tasks** would benefit from training on overlaid annotations (circles, arrows, highlights) at various sizes and positions, with emphasis on narrow characters and mixed-case strings that defeat language priors.
