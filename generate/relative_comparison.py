"""Generate relative comparison tasks.

Two approaches:
1. Dedicated bar charts with controlled height differences for parametric sweeps
2. Additional comparison questions on line charts (which series is higher at point X?)

Tests the perceptual primitive of comparing two visual elements at specific positions.
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

from generate.base import TaskInstance, ensure_dir
from evaluate.prompts import get_prompt

COLORS = list(matplotlib.cm.tab10.colors[:10])

CATEGORY_LABELS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
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


def _make_two_line_chart(x_labels, series1_vals, series2_vals, s1_name, s2_name, output_path):
    """Draw a 2-line chart for relative position comparison."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(x_labels))
    ax.plot(x, series1_vals, marker="o", label=s1_name, color=COLORS[0], linewidth=2)
    ax.plot(x, series2_vals, marker="s", label=s2_name, color=COLORS[1], linewidth=2)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    ax.set_ylabel("Value")
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

                    # Question: which highlighted bar is taller?
                    prompt = (
                        f"Look at the two orange/highlighted bars ({categories[i1]} and {categories[i2]}). "
                        f"Which one has a higher value? Answer with the label in curly braces, "
                        f"e.g. {{{categories[0]}}}."
                    )
                    instances.append(TaskInstance(
                        image_path=os.path.abspath(fpath),
                        prompt=prompt,
                        ground_truth=taller,
                        task_type="chart_bar_compare",
                        subtask=f"bar_diff={diff}",
                        metadata={
                            "chart_type": "comparison_bar",
                            "n_bars": n_bars, "value_diff": diff,
                            "show_grid": show_grid,
                            "bar1": categories[i1], "bar1_val": values[i1],
                            "bar2": categories[i2], "bar2_val": values[i2],
                            "taller": taller,
                        },
                    ))

    # --- Part B: Line comparison (which series is higher at point X?) ---
    for n_pts in n_points_list:
        for i in range(n_per_config * 2):  # more instances since less config variation
            x_labels = MONTH_LABELS[:n_pts]
            s1_name, s2_name = SERIES_NAMES[0], SERIES_NAMES[1]

            # Generate two lines that cross each other (so the answer varies by point)
            s1_base = random.randint(20, 50)
            s2_base = random.randint(20, 50)
            s1_slope = random.uniform(-3, 3)
            s2_slope = random.uniform(-3, 3)
            s1_vals = [max(5, min(95, int(s1_base + s1_slope * j + random.randint(-5, 5))))
                       for j in range(n_pts)]
            s2_vals = [max(5, min(95, int(s2_base + s2_slope * j + random.randint(-5, 5))))
                       for j in range(n_pts)]

            fname = f"comp_line_{n_pts}_{i}.png"
            fpath = os.path.join(out, fname)
            _make_two_line_chart(x_labels, s1_vals, s2_vals, s1_name, s2_name, fpath)

            # Pick a random x point and ask which is higher
            x_idx = random.randint(0, n_pts - 1)
            if s1_vals[x_idx] >= s2_vals[x_idx]:
                higher = s1_name
            else:
                higher = s2_name
            gap = abs(s1_vals[x_idx] - s2_vals[x_idx])

            prompt = (
                f"At {x_labels[x_idx]}, which line has a higher value — "
                f"{s1_name} or {s2_name}? "
                f"Answer with the name in curly braces, e.g. {{{s1_name}}}."
            )
            instances.append(TaskInstance(
                image_path=os.path.abspath(fpath),
                prompt=prompt,
                ground_truth=higher,
                task_type="chart_bar_compare",  # reuse text-answer scorer
                subtask=f"line_gap={gap}",
                metadata={
                    "chart_type": "comparison_line",
                    "n_points": n_pts, "query_x": x_labels[x_idx],
                    "s1_val": s1_vals[x_idx], "s2_val": s2_vals[x_idx],
                    "value_gap": gap, "higher": higher,
                },
            ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_bars_list=[5], value_diffs=[2, 10, 40],
                     n_points_list=[6])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.subtask:20s} -> {inst.ground_truth} "
              f"(diff={inst.metadata.get('value_diff', inst.metadata.get('value_gap', '?'))})")
