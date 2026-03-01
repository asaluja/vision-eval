# Line / Path Following — Evaluation Summary

## Primitive Definition

Can the model trace paths, follow connections, and identify where lines lead? This spans subway-style route tracing, line intersection counting, trend detection in line charts, and step-by-step navigation through flowcharts.

## Key Finding

**Path tracing degrades sharply when distractor paths are present — the model cannot selectively trace which paths connect a specific pair of stations, overcounting by including irrelevant connections. Line intersection detection collapses with polyline complexity. Trend detection is strong (94.8%) when prompted for a specific series but degrades to 81% with 10 overlapping lines — a visual clutter effect consistent with path tracing failures.**

## Tasks Evaluated

### Ceiling Tasks (≥98% accuracy)

| Task | Accuracy | n | Source | Notes |
|------|----------|---|--------|-------|
| Diagram decision following | 100% | 300 | Generated | All templates, all complexities |
| Diagram next-step (excl. multi_decision) | 100% | 150 | Generated | Linear, single_branch, asymmetric |
| Chart line trend (2-4 series) | 100% | 192 | Generated | Specific series named in prompt |

Diagram tasks involve following explicitly labeled arrows between discrete nodes. Trend detection with few series is also ceiling-level when the target series is specified by name — these are fundamentally different from tracing continuous paths through visual clutter.

### Degrading Tasks

---

#### 1. Path Following (Subway Maps)

**Overall**:

| Source | Mode | Accuracy | n |
|--------|------|----------|---|
| Generated | Simple (all paths A→B) | 73.3% | 60 |
| Generated | Distractor (mixed connections) | 56.2% | 80 |
| HF Blind | Distractor (mixed connections) | 51.7% | 720 |

**Simple mode — by path count**:

| n_paths | Accuracy | n |
|---------|----------|---|
| 1 | 100% | 10 |
| 2 | 100% | 10 |
| 3 | 100% | 10 |
| 4 | 50% | 10 |
| 5 | 60% | 10 |
| 6 | 30% | 10 |

Perfect for 1–3 paths. Sharp degradation at 4+ where paths overlap visually.

**Distractor mode — by (total_connections, target_paths)**:

| Total connections | target=1 | target=2 | target=3 |
|-------------------|----------|----------|----------|
| 2 | 90% (9/10) | 100% (10/10) | — |
| 4 | 40% (4/10) | 60% (6/10) | 80% (8/10) |
| 6 | 10% (1/10) | 30% (3/10) | 40% (4/10) |

**HF VLMs-are-Blind — by (total_connections, ground_truth)**:

| Total connections | gt=1 | gt=2 | gt=3 |
|-------------------|------|------|------|
| 2 | 83% (200/240) | — | — |
| 4 | 39% (37/96) | 41% (59/144) | — |
| 6 | 25% (26/104) | 28% (34/120) | 100% (16/16) |

**Synthetic distractor results align closely with HF**, confirming the generator now captures the critical difficulty dimension.

**Error pattern**: Errors are **overwhelmingly overcounts** — 34 of 35 distractor errors are overcounts, 1 undercount. The model counts paths that connect to other stations, not just the queried pair. In HF gt=1 errors, the modal answer is 2 (125 of 177 errors), then 3 (37 errors). The model is not randomly guessing — it's failing to filter by endpoint.

**Root cause**: The model can perceive individual paths but cannot trace them from start to end to verify which stations they connect. When multiple paths visually overlap or cross, it defaults to counting total visible paths rather than selectively tracing endpoint connectivity.

---

#### 2. Line Intersection Counting

**Overall**:

| Source | Accuracy | n |
|--------|----------|---|
| Generated (3-point lines) | 85.0% | 60 |
| Generated (4-point lines) | 32.5% | 40 |
| Generated (5-point lines) | 18.0% | 50 |
| HF Blind (3-point lines) | 64.6% | 3600 |

**Synthetic by (n_points, ground_truth)**:

| Complexity | gt=0 | gt=1 | gt=2 | gt=3 | gt=4 |
|------------|------|------|------|------|------|
| 3-point | 75% (15/20) | 80% (16/20) | 100% (20/20) | — | — |
| 4-point | 20% (2/10) | 50% (5/10) | 30% (3/10) | 30% (3/10) | — |
| 5-point | 0% (0/10) | 30% (3/10) | 40% (4/10) | 10% (1/10) | 10% (1/10) |

**HF by ground truth (3-point lines only)**:

| gt | Accuracy | n |
|----|----------|---|
| 0 | 36.5% (438/1200) | 1200 |
| 1 | 71.1% (853/1200) | 1200 |
| 2 | 86.1% (1033/1200) | 1200 |

**The dominant failure mode is hallucinating intersections at gt=0.** When lines don't intersect:
- 3-point synthetic: 25% error rate, model says 1 (4 times) or 2 (1 time)
- 4-point synthetic: 80% error rate, model says 2 (8 of 8 errors)
- 5-point synthetic: 100% error rate, model says 2 (5), 3 (4), or 1 (1)
- HF gt=0: 63.5% error rate, model says 1 (456 times) or 2 (304 times)

The false positive rate increases monotonically with polyline complexity. At 5-point lines, the model *always* reports intersections even when there are none — it appears to interpret visual proximity of line segments as crossing.

**Synthetic vs HF gap for 3-point**: Our synthetic (84.4%) outperforms HF (64.6%) because HF has 1,200 gt=0 instances (vs our 20), and gt=0 is the hardest case. The HF's larger gt=0 sample reveals a stronger false-positive bias than our smaller sample captures.

