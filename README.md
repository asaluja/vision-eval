# Vision Eval: Characterizing Haiku 4.5's Perceptual Blind Spots

Evaluation framework for systematically mapping where Claude Haiku 4.5's vision breaks down on perception tasks. Generates synthetic test images with controlled parameter axes, evaluates via the Anthropic API, and analyzes failure patterns to inform a targeted finetuning plan.

Built on findings from [VLMs Are Blind](https://arxiv.org/abs/2407.06581) (ACCV 2024) and [VLMs Are Biased](https://vlmsarebiased.github.io/) (ICLR 2026).

## Key Findings

The evaluation (~19K instances across 33 task types) reveals **three mechanistically distinct failure regimes**:

1. **OCR-as-crutch** — The model reads text labels instead of perceiving visual content. Value-label conflicts: 0% accuracy, 100% text-reliant. Grid counting: 49% without text vs 100% with text. This silently affects every chart/table/document task.

2. **Perceptual resolution limits** — Smooth degradation along psychometric curves as visual complexity increases. Path tracing drops to 10-40% with distractors; intersection detection collapses to 18% for complex lines; proximity threshold exists at distance_ratio ~0.05; color discrimination cliff at deltaL ~7-10.

3. **Memorized priors override vision** — Canonical knowledge short-circuits perception. Logo element counting: 1.9% accuracy with 99.8% bias alignment. Board game dimensions: model reports canonical sizes regardless of actual dimensions.

Extended thinking experiments confirm these are **perceptual failures, not reasoning failures** — thinking only helps annotation conflicts (+15pp), the one task where reasoning can override a weak visual signal.

## Setup

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
```

Requires Python 3.9+. Uses `uv` for package management.

## Usage

### Generate + Evaluate

```bash
# Generate test images only (no API calls)
python run_phase1.py --generate-only --n 3 --tasks counting_circles line_intersection

# Evaluate pre-generated images
python run_phase1.py --eval-only --tasks counting_circles --workers 10

# Full pipeline (generate + evaluate)
python run_phase1.py --n 3 --workers 10

# With extended thinking
python run_phase1.py --eval-only --tasks counting_pentagons --thinking --thinking-budget 2048
```

### HuggingFace Benchmarks

```bash
# Evaluate against published benchmarks
python run_benchmarks.py --dataset blind --tasks path_following line_intersection --workers 10
python run_benchmarks.py --dataset biased --topics "Game Board" --workers 10

# List available tasks/topics without downloading
python run_benchmarks.py --list
```

### Interactive Analysis

```bash
streamlit run analyze/app.py
```

The Streamlit dashboard provides accuracy breakdowns by task/subtask, metadata-based filtering, and paginated error card inspection with images.

### Run Tests

```bash
python -m pytest tests/ -q   # 103 tests
```

## Architecture

The pipeline has three phases: **generate → evaluate → analyze**.

```
vision-eval/
├── run_phase1.py              # CLI: synthetic image generation + evaluation
├── run_benchmarks.py          # CLI: HuggingFace benchmark evaluation
├── config.py                  # Global config (model ID, paths, matplotlib backend)
│
├── generate/                  # Image generators
│   ├── base.py                # TaskInstance dataclass, JSONL I/O, make_instances()
│   ├── chart_common.py        # Shared constants for chart generators
│   ├── counting_shapes.py     # Overlapping circles & pentagons
│   ├── line_intersection.py   # Polyline intersection counting
│   ├── touching_circles.py    # Proximity discrimination
│   ├── path_following.py      # Subway-map style path tracing
│   ├── nested_shapes.py       # Recursively nested squares
│   ├── charts.py              # Bar, grouped bar, line charts (multi-task)
│   ├── chart_comparison.py    # Side-by-side chart pairs for data matching
│   ├── pie_charts.py          # Pie charts with controlled label visibility
│   ├── heatmap.py             # Color-encoded value grids
│   ├── tables.py              # Data tables (cell lookup, row count, max)
│   ├── diagrams.py            # Flowcharts (node count, next-step, decisions)
│   ├── circled_letter.py      # Letter localization under overlay
│   ├── grid_counting.py       # Empty vs text-filled grids
│   ├── board_games.py         # Non-standard chess/Go boards
│   ├── patterned_grids.py     # Dice/tally grids with anomalies
│   ├── relative_comparison.py # Controlled-difficulty bar/line comparisons
│   ├── color_discrimination.py# Similar-shade bars + color grids
│   ├── text_reading.py        # Words/numbers at varying size, rotation, contrast
│   └── text_visual_conflict.py# Charts with planted text-visual contradictions
│
├── evaluate/                  # Evaluation harness
│   ├── api.py                 # Anthropic API wrapper (retry, base64, thinking)
│   ├── prompts.py             # Prompt templates (2 variants per task type)
│   ├── score.py               # Regex extractors + score_instance() dispatcher
│   └── run_eval.py            # ThreadPoolExecutor evaluator with resume support
│
├── analyze/
│   └── app.py                 # Streamlit dashboard for error analysis
│
├── data/                      # HuggingFace dataset adapters
│   ├── blind.py               # VLMs-are-Blind benchmark adapter
│   ├── biased.py              # VLMs-are-Biased benchmark adapter (preserves expected_bias)
│   ├── common.py              # Shared parsing utilities
│   └── clip_dino_pairs.py     # CLIP/DINOv2 embedding analysis
│
├── tests/                     # 103 tests for extractors and validation
│   ├── test_score.py
│   └── test_run_eval.py
│
├── checks/                    # Diagnostic scripts for verifying summary claims
│   ├── check_full.py          # Cross-task accuracy audit
│   ├── check_summaries.py     # Summary claim verification
│   ├── check_circled_letter.py# Off-by-one error analysis
│   └── check_diag.py          # Diagram/pie chart diagnostics
│
├── summaries/                 # Per-primitive markdown evaluation summaries + finetuning plan
├── figures/                   # Generated plots, error composites, and figure scripts
├── results/                   # JSONL instance metadata and evaluation results
├── task_inventory.md          # Master inventory of all task entries with primitive mappings
└── anthropic_takehome_context.md  # Full research context and literature review
```

## Core Data Type

`TaskInstance` (defined in `generate/base.py`) is the unit of work throughout the pipeline:

```python
@dataclass
class TaskInstance:
    image_path: str        # Path to generated PNG
    prompt: str            # Formatted evaluation prompt
    ground_truth: Any      # Expected answer (int, str, tuple, etc.)
    task_type: str         # e.g., "counting_circles", "chart_bar_value"
    subtask: str           # Optional sub-categorization
    metadata: dict         # Generator-specific params, prompt_variant index, etc.
```

Instances are serialized as JSONL via `save_instances()` / `load_instances()`.

## Task Types (7 Perceptual Primitives)

All 33 task types map to 7 perceptual primitives:

| Primitive | Task Types | Headline Finding |
|-----------|-----------|-----------------|
| **Counting/Enumeration** | counting_circles, counting_pentagons, nested_squares, grid_counting, chart_bar_count, diagram_node_count, pie_slice_count, table_row_count | Solved for labeled elements (98-100%); degrades with overlap (pentagons 61.5%) and missing text cues (grids 49%) |
| **Spatial Localization** | circled_letter, chart_bar_value, chart_grouped_value, chart_line_value, table_cell_lookup | Solved at low density (100%); series confusion at 9-10 series (~50%); adjacent-letter errors dominate circled letter |
| **Line/Path Following** | line_intersection, path_following, chart_line_trend, diagram_next_step, diagram_decision | Sharp clutter-dependent degradation; 100% simple → 10-40% with distractors; overcounting is 97% of errors |
| **Relative Comparison** | touching_circles, chart_bar_compare, table_max, pie_slice_compare, relative_bar/line_compare, chart_data_match | Solved down to diff=2; proximity threshold at gap ~0.05; pie (73%) much harder than bar (98%) |
| **Color Discrimination** | chart_legend_match, color_grid_odd, heatmap_cell_value | Perceptual cliff at deltaL ~7-10; orange robust, green fragile; heatmap (56%) hardest |
| **Text Reading** | text_word_reading, text_number_reading | Near-perfect at font >=14px; collapses below 10px; numbers degrade faster than words |
| **Prior/Bias Override** | patterned_grid, board_game, conflict_value_label, conflict_title_trend, conflict_legend_color, conflict_annotation | Value-label conflict: 0% (always reads text); logos: 1.9% (99.8% bias-aligned); thinking only helps annotations |

## Parameter Selection Rationale

Following VLMs Are Blind's methodology, generators sweep **high-signal parameters** densely while fixing low-signal ones:

**Swept densely** (affect accuracy):
- Object count, spatial overlap, text presence in grids, number of paths/distractors, shape type, font size, color similarity (deltaL)

**Fixed** (don't affect accuracy per the paper):
- Image resolution, line width/thickness, font selection, color mode (mono vs multi)

Each task generates **two prompt variants** (A and B) per image for robustness testing across semantically equivalent phrasings.

## How to Add a New Task

1. Create `generate/my_task.py` with:
   ```python
   def generate(n_per_config: int, output_dir: str, **kwargs) -> list[TaskInstance]:
       ...
   ```
2. Add prompt templates to `evaluate/prompts.py`:
   ```python
   PROMPTS["my_task"] = [
       "Variant A: {placeholder}",
       "Variant B: {placeholder}",
   ]
   ```
3. Add scoring logic to `evaluate/score.py` in `score_instance()`.
4. Register in `TASK_REGISTRY` in `run_phase1.py`:
   ```python
   "my_task": ("generate.my_task", {}),
   ```

## Evaluation Pipeline Details

**API calls**: `evaluate/api.py` wraps the Anthropic SDK with `temperature=0`, base64 image encoding, exponential backoff on rate limits, and optional extended thinking support.

**Scoring**: `evaluate/score.py` uses regex-based extractors (numbers, yes/no, letters, row/col tuples, trends, free text) with a dispatcher that routes by `task_type`. Numeric tasks use tolerance-based matching (max(2, value * 0.05)) for chart/continuous readings.

**Concurrency**: `evaluate/run_eval.py` uses `ThreadPoolExecutor` (default 10 workers) with thread-safe incremental result writing and resume support (skips already-evaluated `(image_path, prompt)` pairs).

**Pre-eval validation**: Checks for missing images and stale prompts (from regeneration) before making API calls.

## Outputs

| Directory | Contents |
|-----------|----------|
| `results/` | JSONL files only — instance metadata (`*_instances.jsonl`) and evaluation results (`*_results.jsonl`) |
| `summaries/` | Per-primitive markdown evaluation summaries (7 primitives + finetuning plan) |
| `figures/` | Accuracy charts, error composite images, and the Python scripts that generate them |
| `generate/images/` | Generated PNGs organized by task type (gitignored, reproducible) |

## Finetuning Plan (Summary)

The report proposes a three-stage training pipeline:

1. **SFT (~120K examples)**: Break OCR dependency by training on charts without/with deliberately wrong labels, using chain-of-thought visual grounding. Data mix: 35K chart tasks, 2.5K color grids, 2.7K heatmaps, 2K grids, plus 15K solved-task regularization, all doubled via CoT augmentation.

2. **DPO (~12K pairs)**: ~1,725 natural preference pairs from eval failures, augmented ~7× via parameter sweeps. Primary target: 0% value-label conflict (every instance produces a clean pair). Additional pairs from proximity thresholds, color discrimination edges, and path overcounts.

3. **RL with verifiable rewards (~93K episodes)**: 11 task families with difficulty curricula (~200 episodes per step, ×2 for reward variants). All tasks have exactly computable ground truth.

See `summaries/finetuning_plan_summary.md` for the full plan with sample training data.

## Key Files for Orientation

If you're picking up this repo, start here:

1. **`anthropic_takehome_context.md`** — Full research context, literature review, and assignment spec
2. **`summaries/`** — Read any primitive summary to understand the evaluation methodology and findings
3. **`task_inventory.md`** — Master inventory of all task entries with primitive mappings
4. **`CLAUDE.md`** — Detailed developer instructions for Claude Code, including conventions and the task registry

## Dependencies

- `anthropic>=0.40.0` — Anthropic Python SDK
- `Pillow>=10.0` — Image generation
- `matplotlib>=3.8` — Chart/figure generation
- `numpy>=1.26`, `pandas>=2.0` — Numerical/data analysis
- `tqdm>=4.66` — Progress bars
- `datasets>=2.16` — HuggingFace datasets
- `streamlit>=1.30` — Interactive dashboard
- `torch>=2.0`, `transformers>=4.36` — CLIP/DINOv2 embedding analysis
- `pytest>=8.0` — Testing

## Platform Notes

- **macOS**: `config.py` sets `matplotlib.use("Agg")` before any pyplot import (required for headless rendering). Always `import config` before importing pyplot.
- **Python 3.9**: Uses `from __future__ import annotations` for `X | Y` union syntax.
- **Model**: All evaluation targets `claude-haiku-4-5-20251001` (set in `config.py`).

## Future Work: Synthetic Image Pairs

All current evaluation tasks use **single images**. Image pairs are a fundamentally different evaluation paradigm: show two nearly identical images and ask the model to identify or reason about the difference. This directly generates contrastive finetuning data — every pair where the model fails becomes a training example.

**Implemented**: Chart data match (`generate/chart_comparison.py`) — same data rendered as different chart types, ask if values match.

**Proposed pair types** (not yet implemented):
1. **Relative comparison in charts** (highest priority) — two bar charts identical except one bar is slightly taller/shorter
2. **Text/number changes in documents** — same form but a dollar amount differs ($1,234 vs $1,284)
3. **Count changes in charts/diagrams** — same layout, 5 bars vs 6 bars
4. **Spatial localization** — same table, highlighted cell at (2,3) vs (2,4)
5. **Color discrimination** — same chart but legend color mapping is swapped
6. **Line/path following** — same flowchart but "Yes" branch goes left vs right
7. **Prior/bias override** — standard 8×8 chessboard vs 9×8 chessboard

CLIP/DINOv2 embedding scores can validate that pairs are "CLIP traps" (high CLIP similarity, low DINOv2 similarity).

## Known Issues

### Patterned Grid: Generator Bug (Fixed, Needs Re-evaluation)

The `generate/patterned_grids.py` generator had a ground-truth bug: `actual_count` was set to `count` after the cell-drawing loop, but `count` is reassigned on every iteration, so it held the value from the last cell drawn (always 1) rather than the anomaly cell's actual count. All patterned grid results have incorrect ground truth. The task is excluded from summaries and figures pending re-evaluation.

### Extended Thinking Experiments

Extended thinking (`--thinking --thinking-budget 2048`) only helps annotation conflicts (+15pp, 75%→90%). All other tasks are unchanged — value labels (0%→0%), board games (-0.5pp), pie charts (+1.7pp), heatmap (+0.4pp). Increasing budget beyond 2048 does not help. These are perceptual limits, not reasoning bottlenecks.
