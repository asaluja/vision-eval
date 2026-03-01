---
name: eval-primitive
description: Evaluate a perceptual primitive for Haiku 4.5 vision evaluation (generate, eval, analyze)
argument-hint: <primitive_name>
---

Evaluate the perceptual primitive specified by `$ARGUMENTS`.

Valid primitive names:
- `line_path_following`
- `relative_comparison`
- `color_discrimination`
- `text_reading`
- `prior_bias_override`

(Already completed: `counting_enumeration`, `spatial_localization`)

## Workflow

When this skill is invoked with a primitive name, follow these steps **in order**. Each step ends with an explicit checkpoint — **STOP and ask the user for approval before proceeding to the next step.**

### Step 1: Display the Task Inventory

Print the full task inventory for the requested primitive from the table below. For each task, show:
- Task name and whether it's synthetic or HF benchmark
- Primary axes of variation
- Recommended n_per_config for robust coverage
- Whether results already exist (check `results/` directory) and how many

Also compute the **estimated total instance count** based on the axes of variation and n_per_config, so the user understands the scope.

**CHECKPOINT 1**: Ask the user:
- Are the tasks and axes correct?
- Do they want to adjust n_per_config or skip any tasks?
- Confirm they want to proceed to generation.

**Do NOT proceed to Step 2 until the user confirms.**

### Step 2: Generate Synthetic Images

Run generation using `run_phase1.py`:
```bash
cd /Users/asaluja/Documents/Job_Search/anthropic/vision-eval
source .venv/bin/activate && python run_phase1.py --generate-only --n <N> --tasks <task_list>
```

After generation completes, report:
- Number of instances generated per task_type
- Total images created
- Sample a few image paths so the user can spot-check visually if desired

**CHECKPOINT 2**: Ask the user:
- Do the generation counts look right?
- Do they want to spot-check any images before proceeding?
- Confirm they want to proceed to evaluation (this will make API calls and cost credits).
- How many workers to use (default 10)? Higher = faster but more concurrent API calls.
- For multi-task generators (e.g. `chart` produces 9 task_types), should we evaluate all task_types or filter to only the ones relevant to this primitive? Filtering saves API credits but means re-generating later for other primitives.

**Do NOT proceed to Step 3 until the user confirms.**

### Step 3: Evaluate with API

Run evaluation on synthetic. Use the worker count the user selected:
```bash
source .venv/bin/activate && python run_phase1.py --eval-only --tasks <task_list> --workers <N>
```

If the user chose to filter a multi-task generator to specific task_types, create a filtered instances file first:
```python
# Filter e.g. chart_instances.jsonl to only chart_line_trend
import json
with open('results/chart_instances.jsonl') as fin, open('results/<filtered>_instances.jsonl', 'w') as fout:
    for line in fin:
        d = json.loads(line)
        if d['task_type'] in TARGET_TYPES:
            fout.write(line)
```
Then evaluate the filtered file using `load_instances()` + `run_evaluation()` directly.

If HF benchmarks apply, also run:
```bash
source .venv/bin/activate && python run_benchmarks.py --dataset <blind|biased> --tasks <hf_tasks> --workers <N>
```

After evaluation completes, report:
- Raw accuracy numbers per task_type (quick summary table)
- Total instances evaluated and API calls made
- Any errors or failures during evaluation

**CHECKPOINT 3**: Ask the user:
- Do the raw numbers look reasonable?
- Any task_types they want to re-run or investigate before full analysis?
- Confirm they want to proceed to the full analysis and summary writeup.

**Do NOT proceed to Step 4 until the user confirms.**

### Step 4: Analyze & Write Summary

After the user confirms:
1. Load the results JSONL files from `results/`
2. Compute accuracy breakdowns by task_type, subtask, and key metadata axes
3. Identify ceiling tasks (100%) vs degrading tasks
4. Deep-dive into error patterns for degrading tasks (examine individual responses for systematic patterns)
5. Write a summary markdown to `results/<primitive_name>_summary.md` following the format of the existing summaries (see `results/counting_enumeration_summary.md` and `results/spatial_localization_summary.md`)

Present the summary to the user for review. This is the final output — no further checkpoint needed.

---

## Primitive Task Inventories

### 1. `line_path_following`

**Definition**: Can the model trace paths, follow connections, and identify where lines lead?

#### Synthetic Tasks

