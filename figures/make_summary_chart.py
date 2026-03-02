"""Generate a summary dot-plot of accuracy across select tasks and primitives."""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------- data: (primitive, task_label, accuracy, n) ----------
# Ordered by primitive, then descending accuracy within primitive
#
# Footnote [1]: "6 tasks" = chart_bar_count, chart_line_count, chart_series_count,
#   table_row_count, diagram_node_count, pie_slice_count (all gen).
data = [
    # Counting / Enumeration
    ("Counting", "Chart bars/series/lines/rows/nodes/slices (6 tasks) [1]", 0.99, 1636),
    ("Counting", "Circles (counts 5-9, gen)", 0.92, 50),
    ("Counting", "Nested squares (depth 2-5, gen)", 0.883, 60),
    ("Counting", "Nested squares (depth 2-5, VAB2)", 0.842, 240),
    ("Counting", "Grid counting (word, VAB2)", 0.811, 264),
    ("Counting", "Circles (counts 5-9, VAB2)", 0.656, 480),
    ("Counting", "Pentagons (counts 5-9, gen)", 0.60, 250),
    ("Counting", "Grid counting (blank, VAB2)", 0.485, 264),
    ("Counting", "Grid counting (blank, gen)", 0.49, 100),

    # Spatial Localization
    ("Spatial", "Table cell / diagram / bar / pie (labeled)", 1.00, 604),
    ("Spatial", "Grouped bar value (2-3 series)", 0.977, 128),
    ("Spatial", "Diagram next step (gen)", 0.942, 120),
    ("Spatial", "Circled letter (VAB2)", 0.824, 624),
    ("Spatial", "Line chart value (5+ series)", 0.643, 384),
    ("Spatial", "Pie value (no % labels)", 0.533, 60),
    ("Spatial", "Grouped bar value (9-10 series)", 0.516, 128),

    # Line / Path Following
    ("Line/Path", "Diagram decision following", 1.00, 240),
    ("Line/Path", "Trend detection (named series)", 0.948, 576),
    ("Line/Path", "Line intersection (3-pt, gen)", 0.90, 30),
    ("Line/Path", "Path tracing (simple, gen)", 0.741, 54),
    ("Line/Path", "Line intersection (3-pt, VAB2)", 0.646, 3600),
    ("Line/Path", "Path tracing (distractor, gen)", 0.562, 80),
    ("Line/Path", "Path tracing (distractor, VAB2)", 0.517, 720),
    ("Line/Path", "Line intersection (4-pt, gen)", 0.325, 40),
    ("Line/Path", "Line intersection (5-pt, gen)", 0.18, 50),

    # Relative Comparison
    ("Comparison", "Table max / bar comparison (diff>=2)", 1.00, 740),
    ("Comparison", "Touching circles (clear, overlap or dist>=0.2)", 1.00, 282),
    ("Comparison", "Cross-chart data match (gen)", 0.933, 240),
    ("Comparison", "Bar comparison (diff=1)", 0.91, 100),
    ("Comparison", "Pie largest slice (no labels)", 0.733, 60),
    ("Comparison", "Touching circles (near-miss, dist 0.01-0.1)", 0.318, 494),

    # Color Discrimination
    ("Color", "Distinct hues / color grid (easy+hard)", 1.00, 230),
    ("Color", "Color grid (very hard)", 0.86, 100),
    ("Color", "Legend match (same family, 5 bars)", 0.62, 50),
    ("Color", "Heatmap value reading", 0.559, 270),
    ("Color", "Color grid (extreme)", 0.21, 100),

    # Text Reading
    ("Text/OCR", "Words (font>=14, all rotations)", 0.99, 300),
    ("Text/OCR", "Words (font=10)", 0.833, 150),
    ("Text/OCR", "Numbers (font=10)", 0.55, 40),
    ("Text/OCR", "Words (font=8)", 0.453, 150),
    ("Text/OCR", "Numbers (font=8)", 0.20, 40),

    # Prior Bias Override
    ("Prior Bias", "Title trend conflict", 1.00, 40),
    ("Prior Bias", "Annotation conflict", 0.75, 40),
    ("Prior Bias", "Flags -- stars (VAB2)", 0.455, 156),
    ("Prior Bias", "Flags -- stripes (VAB2)", 0.298, 84),
    ("Prior Bias", "Logos (shoe, VAB2)", 0.056, 144),
    ("Prior Bias", "Value label conflict", 0.00, 40),
    ("Prior Bias", "Logos (car, VAB2)", 0.00, 270),
]

# ---------- colors per primitive ----------
COLORS = {
    "Counting":   "#4E79A7",
    "Spatial":    "#F28E2B",
    "Line/Path":  "#E15759",
    "Comparison": "#76B7B2",
    "Color":      "#59A14F",
    "Text/OCR":   "#EDC948",
    "Prior Bias": "#B07AA1",
}

# ---------- build figure ----------
fig, ax = plt.subplots(figsize=(10, 15))

# Sort: group by primitive (in order above), within each group descending accuracy
primitives_order = list(dict.fromkeys(d[0] for d in data))  # preserve insertion order
sorted_data = []
for prim in reversed(primitives_order):
    group = [(p, t, a, n) for p, t, a, n in data if p == prim]
    group.sort(key=lambda x: x[2])  # ascending so highest is at top of group
    sorted_data.extend(group)

labels = [d[1] for d in sorted_data]
accs = [d[2] for d in sorted_data]
colors = [COLORS[d[0]] for d in sorted_data]
ns = [d[3] for d in sorted_data]
prims = [d[0] for d in sorted_data]

y_pos = np.arange(len(sorted_data))

# Draw dots
ax.scatter(accs, y_pos, c=colors, s=80, zorder=3, edgecolors="white", linewidth=0.5)

# Draw lines from 0 to dot
for i, (acc, color) in enumerate(zip(accs, colors)):
    ax.plot([0, acc], [i, i], color=color, linewidth=1.5, alpha=0.4, zorder=2)

# Labels
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xlabel("Accuracy", fontsize=11, fontweight="bold")
ax.set_xlim(-0.05, 1.08)
ax.set_ylim(-0.8, len(sorted_data) - 0.2)

# Format x-axis as percentage
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))

# Add accuracy labels next to dots
for i, (acc, n) in enumerate(zip(accs, ns)):
    ax.text(acc + 0.015, i, f"{acc:.0%}", va="center", ha="left", fontsize=7.5,
            color="#333333")

# Gridlines
ax.axvline(x=0.50, color="#cccccc", linewidth=0.8, linestyle="--", zorder=1)
ax.axvline(x=0.90, color="#cccccc", linewidth=0.8, linestyle="--", zorder=1)
ax.grid(axis="x", alpha=0.15, zorder=1)

# Add primitive group separators
prev_prim = None
for i, prim in enumerate(prims):
    if prev_prim is not None and prim != prev_prim:
        ax.axhline(y=i - 0.5, color="#aaaaaa", linewidth=0.6, linestyle="-")
    prev_prim = prim

# Legend
handles = [mpatches.Patch(color=COLORS[p], label=p) for p in primitives_order]
ax.legend(handles=handles, loc="lower right", fontsize=8, framealpha=0.9,
          title="Primitive", title_fontsize=9)

ax.set_title("Haiku 4.5 Vision: Accuracy Across Select Tasks", fontsize=13,
             fontweight="bold", pad=12)

plt.tight_layout()
plt.savefig("figures/accuracy_summary.png", dpi=180, bbox_inches="tight",
            facecolor="white")
print("Saved figures/accuracy_summary.png")
