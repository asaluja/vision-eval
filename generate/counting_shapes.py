"""Generate overlapping circles and pentagons for counting tasks.

Reimplements the counting tasks from VLMs Are Blind:
- Overlapping circles (Olympic-ring style arrangement)
- Overlapping pentagons (same layout, different shape)
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from generate.base import TaskInstance, ensure_dir, make_instances


def _olympic_layout(n: int, diameter: float, overlap_frac: float = 0.3):
    """Compute (x, y) centers for N shapes in an interlocking arrangement.

    Top row: indices 0, 2, 4, ...
    Bottom row: indices 1, 3, 5, ... (offset down by ~half diameter)
    """
    spacing = diameter * (1 - overlap_frac)
    centers = []
    for i in range(n):
        x = i * spacing
        # Alternate rows: even indices on top, odd on bottom
        y = 0 if i % 2 == 0 else diameter * 0.5
        centers.append((x, y))
    return centers


def _draw_shapes(
    centers: list[tuple[float, float]],
    radius: float,
    shape: str,  # "circle" or "pentagon"
    line_width: float,
    colors: list[str],
    canvas_size: int,
    output_path: str,
):
    """Render shapes to a PNG file."""
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    for i, (cx, cy) in enumerate(centers):
        color = colors[i % len(colors)]
        if shape == "circle":
            patch = patches.Circle(
                (cx, cy), radius, fill=False, edgecolor=color, linewidth=line_width
            )
        else:  # pentagon
            patch = patches.RegularPolygon(
                (cx, cy), numVertices=5, radius=radius,
                orientation=0, fill=False, edgecolor=color, linewidth=line_width
            )
        ax.add_patch(patch)

    # Auto-scale to fit all shapes with padding
    xs = [c[0] for c in centers]
    ys = [c[1] for c in centers]
    pad = radius * 1.5
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)

    dpi = max(100, canvas_size // 6)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


# Default color palettes
MONO_COLORS = ["black"]
MULTI_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]


def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    shape: str = "circle",  # "circle" or "pentagon"
    counts: list[int] | None = None,
    overlap_fracs: list[float] | None = None,
    color_modes: list[str] | None = None,
    canvas_sizes: list[int] | None = None,
    line_widths: list[float] | None = None,
) -> list[TaskInstance]:
    """Generate overlapping shape images for counting tasks.

    Returns list of TaskInstance objects.
    """
    if counts is None:
        counts = [3, 4, 5, 6, 7, 8, 9, 10]
    if overlap_fracs is None:
        overlap_fracs = [0.1, 0.2, 0.3, 0.4, 0.5]  # high-signal: denser sweep
    if color_modes is None:
        color_modes = ["mono"]  # low-signal: fixed (paper: "only change marginally")
    if canvas_sizes is None:
        canvas_sizes = [512]  # low-signal: fixed (paper: resolution invariant)
    if line_widths is None:
        line_widths = [2.0]  # low-signal: fixed (paper: "does not influence ability")

    task_type = f"counting_{shape}s"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    for count in counts:
        for overlap in overlap_fracs:
            for cmode in color_modes:
                for canvas in canvas_sizes:
                    for lw in line_widths:
                        for i in range(n_per_config):
                            colors = MONO_COLORS if cmode == "mono" else MULTI_COLORS
                            diameter = 1.0
                            radius = diameter / 2
                            centers = _olympic_layout(count, diameter, overlap)

                            fname = f"{shape}_{count}_ov{overlap}_c{cmode}_s{canvas}_lw{lw}_{i}.png"
                            fpath = os.path.join(out, fname)

                            _draw_shapes(centers, radius, shape, lw, colors, canvas, fpath)

                            instances.extend(make_instances(
                                fpath, task_type, count,
                                subtask=f"n={count}",
                                metadata={
                                    "count": count, "overlap_frac": overlap,
                                    "color_mode": cmode, "canvas_size": canvas,
                                    "line_width": lw, "shape": shape,
                                },
                            ))

    return instances


if __name__ == "__main__":
    # Quick test: generate a few and display paths
    for s in ["circle", "pentagon"]:
        insts = generate(n_per_config=1, shape=s, counts=[5, 8],
                         overlap_fracs=[0.3], color_modes=["multi"],
                         canvas_sizes=[512], line_widths=[2.0])
        print(f"{s}: generated {len(insts)} images")
        for inst in insts[:2]:
            print(f"  {inst.image_path} -> ground_truth={inst.ground_truth}")