---

#### 3. Chart Line Trend Detection

**Prompt fix context:** The original prompt asked about "the overall trend" without specifying which series, yielding 65.2% accuracy. After fixing the prompt to ask about a **specific named series** (e.g., "Is the trend of Revenue increasing or decreasing?"), accuracy jumped to 94.8%. The ambiguity, not the perception, was the primary failure mode. All results below use the fixed prompt.

| Metric | Value |
|--------|-------|
| Overall accuracy | **94.8%** (546/576) |

**By n_series** (number of lines in the chart):

| n_series | Accuracy | n |
|---------|----------|---|
| 2 | 100% | 64 |
| 3 | 100% | 64 |
| 4 | 100% | 64 |
| 5 | 96.9% | 64 |
| 6 | 93.8% | 64 |
| 7 | 96.9% | 64 |
| 8 | 90.6% | 64 |
| 9 | 93.8% | 64 |
| 10 | 81.2% | 64 |

**Perfect at 2-4 series, degrades with visual clutter.** At 10 series (81%), the chart becomes a dense tangle of overlapping lines where isolating a single named series requires path-tracing ability — the same skill that fails in subway maps.

**By n_categories** (x-axis data points):

| n_categories | Accuracy | n |
|-------------|----------|---|
| 3 | 92.4% | 144 |
| 5 | 97.2% | 144 |
| 7 | 95.8% | 144 |
| 10 | 93.8% | 144 |

Relatively flat across x-axis point counts. The n_categories=3 dip (92.4%) reflects that 3 data points provide weaker visual trend signal — a line through 3 noisy points can look ambiguous.

**Accuracy heatmap: n_series × n_categories:**

| n_series | nc=3 | nc=5 | nc=7 | nc=10 |
|---------|------|------|------|-------|
| 2-4 | 100% | 100% | 100% | 100% |
| 5-7 | 94% | 100% | 96% | 94% |
| 8-10 | 83% | 92% | 92% | 88% |

Errors concentrate in the **high n_series + low n_categories** corner — many overlapping lines with few data points. This is where visual isolation of a single series is hardest and trend signal is weakest.

**Error pattern**: All 30 errors are clean direction misclassifications (no extraction failures). The model identifies the correct series but misreads its direction, likely because overlapping lines with similar trajectories create visual interference.

---

#### 4. Diagram Next-Step (Multi-Decision Only)

| Template | Accuracy | n |
|----------|----------|---|
| linear | 100% | 60 |
| single_branch | 100% | 60 |
| asymmetric | 100% | 30 |
| multi_decision | 76.7% | 30 |

7 errors, all in multi_decision templates. 6 of 7 share the same root cause: the model misidentifies which node a leaf-branch arrow points to when multiple arrows converge on the "End" node. The arrows travel diagonally across the diagram, crossing other arrows — making it ambiguous which destination an arrow reaches. (1 error is an extraction bug where the regex grabs a braced value from reasoning rather than the final answer.)

---

## Cross-Task Patterns

1. **Selective tracing is the core blind spot.** Whether it's tracing which subway paths connect specific stations, or determining whether two lines actually cross vs merely come close, the model struggles to follow continuous paths through visual clutter. It defaults to counting everything visible rather than selectively filtering.

2. **Overcounting is the dominant error direction.** Path following: 97% of distractor errors are overcounts. Line intersection: the model hallucinates crossings at gt=0. The model has a strong prior that visual complexity implies more connections/crossings.

3. **Discrete, labeled navigation is solved; continuous path tracing is not.** Diagram decision-following (100%) uses labeled arrows between discrete boxes. Subway path tracing through overlapping colored lines fails at 4+ total connections. The difference is whether the model must visually follow a continuous line vs read a label on a discrete arrow.

4. **Trend detection is strong when the target series is specified (94.8%), but degrades with line clutter.** The original 65.2% result was a prompt ambiguity artifact — "overall trend" was underspecified when multiple series trend in different directions. With a specific series named, accuracy is near-ceiling at 2-4 series (100%) but drops to 81% at 10 series, revealing that trend detection at high visual complexity is fundamentally a path-isolation problem.

5. **Visual clutter is the universal difficulty axis.** More connections hurt path tracing (90-100% at 2 → 10-40% at 6). More series hurt trend detection (100% at 2-4 → 81% at 10). More line segments hurt intersection counting (84% at 3-point → 18% at 5-point). The common thread: when multiple lines overlap, the model cannot reliably isolate individual paths.

## Finetuning Implications

- **Path following training should emphasize distractor paths.** Simple all-same-endpoint configurations are solvable. Training data needs mixed connections between 4+ stations, with 4-6 total paths, forcing the model to trace endpoints rather than count everything visible.
- **Chain-of-thought for path tracing**: Encourage sequential tracing: "The red path starts at C, goes right to..., and ends at A. The blue path starts at B..." This explicit endpoint verification could overcome the default overcounting behavior.
- **Line intersection training needs gt=0 emphasis.** The false-positive bias (hallucinating crossings) is the primary failure mode. Training on complex polylines that come close but don't intersect would directly target this.
- **Trend detection training should focus on high-series-count charts (8-10 lines).** With a specific series named, accuracy is already 100% at 2-4 series. The remaining gap (81% at 10 series) is a visual isolation problem — training should emphasize identifying and tracing a single named series through dense line clutter.
