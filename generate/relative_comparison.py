"""Generate relative comparison tasks.

Two approaches:
1. Dedicated bar charts with controlled height differences for parametric sweeps
2. Additional comparison questions on line charts (which series is higher at point X?)

Tests the perceptual primitive of comparing two visual elements at specific positions.
"""

from __future__ import annotations

import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from generate.base import ensure_dir, make_instances
from generate.chart_common import COLORS, MONTH_LABELS

CATEGORY_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
SERIES_NAMES = ["Revenue", "Cost", "Profit"]


def _make_comparison_bars(categories, values, highlight_pair, show_grid, output_path):
    """Draw a bar chart where two bars are highlighted for comparison."""
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4472C4"] * len(categories)
    # Highlight the two comparison bars
    i1, i2 = highlight_pair
    colors[i1] = "#ED7D31"
    colors[i2] = "#ED7D31"

    ax.bar(categories, values, color=colors, width=0.6)
    if show_grid:
        ax.yaxis.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)
    ax.set_ylabel("Value")
    ax.set_ylim(0, max(values) * 1.15)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _make_two_line_chart(x_labels, series1_vals, series2_vals, s1_name, s2_name, output_path, y_max=None):
    """Draw a 2-line chart for relative position comparison."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(x_labels))
    ax.plot(x, series1_vals, marker="o", label=s1_name, color=COLORS[0], linewidth=2)
    ax.plot(x, series2_vals, marker="s", label=s2_name, color=COLORS[1], linewidth=2)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    ax.set_ylabel("Value")
    if y_max is not None:
        ax.set_ylim(0, y_max)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    # Bar comparison params
    n_bars_list: list[int] | None = None,
    value_diffs: list[int] | None = None,
    # Line comparison params
    n_points_list: list[int] | None = None,
    line_gaps: list[int] | None = None,
    y_maxes: list[int | None] | None = None,
) -> list[TaskInstance]:
    """Generate relative comparison tasks.

    Part A: Bar charts with controlled height differences.
    Part B: Two-line charts with "which is higher at X?" questions.
    """
    if n_bars_list is None:
        n_bars_list = [4, 6, 8, 10, 12]
    if value_diffs is None:
        # Key axis: how different are the two bars?
        value_diffs = [1, 2, 5, 10, 20, 40]
    if n_points_list is None:
        n_points_list = [5, 8]
    if line_gaps is None:
        line_gaps = [1, 2, 5, 10, 20]
    if y_maxes is None:
        y_maxes = [None, 100, 200]  # None=auto (easy), 100=moderate, 200=compressed (hard)

    out = ensure_dir(os.path.join(output_dir, "relative_comparison"))
    instances = []

    # --- Part A: Bar comparison with controlled difficulty ---
    for n_bars in n_bars_list:
        for diff in value_diffs:
            for show_grid in [False, True]:
                for i in range(n_per_config):
                    categories = CATEGORY_LABELS[:n_bars]
                    # Generate values so two bars differ by exactly `diff`
                    values = [random.randint(20, 80) for _ in range(n_bars)]
                    # Pick two bars to compare
                    i1, i2 = random.sample(range(n_bars), 2)
                    # Set them so they differ by `diff` in a random direction
                    # For small diffs, use higher base values so the % difference is smaller
                    if diff <= 2:
                        base_val = random.randint(60, 95)
                    else:
                        base_val = random.randint(25, 75)
                    if random.random() < 0.5:
                        values[i1] = base_val + diff
                        values[i2] = base_val
                        taller = categories[i1]
                    else:
                        values[i1] = base_val
                        values[i2] = base_val + diff
                        taller = categories[i2]

                    fname = f"comp_bar_{n_bars}_d{diff}_g{int(show_grid)}_{i}.png"
                    fpath = os.path.join(out, fname)
                    _make_comparison_bars(categories, values, (i1, i2), show_grid, fpath)

                    instances.extend(make_instances(
                        fpath, "relative_bar_compare", taller,
                        subtask=f"bar_diff={diff}",
                        metadata={
                            "chart_type": "comparison_bar",
                            "n_bars": n_bars, "value_diff": diff,
                            "show_grid": show_grid,
                            "bar1": categories[i1], "bar1_val": values[i1],
                            "bar2": categories[i2], "bar2_val": values[i2],
                            "taller": taller,
                        },
                        bar1=categories[i1], bar2=categories[i2],
                    ))

    # --- Part B: Line comparison (which series is higher at point X?) ---
    # Sweeps gap and y_max explicitly, like bar comparison sweeps value_diff.
    # y_max=None uses matplotlib auto-scale (easy — gap fills the viewport).
    # y_max=100 or 200 forces a fixed range (hard — gap is visually compressed).
    for n_pts in n_points_list:
        for gap_target in line_gaps:
            for y_max in y_maxes:
                for i in range(n_per_config):
                    x_labels = MONTH_LABELS[:n_pts]
                    s1_name, s2_name = SERIES_NAMES[0], SERIES_NAMES[1]

                    # Choose query point index up front
                    x_idx = random.randint(0, n_pts - 1)

                    # Build lines so the two series differ by exactly gap_target at x_idx.
                    # Base values stay in [20, 80] to leave headroom for the gap.
                    base = random.randint(20, 80 - gap_target)
                    if random.random() < 0.5:
                        s1_query = base + gap_target
                        s2_query = base
                        higher = s1_name
                    else:
                        s1_query = base
                        s2_query = base + gap_target
                        higher = s2_name

                    # Build full series: random walk anchored at the query values
                    def _build_series(query_val, n, anchor_idx):
                        vals = [0] * n
                        vals[anchor_idx] = query_val
                        for j in range(anchor_idx - 1, -1, -1):
                            vals[j] = max(5, min(95, vals[j + 1] + random.randint(-8, 8)))
                        for j in range(anchor_idx + 1, n):
                            vals[j] = max(5, min(95, vals[j - 1] + random.randint(-8, 8)))
                        return vals

                    s1_vals = _build_series(s1_query, n_pts, x_idx)
                    s2_vals = _build_series(s2_query, n_pts, x_idx)

                    y_tag = f"y{y_max}" if y_max is not None else "yauto"
                    fname = f"comp_line_{n_pts}_g{gap_target}_{y_tag}_{i}.png"
                    fpath = os.path.join(out, fname)
                    _make_two_line_chart(x_labels, s1_vals, s2_vals, s1_name, s2_name, fpath, y_max=y_max)

                    instances.extend(make_instances(
                        fpath, "relative_line_compare", higher,
                        subtask=f"gap={gap_target}_y={y_tag}",
                        metadata={
                            "chart_type": "comparison_line",
                            "n_points": n_pts, "query_x": x_labels[x_idx],
                            "s1_val": s1_vals[x_idx], "s2_val": s2_vals[x_idx],
                            "value_gap": gap_target, "y_max": y_max, "higher": higher,
                        },
                        series1=s1_name, series2=s2_name, x_point=x_labels[x_idx],
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_bars_list=[5], value_diffs=[2, 10, 40],
                     n_points_list=[5], line_gaps=[1, 5, 20], y_maxes=[None, 100, 200])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.subtask:30s} -> {inst.ground_truth}")
