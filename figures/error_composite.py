"""Shared renderer for 3-panel error composite figures."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def make_error_composite(
    cases: list[dict],
    output_path: str,
    figsize: tuple[float, float] = (10, 3.8),
    fontsize: float = 7.5,
    cmap: str | None = None,
) -> None:
    """Render a 1×3 grid of error cases and save to output_path.

    Each case dict must have keys: image, gt, model, caption.
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)

    for ax, case in zip(axes, cases):
        img = mpimg.imread(case["image"])
        ax.imshow(img, cmap=cmap)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color("#999999")

        label = (
            f"GT: {case['gt']}  |  Model: {case['model']}\n"
            f"{case['caption']}"
        )
        ax.set_xlabel(label, fontsize=fontsize, labelpad=6)

    fig.tight_layout(pad=1.0)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved {output_path}")
