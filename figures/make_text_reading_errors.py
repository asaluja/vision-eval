"""Generate composite error figure for text reading primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/text_reading/text_word_f10_r90_chigh_1.png",
        "gt": "Forecast",
        "model": "Forrest",
        "caption": "Lexical prior fills in degraded 10px/90\u00b0 text",
    },
    {
        "image": "generate/images/text_reading/text_num_f10_r90_2.png",
        "gt": "256",
        "model": "325",
        "caption": "No lexical rescue for numbers: 0% at 10px/90\u00b0",
    },
    {
        "image": "generate/images/text_reading/text_num_f20_r45_1.png",
        "gt": "518",
        "model": "5128",
        "caption": "Phantom digit insertion at 20px/45\u00b0",
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
fig.savefig("figures/text_reading_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/text_reading_errors.png")
