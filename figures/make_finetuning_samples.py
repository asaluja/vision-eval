"""Generate sample finetuning images for the report."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

COLORS = list(matplotlib.cm.tab10.colors[:10])
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "figures")

def make_no_label_bar():
    """SFT example: bar chart with gridlines but no value labels."""
    categories = ["Jan", "Feb", "Mar", "Apr", "May"]
    values = [45, 73, 38, 82, 61]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(categories, values, color=COLORS[:5], width=0.6)
    ax.set_ylabel("Value")
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    fig.savefig(os.path.join(OUT, "ft_sample_no_label.png"),
                dpi=120, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("Saved ft_sample_no_label.png")


def make_wrong_label_bar():
    """DPO example: bar chart where Apr label says 55 but bar is at ~82."""
    categories = ["Jan", "Feb", "Mar", "Apr", "May"]
    true_values = [45, 73, 38, 82, 61]
    display_labels = [45, 73, 38, 55, 61]  # Apr is wrong

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(categories, true_values, color=COLORS[:5], width=0.6)
    for bar, label in zip(bars, display_labels):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(label), ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("Value")
    ax.set_ylim(0, 100)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    fig.savefig(os.path.join(OUT, "ft_sample_wrong_label.png"),
                dpi=120, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("Saved ft_sample_wrong_label.png")


if __name__ == "__main__":
    make_no_label_bar()
    make_wrong_label_bar()
