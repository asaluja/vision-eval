# Finetuning Plan for Haiku 4.5 Vision Capabilities

## Context

Evaluation across 8 perceptual primitives (~15K evals, 35+ JSONL files) reveals that Haiku 4.5's vision failures are not a continuum — they cluster into three mechanistically distinct regimes requiring different training strategies:

1. **OCR-as-crutch** (value-label conflict 0%, grid counting 50→100% with text): the model reads text instead of perceiving visuals
2. **Perceptual resolution limits** (path tracing, intersection detection, proximity, color discrimination, dense chart reading): degradation scales with visual complexity along smooth psychometric curves — all clearly in-distribution for practical tasks
3. **Memorized priors override vision** (logos 1.9% with 99.8% bias alignment, flags 40% with 83% bias, patterned grids 0% on add-anomaly): canonical knowledge short-circuits perception — though logos/flags are largely out-of-distribution for typical VLM use cases

Each regime needs a different training lever: SFT to establish new behaviors, DPO to calibrate perceptual judgments and override text reliance, RL to sharpen perceptual strategies. The priority ranking reflects practical impact: OCR-as-crutch silently affects every chart/table task, perceptual limits govern the hardest in-distribution failures, and memorized priors — while dramatic — primarily affect niche tasks (brand logos, flag elements) that rarely arise in production.

---

## Training Pipeline: Three Stages

### Stage 1: SFT — Visual Grounding (~300K examples, 2-3 epochs)

**Goal**: Break the OCR dependency. Teach the model to estimate visual quantities from pixel-level cues (gridlines, relative position, bar height) rather than defaulting to text.

| Data Category | Volume | Generator | Purpose |
|---|---|---|---|
| Charts WITHOUT value labels | 80K | `charts.py`, `show_values=False` only | Force visual bar/line height estimation |
| Pie charts WITHOUT % labels | 30K | `pie_charts.py`, `show_percentages=False` | Force angular/proportional estimation (53% baseline) |
| Charts with WRONG value labels | 40K | `text_visual_conflict.py`, `conflict_value_label` | Teach conflict detection and visual override |
| Blank grids (no coordinate text) | 30K | `grid_counting.py`, `with_text=False` | Force visual grid-line counting |
| Non-overlapping shape counting | 30K | `counting_shapes.py`, overlap ≤ 0.1, counts 3-12 | Basic counting without perceptual ambiguity |
| Clear proximity cases | 20K | `touching_circles.py`, dist ∈ {≤0, ≥0.2} | Establish baseline proximity judgment |
| Color grids (ΔL ≥ 10) | 15K | `color_discrimination.py` | Basic shade discrimination |
| Small/rotated text | 15K | `text_reading.py`, font 10-14, rot 30-90° | OCR fundamentals at limits |
| **Regularization: solved tasks** | **70K** | All generators at easy settings | **Prevent catastrophic forgetting** |

**Every SFT target includes chain-of-thought** that references visual landmarks, not text. Example for no-label chart:

> "The gridlines are at 0, 20, 40, 60, 80. The Apr bar extends to roughly halfway between 40 and 60. My estimate: {50}"

Example for wrong-label chart:

> "I see a label '36' above the bar, but comparing the bar height to the y-axis, it reaches approximately 52. The label appears incorrect. {52}"

**Curriculum across Stage 1**:
- Weeks 1-2: 100% no-label charts (force pure visual estimation)
- Weeks 3-4: 80% no-label + 20% wrong-label (introduce conflict detection)
- Weeks 5-6: 60% no-label + 20% wrong-label + 20% correct-label (restore normal text+visual integration)

The reintroduction of correct labels is critical — we don't want a model that ignores all text, we want one that *verifies* text against visual evidence.

---

### Stage 2: DPO — Bias Override and Perceptual Calibration (~75K pairs, 1 epoch)

**Goal**: Override memorized priors with visual evidence. Use high-quality preference pairs where the model's biased answer is consistently wrong.

