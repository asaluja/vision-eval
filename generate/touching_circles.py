"""Generate touching/overlapping circle detection images.

Two circles with variable separation. Task: determine if they are
touching/overlapping or separated.
"""

from __future__ import annotations

import math
import os

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from generate.base import TaskInstance, ensure_dir, make_instances
from evaluate.prompts import get_prompt


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    distance_ratios: list[float] | None = None,
    arrangements: list[str] | None = None,
    canvas_sizes: list[int] | None = None,
    radius_fracs: list[float] | None = None,
) -> list[TaskInstance]:
    """Generate two-circle images for overlap detection.

    distance_ratio: fraction of diameter for gap between circle edges.
      < 0 = overlapping, 0 = touching, > 0 = separated.
    """
    if distance_ratios is None:
        # high-signal: denser near the touching boundary
        distance_ratios = [-0.4, -0.2, -0.1, 0.0, 0.05, 0.1, 0.2, 0.4, 0.6]
    if arrangements is None:
        arrangements = ["horizontal"]  # low-signal: fixed
    if canvas_sizes is None:
        canvas_sizes = [512]  # low-signal: fixed
    if radius_fracs is None:
        radius_fracs = [0.1, 0.15, 0.2]  # high-signal: diameter affects difficulty

    task_type = "touching_circles"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    for dist_r in distance_ratios:
        for radius_frac in radius_fracs:
            for arr in arrangements:
                for canvas in canvas_sizes:
                    for i in range(n_per_config):
                        fname = f"touch_d{dist_r}_r{radius_frac}_a{arr}_s{canvas}_{i}.png"
                        fpath = os.path.join(out, fname)

                        radius = radius_frac
                        # Center-to-center distance: 2*radius + gap
                        gap = dist_r * (2 * radius)
                        center_dist = 2 * radius + gap

                        # Place circle 1 at center, circle 2 offset by arrangement
                        cx1, cy1 = 0.5, 0.5
                        if arr == "horizontal":
                            cx2 = cx1 + center_dist
                            cy2 = cy1
                        elif arr == "vertical":
                            cx2 = cx1
                            cy2 = cy1 + center_dist
                        else:  # diagonal
                            offset = center_dist / math.sqrt(2)
                            cx2 = cx1 + offset
                            cy2 = cy1 + offset

                        fig, ax = plt.subplots(1, 1, figsize=(5, 5))
                        ax.set_xlim(0, 1)
                        ax.set_ylim(0, 1)
                        ax.set_aspect("equal")
                        ax.axis("off")
                        fig.patch.set_facecolor("white")

                        c1 = patches.Circle((cx1, cy1), radius, fill=False,
                                            edgecolor="#1f77b4", linewidth=2.5)
                        c2 = patches.Circle((cx2, cy2), radius, fill=False,
                                            edgecolor="#d62728", linewidth=2.5)
                        ax.add_patch(c1)
                        ax.add_patch(c2)

                        dpi = max(100, canvas // 5)
                        fig.savefig(fpath, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
                        plt.close(fig)

                        # Touching or overlapping if gap <= 0
                        ground_truth = "Yes" if dist_r <= 0 else "No"

                        instances.extend(make_instances(
                            fpath, task_type, ground_truth,
                            subtask=f"dist={dist_r}",
                            metadata={
                                "distance_ratio": dist_r, "arrangement": arr,
                                "canvas_size": canvas, "radius": radius,
                                "actual_state": "overlapping" if dist_r < 0 else
                                               "touching" if dist_r == 0 else "separated",
                            },
                        ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, canvas_sizes=[512])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {os.path.basename(inst.image_path)} -> {inst.ground_truth} "
              f"({inst.metadata['actual_state']})")
