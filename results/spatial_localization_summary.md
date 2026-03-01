# Spatial Localization — Evaluation Summary

## Primitive Definition

Can the model find a specific element in an image and report what's there? This includes reading a value from a specific cell, identifying a circled letter, reading a bar's value, or tracing which step follows another in a flowchart.

## Overall Performance

| Task | Accuracy | n | Notes |
|------|----------|---|-------|
| Table cell lookup | **100%** | 480 | 12 grid sizes × 2 styles × 2 prompt phrasings × 2 query sets |
| Diagram decision (Yes/No) | **100%** | 240 | Across all template complexities |
| Diagram next step | **94.2%** | 120 | All 7 errors in multi_decision template |
| Bar chart value (annotated) | **100%** | 40 | With value labels displayed |
| Bar chart value (unannotated) | 52.5% exact, **100% ≤2** | 40 | Pure estimation noise |
| Grouped bar value (annotated) | **100%** | 40 | With value labels displayed |
| Grouped bar value (unannotated) | 45.0% exact, **100% ≤2** | 40 | Pure estimation noise |
| Line chart value (annotated) | **90.0%** | 40 | 4 catastrophic errors from series confusion |
| Line chart value (unannotated) | 72.5% exact, **100% ≤2** | 40 | Pure estimation noise |
| Circled letter | **82.4%** | 624 | HuggingFace VLMs-are-Blind benchmark |

**Bottom line**: Spatial localization is largely solved for structured, clean layouts. Tables, simple diagrams, and annotated bar charts are at or near 100%. Failures emerge from three specific sources: visual clutter confusing series attribution, complex graph topology confusing edge tracing, and overlaid annotations degrading fine-grained character localization.

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
**Axes**: Chart type, show_values (True/False), show_grid (True), n_categories (3, 5, 7, 10), n_series (1–3 for line)

### Tiered Error Metrics (exact / ±1 / ±2)

**With value annotations (show_values=True):**

| Task | Exact | ≤1 | ≤2 | n |
|------|-------|-----|-----|---|
| Bar value | 100% | 100% | 100% | 40 |
| Grouped bar value | 100% | 100% | 100% | 40 |
| Line value | 90.0% | 90.0% | 90.0% | 40 |

**Without value annotations (show_values=False):**

| Task | Exact | ≤1 | ≤2 | n |
|------|-------|-----|-----|---|
| Bar value | 52.5% | 100% | 100% | 40 |
| Grouped bar value | 45.0% | 90.0% | 100% | 40 |
| Line value | 72.5% | 95.0% | 100% | 40 |

The key structural observation: without annotations, all errors are ≤2 — pure visual estimation noise. With annotations, bar/grouped are perfect (the model just reads the label), but line charts drop to 90% with errors that are *catastrophic* (off by 4–86), not estimation errors.

### Deep Dive: Series Confusion in Annotated Multi-Series Line Charts

All 4 line chart errors occur when `show_values=True` and `n_series ≥ 2`. Every error is a **series confusion**: the model identifies the correct x-axis point but reads the value from the wrong series' label.

| Image | Query | Ground truth | Model answer | Error | What happened |
|-------|-------|-------------|--------------|-------|---------------|
| `line_3x2_g1_v1_0` | Cost at Jan | 39 | 35 | 4 | Read Revenue (35) instead — labels stacked 4px apart |
| `line_3x2_g1_v1_0` | Cost at Jan | 39 | 35 | 4 | Same image, second prompt variant — same error |
| `line_5x3_g1_v1_4` | Wholesale at Apr | 78 | 64 | 14 | Read In-Store (64) instead |
| `line_10x3_g1_v1_1` | Wholesale at Jun | 90 | 4 | 86 | Read Online (4) instead — said "green line (Wholesale)" but grabbed wrong label |

