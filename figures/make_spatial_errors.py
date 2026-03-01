"""Generate composite error figure for spatial localization primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/charts/line_5x3_g1_v1_4.png",
        "gt": "Wholesale @ Apr = 78",
        "model": "64 (read In-Store)",
        "caption": "Series confusion: correct x, wrong line",
    },
    {
        "image": "generate/images/diagrams/flow_multi_decision_n3_4.png",
        "gt": "Next after Run Tests: Complete?",
        "model": "Notify Team",
        "caption": "Arrow tracing fails in multi-decision DAG",
    },
    {
        "image": "data/images/blind/circled_letter_205.png",
        "gt": "t (circled, pos 0)",
        "model": "H",
        "caption": "Lowercase invisible next to uppercase",
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
fig.savefig("figures/spatial_localization_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/spatial_localization_errors.png")
