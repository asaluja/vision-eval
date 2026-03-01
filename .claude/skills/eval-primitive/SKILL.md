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
- `visual_textual_consistency`

(Already completed: `counting_enumeration`, `spatial_localization`)

The authoritative task inventory is at `docs/task_inventory.md`. The inventories below are the working reference for running evals.

## Workflow

When this skill is invoked with a primitive name, follow these steps **in order**. Each step ends with an explicit checkpoint — **STOP and ask the user for approval before proceeding to the next step.**

### Step 1: Display the Task Inventory

Print the full task inventory for the requested primitive from the table below. For each task, show:
- Task type, source (Local/HF), and whether results already exist (check `results/` directory) and how many
- Primary axes of variation
- Recommended n_per_config for robust coverage

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
- How many workers to use (default 10)?
- For multi-task generators (e.g. `chart` produces 9 task_types), should we evaluate all task_types or filter to only the ones relevant to this primitive?

**Do NOT proceed to Step 3 until the user confirms.**

### Step 3: Evaluate with API

Run evaluation on synthetic:
```bash
source .venv/bin/activate && python run_phase1.py --eval-only --tasks <task_list> --workers <N>
```

If filtering a multi-task generator to specific task_types:
```python
import json
with open('results/chart_instances.jsonl') as fin, open('results/<filtered>_instances.jsonl', 'w') as fout:
    for line in fin:
        d = json.loads(line)
        if d['task_type'] in TARGET_TYPES:
            fout.write(line)
```
Then evaluate the filtered file using `load_instances()` + `run_evaluation()` directly.

If HF benchmarks apply:
```bash
source .venv/bin/activate && python run_benchmarks.py --dataset <blind|biased> --tasks <hf_tasks> --workers <N>
```

After evaluation completes, report:
- Raw accuracy numbers per task_type
- Total instances evaluated
- Any errors or failures

**CHECKPOINT 3**: Ask the user:
- Do the raw numbers look reasonable?
- Any task_types to re-run before full analysis?
- Confirm they want to proceed to the full analysis and summary writeup.

**Do NOT proceed to Step 4 until the user confirms.**

### Step 4: Analyze & Write Summary

1. Load the results JSONL files from `results/`
2. Compute accuracy breakdowns by task_type, subtask, and key metadata axes
3. Identify ceiling tasks (100%) vs degrading tasks
4. Deep-dive into error patterns for degrading tasks
5. Write summary to `summaries/<primitive_name>_summary.md` following the format of existing summaries

Present the summary to the user for review.

---

## Primitive Task Inventories

### 1. `line_path_following`

**Definition**: Can the model trace paths, follow connections, and identify where lines lead?

| task_type | Source | Rec. n | Primary Axes |
|---|---|---|---|
| `path_following` | Local | 3 | n_paths: [1,2,3,4,5,6] |
| `path_following` | HF (blind) | — | — |
| `line_intersection` | Local | 3 | n_points: [3,4,5], n_intersections: [0→max] |
| `line_intersection` | HF (blind) | — | — |
| `chart_line_trend` | Local (chart) | 2 | n_categories: [3,5,7,10], n_series: [1,2,3] |
| `diagram_next_step` | Local (diagram) | 2 | template: [linear,single_branch,asymmetric,multi_decision], n_steps: [3,5,7] |
| `diagram_decision` | Local (diagram) | 2 | template: [single_branch,asymmetric,multi_decision], n_steps: [3,5,7] |

**Commands**:
```bash
python run_phase1.py --generate-only --n 3 --tasks path_following line_intersection chart diagram
python run_phase1.py --eval-only --tasks path_following line_intersection chart diagram --workers 10
python run_benchmarks.py --dataset blind --tasks path_following line_intersection --workers 10
```
Filter analysis to: `path_following`, `line_intersection`, `chart_line_trend`, `diagram_next_step`, `diagram_decision`.

---

### 2. `relative_comparison`

**Definition**: Can the model compare two visual elements and determine which is larger/higher/more?

| task_type | Source | Rec. n | Primary Axes |
|---|---|---|---|
| `relative_bar_compare` | Local | 2 | value_diff: [1,2,5,10,20,40], n_bars: [4,6,8,10,12], show_grid: [T/F] |
| `relative_line_compare` | Local | 3 | n_points: [5,8], value_gap (emergent) |
| `chart_bar_compare` | Local (chart) | 2 | n_categories: [3,5,7,10] |
| `table_max` | Local (table) | 2 | n_rows: [3,5,7,10], n_cols: [2,3,5] |
| `pie_slice_compare` | Local (pie_charts) | 2 | n_slices: [3,4,5,6,7,8] |
| `touching_circles` | Local | 3 | distance: [-0.4→0.6], radius: [30,50] |
| `touching_circles` | HF (blind) | — | — |

