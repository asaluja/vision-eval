"""Generate nested squares for counting tasks.

Recursively draws nested squares with a 75% reduction factor per level.
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from generate.base import TaskInstance, ensure_dir
from evaluate.prompts import get_prompt


def _draw_nested_squares(ax, depth: int, line_thickness: float, canvas_frac: float = 0.8):
    """Draw `depth` nested squares on the given axes."""
    # Outer square centered at (0.5, 0.5) with side = canvas_frac
    size = canvas_frac
    reduction = 0.75
    padding_frac = 0.05  # min gap between squares as fraction of parent

    cx, cy = 0.5, 0.5
    for d in range(depth):
        x = cx - size / 2
        y = cy - size / 2
        rect = patches.Rectangle(
            (x, y), size, size,
            fill=False, edgecolor="black", linewidth=line_thickness,
        )
        ax.add_patch(rect)

        # Shrink for next level
        new_size = size * reduction
        # Randomly offset the inner square within available margin
        margin = (size - new_size) / 2
        jitter = margin * 0.4  # max offset from center
        cx += random.uniform(-jitter, jitter)
        cy += random.uniform(-jitter, jitter)
        size = new_size


def generate(
    n_per_config: int = 2,
    output_dir: str = "generate/images",
    depths: list[int] | None = None,
    line_thicknesses: list[float] | None = None,
    canvas_sizes: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate nested square images."""
    if depths is None:
        depths = [2, 3, 4, 5]
    if line_thicknesses is None:
        line_thicknesses = [2.0, 3.0]
    if canvas_sizes is None:
        canvas_sizes = [384, 768]

    task_type = "nested_squares"
    prompt = get_prompt(task_type)
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    for depth in depths:
        for lt in line_thicknesses:
            for canvas in canvas_sizes:
                for i in range(n_per_config):
                    fname = f"nested_d{depth}_lt{lt}_s{canvas}_{i}.png"
                    fpath = os.path.join(out, fname)

                    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1)
                    ax.set_aspect("equal")
                    ax.axis("off")
                    fig.patch.set_facecolor("white")

                    _draw_nested_squares(ax, depth, lt)

                    dpi = max(100, canvas // 5)
                    fig.savefig(fpath, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
                    plt.close(fig)

                    instances.append(TaskInstance(
                        image_path=os.path.abspath(fpath),
                        prompt=prompt,
                        ground_truth=depth,
                        task_type=task_type,
                        subtask=f"depth={depth}",
                        metadata={
                            "depth": depth, "line_thickness": lt,
                            "canvas_size": canvas,
                        },
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, canvas_sizes=[512])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {os.path.basename(inst.image_path)} -> depth={inst.ground_truth}")
