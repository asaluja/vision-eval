"""Generate composite error figure for color discrimination primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/color_discrimination/color_grid_4_blues_extreme_1.png",
        "gt": "A2 (odd cell)",
        "model": "C1",
        "caption": "Blues at \u0394L\u22485: shade invisible",
    },
    {
        "image": "generate/images/color_discrimination/color_grid_4_greens_near_threshold_4.png",
        "gt": "A4 (odd cell)",
        "model": "B4",
        "caption": "Greens hardest family (10% at \u0394L\u22487)",
    },
    {
        "image": "generate/images/color_discrimination/color_bar_5_hard_blues_3.png",
        "gt": "43 (medium blue bar)",
        "model": "56",
        "caption": "5 same-family bars: color confusion + misread",
    },
]

fig, axes = plt.subplots(1, 3, figsize=(10, 3.8))

for ax, case in zip(axes, cases):
    img = mpimg.imread(case["image"])
    ax.imshow(img)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color("#999999")

    label = (
        f"GT: {case['gt']}  |  Model: {case['model']}\n"
        f"{case['caption']}"
    )
    ax.set_xlabel(label, fontsize=7.5, labelpad=6)

fig.tight_layout(pad=1.0)
fig.savefig("figures/color_discrimination_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/color_discrimination_errors.png")