| Source | Pairs | Signal Quality | Construction |
|---|---|---|---|
| Board game non-canonical dims | 15K | **Excellent** (100% bias alignment, 0 variance) | Chosen: explicit count. Rejected: canonical dim. |
| Patterned grid add-anomaly | 10K | **Excellent** (0% accuracy) | Chosen: actual count. Rejected: pattern-expected count. |
| Olympic-layout circles (count ≠ 5) | 8K | Good (22% bias rate) | Chosen: correct count. Rejected: "5". |
| Touching circles at threshold | 12K | Good (0% at threshold distances) | Chosen: "No" (separated). Rejected: "Yes" (touching). |
| Color grid ΔL=5-10 | 10K | Good (18-88% accuracy) | Chosen: correct cell. Rejected: wrong cell. Per-family balanced. |
| Value-label conflict | 10K | **Excellent** (0% accuracy) | Chosen: visual estimate. Rejected: text label value. |
| Annotation conflict (gap < 15) | 5K | Moderate (75% accuracy) | Chosen: actual max bar. Rejected: annotated bar. |
| Path following overcounts | 5K | Good (97% of errors are overcounts) | Chosen: target path count. Rejected: total path count. |

**Extended thinking doesn't help bias override.** Re-running board games and patterned grids with `--thinking --thinking-budget 2048` produced no improvement (+1.6pp grids, -0.5pp boards). This confirms the failure is perceptual, not reasoning — the model can't see the deviation from the memorized pattern regardless of how much it thinks. Implication: DPO is the right lever here, not chain-of-thought. The model needs to learn to *count* rather than *recall*, and that requires training signal, not inference-time compute.

**Why board games are the single best DPO source**: 100% bias alignment with zero variance across 400 evaluations means every non-canonical instance produces a perfectly clean preference pair — no noise, no ambiguity, no edge cases. The chosen response always includes explicit counting ("1, 2, 3, 4, 5, 6, 7 — that's 7 rows"), teaching the model to count before answering. The rejected response always pattern-matches ("chess board = 8 rows").

**Critical safeguard**: Include canonical-dimension boards (8×8 chess, 19×19 Go) in the training set where both chosen and rejected demonstrate counting — the chosen response counts and gets the canonical number, the rejected gets it wrong. This prevents the model from learning "always say non-canonical."

---

### Stage 3: RL with Verifiable Rewards (~175K episodes, 500-1000 steps × batch 256)

**Goal**: Sharpen perceptual strategies via reward-shaped exploration. All tasks here have exactly computable ground truth.

| Task | Volume | Reward Function | Curriculum |
|---|---|---|---|
| Overlapping shape counting | 50K | `R=1.0` exact, `0.5` if ±1, `0.0` else | overlap 0.1 → 0.5 |
| Pie value estimation (no labels) | 20K | `R=1.0` within ±2pp, `0.5` within ±5pp, `0.0` else | n_slices 3 → 8 |
| Pie slice comparison (no labels) | 15K | `R=1.0` correct, `0.0` else | gap between top-2 slices: 15pp → 3pp |
| Path following (distractor) | 40K | `R=1.0` exact, `0.0` else (answer space is 1-3) | total_connections 2 → 6 |
| Line intersection | 30K | `R=1.0` exact, `0.3` if ±1, `+0.2` bonus if GT=0 ∧ pred=0 | 3-point → 5-point |
| Dense chart value reading | 40K | `R=1.0` within tolerance, `0.5` within 2× tolerance | n_series 3 → 10 |
| Small rotated numbers | 15K | `R=1.0` exact, `0.0` else | font 20 → 10 |

**Key design choices**:
- **Partial credit for counting** (0.5 for ±1): prevents reward sparsity at high counts where exact match is genuinely hard
- **No partial credit for path following**: answer space is tiny (1-3), model must learn endpoint tracing not approximate counting
- **Anti-false-positive bonus for intersections** (+0.2 for correct GT=0): directly targets the dominant failure mode (63.5% false-positive rate at GT=0 in HF)
- **All curricula start where the model already succeeds** (~90%+ accuracy), providing warm reward signal before pushing into failure regimes
- Temperature sampling during rollouts; 500-token response cap to prevent reward hacking

---

## Deep Dive: Visual Grounding (the OCR-as-Crutch Problem)

This is the highest-leverage failure because it's not an isolated task — it's an *architectural behavior* that silently affects every chart, table, and document task. When text is correct, OCR-reliance produces correct answers (masking blindness). When text is wrong or absent, it collapses.

### Evidence Chain

