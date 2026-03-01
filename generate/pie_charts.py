"""Generate pie chart images for counting, value estimation, and comparison.

Pie charts test angular/proportional reasoning — a fundamentally different
perceptual channel than bar height or line position. Key axes:
- n_slices: 3-8 (counting difficulty)
- show_percentages: whether % labels are shown (value reading shortcut)
- show_labels: whether category labels are shown

Task types generated:
- pie_slice_count: count the number of slices
- pie_value_estimate: estimate percentage of a named slice (no % labels)
- pie_slice_compare: identify largest/smallest slice (no % labels)
"""

from __future__ import annotations

import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from generate.base import TaskInstance, ensure_dir, make_instances
from generate.chart_common import COLORS, CATEGORY_POOLS


def _render_pie(categories, values, show_percentages, show_labels, output_path):
    """Render a pie chart with controlled label visibility."""
    fig, ax = plt.subplots(figsize=(7, 7))

    labels = categories if show_labels else [None] * len(categories)
    autopct = (lambda pct: f"{pct:.0f}%") if show_percentages else None

    wedges, texts, *autotexts = ax.pie(
        values,
        labels=labels,
        autopct=autopct,
        colors=COLORS[:len(categories)],
        startangle=random.randint(0, 359),
        textprops={"fontsize": 10},
    )

    # Add legend when labels are hidden (so model can still identify slices by color)
    if not show_labels:
        ax.legend(wedges, categories, loc="upper left", fontsize=9,
                  bbox_to_anchor=(0.85, 1.0))

    ax.set_aspect("equal")
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _generate_values(n_slices: int) -> list[int]:
    """Generate slice values that sum to 100 with reasonable distribution.

    Ensures no slice is below 3% (too small to see) and at least two slices
    are within 5% of each other (to create comparison difficulty).
    """
    while True:
        # Generate random proportions
        raw = [random.randint(5, 50) for _ in range(n_slices)]
        total = sum(raw)
        # Normalize to sum to 100
        values = [round(v / total * 100) for v in raw]
        # Fix rounding to sum exactly to 100
        diff = 100 - sum(values)
        values[0] += diff

        if all(v >= 3 for v in values):
            return values


def generate(
    n_per_config: int = 3,
    output_dir: str = "generate/images",
    n_slices_list: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate pie chart images with multiple question types per chart."""
    if n_slices_list is None:
        n_slices_list = [3, 4, 5, 6, 7, 8]

    out = ensure_dir(os.path.join(output_dir, "pie_charts"))
    instances: list[TaskInstance] = []

    for n_slices in n_slices_list:
        for i in range(n_per_config):
            valid_pools = [p for p in CATEGORY_POOLS if len(p) >= n_slices]
            categories = random.choice(valid_pools)[:n_slices]
            values = _generate_values(n_slices)

            # --- Task 1: Slice counting (no labels, no percentages) ---
            fname_count = f"pie_count_n{n_slices}_{i}.png"
            fpath_count = os.path.join(out, fname_count)
            _render_pie(categories, values,
                        show_percentages=False, show_labels=False,
                        output_path=fpath_count)

            instances.extend(make_instances(
                fpath_count, "pie_slice_count", n_slices,
                subtask=f"pie_count_n{n_slices}",
                metadata={
                    "n_slices": n_slices,
                    "categories": categories,
                    "values": values,
                    "show_percentages": False,
                    "show_labels": False,
                },
            ))

            # --- Task 2: Value estimation (labels, no percentages) ---
            fname_val = f"pie_value_n{n_slices}_{i}.png"
            fpath_val = os.path.join(out, fname_val)
            _render_pie(categories, values,
                        show_percentages=False, show_labels=True,
                        output_path=fpath_val)

            # Query a random slice
            q_idx = random.randint(0, n_slices - 1)
            instances.extend(make_instances(
                fpath_val, "pie_value_estimate", values[q_idx],
                subtask=f"pie_value_n{n_slices}",
                metadata={
                    "n_slices": n_slices,
                    "categories": categories,
                    "values": values,
                    "query_category": categories[q_idx],
                    "show_percentages": False,
                    "show_labels": True,
                },
                category=categories[q_idx],
            ))

            # --- Task 3: Also test value estimation WITH percentages (ceiling) ---
            fname_val_pct = f"pie_value_pct_n{n_slices}_{i}.png"
            fpath_val_pct = os.path.join(out, fname_val_pct)
            _render_pie(categories, values,
                        show_percentages=True, show_labels=True,
                        output_path=fpath_val_pct)

            instances.extend(make_instances(
                fpath_val_pct, "pie_value_estimate", values[q_idx],
                subtask=f"pie_value_pct_n{n_slices}",
                metadata={
                    "n_slices": n_slices,
                    "categories": categories,
                    "values": values,
                    "query_category": categories[q_idx],
                    "show_percentages": True,
                    "show_labels": True,
                },
                category=categories[q_idx],
            ))

            # --- Task 4: Comparison — largest slice (no percentages) ---
            max_idx = values.index(max(values))
            instances.extend(make_instances(
                fpath_val, "pie_slice_compare", categories[max_idx],
                subtask=f"pie_compare_n{n_slices}",
                metadata={
                    "n_slices": n_slices,
                    "categories": categories,
                    "values": values,
                    "max_idx": max_idx,
                    "max_value": values[max_idx],
                    "show_percentages": False,
                },
            ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_slices_list=[4, 6])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} {inst.subtask:25s} gt={inst.ground_truth}")
