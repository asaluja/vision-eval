"""Generate composite error figure for line/path following primitive."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

cases = [
    {
        "image": "generate/images/path_following/paths_6_s512_lw4.0_0.png",
        "gt": "6 paths A\u2192B",
        "model": "5",
        "caption": "Loses track of overlapping colored paths",
    },
    {
        "image": "generate/images/line_intersection/lines_p5_int0_s512_lw3.0_0.png",
        "gt": "0 intersections",
        "model": "2",
        "caption": "Hallucinates crossings from visual proximity",
    },
    {
        "image": "generate/images/charts/line_3x10_g1_v0_0.png",
        "gt": "Online: increasing",
        "model": "decreasing",
        "caption": "Can't isolate named series in 10-line chart",
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
fig.savefig("figures/line_path_following_errors.png", dpi=200, bbox_inches="tight",
            facecolor="white")
print("Saved figures/line_path_following_errors.png")
