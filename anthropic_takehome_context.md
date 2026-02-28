# Anthropic Take-Home: Vision Blind Spots — Research Context

## Assignment

**Task**: Characterize Haiku 4.5's blind spots on perception tasks and propose a finetuning plan to fix them.
**Duration**: 24 hours (due Monday March 2, 8:30am PT)
**Model to test**: `claude-haiku-4-5-20251001`
**API key**: Provided by Anthropic (use via `ANTHROPIC_API_KEY` env var or `anthropic.Anthropic(api_key=...)`)

### Deliverables
1. **Code repository (GitHub)**: All code, legible and well-organized so another researcher with Claude Code could pick up where you left off.
2. **Final report (Google Doc)**: Max 3 pages of text, but can include lots of example images/charts/graphs (10-page doc is fine). Characterize the biggest blindness issues precisely so they can be comprehensively addressed in the finetuning plan.

### What to do
1. Think about business-relevant visual reasoning tasks (charts, graphs, diagrams, flowcharts, tables, documents)
2. Consider underlying perceptual challenges (localization, line following, counting, spatial relationships)
3. Test Haiku 4.5 on a range of perceptual tasks — find where it does well and poorly
4. Characterize the worst blind spots as thoroughly as possible
5. Propose a finetuning plan: data composition, SL vs RL mix, data generation approach
6. **Deep dive on at least one issue**: generate sample finetuning data, explain rationale, describe RL scoring

---

## Key Papers & Findings