**Commands**:
```bash
python run_phase1.py --generate-only --n 3 --tasks relative_comparison chart table touching_circles pie_charts
python run_phase1.py --eval-only --tasks relative_comparison chart table touching_circles pie_charts --workers 10
python run_benchmarks.py --dataset blind --tasks touching_circles --workers 10
```
Filter analysis to: `relative_bar_compare`, `relative_line_compare`, `chart_bar_compare`, `table_max`, `pie_slice_compare`, `touching_circles`.

---

### 3. `color_discrimination`

**Definition**: Can the model distinguish colors, match legend entries to series, and detect shade differences?

| task_type | Source | Rec. n | Primary Axes |
|---|---|---|---|
| `chart_legend_match` | Local | 3 | n_bars: [3,4,5], difficulty: [easy,hard], color_family: [blues,reds,greens,purples,oranges] |
| `color_grid_odd` | Local | 3 | grid_size: [4,6], color_family: [blues,reds,greens,purples,oranges], grid_difficulty: [easy,hard,very_hard,near_threshold,extreme] |
| `heatmap_cell_value` | Local | 2 | grid_size: [4×4,6×6,4×6], colormap: [viridis,RdBu,YlOrRd], value_range: [0-100,0-10,-1-1] |

**Commands**:
```bash
python run_phase1.py --generate-only --n 3 --tasks color_discrimination heatmap
python run_phase1.py --eval-only --tasks color_discrimination heatmap --workers 10
```

---

### 4. `text_reading`

**Definition**: Can the model read text at varying sizes, rotations, and contrast levels?

| task_type | Source | Rec. n | Primary Axes |
|---|---|---|---|
| `text_word_reading` | Local | 2 | font_size: [48,32,20,14,10], rotation: [0,15,30,45,90], contrast: [high,medium,low] |
| `text_number_reading` | Local | 2 | font_size: [48,32,20,14,10], rotation: [0,30,45,90] |

**Commands**:
```bash
python run_phase1.py --generate-only --n 2 --tasks text_reading
python run_phase1.py --eval-only --tasks text_reading --workers 10
```

---

### 5. `prior_bias_override`

**Definition**: Can the model report what it actually sees, overriding memorized canonical defaults?

| task_type | Source | Rec. n | Primary Axes |
|---|---|---|---|
| `patterned_grid` | Local | 3 | grid_size: [6,8,10], grid_type: [dice,tally], anomaly: [add,remove] |
| `patterned_grid` | HF (biased) | — | — |
| `flags` | HF (biased) | — | — |
| `logos` | HF (biased) | — | — |

**Commands**:
```bash
python run_phase1.py --generate-only --n 3 --tasks patterned_grid
python run_phase1.py --eval-only --tasks patterned_grid --workers 10
python run_benchmarks.py --dataset biased --topics "Patterned Grid" "Flags" "Logos" --workers 10
```
Always report **bias alignment rate** alongside accuracy for this primitive.

---

### 6. `visual_textual_consistency`

**Definition**: Does the model ground its answers in visual content, or does it defer to text annotations?

| task_type | Source | Rec. n | Primary Axes |
|---|---|---|---|
| `conflict_value_label` | Local | 3 | n_bars: [3,5,7], conflict_magnitude: [small,large] |
| `conflict_title_trend` | Local | 3 | n_points: [5,8,12], conflict_type: [increasing↔decreasing] |
| `conflict_legend_color` | Local | 3 | n_series: [2,3,4] |
| `conflict_annotation` | Local | 3 | n_bars: [4,6,8], gap_to_second: [small,large] |
| `chart_data_match` | Local | 2 | n_categories: [3,4,5,6], chart_pair: [bar/pie,bar_v/bar_h,bar/line], match: [T/F] |

**Commands**:
```bash
python run_phase1.py --generate-only --n 3 --tasks text_visual_conflict chart_comparison
python run_phase1.py --eval-only --tasks text_visual_conflict chart_comparison --workers 10
```
For each error, also check `text_reliant` flag in metadata — this is the key signal for grounding failures.

---

## Summary Report Template

```markdown
# <Primitive Name> — Evaluation Summary

## Primitive Definition
<1-2 sentences>

## Key Finding
**<Bold one-liner>**

## Tasks Evaluated

### Ceiling Tasks (≥95% accuracy)
<Table>

### Degrading Tasks
#### <Task Name>
- Accuracy table (Local vs HF)
- Breakdown by primary axis
- Error pattern analysis

## Cross-Task Patterns
<Numbered insights spanning multiple tasks>

## Finetuning Implications
<Bullet points for training data curation>
```

## Important Notes

- The `chart`, `table`, `diagram`, and `pie_charts` generators each produce MULTIPLE task_types. Generate the full task and filter analysis to the relevant task_types for the primitive.
- Always check `docs/task_inventory.md` for current result counts before deciding what to regenerate.
- The pipeline's resume support skips already-evaluated `(image_path, prompt)` pairs — safe to re-run.
- For `prior_bias_override`, always report **bias alignment rate** alongside accuracy.
- For `visual_textual_consistency`, check the `text_reliant` metadata flag on errors.
- HF biased `flags`/`logos` task_types will be `flags` and `logos` via the lowercase fallback in `data/biased.py`.