The worst case (`line_10x3_g1_v1_1`) is especially revealing: the model's response explicitly says *"Looking at the green line (Wholesale)"* — correct series identification — but then reads value 4, which belongs to the blue Online line 86 units away. With 10 categories × 3 series = 30 data labels on the chart, the visual density overwhelms accurate label-to-line association.

The `line_3x2` case shows this can happen even on simple charts: at Jan, Revenue (blue, 35) and Cost (orange, 39) are only 4 units apart, with their value labels nearly touching. Both prompt variants fail identically, confirming a perceptual issue.

**Paradoxical finding**: `show_values=True` *hurts* accuracy on multi-series line charts (90%) compared to `show_values=False` (100% within ±2). Without labels, the model estimates from gridlines and gets it right. With labels, it sometimes grabs a nearby label from the wrong series — and since the label is an exact value from a different series, the error is catastrophic rather than gradual.

### Deep Dive: Visual Estimation Without Labels

When `show_values=False`, the model must estimate bar heights / line positions from the y-axis grid. All errors are small:

- **Bar charts**: 19 off-by-1 errors out of 40 (no off-by-2). Direction is balanced: 10 over-estimates, 9 under-estimates.
- **Grouped bar charts**: 18 off-by-1, 4 off-by-2. The off-by-2 cases involve very small ground truth values (5 and 8), where bars are short relative to the chart height.
- **Line charts**: 9 off-by-1, 2 off-by-2.

In 19 of 22 bar/grouped error-producing images, both prompt variants give the same wrong answer — the error is in the visual perception, not prompt interpretation.

An interesting non-monotonic pattern with `n_categories` (bar charts, exact match without labels):

| n_categories | Bar accuracy | Grouped accuracy |
|-------------|-------------|-----------------|
| 3 | 20% | 20% |
| 5 | **100%** | **90%** |
| 7 | 40% | 40% |
| 10 | 50% | 30% |

n_categories=3 is paradoxically the hardest (wider bars, coarser y-axis scale makes fine-grained estimation harder), while n_categories=5 is easiest (gridline spacing may align better with generated values). This pattern deserves further investigation but doesn't affect the core finding: **localization is 100% — the model always finds the right bar, it just can't estimate the exact pixel height.**

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

Spatial localization in **structured, unambiguous layouts** is effectively a solved capability for Haiku 4.5:
- Grid/table lookup: 100% up to 10×5
- Diagram decision-following: 100% across all complexity levels
- Chart element identification: 100% (the model always finds the right bar/line/point)

### Where It Breaks Down

Failures cluster around three mechanisms:

1. **Series/label attribution in dense charts** — When multiple value labels are visually proximate (especially in multi-series line charts), the model correctly localizes the x-axis position but grabs the wrong series' label. This produces catastrophic errors (off by 4–86) and, paradoxically, makes annotated charts *less* reliable than unannotated ones for multi-series contexts.

2. **Arrow tracing through visual clutter** — In complex DAGs where multiple arrows converge on a shared terminal node, the model follows the wrong arrow. This is specific to the topology — cascaded decision nodes where 3+ leaf-branch arrows cross each other on the way to "End".

3. **Fine-grained character localization under overlay** — When a circle overlays text, the model localizes to the right general region but is off by one character ~70% of the time an error occurs. This is exacerbated by: (a) narrow characters whose circles become ambiguously thin, (b) lowercase characters flanked by visually dominant uppercase neighbors, and (c) word-level language priors that can override what the model actually sees in the image.

### Implications for Fine-Tuning

- **Multi-series chart training data should include dense annotation layouts** with close-proximity data points. Chain-of-thought grounding ("I see three lines; the green line labeled 'Wholesale' passes through 90 at Jun") could force the model to verify label-line association explicitly.
- **Diagram training should emphasize complex topologies** with converging arrows, not just linear/single-branch layouts where the model already excels.
- **Character-level localization tasks** would benefit from training on overlaid annotations (circles, arrows, highlights) at various sizes and positions, with emphasis on narrow characters and mixed-case strings that defeat language priors.