### 1. "VLMs Are Blind" (Rahmanzadehgervi et al., ACCV 2024)
- **Paper**: [arXiv:2407.06581](https://arxiv.org/abs/2407.06581) | [Project page](https://vlmsareblind.github.io/)
- **Core finding**: SOTA VLMs fail at elementary visual tasks (counting, path following, spatial discrimination). Average 58% accuracy on BlindTest vs ~100% human.
- **BlindTest benchmark (7 tasks)**:
  - Count line intersections
  - Detect overlapping/touching circles
  - Identify circled letters
  - Count overlapping circles (Olympic rings bias: Gemini says "5" 99% of the time for >5 circles)
  - Count overlapping pentagons
  - Count nested squares
  - Count grid rows/columns (adding text to cells dramatically helps — model uses language cues not vision)
  - Subway map path following (95% on 1 path → 25% on 3 paths)
- **Root cause**: Linear probing shows vision encoders HAVE the info. The LM decoder fails to extract fine-grained spatial info. Problem is NOT in the encoder.
- **Resolution doesn't help**: Performance is invariant to image resolution (384 vs 1155 px).
- **Dense/overlapping features are the killer**: Performance approaches 100% when shapes are well-separated.
- **Claude 3.5 Sonnet was best model (77.84%)**, GPT-4o worst (45%).
- **NOTE**: The paper did NOT attempt finetuning. It's purely diagnostic.

### 2. "VLMs Are Biased" (Vo et al., ICLR 2026)
- **Paper**: [Project page](https://vlmsarebiased.github.io/)
- **Core finding**: VLMs rely on memorized knowledge instead of visual analysis. 100% accuracy on unmodified images → 17% on counterfactual images with subtle modifications. **75.7% of errors are bias-aligned** (not random — models give the canonical memorized answer).
- **7 failure categories**:
  - Animal legs (dog with 5 legs → model says 4): **2.12% accuracy**
  - Car logos (Audi with 5 rings → model says 4): **0.44% accuracy**
  - National flags (US flag 14 stripes → model says 13): **9.25%**
  - Shoe logos (Adidas 4 stripes): **17.57%**
  - Chess pieces: **26.25%**
  - Game boards (grid dimensions): **2.26%**
  - Optical illusions: **50.87%**
- **Prompting doesn't fix it**: "Don't use prior knowledge" → +1.87%. "Double-check your answer" → +2.70%. Negligible.
- **Background removal helped most**: +21 percentage points — contextual cues trigger memorized priors.
- **Adversarial text labels made it worse**: -4.49%, especially for thinking models.
- **The paper did NOT attempt finetuning.** Only prompting-based mitigations.

### 3. "Eyes Wide Shut" / MMVP (Tong et al., CVPR 2024)
- **Paper**: [arXiv:2401.06209](https://arxiv.org/abs/2401.06209) | [Project page](https://tsb0601.github.io/mmvp_blog/)
- **Core idea**: Use CLIP vs DINOv2 embedding discrepancy to find blind spots. High CLIP similarity (>0.95) + low DINOv2 similarity (<0.6) = CLIP has discarded a meaningful visual distinction.
- **9 visual patterns where CLIP fails**:
  1. Orientation/Direction
  2. Presence of specific features
  3. State/Condition
  4. Quantity/Count
  5. Positional/Relational context
  6. Color/Appearance
  7. Structural/Physical characteristics
  8. Text in images
  9. Viewpoint/Perspective
- **7/9 patterns don't improve with CLIP scaling.** Only Color and State improve with bigger models.
- **Human annotation pipeline**: Embedding computation + threshold filtering (automated) → pair selection + question writing + categorization (manual). The manual steps are the bottleneck.
- **Proposed fix (I-MoF)**: Interleave CLIP + DINOv2 tokens before feeding to LM. +10.7% on MMVP without degrading instruction following. But this is architectural, not finetuning.
- **Automating the pipeline** (our idea): Feed both images in a CLIP-blind pair to the VLM. If it gives identical descriptions → confirmed blind spot. Use DINOv2 attention maps to localize the difference, auto-generate questions with an LLM. The model's own failures become a self-supervised signal.

### 4. MM1 (Apple, arXiv:2403.09611)
- **Key finding on data mix**: Connector architecture barely matters (linear projection ≈ Q-Former ≈ C-Abstractor). What matters is data composition and image resolution.
- **Optimal data mix**: 45% image-caption pairs / 45% interleaved image-text / 10% text-only
- **Tradeoff**: Captions → zero-shot performance. Interleaved → few-shot/in-context learning. Can't maximize both.
- **Resolution is the biggest architectural lever** — more impactful than model size or connector design.
- **Gap**: MM1 never analyzes spatial/geometric reasoning by data type. Whether interleaved data helps with spatial understanding is plausible but unproven.

### 5. Related Papers (Not Deeply Analyzed)
- **AutoBench-V (NeurIPS 2024)**: Fully automated synthetic benchmark using diffusion models. No human annotation. General-purpose, not CLIP-blind-spot specific. [arXiv:2410.21259](https://arxiv.org/abs/2410.21259)
- **AutoHallusion (EMNLP 2024)**: Automatically generates hallucination benchmarks by probing VLM language priors. 97.7% hallucination induction on GPT-4V. [arXiv:2406.10900](https://arxiv.org/abs/2406.10900)
- **DIVA (ICLR 2025)**: Uses diffusion model feedback to improve CLIP representations. Addresses MMVP-style failures. [arXiv:2407.20171](https://arxiv.org/abs/2407.20171)
- **BLINK (2024)**: Reformats 14 classic CV tasks into VLM benchmark. Human 95.7%, GPT-4V 51.3%. [arXiv:2404.12390](https://arxiv.org/abs/2404.12390)
- **Cambrian-1 (NeurIPS 2024)**: Evaluates 20+ vision encoders, proposes Spatial Vision Aggregator. Builds on MMVP. [arXiv:2406.16860](https://arxiv.org/abs/2406.16860)

### 6. CLoVe (Avneesh's Own Paper — Castro, Ziai, Saluja et al.)
- **Paper**: [arXiv:2402.15021](https://arxiv.org/abs/2402.15021)
- **Problem**: CLIP text representations are invariant to word order (compositionality failure).
- **Solution**: (1) Generate hard negative captions via scene graph parsing + WordNet replacement, (2) Finetune with hard negatives in contrastive batch, (3) Model patching — interpolate finetuned + pretrained weights (α≈0.6) to preserve general performance while retaining compositionality gains.
- **Result**: ~10% absolute improvement on compositionality benchmarks, maintaining ImageNet performance.
- **Relevance**: Hard negative generation and model patching ideas transfer directly to VLM blind spot fixes. Can cite as prior work.

---

## Diagnostic Framework

### Two-Axis Taxonomy

**Axis 1 — Failure type:**
- **Perceptual** (can't see it) — VLMs are Blind
- **Bias/prior override** (won't look) — VLMs are Biased
- **Reasoning** (sees it but can't reason about it)

**Axis 2 — Visual domain:**
- Geometric/synthetic
- Text/documents
- Natural images
- Charts/data visualization

### Business-Relevant Task Categories to Test
- **Charts/graphs**: Value extraction, trend reading, comparing bar heights
- **Diagrams/flowcharts**: Path following, relationship parsing, node counting
- **Tables/documents**: Cell reading, row/column counting, field extraction
- **Receipts/invoices**: OCR, field extraction from structured layouts
- **UI screenshots**: Element localization, button identification

### Perceptual Challenges to Probe
- Counting (objects, lines, grid elements)
- Localization (which element is circled/highlighted)
- Line/path following
- Spatial relationships (left/right, above/below, overlap detection)
- Fine-grained discrimination (similar shapes/objects)
- Text reading (small, rotated, stylized, handwritten)
- Color precision (similar shades)
- Negation/absence ("what's NOT in this image?")

---

## Proposed Finetuning Approaches

### A. SFT (Supervised Finetuning)

1. **Synthetic spatial/geometric data**: Programmatically generate counting, intersection, overlap, path-tracing tasks with ground truth. Curriculum from easy (well-separated) → hard (overlapping, dense).
2. **Counterfactual canonical objects**: Modified logos, flags, animals to break memorization bias.
3. **Grounded chain-of-thought supervision**: Train on (image, step-by-step reasoning, answer) not just (image, answer). Example: "I see circles. Counting left to right: 1, 2, 3, 4, 5, 6. There are 6."
4. **Business-relevant synthetic data**: Programmatically generated charts, tables, flowcharts with known ground truth values.

### B. RL (Reinforcement Learning)

1. **Outcome-based RL with verifiable rewards** (DeepSeek-R1 style): Spatial/geometric tasks have programmatically verifiable ground truth. Reward = correct answer. No reward model or human labeling needed.
2. **DPO with bias-exploiting preference pairs**: Chosen = correct answer with grounded reasoning. Rejected = memorized canonical answer. The Biased paper shows 75.7% of errors are bias-aligned, so you KNOW what the rejected response will be. Fully automated pair generation.
3. **Process reward for visual grounding**: Reward traces referencing specific visual locations. Penalize traces invoking prior knowledge. Train PRM on synthetic data.
4. **Contrastive RL**: Present visually similar but different-answer image pairs. Reward getting BOTH right.
5. **Curriculum RL**: Easy spatial tasks → progressively harder.

### C. Model Patching (from CLoVe)
- Finetune aggressively for spatial reasoning, then interpolate with original weights: `w = (1-α)·w_pretrained + α·w_finetuned`
- Preserves general capabilities. α ≈ 0.4–0.7 optimal.

### Deep Dive Template (for at least one blind spot)
- Identify specific failure mode
- Generate sample finetuning data programmatically
- Explain why this data addresses the failure
- Describe RL scoring: what's the reward signal, how is it computed, is it verifiable?
- Show example (chosen, rejected) pairs for DPO if applicable

---

## Suggested Repo Structure

```
anthropic-vision-eval/
├── README.md
├── requirements.txt
├── config.py                  # API key, model config
├── generate/                  # Image generation scripts
│   ├── geometric.py           # Counting, intersections, overlaps
│   ├── charts.py              # Bar charts, line graphs
│   ├── diagrams.py            # Flowcharts, diagrams
│   ├── tables.py              # Grid/table images
│   ├── counterfactual.py      # Modified canonical objects
│   └── utils.py
├── evaluate/                  # Run Haiku 4.5 against generated images
│   ├── run_eval.py            # Main evaluation loop
│   ├── prompts.py             # Standardized prompts per task
│   └── score.py               # Automated scoring
├── analyze/                   # Analysis and visualization
│   ├── results_analysis.py
│   └── visualize.py           # Charts/figures for report
├── finetune/                  # Finetuning proposal
│   ├── sample_data/           # Generated sample training data
│   └── data_generation.py     # Script to generate at scale
├── results/                   # Raw results
└── figures/                   # Figures for report
```

---

## Priority Order for Execution

1. **Build image generation + evaluation harness** (foundation)
2. **Broad sweep** across task categories to identify worst areas
3. **Deep characterization** of 2-3 worst blind spots (vary parameters: size, complexity, density)
4. **Generate sample finetuning data** for deep dive category
5. **Write report** once results and figures are ready
