"""Generate charts with planted text-visual contradictions.

Tests whether the model grounds its answers in the visual content or
just reads and trusts the text annotations. Each subtask type creates
a chart where some text element (label, title, legend, annotation)
contradicts the visual rendering. Ground truth is always the VISUAL
truth; metadata tracks what the text-reliant answer would be.

Subtask types:
- conflict_value_label: bar height ≠ its text label
- conflict_title_trend: chart title contradicts the visible trend
- conflict_legend_color: legend maps colors to wrong series names
- conflict_annotation: "Highest" arrow points to wrong bar
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

SERIES_PAIRS = [
    ("Revenue", "Cost"),
    ("Sales", "Returns"),
    ("Imports", "Exports"),
    ("Online", "In-Store"),
]

TREND_TITLES = {
    "increasing": [
        "Declining {metric} Over Time",
        "{metric} Decreasing Steadily",
        "Downward Trend in {metric}",
    ],
    "decreasing": [
        "Rising {metric} Over Time",
        "{metric} Increasing Steadily",
        "Upward Trend in {metric}",
    ],
}

METRIC_NAMES = ["Revenue", "Sales", "Output", "Performance", "Growth"]


# --------------- Renderers ---------------

def _render_value_label_conflict(categories, true_values, display_labels, output_path):
    """Bar chart where some bars have wrong text labels.

    true_values: actual bar heights.
    display_labels: what's shown as text above each bar (some differ from true_values).
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, true_values, color=COLORS[:len(categories)], width=0.6)

    for bar, label in zip(bars, display_labels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(label), ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Value")
    ax.set_ylim(0, max(true_values) * 1.2)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _render_title_trend_conflict(x_labels, values, title, output_path):
    """Line chart with a title that contradicts the visible trend."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(x_labels))
    ax.plot(x, values, marker="o", color=COLORS[0], linewidth=2)

    for xi, val in zip(x, values):
        ax.text(xi, val + 1.5, str(val), ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("Value")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _render_legend_color_conflict(categories, data, true_names, swapped_names, output_path):
    """Grouped bar chart where legend labels are swapped.

    data: (2, n_categories) — two series.
    true_names: actual series identities (e.g., ["Revenue", "Cost"]).
    swapped_names: what the legend shows (reversed).
    The bars are rendered in true_names order, but the legend says swapped_names.
    """
    n_cat = len(categories)
    x = np.arange(n_cat)
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    # Render bars with true data ordering but swapped legend labels
    bars1 = ax.bar(x - width / 2, data[0], width, color=COLORS[0], label=swapped_names[0])
    bars2 = ax.bar(x + width / 2, data[1], width, color=COLORS[1], label=swapped_names[1])

    # Add value labels
    for bar_group in [bars1, bars2]:
        for bar in bar_group:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    str(int(bar.get_height())), ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel("Value")
    ax.legend()
    ax.set_ylim(0, max(max(data[0]), max(data[1])) * 1.2)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _render_annotation_conflict(categories, values, wrong_idx, output_path):
    """Bar chart with 'Highest' annotation pointing to the wrong bar."""
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, values, color=COLORS[:len(categories)], width=0.6)

    # Value labels on all bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(val), ha="center", va="bottom", fontsize=9)

    # Add misleading annotation arrow to wrong bar
    wrong_bar = bars[wrong_idx]
    ax.annotate(
        "Highest",
        xy=(wrong_bar.get_x() + wrong_bar.get_width() / 2, wrong_bar.get_height()),
        xytext=(wrong_bar.get_x() + wrong_bar.get_width() / 2,
                wrong_bar.get_height() + max(values) * 0.2),
        fontsize=11, fontweight="bold", color="red", ha="center",
        arrowprops=dict(arrowstyle="->", color="red", lw=2),
    )

    ax.set_ylabel("Value")
    ax.set_ylim(0, max(values) * 1.4)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


# --------------- Helpers ---------------

def _wrong_value(true_val: int, min_pct: float = 0.15, max_pct: float = 0.40) -> int:
    """Generate a wrong value that differs from the true value by 15-40%."""
    direction = random.choice([-1, 1])
    shift = max(5, int(true_val * random.uniform(min_pct, max_pct)))
    wrong = true_val + direction * shift
    return max(5, min(99, wrong))


def _pick_categories(n: int) -> list[str]:
    """Pick n category labels from a random pool."""
    valid = [p for p in CATEGORY_POOLS if len(p) >= n]
    return random.choice(valid)[:n]


# --------------- Generator ---------------

def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    n_categories_list: list[int] | None = None,
    conflict_types: list[str] | None = None,
) -> list[TaskInstance]:
    """Generate charts with text-visual contradictions."""
    if n_categories_list is None:
        n_categories_list = [3, 4, 5, 6]
    if conflict_types is None:
        conflict_types = ["value_label", "title_trend", "legend_color", "annotation"]

    out = ensure_dir(os.path.join(output_dir, "text_visual_conflict"))
    instances: list[TaskInstance] = []

    for n_cat in n_categories_list:
        for ctype in conflict_types:
            for i in range(n_per_config):
                categories = _pick_categories(n_cat)
                values = [random.randint(15, 90) for _ in range(n_cat)]

                if ctype == "value_label":
                    instances.extend(_gen_value_label(
                        categories, values, n_cat, i, out))

                elif ctype == "title_trend":
                    instances.extend(_gen_title_trend(
                        n_cat, i, out))

                elif ctype == "legend_color":
                    instances.extend(_gen_legend_color(
                        categories, n_cat, i, out))

                elif ctype == "annotation":
                    instances.extend(_gen_annotation(
                        categories, values, n_cat, i, out))

    return instances


def _gen_value_label(categories, values, n_cat, idx, out_dir) -> list[TaskInstance]:
    """Generate a value-label conflict instance."""
    # Pick which bar to query (always a conflicted one)
    query_idx = random.randint(0, n_cat - 1)

    # Create display labels — wrong for the query bar
    display_labels = values.copy()
    wrong_val = _wrong_value(values[query_idx])
    display_labels[query_idx] = wrong_val

    fname = f"value_label_n{n_cat}_{idx}.png"
    fpath = os.path.join(out_dir, fname)
    _render_value_label_conflict(categories, values, display_labels, fpath)

    return make_instances(
        fpath, "conflict_value_label", values[query_idx],
        subtask=f"value_label_n{n_cat}",
        metadata={
            "n_categories": n_cat,
            "categories": categories,
            "true_values": values,
            "display_labels": display_labels,
            "query_idx": query_idx,
            "visual_answer": values[query_idx],
            "text_answer": wrong_val,
        },
        category=categories[query_idx],
    )


def _gen_title_trend(n_cat, idx, out_dir) -> list[TaskInstance]:
    """Generate a title-trend conflict instance."""
    x_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"][:n_cat]

    # Generate clear trend
    actual_trend = random.choice(["increasing", "decreasing"])
    base = random.randint(15, 40)
    slope = random.randint(4, 8)
    if actual_trend == "decreasing":
        slope = -slope
    values = [max(5, min(95, base + slope * j + random.randint(-2, 2)))
              for j in range(n_cat)]

    # Pick contradictory title
    metric = random.choice(METRIC_NAMES)
    wrong_trend = "decreasing" if actual_trend == "increasing" else "increasing"
    title = random.choice(TREND_TITLES[actual_trend]).format(metric=metric)

    fname = f"title_trend_n{n_cat}_{idx}.png"
    fpath = os.path.join(out_dir, fname)
    _render_title_trend_conflict(x_labels, values, title, fpath)

    return make_instances(
        fpath, "conflict_title_trend", actual_trend,
        subtask=f"title_trend_{actual_trend}",
        metadata={
            "n_categories": n_cat,
            "x_labels": x_labels,
            "values": values,
            "title": title,
            "visual_answer": actual_trend,
            "text_answer": wrong_trend,
        },
    )


def _gen_legend_color(categories, n_cat, idx, out_dir) -> list[TaskInstance]:
    """Generate a legend-color conflict instance."""
    true_names = list(random.choice(SERIES_PAIRS))
    swapped_names = [true_names[1], true_names[0]]

    # Two series with distinct values
    data = [
        [random.randint(15, 90) for _ in range(n_cat)],
        [random.randint(15, 90) for _ in range(n_cat)],
    ]

    fname = f"legend_color_n{n_cat}_{idx}.png"
    fpath = os.path.join(out_dir, fname)
    _render_legend_color_conflict(categories, data, true_names, swapped_names, fpath)

    # Query asks about a series name that appears in the LEGEND (swapped)
    # The legend says COLORS[0] is swapped_names[0], but it's actually true_names[0]
    query_series = swapped_names[0]  # e.g., legend says blue="Cost"
    query_cat_idx = random.randint(0, n_cat - 1)
    query_cat = categories[query_cat_idx]

    # If model trusts legend: blue bars are "Cost" → data[0][query_cat_idx]
    # If model trusts visual: blue bars are "Revenue" (true_names[0]) → would need to
    # answer with data[1] for the actual "Cost"
    # Ground truth: the VISUAL truth — the series the legend CLAIMS is query_series
    # is actually rendered with data for true_names[0] (since legend is swapped)
    visual_answer = data[0][query_cat_idx]  # what the blue bars actually show
    text_answer = data[1][query_cat_idx]    # what actual "Cost" data would be

    return make_instances(
        fpath, "conflict_legend_color", visual_answer,
        subtask=f"legend_color_n{n_cat}",
        metadata={
            "n_categories": n_cat,
            "categories": categories,
            "true_names": true_names,
            "swapped_names": swapped_names,
            "data": data,
            "query_series": query_series,
            "query_category": query_cat,
            "visual_answer": visual_answer,
            "text_answer": text_answer,
        },
        series=query_series, category=query_cat,
    )


def _gen_annotation(categories, values, n_cat, idx, out_dir) -> list[TaskInstance]:
    """Generate an annotation conflict instance."""
    # Find actual max and pick a different bar for the wrong annotation
    true_max_idx = values.index(max(values))
    candidates = [j for j in range(n_cat) if j != true_max_idx]
    wrong_idx = random.choice(candidates)

    fname = f"annotation_n{n_cat}_{idx}.png"
    fpath = os.path.join(out_dir, fname)
    _render_annotation_conflict(categories, values, wrong_idx, fpath)

    return make_instances(
        fpath, "conflict_annotation", categories[true_max_idx],
        subtask=f"annotation_n{n_cat}",
        metadata={
            "n_categories": n_cat,
            "categories": categories,
            "values": values,
            "true_max_idx": true_max_idx,
            "wrong_idx": wrong_idx,
            "visual_answer": categories[true_max_idx],
            "text_answer": categories[wrong_idx],
        },
    )


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_categories_list=[4, 5])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} {inst.subtask:25s} "
              f"gt={str(inst.ground_truth):12s} "
              f"text_ans={str(inst.metadata.get('text_answer', '')):12s} "
              f"{os.path.basename(inst.image_path)}")
