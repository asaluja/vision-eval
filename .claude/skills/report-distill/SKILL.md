---
name: report-distill
description: Distill a detailed evaluation summary .md file into a copy-pastable 1-page report section
argument-hint: <path-to-summary.md>
---

Distill the detailed evaluation summary at `$ARGUMENTS` into a concise, copy-pastable report section targeting ~1 page in Google Docs.

## Output format

Produce exactly three things, in this order:

### 1. CSV table
A CSV table (with header row) summarizing accuracy on each task. The user will paste this into Google Sheets and then copy into Google Docs as a formatted table. Keep task names short. Include columns: Task, Accuracy, n.

### 2. Bullet points (3-5)
Each bullet is a standalone paragraph starting with a **bolded claim** followed by 1-2 sentences of evidence. Do NOT prefix with `-` or `*` — the user will apply bullet formatting in Google Docs. Separate bullets with blank lines.

Focus on:
- What's solved (near-100% tasks)
- The specific failure modes with concrete numbers
- Any surprising or counterintuitive findings

### 3. Composite error figure
Create a compact composite figure (3 panels side-by-side) showing the most illustrative failure cases. Save it to `figures/<primitive>_errors.png`.

For each panel:
- Show the image (crop whitespace if needed)
- Below it, show: GT value, Model output, and a 1-line explanation
- Keep it compact — the figure should fit as a half-width image in a Google Doc

Use matplotlib with `Agg` backend. Use `.venv/bin/python` to run the script.

## Process

1. Read the summary .md file
2. Read the underlying `results/*_results.jsonl` files to find concrete error cases (filter for `correct: false` or `correct: 0`)
3. Identify the 3 most illustrative/diverse failure cases — pick errors that represent different failure modes, not 3 instances of the same bug
4. Look at the actual images for those error cases to verify they're visually clear
5. Generate the CSV, bullets, and figure
6. Output the CSV and bullets as text in the conversation (for copy-paste) and save the figure to disk
