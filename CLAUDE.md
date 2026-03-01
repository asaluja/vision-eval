# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vision evaluation framework for characterizing Haiku 4.5's perceptual blind spots. Generates synthetic test images across controlled parameter axes, evaluates via API, and analyzes failure patterns. Built on findings from VLMs Are Blind (ACCV 2024) and VLMs Are Biased (ICLR 2026).

## Commands

```bash
# Setup
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Generate images only (no API calls)
python run_phase1.py --generate-only --n 3 --tasks counting_circles line_intersection

# Evaluate pre-generated images
python run_phase1.py --eval-only --tasks counting_circles --workers 10

# Full generate + evaluate
ANTHROPIC_API_KEY=... python run_phase1.py --n 3 --workers 10

# With extended thinking
python run_phase1.py --eval-only --tasks counting_pentagons --thinking --thinking-budget 8000

# HF benchmark evaluation
python run_benchmarks.py --dataset blind --tasks path_following line_intersection --workers 10
python run_benchmarks.py --dataset biased --topics "Game Board" --workers 10
python run_benchmarks.py --list  # show available tasks/topics

# Interactive analysis
streamlit run analyze/app.py

# Test a single generator standalone
python -m generate.counting_shapes
python -m generate.charts
```

## Architecture

The pipeline has three phases: **generate → evaluate → analyze**.

### Core Data Type

`TaskInstance` (in `generate/base.py`) is the unit of work throughout the pipeline — a dataclass holding `image_path`, `prompt`, `ground_truth`, `task_type`, `subtask`, and `metadata`. Saved/loaded as JSONL.

### Generate

Each generator module in `generate/` exports a `generate()` function that produces images and returns `list[TaskInstance]`. Generators sweep **high-signal parameters** (count, overlap, depth) densely while fixing low-signal ones (resolution, line width, font) per VLMs Are Blind findings.

`make_instances()` in `base.py` creates one `TaskInstance` per prompt variant for each image, enabling robustness testing across semantically equivalent prompts.

Multi-task generators (`chart`, `table`, `diagram`) produce several task_types each — you can't generate a single sub-type independently. Generate the full task and filter at analysis time.

### Evaluate

- `evaluate/prompts.py`: `PROMPTS` dict maps `task_type → list[str]` (dual prompt variants A & B)
- `evaluate/score.py`: Task-specific regex extractors (`extract_number`, `extract_yes_no`, `extract_letter`, etc.) plus `score_instance()` dispatcher
- `evaluate/api.py`: Anthropic API wrapper with retry/backoff, base64 image encoding, thinking support
- `evaluate/run_eval.py`: ThreadPoolExecutor-based concurrent evaluator with resume support (skips already-evaluated `(image_path, prompt)` pairs)

### Analyze

`analyze/app.py` is a Streamlit dashboard loading `results/*_results.jsonl` into pandas for accuracy breakdowns and error card inspection.

### Data (HF benchmarks)

`data/blind.py` and `data/biased.py` adapt HuggingFace datasets into `TaskInstance` objects. The biased dataset tracks `expected_bias` in metadata for DPO pair generation.

## Task Registry

`TASK_REGISTRY` in `run_phase1.py` maps task names to `(module_path, kwargs)` pairs. To add a new task:

1. Create `generate/my_task.py` with `generate(n_per_config, output_dir, **kwargs) → list[TaskInstance]`
2. Add prompt templates to `evaluate/prompts.py` under `PROMPTS["my_task"]`
3. Add scoring logic to `evaluate/score.py` in `score_instance()`
4. Register in `TASK_REGISTRY` in `run_phase1.py`

## Key Directories

- `generate/images/` — generated PNGs organized by task type
- `summaries/` — per-primitive markdown summaries (compiled into report via `/report-compile`)
- `results/` — JSONL instance metadata and evaluation results only (no HTML, no markdown summaries)
- `figures/` — charts, plots, and error composite PNGs for the report
- `data/cache/` and `data/images/` — HF dataset downloads

## Important Conventions

- `config.py` sets `matplotlib.use("Agg")` before any pyplot import (required for headless macOS rendering). Always `import config` or set the backend before importing pyplot.
- `MODEL_ID` in `config.py` is `claude-haiku-4-5-20251001` — all evaluation targets this model.
- Requires `from __future__ import annotations` for `X | Y` union syntax (Python 3.9).
- Uses `uv` for virtual environment and package management.
- All output figures/plots go in `figures/`, not `results/`. The `results/` directory is for JSONL data and `report.html` only. Summaries go in `summaries/`.
