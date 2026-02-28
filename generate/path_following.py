"""Generate subway-map-style path following images.

Colored paths connect labeled stations. Task: count how many distinct
paths connect station A to station B.
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from generate.base import TaskInstance, ensure_dir
from evaluate.prompts import get_prompt

# Station positions (on an 18x18 canvas)
STATIONS = {
    "A": (1, 9),    # left
    "B": (17, 9),   # right
    "C": (9, 17),   # top
    "D": (9, 1),    # bottom
}

PATH_COLORS = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
    "#a65628", "#f781bf", "#999999", "#66c2a5", "#fc8d62",
]


def _random_path(start: tuple, end: tuple, grid_size: int = 18, existing_points: set = None):
    """Generate a random path from start to end using a simple random walk.

    Returns list of (x, y) waypoints.
    """
    if existing_points is None:
        existing_points = set()

    sx, sy = start
    ex, ey = end
    path = [(sx, sy)]
    cx, cy = sx, sy
    max_steps = 40
    steps = 0

    while (cx, cy) != (ex, ey) and steps < max_steps:
        # Bias towards end point
        dx = 1 if ex > cx else -1 if ex < cx else 0
        dy = 1 if ey > cy else -1 if ey < cy else 0

        moves = []
        if dx != 0:
            moves.extend([(dx, 0)] * 3)  # bias towards target
        if dy != 0:
            moves.extend([(0, dy)] * 3)
        # Add some random perpendicular movement
        moves.extend([(0, 1), (0, -1), (1, 0), (-1, 0)])

        random.shuffle(moves)
        moved = False
        for mx, my in moves:
            nx, ny = cx + mx, cy + my
            if 1 <= nx < grid_size and 1 <= ny < grid_size:
                if (nx, ny) not in existing_points or (nx, ny) == (ex, ey):
                    cx, cy = nx, ny
                    path.append((cx, cy))
                    moved = True
                    break
        if not moved:
            # Force move toward target
            cx += dx
            cy += dy
            cx = max(1, min(grid_size - 1, cx))
            cy = max(1, min(grid_size - 1, cy))
            path.append((cx, cy))
        steps += 1

    if path[-1] != (ex, ey):
        path.append((ex, ey))

    return path


def _simplify_path(path: list[tuple], tolerance: int = 2):
    """Simplify path by removing collinear points."""
    if len(path) <= 2:
        return path
    simplified = [path[0]]
    for i in range(1, len(path) - 1):
        prev = simplified[-1]
        curr = path[i]
        nxt = path[i + 1]
        # Keep point if direction changes
        d1 = (curr[0] - prev[0], curr[1] - prev[1])
        d2 = (nxt[0] - curr[0], nxt[1] - curr[1])
        if d1 != d2:
            simplified.append(curr)
    simplified.append(path[-1])
    return simplified


def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    path_counts: list[int] | None = None,
    canvas_sizes: list[int] | None = None,
    line_widths: list[float] | None = None,
) -> list[TaskInstance]:
    """Generate subway map path-following images."""
    if path_counts is None:
        path_counts = [1, 2, 3, 4, 5]
    if canvas_sizes is None:
        canvas_sizes = [512, 768]
    if line_widths is None:
        line_widths = [3.0, 5.0]

    task_type = "path_following"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    start_label, end_label = "A", "B"
    start_pos = STATIONS[start_label]
    end_pos = STATIONS[end_label]

    for n_paths in path_counts:
        for canvas in canvas_sizes:
            for lw in line_widths:
                for i in range(n_per_config):
                    fname = f"paths_{n_paths}_s{canvas}_lw{lw}_{i}.png"
                    fpath = os.path.join(out, fname)

                    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
                    ax.set_xlim(0, 18)
                    ax.set_ylim(0, 18)
                    ax.set_aspect("equal")
                    ax.axis("off")
                    fig.patch.set_facecolor("white")
                    ax.set_facecolor("white")

                    # Generate paths
                    used_points = set()
                    paths = []
                    for p_idx in range(n_paths):
                        path = _random_path(start_pos, end_pos,
                                            existing_points=used_points)
                        path = _simplify_path(path)
                        paths.append(path)
                        used_points.update(path[1:-1])  # exclude endpoints

                    # Draw paths
                    for p_idx, path in enumerate(paths):
                        color = PATH_COLORS[p_idx % len(PATH_COLORS)]
                        xs, ys = zip(*path)
                        ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle="round")

                    # Draw station markers
                    for label, (sx, sy) in STATIONS.items():
                        circle = patches.Circle((sx, sy), 0.6, facecolor="white",
                                                edgecolor="black", linewidth=2, zorder=10)
                        ax.add_patch(circle)
                        ax.text(sx, sy, label, ha="center", va="center",
                                fontsize=14, fontweight="bold", zorder=11)

                    dpi = max(100, canvas // 8)
                    fig.savefig(fpath, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
                    plt.close(fig)

                    prompt = get_prompt(task_type, start=start_label, end=end_label)
                    instances.append(TaskInstance(
                        image_path=os.path.abspath(fpath),
                        prompt=prompt,
                        ground_truth=n_paths,
                        task_type=task_type,
                        subtask=f"n_paths={n_paths}",
                        metadata={
                            "n_paths": n_paths, "canvas_size": canvas,
                            "line_width": lw, "start": start_label,
                            "end": end_label,
                        },
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, path_counts=[1, 3, 5],
                     canvas_sizes=[512], line_widths=[4.0])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {os.path.basename(inst.image_path)} -> {inst.ground_truth} paths")