| Finding | Accuracy | What It Proves |
|---|---|---|
| Value-label conflict | 0% (100% text-reliant) | Model reads label, never estimates bar height |
| Grid counting with/without text | 100% vs 49% | 51pp gap = model reads coordinates, doesn't count lines |
| Line chart show_values=True vs False | 72% vs 80% | Labels *hurt* because model grabs wrong-series label |
| Chart axis label reading | 100% at font 7px | Model can OCR tiny text — this is its primary strategy |

### Sample Training Data Generation

I would extend the existing `text_visual_conflict.py` generator. Here's concretely what the training instances look like:

**Type A: No-label bar chart (SFT)**

```python
# Generate: 5-bar chart, gridlines at 0/20/40/60/80, no value annotations
# Ground truth: Product C = 73 (bar height between 60 and 80 gridlines)
#
# SFT target response:
# "Looking at the Product C bar relative to the y-axis gridlines.
#  The gridlines are at 0, 20, 40, 60, and 80. The top of the
#  Product C bar is about two-thirds of the way between the 60
#  and 80 gridlines. I estimate approximately 73. {73}"
#
# Scoring: tolerance = max(2, 73 * 0.05) = 3.65 → accepts 69-77
```

**Type B: Wrong-label bar chart (SFT + DPO)**

```python
# Generate: 4-bar chart, Jan bar visual height = 82, displayed label = "55"
# Ground truth: 82 (visual), text_answer: 55 (wrong label)
#
# SFT target response:
# "I see a text label showing '55' above the Jan bar. However,
#  looking at the actual bar height against the y-axis — the
#  gridlines are at 0, 20, 40, 60, 80 — the bar clearly extends
#  just above the 80 line. The label does not match the visual.
#  Based on bar height: {82}"
#
# DPO chosen (same as SFT target): "{82}" with visual reasoning
# DPO rejected (actual model output): "{55}" — reads label directly
#
# Scoring: tolerance = max(2, 82 * 0.05) = 4.1 → accepts 78-86
# text_reliant check: |extracted - 55| ≤ 2 → True = model read label
```

**Type C: No-label line chart, multiple series (RL)**

```python
# Generate: 7-series line chart, no annotations, gridlines every 20
# Query: "What is the value of Wholesale for Apr?"
# Ground truth: 64
#
# RL reward function:
def reward(response, gt=64, metadata={}):
    extracted = extract_number(response)
    if extracted is None:
        return 0.0
    error = abs(extracted - gt)
    tolerance = max(2, gt * 0.05)  # = 3.2

    # Primary: accuracy
    if error <= tolerance:       # 61-67
        r = 1.0
    elif error <= 2 * tolerance: # 58-70
        r = 0.5
    else:
        r = 0.0

    # Bonus: visual reasoning present
    visual_cues = ["gridline", "y-axis", "extends to", "between"]
    if any(cue in response.lower() for cue in visual_cues):
        r += 0.1

    return min(1.0, r)

# Why tolerance-based: the model must visually interpolate between
# gridlines. Demanding exact match would be unfair — even humans
# estimate. The 5%-or-2 tolerance matches what we already use in
# evaluate/score.py, ensuring training and eval metrics align.
```

### Why This Scoring Approach

The reward function for visual grounding has three deliberate design choices:

1. **Tolerance-based primary reward** (not exact match): Bar heights must be visually interpolated between gridlines. A model that correctly identifies the bar is between 60 and 80, closer to 80, and answers 75 instead of 73 should not receive zero reward. The ±5% tolerance from `score.py` is already calibrated against human estimation error.

2. **Bonus for visual reasoning** (+0.1): We want the model to develop and articulate a visual estimation strategy. Responses that reference gridlines, axis positions, or relative heights demonstrate the model is actually looking at the image rather than pattern-matching or guessing. This bonus is small enough not to dominate the accuracy signal but large enough to break ties.

3. **No negative reward for text-reliance in RL** (unlike the DPO signal): In the RL setting, show_values=False means there are no labels to read. If the model hallucinates a label, it will simply get the wrong number and receive low accuracy reward. The text-reliance penalty is only needed in the DPO setting where wrong labels are present and the model must actively resist reading them.

### Expected Outcomes

