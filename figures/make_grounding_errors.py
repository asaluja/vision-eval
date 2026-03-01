"""Generate composite error figure for text-visual consistency (grounding) primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/text_visual_conflict/value_label_n6_1.png",
        "gt": "Product D = 89 (bar height)",
        "model": "56 (reads wrong label)",
        "caption": "0% accuracy: always trusts text over visual",
    },
    {
        "image": "generate/images/text_visual_conflict/annotation_n3_1.png",
        "gt": "Product C (highest bar)",
        "model": "Product B",
        "caption": "\"Highest\" arrow fools model at small gap",
    },
    {
        "image": "generate/images/text_visual_conflict/title_trend_n3_0.png",
        "gt": "Decreasing",
        "model": "Decreasing \u2713",
        "caption": "100%: ignores \"Rising Sales\" title correctly",
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
    ax.set_xlabel(label, fontsize=7, labelpad=6)

fig.tight_layout(pad=1.0)
fig.savefig("figures/text_visual_consistency_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/text_visual_consistency_errors.png")
