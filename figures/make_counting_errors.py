"""Generate composite error figure for counting/enumeration primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/counting_circles/circle_10_ov0.3_cmono_s512_lw2.0_0.png",
        "gt": "10 circles",
        "model": "15",
        "caption": "Large shapes + overlap \u2192 overcounting",
    },
    {
        "image": "data/images/blind/counting_circles_20.png",
        "gt": "7 circles",
        "model": "5",
        "caption": "Small shapes on large canvas \u2192 undercounting",
    },
    {
        "image": "generate/images/counting_pentagons/pentagon_6_ov0.3_cmono_s512_lw2.0_0.png",
        "gt": "6 pentagons",
        "model": "8",
        "caption": "Complex shapes compound overlap errors",
    },
]

fig, axes = plt.subplots(1, 3, figsize=(9, 3.8))

for ax, case in zip(axes, cases):
    img = mpimg.imread(case["image"])
    ax.imshow(img, cmap="gray")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color("#999999")

    label = (
        f"GT: {case['gt']}  |  Model: {case['model']}\n"
        f"{case['caption']}"
    )
    ax.set_xlabel(label, fontsize=8, labelpad=6)

fig.tight_layout(pad=1.0)
fig.savefig("figures/counting_enumeration_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/counting_enumeration_errors.png")
