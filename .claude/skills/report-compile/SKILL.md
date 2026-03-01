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
- `prior_bias_override_summary.md` (includes visual-textual consistency: value label, title trend, legend color, and annotation conflicts)

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

### 3. Write per-section bullets

For each of the 7 primitives, write bullets following these rules:

- **1 "Solved" bullet**: ceiling tasks with near-100% accuracy. Use the `<span class="regime-label solved">Solved</span>` tag. If no ceiling tasks exist, use `<span class="regime-label broken">No ceiling tasks</span>`.
- **2-3 blind-spot bullets**: each is a `<strong>bolded claim</strong>` followed by 1 sentence of evidence with concrete numbers. Max 2 sentences per bullet.
- **Budget**: ~150 words per section max.
- Focus on blind spots and surprises, not expected behavior.
- **Use "VAB2" not "HF"** when referring to the benchmark datasets in body text.

### 4. Compose `report.html`

Use this HTML template structure:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    font-family: 'Google Sans', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.45;
    max-width: 7.5in;
    margin: 0.5in auto;
    color: #222;
  }
  h1 {
    font-size: 16pt;
    margin-bottom: 4px;
  }
  h2 {
    font-size: 12pt;
    margin-top: 14px;
    margin-bottom: 4px;
    color: #1a1a1a;
    border-bottom: 1px solid #ddd;
    padding-bottom: 2px;
  }
  ul {
    margin-top: 3px;
    margin-bottom: 8px;
    padding-left: 20px;
  }
  li {
    margin-bottom: 5px;
  }
  img {
    width: 100%;
    margin: 8px 0;
  }
  .caption {
    font-size: 9pt;
    color: #666;
    text-align: center;
    margin-top: -4px;
    margin-bottom: 10px;
  }
  strong { color: #111; }
  .regime-label {
    display: inline-block;
    font-size: 9pt;
    font-weight: bold;
    padding: 1px 6px;
    border-radius: 3px;
    margin-right: 4px;
  }
  .solved { background: #d4edda; color: #155724; }
  .degrading { background: #fff3cd; color: #856404; }
  .broken { background: #f8d7da; color: #721c24; }
  table.overview {
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
    margin: 10px 0 16px 0;
  }
  table.overview th {
    background: #f5f5f5;
    font-weight: bold;
    text-align: left;
    padding: 5px 8px;
    border: 1px solid #ccc;
  }
  table.overview td {
    padding: 5px 8px;
    border: 1px solid #ccc;
    vertical-align: top;
  }
  table.overview tr:nth-child(even) {
    background: #fafafa;
  }
</style>
</head>
<body>

<h1>Per-Primitive Findings</h1>

<!-- Overview table: 7 primitives with example applications and eval tasks.
     Populate from task_inventory.md (docs/task_inventory.md) and the summaries.
     Use this exact structure: -->
<table class="overview">
<tr>
  <th>Perceptual Primitive</th>
  <th>Example Applications (Prompts)</th>
  <th>Example Eval Tasks</th>
</tr>
<!-- One <tr> per primitive (7 rows). Example Eval Tasks must reflect
     the tasks actually run (see docs/task_inventory.md).
     Prior / Bias Override row includes visual-textual consistency tasks. -->
</table>

<img src="figures/accuracy_summary.png" alt="Accuracy summary across all tasks">
<div class="caption">Figure 1. Accuracy across all evaluated tasks, grouped by perceptual primitive. Dashed lines at 50% and 90%.</div>

<!-- 7 sections: one <h2> + <ul> per primitive -->
<!-- Embed per-primitive error figures where they exist: -->
<!-- <img src="figures/<primitive>_errors.png"> -->

</body>
</html>
```

Section order (7 sections — visual-textual consistency is folded into Prior / Bias Override):
1. Counting / Enumeration
2. Spatial Localization
3. Line / Path Following
4. Relative Comparison
5. Color Discrimination
6. Text Reading (OCR)
7. Prior / Bias Override (includes visual-textual consistency: value label conflicts, title/trend conflicts, legend color conflicts, annotation conflicts)

For each section, after the bullet list, check if `figures/<primitive>_errors.png` exists and embed it if so (e.g., `figures/counting_enumeration_errors.png`, `figures/spatial_localization_errors.png`). For Prior / Bias Override, embed both `figures/prior_bias_override_errors.png` and `figures/text_visual_consistency_errors.png` if both exist (this section merges two sources of content).

### 4.5. Review and update figures

Before embedding, review all `.png` files in `figures/` that are candidates for inclusion:

- **Read each figure** to visually inspect what it shows.
- **Check if it's still accurate** — does it reflect the latest data in the summaries? If a summary was updated (e.g., pie charts added to counting) but the figure wasn't regenerated, the figure is stale.
- **Check if it's relevant** — does it add information beyond what the bullets already say? Error composite images showing specific failure cases are high-value. Generic accuracy bar charts that just repeat the numbers in the text are low-value.
- **Regenerate stale figures** by finding and running the corresponding `figures/make_*.py` script with updated data.
- **Drop irrelevant figures** — don't embed a figure just because it exists. Every figure should earn its space by showing something the text can't easily convey (e.g., visual error patterns, accuracy heatmaps by parameter, example failure cases).

### 5. Embed images as base64

After writing the HTML with `<img src="figures/...">` tags, run `figures/embed_images.py` to produce a self-contained version with base64 data URIs:

```bash
.venv/bin/python figures/embed_images.py report.html
```

This rewrites `report.html` in-place, replacing each `src="figures/foo.png"` with an inline `src="data:image/png;base64,..."`. The result is a single self-contained HTML file whose images survive copy-paste into Google Docs.

### 6. Output

Print the output path (`report.html`). The user will open in a browser, Cmd+A, Cmd+C, paste into Google Docs. Note: `report.html` lives at the project root, NOT in `results/` (which is reserved for JSONL data only).
