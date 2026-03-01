"""Create compact composite figure for spatial localization error cases."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec

cases = [
    {
        "image": "generate/images/charts/line_10x3_g1_v1_1.png",
        "title": "Series confusion",
        "prompt": "Read the Wholesale data point at Jun.",
        "gt": "90",
        "model": "4",
        "note": 'Says "green line (Wholesale)"\nbut reads Online\'s label',
    },
    {
        "image": "generate/images/diagrams/flow_multi_decision_n5_1.png",
        "title": "Arrow tracing failure",
        "prompt": 'Next step after "Check Inventory"?',
        "gt": "End",
        "model": "Update Database",
        "note": "Arrow to End crosses near\nUpdate Database",
    },
    {
        "image": "data/images/blind/circled_letter_612.png",
        "title": "Word priors override vision",
        "prompt": "What is the circled letter?",
        "gt": "t",
        "model": "S",
        "note": 'Hallucinates plural\n"Acknowledgements"',
        "crop": (100, 350, 950, 700),
    },
]

fig = plt.figure(figsize=(14, 5.5), facecolor="white")

gs = GridSpec(2, 3, figure=fig, height_ratios=[3, 1.2], hspace=0.08, wspace=0.12,
              left=0.02, right=0.98, top=0.92, bottom=0.02)

for col, case in enumerate(cases):
    ax_img = fig.add_subplot(gs[0, col])
    img = mpimg.imread(case["image"])
    if case.get("crop"):
        l, t, r, b = case["crop"]
        img = img[t:b, l:r]
    ax_img.imshow(img)
    ax_img.set_xticks([])
    ax_img.set_yticks([])
    for spine in ax_img.spines.values():
        spine.set_edgecolor("#aaaaaa")
        spine.set_linewidth(0.5)
    ax_img.set_title(case["title"], fontsize=10, fontweight="bold", pad=4)

    ax_txt = fig.add_subplot(gs[1, col])
    ax_txt.axis("off")

    txt = (
        f"GT: {case['gt']}   Model: {case['model']}\n"
        f"{case['note']}"
    )
    ax_txt.text(0.5, 0.95, txt, fontsize=8.5, color="#333333",
                transform=ax_txt.transAxes, verticalalignment="top",
                horizontalalignment="center", family="sans-serif",
                linespacing=1.4,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5",
                          edgecolor="#dddddd", linewidth=0.5))

plt.savefig("results/spatial_localization_errors.png", dpi=200,
            bbox_inches="tight", facecolor="white", pad_inches=0.1)
print("Saved to results/spatial_localization_errors.png")
