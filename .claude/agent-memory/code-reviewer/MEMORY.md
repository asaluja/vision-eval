# Vision Eval Project - Code Reviewer Memory

## Project Structure
- `config.py` sets `matplotlib.use("Agg")` globally, but only works when imported (runners import it, generators/figures do not)
- `generate/base.py` has `TaskInstance`, `make_instances()`, `save_instances()`, `load_instances()`, `ensure_dir()`
- `make_instances()` creates dual prompt variants (A/B) from `PROMPTS` dict -- this is the intended pattern
- Three generators bypass `make_instances()` and construct `TaskInstance` directly: `color_discrimination.py`, `text_reading.py`, `relative_comparison.py`

## Key Patterns
- `_get_font()` is duplicated in 5 files: `circled_letter.py`, `grid_counting.py`, `patterned_grids.py`, `tables.py`, `text_reading.py`
- `get_prompt` is imported but never used in 11 generator files (vestigial from before `make_instances()` was created)
- `matplotlib.use("Agg")` is called redundantly in 3 generators + all 8 figures scripts + analyze/app.py + config.py
- `COLORS = list(matplotlib.cm.tab10.colors[:10])` duplicated in: `charts.py`, `chart_comparison.py`, `text_visual_conflict.py`, `pie_charts.py`
- `CATEGORY_POOLS` duplicated (similar but slightly different) in: `chart_comparison.py`, `text_visual_conflict.py`, `pie_charts.py`

## Scoring/Prompts Coverage
- Tasks in score.py but not PROMPTS (by design): `board_game`, `color_grid_odd`, `optical_illusion`, `text_number_reading`, `text_word_reading`
- These are either HF benchmark tasks or tasks that use custom prompts constructed inline in generators

## Figures Scripts
- All 8 `make_*_errors.py` scripts follow identical boilerplate: define cases list, create 1x3 subplot, loop over cases with same rendering code
- `results/make_spatial_figure.py` is a misplaced figures script (saves to results/ instead of figures/)

## Anti-Patterns Found
- `line_intersection.py` uses `n_per_intersection` param name; all others use `n_per_config` -- causes special-casing in `run_phase1.py`
- `sys` imported but unused in `run_phase1.py` and `run_benchmarks.py`
- `numpy` imported but unused in `counting_shapes.py`
- `seaborn` in `requirements.txt` but never imported
- `finetune/` directory exists with empty `__init__.py` -- dead code