| Task | Generator | task_type in registry | Primary Axes | Recommended n |
|------|-----------|----------------------|--------------|---------------|
| Subway path counting | `path_following` | `path_following` | n_paths: [1,2,3,4,5,6] | 3 |
| Line intersection counting | `line_intersection` | `line_intersection` | n_intersections: [1,2,3,4,5] | 3 |
| Line chart trend detection | `chart` | `chart_line_trend` | n_categories: [3,5,7,10], n_series: [1,2,3] | 2 |
| Diagram next-step tracing | `diagram` | `diagram_next_step` | template: [linear, single_branch, asymmetric, multi_decision], n_steps: [3,5,7] | 2 |
| Diagram decision following | `diagram` | `diagram_decision` | template: [single_branch, asymmetric, multi_decision], n_steps: [3,5,7] | 2 |

#### HF Benchmark Tasks

| Dataset | HF Task Name | Our task_type |
|---------|-------------|---------------|
| VLMs-are-Blind | "Subway Connections" | path_following |
| VLMs-are-Blind | "Line Plot Intersections" | line_intersection |

#### Key Axes of Variation
- **Path count** (1-6): More paths = more visual clutter, harder to distinguish
- **Intersection count** (1-5): More crossings = harder to count
- **Diagram topology**: Linear (trivial) → multi_decision (hard, convergent arrows)
- **Trend ambiguity**: Clear monotonic vs noisy/flat trends

#### Commands
```bash
# Generate
python run_phase1.py --generate-only --n 3 --tasks path_following line_intersection chart diagram

# Evaluate synthetic
python run_phase1.py --eval-only --tasks path_following line_intersection chart diagram --workers 10

# Evaluate HF
python run_benchmarks.py --dataset blind --tasks path_following line_intersection --workers 10
```

**Note**: The `chart` and `diagram` generators produce multiple task_types each. For this primitive, focus analysis on: `path_following`, `line_intersection`, `chart_line_trend`, `diagram_next_step`, `diagram_decision`.

---

### 2. `relative_comparison`

**Definition**: Can the model compare two visual elements and determine which is larger/higher/closer/more?

#### Synthetic Tasks

| Task | Generator | task_type | Primary Axes | Recommended n |
|------|-----------|-----------|--------------|---------------|
| Bar height comparison | `relative_comparison` | `chart_bar_compare` | value_diff: [1,2,5,10,20,40], n_bars: [4,6,8], show_grid: [T/F] | 2 |
| Line series comparison | `relative_comparison` | `chart_bar_compare` | n_points: [5,8], value_gap (emergent) | 3 |
| Highest bar identification | `chart` | `chart_bar_compare` | n_categories: [3,5,7,10] | 2 |
| Table max value | `table` | `table_max` | n_rows: [3,5,7,10], n_cols: [2,3,5] | 2 |
| Touching/proximity detection | `touching_circles` | `touching_circles` | distance: [-0.4,-0.2,0,0.2,0.4,0.6], radius: [30,50] | 3 |

#### HF Benchmark Tasks
None directly applicable.

#### Key Axes of Variation
- **Value difference** (1-40): Critical axis. Diff=1 is near-threshold; diff=40 is trivial
- **Show grid**: Gridlines should help estimation but may not affect comparison
- **Number of distractors**: More bars/points = more visual clutter
- **Chart type**: Bar (discrete, easy) vs line (continuous, harder at crossing points)
- **Proximity distance** (-0.4 to 0.6): Negative = overlapping, 0 = touching, positive = separated. Tests fine-grained spatial discrimination.

#### Commands
```bash
# Generate
python run_phase1.py --generate-only --n 3 --tasks relative_comparison chart table touching_circles

# Evaluate
python run_phase1.py --eval-only --tasks relative_comparison chart table touching_circles --workers 10
```

**Note**: Filter analysis to task_types: `chart_bar_compare`, `table_max`, `touching_circles`. The `chart` generator's `chart_bar_compare` tasks use natural data (highest bar), while `relative_comparison` generator uses controlled value diffs.

---

### 3. `color_discrimination`

**Definition**: Can the model distinguish colors, match legend entries to data series, and detect shade differences?

#### Synthetic Tasks

