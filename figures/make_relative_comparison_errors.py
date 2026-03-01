"""Generate composite error figure for relative comparison primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/relative_comparison/comp_bar_4_d1_g1_2.png",
        "gt": "D taller (diff=1)",
        "model": "B",
        "caption": "1-unit bar diff is below resolution",
    },
    {
        "image": "generate/images/touching_circles/touch_d0.1_r0.1_ahorizontal_s512_0.png",
        "gt": "Not touching (10px gap)",
        "model": "Yes, touching",
        "caption": "r=0.10: always-touching bias up to 10px",
    },
    {
        "image": "generate/images/touching_circles/touch_d0.05_r0.2_ahorizontal_s512_0.png",
        "gt": "Not touching (5px gap)",
        "model": "Yes, touching",
        "caption": "r=0.20: gap below 12px threshold",
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
fig.savefig("figures/relative_comparison_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/relative_comparison_errors.png")
