"""Generate composite error figure for prior bias override primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/board_games/chess_7x8_s512_0.png",
        "gt": "7 rows",
        "model": "8 (canonical)",
        "caption": "100% bias alignment: always outputs 8\u00d78",
    },
    {
        "image": "generate/images/patterned_grid/pgrid_dice_add_g6_s768_0.png",
        "gt": "1 (cell has extra dot)",
        "model": "4",
        "caption": "Add-anomaly: 0% \u2014 extra dot is invisible",
    },
    {
        "image": "data/images/biased/Ebbinghaus_001_Q1_notitle_px384.png",
        "gt": "Same size (Yes)",
        "model": "No",
        "caption": "Ebbinghaus illusion: 50% = pure chance",
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
fig.savefig("figures/prior_bias_override_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/prior_bias_override_errors.png")