| Task | Generator | task_type | Primary Axes | Recommended n |
|------|-----------|-----------|--------------|---------------|
| Legend-to-bar matching (distinct colors) | `color_discrimination` | `chart_bar_value` | n_bars: [3,4,5], difficulty: easy | 3 |
| Legend-to-bar matching (similar shades) | `color_discrimination` | `chart_bar_value` | n_bars: [3,4,5], difficulty: hard, color_family: [blues,reds,greens,purples,oranges] | 3 |
| Odd-shade cell in color grid | `color_discrimination` | `color_grid_odd` | grid_size: [4,6], color_family: [blues,reds,greens,purples,oranges] | 3 |

#### HF Benchmark Tasks
None directly applicable.

#### Key Axes of Variation
- **Difficulty** (easy/hard): Maximally distinct colors vs same-family similar shades
- **Color family**: Blues, reds, greens, purples, oranges — some families may be easier (wider perceptual gamut)
- **Grid size**: Larger grid = smaller cells = harder to spot the odd shade
- **Number of bars**: More bars with similar colors = harder to match to legend

#### Commands
```bash
# Generate
python run_phase1.py --generate-only --n 3 --tasks color_discrimination

# Evaluate
python run_phase1.py --eval-only --tasks color_discrimination --workers 10
```

---

### 4. `text_reading`

**Definition**: Can the model read text at varying sizes, rotations, and contrast levels (OCR stress test)?

#### Synthetic Tasks

| Task | Generator | task_type | Primary Axes | Recommended n |
|------|-----------|-----------|--------------|---------------|
| Isolated word reading | `text_reading` | `text_word_reading` | font_size: [48,32,20,14,10], rotation: [0,15,30,45,90], contrast: [high,medium,low] | 2 |
| Isolated number reading | `text_reading` | `text_number_reading` | font_size: [48,32,20,14,10], rotation: [0,30,45,90] | 2 |
| Chart axis label reading | `text_reading` | `chart_bar_value` | label_font_size: [12,9,7], label_rotation: [0,30,45,60] | 2 |

#### HF Benchmark Tasks

| Dataset | HF Task Name | Our task_type | Relevance |
|---------|-------------|---------------|-----------|
| VLMs-are-Blind | "Circled Letter" | circled_letter | Tests character-level text recognition under overlay |

#### Key Axes of Variation
- **Font size** (10-48px): The primary difficulty axis. Below ~14px, OCR degrades significantly
- **Rotation** (0-90°): Text at angles requires spatial invariance
- **Contrast** (high/medium/low): Low contrast (gray-on-gray) tests sensitivity
- **Font size × rotation interaction**: Small + rotated is the hardest combination
- **Label context**: Text embedded in charts vs isolated

#### Commands
```bash
# Generate
python run_phase1.py --generate-only --n 2 --tasks text_reading

# Evaluate synthetic
python run_phase1.py --eval-only --tasks text_reading --workers 10

# Evaluate HF (circled letter as text recognition baseline)
python run_benchmarks.py --dataset blind --tasks circled_letter --workers 10
```

---

### 5. `prior_bias_override`

**Definition**: Can the model report what it actually sees, overriding memorized defaults (8×8 chess, standard dice patterns)?

#### Synthetic Tasks

| Task | Generator | task_type | Primary Axes | Recommended n |
|------|-----------|-----------|--------------|---------------|
| Dice grid anomaly counting | `patterned_grid` | `patterned_grid` | grid_size: [6,8,10], grid_type: dice, anomaly: [add,remove] | 3 |
| Tally grid anomaly counting | `patterned_grid` | `patterned_grid` | grid_size: [6,8,10], grid_type: tally, anomaly: [add,remove] | 3 |
| Chess board dimension counting | `board_games` | `board_game_rows`/`board_game_cols` | dims: [7×8,9×8,8×7,8×9,8×8] | 1 (deterministic) |
| Go board dimension counting | `board_games` | `board_game_rows`/`board_game_cols` | dims: [18×19,20×19,19×18,19×20,19×19] | 1 (deterministic) |

#### HF Benchmark Tasks

| Dataset | HF Task Name | Our task_type | Split |
|---------|-------------|---------------|-------|
| VLMs-are-Biased | "Game Board" | board_game | main |
| VLMs-are-Biased | "Patterned Grid" | patterned_grid | main |
| VLMs-are-Biased | "Optical Illusion" | optical_illusion | main |

#### Key Axes of Variation
- **Anomaly type** (add/remove): Does the model notice +1 or -1 deviations from pattern?
- **Grid type** (dice/tally): Different visual patterns, different priors
- **Grid size** (6-10): Larger grid = more context reinforcing the pattern = stronger bias
- **Game type** (chess/go): Different canonical dimensions (8×8 vs 19×19)
- **Dimension offset** (±1 from canonical): Tests if model defaults to memorized size
- **Bias alignment**: Track whether errors match `expected_bias` in metadata (key for DPO)

