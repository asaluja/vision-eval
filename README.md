# Vision Eval: Characterizing Haiku 4.5 Blind Spots

Evaluation framework for characterizing vision blind spots in Claude Haiku 4.5, building on findings from:
- [VLMs Are Blind](https://arxiv.org/abs/2407.06581) (Rahmanzadehgervi et al., ACCV 2024)
- [VLMs Are Biased](https://vlmsarebiased.github.io/) (Vo et al., ICLR 2026)

## Quick Start

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Generate test images only
python run_phase1.py --generate-only --n 3

# Run full evaluation
ANTHROPIC_API_KEY=... python run_phase1.py --n 3 --workers 10

# Interactive error analysis
streamlit run analyze/app.py
```

## Parameter Selection Rationale

The VLMs Are Blind paper systematically tested which image parameters affect VLM accuracy. We use their findings to focus evaluation on parameters that actually matter:

### High-signal parameters (swept densely)

| Parameter | Finding | Citation |
|-----------|---------|----------|
| **Object count** | More overlapping objects = dramatically worse accuracy | §4.1, Fig 5 |
| **Spatial proximity / overlap** | "VLMs tend to perform more poorly when circles are closer together" | §4.2, Fig 3 |
| **Text presence in grids** | Empty grid 26% → text-filled 53% (GPT-4o); VLMs use OCR cues, not vision | §4.6, Table 3 |
| **Number of paths** | 1 path 59% → 3 paths 26% mean accuracy | §4.7, Fig 8 |
| **Shape type** | Pentagons significantly harder than circles | §4.4, Table 2 |
| **Circle diameter** | Smaller circles harder for overlap detection | §4.2 |
| **Word choice** | Random strings harder than real words for letter identification | §4.3 |

### Low-signal parameters (fixed to single value)

| Parameter | Finding | Citation |
|-----------|---------|----------|
| **Image resolution** | "Image resolution does not affect VLMs performance" | §A.2 |
| **Line width/thickness** | "Line thickness does not influence VLM ability to count intersections" | §A.1 |
| **Font selection** | "Font selection does not vary the performance of the models" | §A.3 |
| **Color (mono vs multi)** | "Accuracy only changes marginally" | §E.2 |
| **Prompt wording** | "Different prompts result in similar accuracy" | §A.4 |

## Task Types

### VLMs Are Blind (perceptual primitives)

| Task | Generator | High-signal axes | What it tests |
|------|-----------|-----------------|---------------|
| Counting circles | `counting_shapes.py` | count (3-10), overlap (0.1-0.5) | Counting with overlap |
| Counting pentagons | `counting_shapes.py` | count (3-10), overlap (0.1-0.5) | Shape-dependent counting |
| Line intersections | `line_intersection.py` | n_intersections (0-2) | Spatial precision |
| Nested squares | `nested_shapes.py` | depth (2-7) | Nested structure counting |
| Touching circles | `touching_circles.py` | distance (-0.4 to 0.6), radius | Proximity discrimination |
| Circled letter | `circled_letter.py` | word, target position | Spatial localization |
| Grid counting | `grid_counting.py` | grid size, with/without text | Row/col counting |
| Path following | `path_following.py` | n_paths (1-6) | Line following |

### VLMs Are Biased (prior override)

| Task | Generator | High-signal axes | What it tests |
|------|-----------|-----------------|---------------|
| Patterned grids | `patterned_grids.py` | grid type (dice/tally), anomaly type | Counting vs. pattern bias |
| Board games | `board_games.py` | game type, dimension variants | Dimension counting vs. canonical bias |

## Project Structure

```
├── run_phase1.py           # CLI runner (--generate-only, --eval-only, --tasks, --n, --workers)
├── config.py               # Model config, paths
├── generate/               # Image generators (one per task type)
│   ├── base.py             # TaskInstance dataclass, JSONL I/O
│   ├── counting_shapes.py  # Circles + pentagons
│   ├── line_intersection.py
│   ├── nested_shapes.py
│   ├── touching_circles.py
│   ├── circled_letter.py
│   ├── grid_counting.py
│   ├── path_following.py
│   ├── patterned_grids.py
│   └── board_games.py
├── evaluate/               # Evaluation harness
│   ├── api.py              # Anthropic API wrapper (retry, rate limiting)
│   ├── prompts.py          # Prompt templates per task
│   ├── score.py            # Answer extraction + scoring
│   └── run_eval.py         # Concurrent evaluation orchestrator
├── analyze/
│   └── app.py              # Streamlit error analysis UI
├── results/                # Evaluation results (JSONL)
└── figures/                # Charts for report
```
