"""Generate chart comparison images for cross-representation data equivalence.

Given the same underlying data, renders two different chart types side by side
and asks whether the data is the same or different. Tests whether the model
can extract actual values from visual encodings rather than relying on
surface-level features.

Sweep axes:
- n_categories: 3-6 (number of data categories)
- chart_pair: (bar, pie), (bar_v, bar_h), (bar, line)
- match: True/False (same vs. different data)
- perturbation_type: swap, shift, replace (for different-data cases)
"""

from __future__ import annotations

import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from generate.base import TaskInstance, ensure_dir, make_instances
from generate.chart_common import COLORS, CATEGORY_POOLS

CHART_PAIRS = [
    ("bar_v", "pie"),
    ("bar_v", "bar_h"),
    ("bar_v", "line"),
]


# --------------- Chart Renderers ---------------

def _render_bar_v(ax, categories, values):
    """Vertical bar chart on given axes."""
    bars = ax.bar(categories, values, color=COLORS[:len(categories)], width=0.6)
    ax.set_ylabel("Value")
    ax.set_ylim(0, max(values) * 1.25)
    ax.tick_params(axis="x", rotation=30 if len(categories) > 5 else 0)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(val), ha="center", va="bottom", fontsize=8)


def _render_bar_h(ax, categories, values):
    """Horizontal bar chart on given axes."""
    y_pos = range(len(categories))
    bars = ax.barh(y_pos, values, color=COLORS[:len(categories)], height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.set_xlabel("Value")
    ax.set_xlim(0, max(values) * 1.25)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                str(val), ha="left", va="center", fontsize=8)


def _render_pie(ax, categories, values):
    """Pie chart on given axes."""
    ax.pie(values, labels=categories, colors=COLORS[:len(categories)],
           autopct=lambda pct: f"{pct:.0f}%", startangle=90, textprops={"fontsize": 8})
    ax.set_aspect("equal")


def _render_line(ax, categories, values):
    """Line chart on given axes."""
    x = range(len(categories))
    ax.plot(x, values, marker="o", color=COLORS[0], linewidth=2)
    for xi, val in zip(x, values):
        ax.text(xi, val + 1.5, str(val), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel("Value")
    ax.set_ylim(0, max(values) * 1.25)
    ax.tick_params(axis="x", rotation=30 if len(categories) > 5 else 0)


RENDERERS = {
    "bar_v": _render_bar_v,
    "bar_h": _render_bar_h,
    "pie": _render_pie,
    "line": _render_line,
}

CHART_DISPLAY_NAMES = {
    "bar_v": "Vertical Bar",
    "bar_h": "Horizontal Bar",
    "pie": "Pie",
    "line": "Line",
}


# --------------- Data Perturbation ---------------

def _perturb_swap(values: list[int]) -> list[int]:
    """Swap two adjacent values."""
    result = values.copy()
    # Pick two values that are different enough to notice
    indices = list(range(len(result)))
    random.shuffle(indices)
    for i in indices:
        j = (i + 1) % len(result)
        if abs(result[i] - result[j]) >= 5:
            result[i], result[j] = result[j], result[i]
            return result
    # Fallback: just swap first two
    result[0], result[1] = result[1], result[0]
    return result


def _perturb_shift(values: list[int]) -> list[int]:
    """Change one value by a noticeable amount (15-35%)."""
    result = values.copy()
    idx = random.randint(0, len(result) - 1)
    direction = random.choice([-1, 1])
    shift = max(5, int(result[idx] * random.uniform(0.15, 0.35)))
    result[idx] = max(5, min(95, result[idx] + direction * shift))
    return result


def _perturb_replace(values: list[int]) -> list[int]:
    """Replace one value with a completely new random value."""
    result = values.copy()
    idx = random.randint(0, len(result) - 1)
    old_val = result[idx]
    # Ensure new value is noticeably different
    while abs(result[idx] - old_val) < 10:
        result[idx] = random.randint(10, 90)
    return result


PERTURBATIONS = {
    "swap": _perturb_swap,
    "shift": _perturb_shift,
    "replace": _perturb_replace,
}


# --------------- Composite Image ---------------

def _make_comparison_image(
    categories: list[str],
    left_values: list[int],
    right_values: list[int],
    left_type: str,
    right_type: str,
    output_path: str,
) -> None:
    """Render two charts side by side as a single image."""
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(14, 5))

    ax_left.set_title(f"Chart A ({CHART_DISPLAY_NAMES[left_type]})", fontsize=11, pad=10)
    ax_right.set_title(f"Chart B ({CHART_DISPLAY_NAMES[right_type]})", fontsize=11, pad=10)

    RENDERERS[left_type](ax_left, categories, left_values)
    RENDERERS[right_type](ax_right, categories, right_values)

    fig.tight_layout(pad=2.0)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)


# --------------- Generator ---------------

def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    n_categories_list: list[int] | None = None,
    chart_pairs: list[tuple[str, str]] | None = None,
    perturbation_types: list[str] | None = None,
) -> list[TaskInstance]:
    """Generate chart comparison images.

    Each config produces one matching pair (same data) and one non-matching pair
    (perturbed data), to ensure balanced yes/no ground truth.
    """
    if n_categories_list is None:
        n_categories_list = [3, 4, 5, 6]
    if chart_pairs is None:
        chart_pairs = CHART_PAIRS
    if perturbation_types is None:
        perturbation_types = list(PERTURBATIONS.keys())

    out = ensure_dir(os.path.join(output_dir, "chart_comparison"))
    instances: list[TaskInstance] = []

    for n_cat in n_categories_list:
        for left_type, right_type in chart_pairs:
            for i in range(n_per_config):
                # Pick category labels
                valid_pools = [p for p in CATEGORY_POOLS if len(p) >= n_cat]
                categories = random.choice(valid_pools)[:n_cat]
                base_values = [random.randint(10, 90) for _ in range(n_cat)]

                # --- Same data (ground truth = Yes) ---
                fname_same = f"cmp_{left_type}_{right_type}_n{n_cat}_same_{i}.png"
                fpath_same = os.path.join(out, fname_same)
                _make_comparison_image(
                    categories, base_values, base_values,
                    left_type, right_type, fpath_same,
                )
                instances.extend(make_instances(
                    fpath_same, "chart_data_match", "Yes",
                    subtask=f"{left_type}_vs_{right_type}_n{n_cat}",
                    metadata={
                        "left_type": left_type, "right_type": right_type,
                        "n_categories": n_cat, "match": True,
                        "categories": categories,
                        "left_values": base_values, "right_values": base_values,
                    },
                ))

                # --- Different data (ground truth = No) ---
                perturb_type = random.choice(perturbation_types)
                perturbed = PERTURBATIONS[perturb_type](base_values)

                fname_diff = f"cmp_{left_type}_{right_type}_n{n_cat}_diff_{perturb_type}_{i}.png"
                fpath_diff = os.path.join(out, fname_diff)
                _make_comparison_image(
                    categories, base_values, perturbed,
                    left_type, right_type, fpath_diff,
                )
                instances.extend(make_instances(
                    fpath_diff, "chart_data_match", "No",
                    subtask=f"{left_type}_vs_{right_type}_n{n_cat}",
                    metadata={
                        "left_type": left_type, "right_type": right_type,
                        "n_categories": n_cat, "match": False,
                        "perturbation": perturb_type,
                        "categories": categories,
                        "left_values": base_values, "right_values": perturbed,
                    },
                ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_categories_list=[4])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.subtask:30s} gt={inst.ground_truth}  {os.path.basename(inst.image_path)}")
