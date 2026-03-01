"""Generate heatmap cell-value reading tasks.

Creates 2D grids where each cell's color encodes an integer value. The model
must read the value of a specific named cell (e.g. "B3") from the colorbar.

High-signal sweep axes (per VLMs Are Blind methodology):
  - grid_sizes: (rows, cols) tuples — affects spatial density
  - colormaps: viridis, RdBu, YlOrRd — tests colormap-reading ability
  - value_ranges: (min, max) — affects colorbar scale interpretation
"""

from __future__ import annotations

import os
import random
import string

import matplotlib
matplotlib.use("Agg")  # headless rendering, must be before pyplot import
import matplotlib.pyplot as plt
import numpy as np

from generate.base import ensure_dir, make_instances, TaskInstance


def _make_heatmap(
    grid_values: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
    cmap: str,
    vmin: float,
    vmax: float,
    query_row: int,
    query_col: int,
    output_path: str,
) -> None:
    """Render a heatmap PNG with colorbar and axis labels."""
    rows, cols = grid_values.shape
    fig_w = max(5, cols * 0.9 + 2.0)
    fig_h = max(4, rows * 0.9 + 1.0)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    im = ax.imshow(
        grid_values,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        aspect="auto",
    )
    fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)

    # Axis ticks: columns on x-axis (1, 2, 3...), rows on y-axis (A, B, C...)
    ax.set_xticks(range(cols))
    ax.set_xticklabels(col_labels, fontsize=10)
    ax.set_yticks(range(rows))
    ax.set_yticklabels(row_labels, fontsize=10)

    # Highlight query cell with a bold white border
    rect = plt.Rectangle(
        (query_col - 0.5, query_row - 0.5), 1, 1,
        linewidth=2.5, edgecolor="white", facecolor="none",
    )
    ax.add_patch(rect)

    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    grid_sizes: list[tuple[int, int]] | None = None,
    colormaps: list[str] | None = None,
    value_ranges: list[tuple[int, int]] | None = None,
) -> list[TaskInstance]:
    """Generate heatmap cell-value reading tasks.

    Sweeps grid_sizes x colormaps x value_ranges, rendering n_per_config
    images per combination. Each image gets one query cell (row letter + col
    number, e.g. "B3") and the integer ground-truth value at that cell.
    """
    if grid_sizes is None:
        grid_sizes = [(4, 4), (6, 6), (4, 6)]
    if colormaps is None:
        colormaps = ["viridis", "RdBu", "YlOrRd"]
    if value_ranges is None:
        value_ranges = [(0, 100), (0, 10), (-1, 1)]

    out = ensure_dir(os.path.join(output_dir, "heatmap"))
    instances: list[TaskInstance] = []

    for n_rows, n_cols in grid_sizes:
        row_labels = list(string.ascii_uppercase[:n_rows])   # A, B, C, ...
        col_labels = [str(c + 1) for c in range(n_cols)]    # 1, 2, 3, ...

        for cmap in colormaps:
            for vmin, vmax in value_ranges:
                for i in range(n_per_config):
                    # Generate integer grid values within [vmin, vmax]
                    int_min, int_max = int(vmin), int(vmax)
                    if int_min == int_max:
                        int_max = int_min + 1
                    grid_values = np.random.randint(
                        int_min, int_max + 1,
                        size=(n_rows, n_cols),
                    ).astype(float)

                    # Pick a random query cell
                    q_row = random.randint(0, n_rows - 1)
                    q_col = random.randint(0, n_cols - 1)
                    row_label = row_labels[q_row]   # e.g. "B"
                    col_label = col_labels[q_col]   # e.g. "3"
                    cell_id = f"{row_label}{col_label}"   # e.g. "B3"
                    cell_value = int(grid_values[q_row, q_col])

                    # Filename encodes config for easy inspection
                    vrange_tag = f"{int_min}to{int_max}".replace("-", "neg")
                    fname = (
                        f"heatmap_{n_rows}x{n_cols}_{cmap}_"
                        f"{vrange_tag}_{i}.png"
                    )
                    fpath = os.path.join(out, fname)

                    _make_heatmap(
                        grid_values,
                        row_labels,
                        col_labels,
                        cmap=cmap,
                        vmin=float(int_min),
                        vmax=float(int_max),
                        query_row=q_row,
                        query_col=q_col,
                        output_path=fpath,
                    )

                    subtask = f"heatmap_{n_rows}x{n_cols}_{cmap}"
                    instances.extend(make_instances(
                        fpath,
                        "heatmap_cell_value",
                        cell_value,
                        subtask=subtask,
                        metadata={
                            "grid_rows": n_rows,
                            "grid_cols": n_cols,
                            "colormap": cmap,
                            "value_min": int_min,
                            "value_max": int_max,
                            "query_row": q_row,
                            "query_col": q_col,
                            "row_label": row_label,
                            "col_label": col_label,
                            "cell_id": cell_id,
                        },
                        row=row_label,
                        col=col_label,
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1)
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(
            f"  {inst.task_type:25s}  {inst.subtask:30s}  "
            f"cell={inst.metadata['cell_id']}  gt={inst.ground_truth}"
        )