| Metric | Before | After Stage 1 | After All 3 |
|---|---|---|---|
| Value-label conflict accuracy | 0% | 60-80% | 75-85% |
| Value-label text-reliant rate | 100% | 10-20% | 5-10% |
| Grid counting (blank) | 49% | 75-85% | 80-90% |
| Chart value (no labels, ≤5 series) | ~85% | 90-95% | 92-97% |
| Chart value (no labels, 8-10 series) | ~50% | 55-65% | 65-75% |
| Pie value estimate (no % labels) | 53% | 65-75% | 70-80% |
| Pie slice comparison (no % labels) | 73% | 80-85% | 85-90% |

The residual gap (not reaching 100%) is genuine visual estimation error — even with perfect grounding, interpolating between gridlines or estimating angular proportions has irreducible noise. Pie charts have a wider residual gap than bars because angular estimation is perceptually harder than height estimation.

---

## Per-Primitive Training Budget Summary

| Primitive | Primary Stage | SFT | DPO | RL | Expected Lift |
|---|---|---|---|---|---|
| **Text-Visual Consistency** (grounding) | Stage 1 | 70% | 20% | 10% | 0% → 75% (value-label) |
| **Prior Bias Override** | Stage 2 | 10% | 80% | 10% | 60% → 90% (board games) |
| **Counting/Enumeration** | Stage 3 | 30% | 10% | 60% | 62% → 80% (overlapping shapes) |
| **Line/Path Following** | Stage 3 | 20% | 10% | 70% | 52% → 70% (distractor paths) |
| **Spatial Localization** | Stages 1+3 | 50% | 0% | 50% | 75% → 85% (dense charts) |
| **Relative Comparison** | Stage 2 | 20% | 60% | 20% | 60% → 80% (touching circles) |
| **Color Discrimination** | Stage 2 | 20% | 60% | 20% | 18% → 45% (extreme ΔL) |
| **Text Reading** | Stage 1 | 80% | 0% | 20% | 0% → 40% (font10+rot90 numbers) |

---

## Holdout Evaluation Protocol

Reserve 20% of parameter space per generator for held-out test:

- Charts: hold out n_categories=9, n_series=7
- Board games: hold out 10×10 chess, 17×17 Go (novel dimensions beyond ±1)
- Touching circles: hold out dist=0.035, dist=0.075 (interpolation)
- Color grids: hold out "purples" family entirely
- Path following: hold out total_connections=5 with target=2
- Pie charts: hold out n_slices=7 (interpolation between trained 6 and 8)

**Regression monitoring**: After each stage, run full eval via `python run_phase1.py --eval-only --workers 10` across all tasks. Critical regression gates:
- Table cell lookup must remain 100%
- Diagram decision following must remain 100%
- Simple bar chart (with correct labels) must remain ≥98%

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Catastrophic forgetting on solved tasks | Medium | High | 70K regularization examples in Stage 1; regression gates after each stage |
| DPO over-correction (always say non-canonical) | Low-Medium | Medium | Include canonical boards in chosen set; both chosen/rejected demonstrate counting |
| Vision encoder resolution is the hard limit | High for proximity/color | Low (we set realistic targets) | Focus budget on LM-side failures (grounding, bias); accept ceilings on encoder-limited tasks |
| CoT training increases latency 3-5× | Medium | Medium | Post-training distillation to compress reasoning; or RL to reward concise correct responses |
| Synthetic rendering artifacts cause overfitting | Low-Medium | Medium | Diversify backends (matplotlib, Plotly, PIL); augment with JPEG compression, DPI jitter, color noise |
| Unknown encoder architecture | Certain | Variable | If possible, finetune encoder jointly; if not, accept encoder-limited ceilings |

---

## Implementation: What to Build

The existing generator infrastructure (`generate/*.py` + `evaluate/score.py`) covers ~80% of what's needed. Extensions required:

1. **SFT response generator**: Script that takes TaskInstance + ground_truth and produces CoT target responses with visual reasoning language
2. **DPO pair formatter**: Script that reads `*_results.jsonl`, filters by `bias_aligned=True` or `text_reliant=True`, and emits `(chosen, rejected)` pairs
3. **RL reward functions**: Module implementing the reward functions above, compatible with whatever RL framework is used internally
4. **Curriculum scheduler**: Config that controls difficulty ramp across training steps
5. **Scale-up generation**: Increase `n_per_config` from current 2-10 to 50-200 for training-scale data volumes