#### Commands
```bash
# Generate
python run_phase1.py --generate-only --n 3 --tasks patterned_grid board_games

# Evaluate synthetic
python run_phase1.py --eval-only --tasks patterned_grid board_games --workers 10

# Evaluate HF
python run_benchmarks.py --dataset biased --topics "Game Board" "Patterned Grid" "Optical Illusion" --workers 10
```

---

## Summary Report Template

The summary should follow this structure (match existing reports):

```markdown
# <Primitive Name> — Evaluation Summary

## Primitive Definition
<1-2 sentences defining the capability>

## Key Finding
**<Bold one-liner summarizing the main takeaway>**

## Tasks Evaluated

### Ceiling Tasks (100% exact match)
<Table of tasks that hit 100%>

### Degrading Tasks
<For each degrading task:>
#### <Task Name>
- Overall accuracy table (Generated vs HF)
- Breakdown by primary axis of variation
- Deep-dive into error patterns

## Cross-Task Patterns
<Numbered list of insights that span multiple tasks>

## Finetuning Implications
<Bullet points on what this means for training data curation>
```

## Existing Data Inventory

Before generating/evaluating, check what already exists. As of the initial setup, these results are available:

| Results File | task_types | Count | Relevant Primitive(s) |
|---|---|---|---|
| `path_following_results.jsonl` | path_following | 6 | line_path_following |
| `line_intersection_results.jsonl` | line_intersection | 3 | line_path_following |
| `diagram_spatial_results.jsonl` | diagram_decision, diagram_next_step | 120 | line_path_following, spatial_localization |
| `diagram_spatial_v2_results.jsonl` | diagram_decision, diagram_next_step | 360 | line_path_following, spatial_localization |
| `chart_spatial_results.jsonl` | chart_bar_value, chart_grouped_value | 160 | spatial_localization |
| `chart_line_value_results.jsonl` | chart_line_value | 80 | spatial_localization |
| `chart_counting_results.jsonl` | chart_bar_count, etc. | varies | counting_enumeration |
| `patterned_grid_results.jsonl` | patterned_grid | 12 | prior_bias_override |
| `board_games_results.jsonl` | board_game_rows, board_game_cols | 20 | prior_bias_override |
| `counting_circles_results.jsonl` | counting_circles | 80 | counting_enumeration |
| `touching_circles_results.jsonl` | touching_circles | 27 | relative_comparison |
| `blind_benchmark_results.jsonl` | mixed | varies | multiple |

**Key gaps** (no existing results):
- `relative_comparison` — no results for `chart_bar_compare` with controlled value diffs or `table_max`; `touching_circles` has only 27 results (needs more coverage)
- `color_discrimination` — no results for `color_grid_odd` or color-matched `chart_bar_value`
- `text_reading` — no results for `text_word_reading`, `text_number_reading`, or label stress tests
- `chart_line_trend` — no results for trend detection
- HF biased benchmark — no results for "Game Board", "Patterned Grid", "Optical Illusion"

When a primitive has small existing result counts (e.g., path_following=6, line_intersection=3), **regenerate with the recommended n_per_config** to get robust coverage. The pipeline's resume support will skip already-evaluated instances.

## Important Notes

- The `chart`, `table`, and `diagram` generators each produce MULTIPLE task_types. When evaluating a primitive, you must generate the full task set but then **filter your analysis** to only the task_types relevant to that primitive.
- Some task_types are shared across primitives (e.g., `chart_bar_compare` appears in both Relative Comparison and Spatial Localization). That's fine — the same data serves different analytical lenses.
- Board games generator is deterministic (n_per_config is capped at 1 internally), so don't expect multiple replicas.
- Always check if results files already exist before re-running evaluation (the pipeline supports resume via already-evaluated instance deduplication).
- For bias tasks, always report **bias alignment rate** alongside accuracy — this is the key metric for DPO training data quality.
- When running `run_phase1.py` with multi-task generators like `chart`, all chart task_types are generated together. You can't generate only `chart_line_trend` independently — generate the full `chart` task and filter at analysis time.
- The analysis step should use Python to load JSONL files, compute accuracy, and write the summary. Use `pandas` for aggregation. Read the existing summaries for formatting reference.
