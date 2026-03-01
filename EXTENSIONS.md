# Extensions: Synthetic Image Pairs

## Motivation

All current evaluation tasks use **single images**. Image pairs are a fundamentally different evaluation paradigm: show two nearly identical images and ask the model to identify or reason about the difference. This is higher-value than single-image tasks because:

1. **Directly generates finetuning data** — every pair where CLIP can't see the difference and Haiku gets it wrong is a contrastive training example
2. **Start from what matters, verify it's a blind spot** — unlike natural-image approaches (MMVP) where you find blind spots and then figure out why they matter
3. **CLIP embedding analysis adds rigor** — pairs designed so CLIP cosine similarity is high (semantically identical) but the perceptual difference is task-critical

## Status

- [x] **Chart data match** (`generate/chart_comparison.py`) — same data rendered as different chart types, ask if values match. First implementation of this paradigm.
- [ ] Everything below is future work.

## Per-Primitive Pair Types

### 1. Relative Comparison in Charts (HIGHEST PRIORITY)

Most common real-world question, small visual delta, CLIP almost certainly blind to it.

- Two bar charts identical except bar A is slightly taller than bar B in one, and slightly shorter in the other
- Two line charts where the red line crosses above/below the blue line at different points
- "Which is bigger?" with a small delta is exactly where CLIP says "same image"

### 2. Text/Number Changes in Documents (HIGH PRIORITY)

Directly tests whether the model reads or hallucinates values.

- Same form, but the dollar amount is $1,234 vs. $1,284
- Same chart, but the y-axis label says "Revenue ($M)" vs. "Revenue ($K)"
- Same slide, but a bullet point says "increased" vs. "decreased"

### 3. Count Changes in Charts/Diagrams (HIGH PRIORITY)

Fundamental and easy to generate at scale.

- Same chart layout, 5 bars vs. 6 bars
- Same scatter plot, 8 points vs. 9 points
- Same diagram, 4 nodes vs. 5 nodes
- Perfect CLIP traps — overall composition is identical, only the count changes

### 4. Spatial Localization

- Same table, but the highlighted cell is at (2,3) vs. (2,4)
- Same bar chart, but the tallest bar is the 3rd vs. the 4th
- Same UI mockup, but the error icon is next to a different field

### 5. Color Discrimination

- Same chart, but the legend maps blue->Revenue, red->Cost in one and colors are swapped in the other
- Same heatmap, but one cell is slightly darker
- Same dashboard, green status indicator vs. yellow

### 6. Line / Path Following

- Same flowchart structure, but the "Yes" branch goes left in one and right in the other
- Same line chart, but the trend goes up at the end vs. down
- Same network diagram, but one edge is rerouted

### 7. Prior / Bias Override

- Standard 8x8 chessboard vs. 9x8 chessboard
- Standard die face with 6 dots vs. 7 dots
- CLIP will almost certainly conflate these — it's seen millions of chessboards and "knows" what one looks like

---

# Extended Thinking Experiments

## Prior / Bias Override with Extended Thinking

The prior/bias override primitive tests whether the model reports what it sees vs. what it "knows" (e.g., 9×8 chessboard, die with 7 dots). Extended thinking may help the model override memorized defaults by giving it space to count carefully before committing to an answer.

- [x] Ran with `--thinking --thinking-budget 2048`

### Results

| Task | Baseline | Thinking | Delta |
|------|----------|----------|-------|
| Patterned grid | 15.5% | 17.1% | +1.6pp |
| Board games | 60.0% | 59.5% | -0.5pp |

**Extended thinking makes no difference.** The `_add` anomaly subtasks stay at 0%, canonical dimensions stay at 100%, and off-by-one board dimensions stay at 50%. This confirms the bias override failure is **perceptual, not reasoning** — the model can't see the extra dot or extra row regardless of how much it thinks about it. More thinking budget won't help when the visual representation itself doesn't encode the deviation from the memorized default.

---

## Implementation Notes (Image Pairs)

- Each pair type needs its own generator in `generate/`
- Ground truth is typically Yes/No ("are these the same?") or a specific difference description
- The `chart_comparison.py` generator can serve as a template for the side-by-side composite image pattern
- CLIP/DINOv2 embedding scores can be computed post-hoc on generated pairs to validate that they are indeed "CLIP traps" (high CLIP sim, low DINOv2 sim)
- For finetuning: pairs where Haiku fails become contrastive training examples — show both images, teach the model to articulate the difference
