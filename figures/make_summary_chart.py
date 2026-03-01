"""Generate a summary dot-plot of accuracy across all tasks and primitives."""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------- data: (primitive, task_label, accuracy, n) ----------
# Ordered by primitive, then descending accuracy within primitive
data = [
    # Counting / Enumeration
    ("Counting", "Chart bars/series/lines/rows/nodes/slices (6 tasks)", 0.99, 1636),
    ("Counting", "Circles (counts 5-9, gen)", 0.90, 50),
    ("Counting", "Nested squares (depth 2-5)", 0.85, 306),
    ("Counting", "HF circles (counts 5-9)", 0.66, 480),
    ("Counting", "Grid counting (blank)", 0.62, 638),
    ("Counting", "Pentagons (counts 5-9, gen)", 0.60, 250),

    # Spatial Localization
    ("Spatial", "Table cell / diagram / bar / pie (labeled)", 1.00, 904),
    ("Spatial", "Grouped bar value (2-3 series)", 0.97, 128),
    ("Spatial", "Circled letter (HF)", 0.82, 624),
    ("Spatial", "Line chart value (5+ series)", 0.65, 384),
    ("Spatial", "Pie value (no % labels)", 0.53, 60),
    ("Spatial", "Grouped bar value (9-10 series)", 0.51, 128),

    # Line / Path Following
    ("Line/Path", "Diagram decision following", 1.00, 450),
    ("Line/Path", "Trend detection (named series)", 0.95, 576),
    ("Line/Path", "Intersection counting (3-pt lines)", 0.65, 3660),
    ("Line/Path", "Path counting (distractor mode)", 0.53, 800),
    ("Line/Path", "Intersection counting (5-pt lines)", 0.18, 50),

    # Relative Comparison
    ("Comparison", "Table max / bar comparison (diff>=2)", 1.00, 740),
    ("Comparison", "Touching circles (gap>=15px)", 1.00, 300),
    ("Comparison", "Bar comparison (diff=1)", 0.91, 100),
    ("Comparison", "Pie largest slice (no labels)", 0.73, 60),
    ("Comparison", "Touching circles (gap 1-12px)", 0.15, 350),

    # Color Discrimination
    ("Color", "Distinct hues / color grid (DL>=16)", 1.00, 230),
    ("Color", "Color grid (DL~10)", 0.86, 100),
    ("Color", "Legend match (same family, 5 bars)", 0.62, 50),
    ("Color", "Heatmap value reading", 0.56, 270),
    ("Color", "Color grid (DL~5)", 0.21, 100),

    # Text Reading
    ("Text/OCR", "Words (font>=14, all rotations)", 0.99, 300),
    ("Text/OCR", "Words (font=10)", 0.83, 150),
    ("Text/OCR", "Numbers (font=10)", 0.55, 40),
    ("Text/OCR", "Words (font=8)", 0.45, 150),
    ("Text/OCR", "Numbers (font=8)", 0.20, 40),

    # Prior Bias Override
    ("Prior Bias", "Flags (HF)", 0.40, 240),
    ("Prior Bias", "Patterned grid (remove anomaly)", 0.31, 126),
    ("Prior Bias", "Logos (shoe, HF)", 0.056, 144),
    ("Prior Bias", "Patterned grid (add anomaly)", 0.00, 126),
    ("Prior Bias", "Logos (car, HF)", 0.00, 270),

    # Visual-Textual Consistency
    ("Grounding", "Title trend / legend color conflict", 1.00, 80),
    ("Grounding", "Annotation conflict", 0.75, 40),
    ("Grounding", "Value label conflict", 0.00, 40),
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
    "Grounding":  "#FF9DA7",
}

# ---------- build figure ----------
fig, ax = plt.subplots(figsize=(10, 12))

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

ax.set_title("Haiku 4.5 Vision: Accuracy Across All Tasks", fontsize=13,
             fontweight="bold", pad=12)

plt.tight_layout()
plt.savefig("figures/accuracy_summary.png", dpi=180, bbox_inches="tight",
            facecolor="white")
print("Saved figures/accuracy_summary.png")
