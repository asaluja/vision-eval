"""
Generate composite error figure for text_visual_consistency primitive.
3 panels side-by-side showing the most illustrative failure cases.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import textwrap

# --- Panel definitions ---
panels = [
    {
        "image": "/Users/asaluja/Documents/Job_Search/anthropic/vision-eval/generate/images/text_visual_conflict/value_label_n3_3.png",
        "gt": "52 (bar height)",
        "model": "36 (reads label)",
        "explanation": "Label '36' placed on bar actually at height 52; model reads the text, ignores the visual bar.",
    },
    {
        "image": "/Users/asaluja/Documents/Job_Search/anthropic/vision-eval/generate/images/text_visual_conflict/annotation_n3_1.png",
        "gt": "Product C (highest bar)",
        "model": "Product B (annotated)",
        "explanation": "Bars: A=15, B=20, C=22 (gap=2). 'Highest' arrow on B tips model toward wrong answer when bars are nearly equal.",
    },
    {
        "image": "/Users/asaluja/Documents/Job_Search/anthropic/vision-eval/generate/images/text_visual_conflict/annotation_n4_1.png",
        "gt": "West (value=46)",
        "model": "South (annotated, value=44)",
        "explanation": "Bars: North=33, South=44, East=34, West=46 (gap=2). 'Highest' arrow on South; model follows annotation over visual.",
    },
]

fig, axes = plt.subplots(1, 3, figsize=(13, 5.5))
fig.patch.set_facecolor("white")

for ax, panel in zip(axes, panels):
    img = mpimg.imread(panel["image"])
    ax.imshow(img)
    ax.axis("off")

    # Build caption text below image
    wrapped = textwrap.fill(panel["explanation"], width=44)
    caption = f"GT: {panel['gt']}\nModel: {panel['model']}\n\n{wrapped}"

    ax.text(
        0.5, -0.03,
        caption,
        transform=ax.transAxes,
        fontsize=7.5,
        verticalalignment="top",
        horizontalalignment="center",
        fontfamily="monospace",
        color="#222222",
        wrap=False,
    )

plt.suptitle(
    "Text-Visual Consistency: Representative Failure Cases",
    fontsize=10,
    fontweight="bold",
    y=1.01,
)
plt.tight_layout(pad=1.5)
plt.savefig(
    "/Users/asaluja/Documents/Job_Search/anthropic/vision-eval/figures/text_visual_consistency_errors.png",
    dpi=150,
    bbox_inches="tight",
    facecolor="white",
)
print("Saved figures/text_visual_consistency_errors.png")
