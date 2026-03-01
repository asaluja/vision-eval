"""Generate chart images for value reading, comparison, and trend tasks.

Chart types:
- Simple bar chart: read values, compare bars, count bars
- Grouped bar chart: read values with legend matching (color discrimination)
- Line chart: read values, detect trend, count lines

Each image generates 3+ TaskInstances (different questions about the same chart).
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import matplotlib
import numpy as np

from generate.base import TaskInstance, ensure_dir, make_instances

# Category label pools
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PRODUCT_LABELS = ["Product A", "Product B", "Product C", "Product D",
                  "Product E", "Product F", "Product G", "Product H"]
TEAM_LABELS = ["Team 1", "Team 2", "Team 3", "Team 4",
               "Team 5", "Team 6", "Team 7", "Team 8"]

SERIES_NAMES = [
    ["Revenue", "Cost", "Profit"],
    ["2023", "2024", "2025"],
    ["Online", "In-Store", "Wholesale"],
]

COLORS = list(matplotlib.cm.tab10.colors[:10])


def _make_bar_chart(categories, values, show_grid, show_values, title, output_path):
    """Render a simple bar chart."""
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, values, color=COLORS[:len(categories)], width=0.6)

    if show_values:
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    str(val), ha="center", va="bottom", fontsize=9)

    if show_grid:
        ax.yaxis.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)

    ax.set_ylabel("Value")
    if title:
        ax.set_title(title)
    ax.set_ylim(0, max(values) * 1.15)
    plt.xticks(rotation=30 if len(categories) > 6 else 0, ha="right" if len(categories) > 6 else "center")
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _make_grouped_bar_chart(categories, data, series_names, show_grid, show_values, output_path):
    """Render a grouped bar chart. data is (n_series, n_categories)."""
    n_series = len(series_names)
    x = np.arange(len(categories))
    width = 0.7 / n_series

    fig, ax = plt.subplots(figsize=(8, 5))
    for s_idx, (s_name, s_values) in enumerate(zip(series_names, data)):
        offset = (s_idx - n_series / 2 + 0.5) * width
        bars = ax.bar(x + offset, s_values, width, label=s_name, color=COLORS[s_idx])
        if show_values:
            for bar, val in zip(bars, s_values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        str(val), ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.set_ylabel("Value")
    if show_grid:
        ax.yaxis.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)
    ax.set_ylim(0, max(max(row) for row in data) * 1.15)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _make_line_chart(x_labels, data, series_names, show_grid, show_values, output_path):
    """Render a line chart. data is (n_series, n_points)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(x_labels))

    for s_idx, (s_name, s_values) in enumerate(zip(series_names, data)):
        ax.plot(x, s_values, marker="o", label=s_name, color=COLORS[s_idx], linewidth=2)
        if show_values:
            for xi, val in zip(x, s_values):
                ax.text(xi, val + 1.5, str(val), ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    if len(series_names) > 1:
        ax.legend()
    ax.set_ylabel("Value")
    if show_grid:
        ax.yaxis.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    n_categories_list: list[int] | None = None,
    chart_types: list[str] | None = None,
    show_grids: list[bool] | None = None,
    show_values_list: list[bool] | None = None,
) -> list[TaskInstance]:
    """Generate chart images with multiple questions per chart."""
    if n_categories_list is None:
        n_categories_list = [3, 5, 7, 10]
    if chart_types is None:
        chart_types = ["bar", "grouped_bar", "line"]
    if show_grids is None:
        show_grids = [False, True]
    if show_values_list is None:
        show_values_list = [False, True]

    out = ensure_dir(os.path.join(output_dir, "charts"))
    instances = []

    for n_cat in n_categories_list:
        for ctype in chart_types:
            for show_grid in show_grids:
                for show_vals in show_values_list:
                    for i in range(n_per_config):
                        # Pick category labels (pool must be large enough)
                        valid_pools = [p for p in [MONTH_LABELS, PRODUCT_LABELS, TEAM_LABELS]
                                       if len(p) >= n_cat]
                        if not valid_pools:
                            continue
                        label_pool = random.choice(valid_pools)
                        categories = label_pool[:n_cat]

                        if ctype == "bar":
                            values = [random.randint(5, 95) for _ in range(n_cat)]
                            fname = f"bar_{n_cat}_g{int(show_grid)}_v{int(show_vals)}_{i}.png"
                            fpath = os.path.join(out, fname)
                            _make_bar_chart(categories, values, show_grid, show_vals, "", fpath)

                            # Q1: value reading (random category)
                            q_cat = random.choice(categories)
                            q_val = values[categories.index(q_cat)]
                            instances.extend(make_instances(
                                fpath, "chart_bar_value", q_val,
                                subtask=f"bar_n{n_cat}_grid{int(show_grid)}_vals{int(show_vals)}",
                                metadata={"chart_type": "bar", "n_categories": n_cat,
                                          "show_grid": show_grid, "show_values": show_vals,
                                          "categories": categories, "values": values,
                                          "query_category": q_cat},
                                category=q_cat,
                            ))

                            # Q2: comparison (highest)
                            max_cat = categories[values.index(max(values))]
                            instances.extend(make_instances(
                                fpath, "chart_bar_compare", max_cat,
                                subtask=f"bar_n{n_cat}_grid{int(show_grid)}_vals{int(show_vals)}",
                                metadata={"chart_type": "bar", "n_categories": n_cat,
                                          "show_grid": show_grid, "show_values": show_vals,
                                          "categories": categories, "values": values},
                            ))

                            # Q3: count bars
                            instances.extend(make_instances(
                                fpath, "chart_bar_count", n_cat,
                                subtask=f"bar_n{n_cat}",
                                metadata={"chart_type": "bar", "n_categories": n_cat},
                            ))

                        elif ctype == "grouped_bar":
                            n_series = random.choice([2, 3])
                            series = random.choice(SERIES_NAMES)[:n_series]
                            data = [[random.randint(5, 95) for _ in range(n_cat)]
                                    for _ in range(n_series)]
                            fname = f"grouped_{n_cat}x{n_series}_g{int(show_grid)}_v{int(show_vals)}_{i}.png"
                            fpath = os.path.join(out, fname)
                            _make_grouped_bar_chart(categories, data, series, show_grid, show_vals, fpath)

                            # Q1: value reading (random series + category)
                            s_idx = random.randint(0, n_series - 1)
                            c_idx = random.randint(0, n_cat - 1)
                            instances.extend(make_instances(
                                fpath, "chart_grouped_value", data[s_idx][c_idx],
                                subtask=f"grouped_n{n_cat}_s{n_series}",
                                metadata={"chart_type": "grouped_bar", "n_categories": n_cat,
                                          "n_series": n_series, "show_grid": show_grid,
                                          "show_values": show_vals,
                                          "categories": categories, "series": series,
                                          "data": data, "query_series": series[s_idx],
                                          "query_category": categories[c_idx]},
                                series=series[s_idx], category=categories[c_idx],
                            ))

                            # Q2: count bars per group (n_series)
                            instances.append(TaskInstance(
                                image_path=os.path.abspath(fpath),
                                prompt="How many different colored bar groups are shown in each category? "
                                       "Answer with a number in curly braces, e.g. {3}.",
                                ground_truth=n_series,
                                task_type="chart_bar_count",
                                subtask=f"grouped_series_count",
                                metadata={"chart_type": "grouped_bar", "n_series": n_series},
                            ))

                        elif ctype == "line":
                            n_series = random.choice([1, 2, 3])
                            series = random.choice(SERIES_NAMES)[:n_series]
                            # Generate data with a clear trend for the first series
                            base = random.randint(10, 40)
                            trend_dir = random.choice(["increasing", "decreasing"])
                            slope = random.randint(3, 8) if trend_dir == "increasing" else -random.randint(3, 8)
                            data = []
                            for s in range(n_series):
                                if s == 0:
                                    vals = [base + slope * j + random.randint(-3, 3) for j in range(n_cat)]
                                    vals = [max(1, min(99, v)) for v in vals]
                                else:
                                    vals = [random.randint(10, 90) for _ in range(n_cat)]
                                data.append(vals)

                            x_labels = MONTH_LABELS[:n_cat]
                            fname = f"line_{n_cat}x{n_series}_g{int(show_grid)}_v{int(show_vals)}_{i}.png"
                            fpath = os.path.join(out, fname)
                            _make_line_chart(x_labels, data, series, show_grid, show_vals, fpath)

                            # Q1: value at point (random x)
                            x_idx = random.randint(0, n_cat - 1)
                            instances.extend(make_instances(
                                fpath, "chart_line_value", data[0][x_idx],
                                subtask=f"line_n{n_cat}_s{n_series}",
                                metadata={"chart_type": "line", "n_categories": n_cat,
                                          "n_series": n_series, "show_grid": show_grid,
                                          "show_values": show_vals,
                                          "x_labels": x_labels, "data": data,
                                          "series": series, "query_x": x_labels[x_idx]},
                                x_label=x_labels[x_idx],
                            ))

                            # Q2: trend direction (first series)
                            # Compute actual trend from data
                            first_vals = data[0]
                            actual_trend = "increasing" if first_vals[-1] > first_vals[0] else "decreasing"
                            instances.extend(make_instances(
                                fpath, "chart_line_trend", actual_trend,
                                subtask=f"line_trend_{actual_trend}",
                                metadata={"chart_type": "line", "trend": actual_trend,
                                          "first_series_values": first_vals},
                            ))

                            # Q3: count lines
                            if n_series > 1:
                                instances.extend(make_instances(
                                    fpath, "chart_line_count", n_series,
                                    subtask=f"line_count_s{n_series}",
                                    metadata={"chart_type": "line", "n_series": n_series},
                                ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_categories_list=[5],
                     chart_types=["bar", "grouped_bar", "line"],
                     show_grids=[True], show_values_list=[False])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} -> {inst.ground_truth}")
