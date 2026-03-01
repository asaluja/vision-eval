"""Generate subway-map-style path following images.

Two modes:
1. Simple: all paths connect queried pair (A→B). Tests counting with visual clutter.
2. Distractor: paths connect various station pairs. The question asks about a
   specific pair, and the model must trace which paths connect it vs ignore others.
   This matches the HF VLMs-are-Blind "Subway Connections" task structure.
"""

from __future__ import annotations

import itertools
import os
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from generate.base import TaskInstance, ensure_dir, make_instances

# Station positions (on an 18x18 canvas)
STATIONS = {
    "A": (1, 9),    # left
    "B": (17, 9),   # right
    "C": (9, 17),   # top
    "D": (9, 1),    # bottom
}

# All directed pairs between stations
ALL_PAIRS = [(a, b) for a, b in itertools.permutations(STATIONS.keys(), 2)]

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


def _draw_subway_map(connections, output_path, canvas_size=512, line_width=4.0):
    """Draw a subway map with the given connections.

    Args:
        connections: list of (start_label, end_label) tuples
    Returns:
        path to saved image
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 18)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    used_points = set()
    for p_idx, (start_label, end_label) in enumerate(connections):
        start_pos = STATIONS[start_label]
        end_pos = STATIONS[end_label]
        path = _random_path(start_pos, end_pos, existing_points=used_points)
        path = _simplify_path(path)
        used_points.update(path[1:-1])

        color = PATH_COLORS[p_idx % len(PATH_COLORS)]
        xs, ys = zip(*path)
        ax.plot(xs, ys, color=color, linewidth=line_width, solid_capstyle="round")

    # Draw station markers
    for label, (sx, sy) in STATIONS.items():
        circle = patches.Circle((sx, sy), 0.6, facecolor="white",
                                edgecolor="black", linewidth=2, zorder=10)
        ax.add_patch(circle)
        ax.text(sx, sy, label, ha="center", va="center",
                fontsize=14, fontweight="bold", zorder=11)

    dpi = max(100, canvas_size // 8)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    path_counts: list[int] | None = None,
    canvas_sizes: list[int] | None = None,
    line_widths: list[float] | None = None,
    # Distractor mode params
    total_connections_list: list[int] | None = None,
    target_counts_list: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate subway map path-following images.

    Part A (simple): All paths go between queried pair. Tests visual counting.
    Part B (distractor): Mix of connections between various pairs. Tests
        selective path tracing — matching HF VLMs-are-Blind structure.
    """
    if path_counts is None:
        path_counts = [1, 2, 3, 4, 5, 6]
    if canvas_sizes is None:
        canvas_sizes = [512]
    if line_widths is None:
        line_widths = [4.0]
    if total_connections_list is None:
        total_connections_list = [2, 4, 6]
    if target_counts_list is None:
        target_counts_list = [1, 2, 3]

    task_type = "path_following"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    # --- Part A: Simple (all paths connect A→B, no distractors) ---
    for n_paths in path_counts:
        for canvas in canvas_sizes:
            for lw in line_widths:
                for i in range(n_per_config):
                    fname = f"paths_{n_paths}_s{canvas}_lw{lw}_{i}.png"
                    fpath = os.path.join(out, fname)

                    connections = [("A", "B")] * n_paths
                    _draw_subway_map(connections, fpath, canvas, lw)

                    instances.extend(make_instances(
                        fpath, task_type, n_paths,
                        subtask=f"simple_n={n_paths}",
                        metadata={
                            "mode": "simple",
                            "n_target_paths": n_paths,
                            "n_distractor_paths": 0,
                            "n_total_connections": n_paths,
                            "canvas_size": canvas, "line_width": lw,
                        },
                        start="A", end="B",
                    ))

    # --- Part B: Distractor (mixed connections, query about one pair) ---
    for n_total in total_connections_list:
        for n_target in target_counts_list:
            if n_target > n_total:
                continue
            n_distractor = n_total - n_target
            for canvas in canvas_sizes:
                for lw in line_widths:
                    for i in range(n_per_config):
                        # Pick a random query pair
                        query_pair = random.choice([("A", "B"), ("C", "A"),
                                                    ("B", "D"), ("C", "D")])
                        q_start, q_end = query_pair

                        # Build connections: n_target for query pair + distractors
                        connections = [query_pair] * n_target
                        # Pick distractor pairs (different from query pair)
                        other_pairs = [(a, b) for a, b in
                                       [("A", "B"), ("C", "A"), ("B", "D"),
                                        ("C", "D"), ("A", "D"), ("C", "B")]
                                       if (a, b) != query_pair]
                        for _ in range(n_distractor):
                            connections.append(random.choice(other_pairs))
                        random.shuffle(connections)

                        fname = (f"paths_dist_t{n_total}_q{n_target}"
                                 f"_{q_start}{q_end}_s{canvas}_{i}.png")
                        fpath = os.path.join(out, fname)
                        _draw_subway_map(connections, fpath, canvas, lw)

                        instances.extend(make_instances(
                            fpath, task_type, n_target,
                            subtask=f"distractor_total={n_total}_target={n_target}",
                            metadata={
                                "mode": "distractor",
                                "n_target_paths": n_target,
                                "n_distractor_paths": n_distractor,
                                "n_total_connections": n_total,
                                "query_start": q_start, "query_end": q_end,
                                "canvas_size": canvas, "line_width": lw,
                            },
                            start=q_start, end=q_end,
                        ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, path_counts=[1, 3, 5],
                     total_connections_list=[4, 6],
                     target_counts_list=[1, 2])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        mode = inst.metadata.get("mode", "simple")
        print(f"  {os.path.basename(inst.image_path)} -> {inst.ground_truth} "
              f"({mode}, total={inst.metadata['n_total_connections']})")
