---
name: report-compile
description: Compile all 7 primitive summaries into a single HTML report for Google Docs
---

Compile all primitive summaries into a single condensed HTML report at `report.html` (project root).

## Process

### 1. Read all summaries

Read all 7 files in `summaries/`:
- `counting_enumeration_summary.md`
- `spatial_localization_summary.md`
- `line_path_following_summary.md`
- `relative_comparison_summary.md`
- `color_discrimination_summary.md`
- `text_reading_summary.md`
- `prior_bias_override_summary.md` (includes visual-textual consistency: value label, title trend, and annotation conflicts)

Also read `docs/task_inventory.md` for the task list and `results/finetuning_plan.md` for training pipeline details.

### 2. Update and regenerate the summary chart

Read `figures/make_summary_chart.py`. Update the `data` array to reflect the current accuracies from the summaries you just read. Then run:

```bash
.venv/bin/python figures/make_summary_chart.py
```

This regenerates `figures/accuracy_summary.png`.

### 2.5. Chart data rules

When updating the `data` array in `make_summary_chart.py` or writing body text:

1. **Use "VAB2" not "HF"** in all rendered labels. "VAB2" stands for "VLMs Are Blind/Biased" and refers to the HuggingFace benchmark datasets. Never use "HF" in chart labels or report body text.
2. **Never combine gen + VAB2 into a single chart row.** If a task has both generated and VAB2 data, they must appear as separate rows with distinct labels (e.g., `"Nested squares (depth 2-5, gen)"` and `"Nested squares (depth 2-5, VAB2)"`).
3. **Use difficulty names, not ΔL values**, for color discrimination tasks: easy, hard, very_hard, near_threshold, extreme. Put the ΔL-to-difficulty mapping only in the appendix.
4. **Use distance ratio, not pixels**, for touching circles parameters (e.g., "dist=0.10" not "10px gap").
5. **`conflict_legend_color` is removed** — it was not adversarial (bars had value labels). Do not include it.
6. **Use exact accuracies** (e.g., 0.977 not 0.97) so the chart displays rounded percentages correctly. Verify every number against the actual results JSONL files.
7. **Only use v2 results files** when both v1 and v2 exist for the same task.

### 3. Regenerate error composite figures

For each primitive, check if the corresponding `figures/make_*_errors.py` script exists and regenerate:

```bash
.venv/bin/python -m figures.make_counting_enumeration_errors
.venv/bin/python -m figures.make_spatial_localization_errors
.venv/bin/python -m figures.make_line_path_following_errors
.venv/bin/python -m figures.make_relative_comparison_errors
.venv/bin/python -m figures.make_color_errors
.venv/bin/python -m figures.make_text_reading_errors
.venv/bin/python -m figures.make_prior_bias_errors
```

Review each generated image for stale references (ΔL values, pixel measurements, removed tasks).

### 4. Write the report header

The report starts with:

```html
<h2>Categorization into Primitives</h2>
<p>We first consider which capabilities are important for the stated goals.</p>
```

Followed by the overview table.

### 4.5. Overview table format

The overview table uses `class="overview"` and has 3 columns: Perceptual Primitive, Example Applications (Prompts), Example Eval Tasks. Items in columns 2 and 3 must use **numbered `<ol>` lists**, not `<br>`-separated text. Include this CSS for tight spacing:

```css
table.overview td ol {
  margin: 2px 0;
  padding-left: 18px;
  line-height: 1.25;
}
table.overview td ol li {
  margin-bottom: 1px;
  font-size: 9pt;
}
```

### 5. Write per-section bullets

For each of the 7 primitives, write bullets following these rules:

- **1 "Solved" bullet**: ceiling tasks with near-100% accuracy. Use the `<span class="regime-label solved">Solved</span>` tag. If no ceiling tasks exist, use `<span class="regime-label broken">No ceiling tasks</span>`.
- **2-3 blind-spot bullets**: each is a `<strong>bolded claim</strong>` followed by 1 sentence of evidence with concrete numbers. Max 2 sentences per bullet.
- **Budget**: ~150 words per section max.
- Focus on blind spots and surprises, not expected behavior.
- **Use "VAB2" not "HF"** when referring to the benchmark datasets in body text.
- **Use difficulty names** (not ΔL) for color discrimination.
- **Use distance ratio** (not px) for touching circles.

Section order (7 sections):
1. Counting / Enumeration
2. Spatial Localization
3. Line / Path Following
4. Relative Comparison
5. Color Discrimination
6. Text Reading (OCR)
7. Prior / Bias Override (includes value label conflicts, title/trend conflicts, annotation conflicts — NOT legend color conflicts)

For each section, after the bullet list, embed the error composite figure if it exists.

### 6. Write appendices

After the 7 primitive sections, add two appendix tables:

#### Appendix A: Task Inventory
`<h2>Appendix: Task Inventory</h2>` with a `class="overview"` table:
- Columns: Task, Primitive, *n*, Axes of Variation
- Populate from results JSONL files (group by task_type, count instances, extract varying metadata keys)
- Sort by primitive, then alphabetically by task name
- Add a total row at the bottom

#### Appendix B: Benchmark Comparison
`<h2>Appendix: Benchmark Comparison</h2>` with a `class="overview"` table:
- Columns: Benchmark, Task, Best Paper Model, Paper Acc., Haiku 4.5 Acc., *n*
- VLMs Are Blind (ACCV 2024) tasks: compare against best of GPT-4o, Gemini 1.5 Pro, Sonnet 3, Sonnet 3.5
- VLMs Are Biased (ICLR 2026) tasks: compare against best of Gemini 2.5 Pro, Sonnet 3.7, GPT-4.1, o3, o4-mini
- Bold the higher accuracy in each row
- Compute Haiku 4.5 numbers from `results/blind_*_results.jsonl` and `results/biased_benchmark_results.jsonl`
- Add a footnote summarizing wins/losses

### 7. Embed images as base64

After writing the HTML with `<img src="figures/...">` tags, run `figures/embed_images.py` to produce a self-contained version with base64 data URIs:

```bash
.venv/bin/python figures/embed_images.py report.html
```

This rewrites `report.html` in-place, replacing each `src="figures/foo.png"` with an inline `src="data:image/png;base64,..."`. The result is a single self-contained HTML file whose images survive copy-paste into Google Docs.

### 8. Output

Print the output path (`report.html`). The user will open in a browser, Cmd+A, Cmd+C, paste into Google Docs. Note: `report.html` lives at the project root, NOT in `results/` (which is reserved for JSONL data only).
