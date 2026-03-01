"""Generate line intersection counting images.

Two colored lines (blue + red) on a white canvas. Each line is a 3-point
polyline, so there can be 0, 1, or 2 intersections. Ground truth is
computed analytically.
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import numpy as np

from generate.base import TaskInstance, ensure_dir, make_instances
from evaluate.prompts import get_prompt


def _segment_intersection(p1, p2, p3, p4):
    """Check if line segment (p1-p2) intersects (p3-p4).

    Returns the intersection point or None.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None  # Parallel

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)
    return None


def _count_intersections(blue_pts, red_pts):
    """Count intersections between two 3-point polylines (each has 2 segments)."""
    count = 0
    for i in range(len(blue_pts) - 1):
        for j in range(len(red_pts) - 1):
            if _segment_intersection(blue_pts[i], blue_pts[i + 1],
                                     red_pts[j], red_pts[j + 1]) is not None:
                count += 1
    return count


def _random_polyline(n_points: int = 3, grid_size: int = 12):
    """Generate a random 3-point polyline with x-coords at fixed spacing."""
    xs = np.linspace(0, grid_size, n_points)
    ys = [random.randint(1, grid_size - 1) for _ in range(n_points)]
    return list(zip(xs, ys))


def generate(
    n_per_intersection: int = 10,
    output_dir: str = "generate/images",
    canvas_sizes: list[int] | None = None,
    line_widths: list[float] | None = None,
    max_attempts: int = 200,
) -> list[TaskInstance]:
    """Generate line intersection images with balanced 0/1/2 intersection counts."""
    if canvas_sizes is None:
        canvas_sizes = [512]  # low-signal: fixed
    if line_widths is None:
        line_widths = [3.0]  # low-signal: fixed

    task_type = "line_intersection"
    out = ensure_dir(os.path.join(output_dir, task_type))

    # Pre-generate line pairs balanced across intersection counts
    target_counts = {0: n_per_intersection, 1: n_per_intersection, 2: n_per_intersection}
    collected = {0: [], 1: [], 2: []}

    attempts = 0
    while any(len(v) < target_counts[k] for k, v in collected.items()) and attempts < max_attempts * 10:
        blue = _random_polyline()
        red = _random_polyline()
        n_int = _count_intersections(blue, red)
        if n_int in collected and len(collected[n_int]) < target_counts[n_int]:
            collected[n_int].append((blue, red))
        attempts += 1

    instances = []
    for n_int, pairs in collected.items():
        for idx, (blue, red) in enumerate(pairs):
            for canvas in canvas_sizes:
                for lw in line_widths:
                    fname = f"lines_int{n_int}_s{canvas}_lw{lw}_{idx}.png"
                    fpath = os.path.join(out, fname)

                    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
                    ax.set_xlim(-0.5, 12.5)
                    ax.set_ylim(-0.5, 12.5)
                    ax.set_aspect("equal")
                    ax.grid(True, alpha=0.3, color="gray")
                    ax.set_facecolor("white")
                    fig.patch.set_facecolor("white")

                    bx, by = zip(*blue)
                    rx, ry = zip(*red)
                    ax.plot(bx, by, color="blue", linewidth=lw)
                    ax.plot(rx, ry, color="red", linewidth=lw)
                    ax.axis("off")

                    dpi = max(100, canvas // 5)
                    fig.savefig(fpath, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
                    plt.close(fig)

                    instances.extend(make_instances(
                        fpath, task_type, n_int,
                        subtask=f"intersections={n_int}",
                        metadata={
                            "n_intersections": n_int, "canvas_size": canvas,
                            "line_width": lw, "blue_points": blue, "red_points": red,
                        },
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_intersection=3, canvas_sizes=[512], line_widths=[3.0])
    print(f"Generated {len(insts)} instances")
    for inst in insts[:6]:
        print(f"  {os.path.basename(inst.image_path)} -> {inst.ground_truth}")
