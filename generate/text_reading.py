"""Generate text reading / OCR stress test images.

Tests text reading under varying difficulty:
1. Font size variation (large to tiny)
2. Rotation (horizontal to diagonal to vertical)
3. Contrast variation (black-on-white to low-contrast gray-on-gray)
4. Chart axis labels at varying sizes and rotations

This isolates the text reading primitive that all chart/table/document tasks depend on.
"""

from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt

from generate.base import ensure_dir, make_instances, _get_font

# Word pools for reading tasks
WORDS = [
    "Revenue", "Expenses", "Margin", "Growth", "Budget",
    "Forecast", "Quarterly", "Analysis", "Performance", "Benchmark",
    "Inventory", "Logistics", "Marketing", "Strategy", "Compliance",
]

NUMBERS = ["42", "137", "256", "89", "1024", "73", "518", "365", "99", "2048"]


def _draw_text_on_canvas(
    text: str,
    font_size: int,
    rotation: int,
    fg_color: str,
    bg_color: str,
    canvas_size: int,
    output_path: str,
):
    """Draw text on a canvas with specified font size, rotation, and contrast."""
    img = Image.new("RGB", (canvas_size, canvas_size), bg_color)
    font = _get_font(font_size)

    # Render text on a temporary image, then rotate and paste
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Create text image with padding
    pad = 20
    text_img = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((pad, pad - bbox[1]), text, fill=fg_color, font=font)

    # Rotate
    if rotation != 0:
        text_img = text_img.rotate(rotation, expand=True, resample=Image.BICUBIC)

    # Paste centered
    paste_x = (canvas_size - text_img.width) // 2
    paste_y = (canvas_size - text_img.height) // 2
    img.paste(text_img, (paste_x, paste_y), text_img)

    img.save(output_path)


def _draw_chart_with_labels(
    categories: list[str],
    values: list[int],
    label_font_size: int,
    label_rotation: int,
    output_path: str,
):
    """Draw a bar chart where axis labels are at controlled size/rotation."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(categories, values, color="#4472C4", width=0.6)
    ax.set_ylabel("Value")
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(values) * 1.15)

    # Control label appearance
    plt.xticks(rotation=label_rotation, fontsize=label_font_size,
               ha="right" if label_rotation > 20 else "center")
    plt.yticks(fontsize=label_font_size)

    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    # Isolated text params
    font_sizes: list[int] | None = None,
    rotations: list[int] | None = None,
    contrasts: list[str] | None = None,
    # Chart label params
    label_font_sizes: list[int] | None = None,
    label_rotations: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate text reading tasks at varying difficulty levels."""
    if font_sizes is None:
        font_sizes = [48, 32, 20, 14, 10]  # large to tiny
    if rotations is None:
        rotations = [0, 15, 30, 45, 90]
    if contrasts is None:
        contrasts = ["high", "medium", "low"]
    if label_font_sizes is None:
        label_font_sizes = [12, 9, 7]
    if label_rotations is None:
        label_rotations = [0, 30, 45, 60]

    out = ensure_dir(os.path.join(output_dir, "text_reading"))
    instances = []

    canvas_size = 512

    # Contrast levels
    contrast_map = {
        "high": ("black", "white"),
        "medium": ("#555555", "#DDDDDD"),
        "low": ("#888888", "#BBBBBB"),
    }

    # --- Part A: Isolated word reading ---
    for fs in font_sizes:
        for rot in rotations:
            for contrast in contrasts:
                for i in range(n_per_config):
                    word = random.choice(WORDS)
                    fg, bg = contrast_map[contrast]

                    fname = f"text_word_f{fs}_r{rot}_c{contrast}_{i}.png"
                    fpath = os.path.join(out, fname)
                    _draw_text_on_canvas(word, fs, rot, fg, bg, canvas_size, fpath)

                    instances.extend(make_instances(
                        fpath, "text_word_reading", word,
                        subtask=f"font{fs}_rot{rot}_c{contrast}",
                        metadata={
                            "text": word, "font_size": fs, "rotation": rot,
                            "contrast": contrast,
                        },
                    ))

    # --- Part B: Isolated number reading ---
    for fs in font_sizes:
        for rot in [0, 30, 45, 90]:  # fewer rotation values for numbers
            for i in range(n_per_config):
                number = random.choice(NUMBERS)
                fg, bg = "black", "white"

                fname = f"text_num_f{fs}_r{rot}_{i}.png"
                fpath = os.path.join(out, fname)
                _draw_text_on_canvas(number, fs, rot, fg, bg, canvas_size, fpath)

                instances.extend(make_instances(
                    fpath, "text_number_reading", int(number),
                    subtask=f"font{fs}_rot{rot}",
                    metadata={
                        "text": number, "font_size": fs, "rotation": rot,
                    },
                ))

    # --- Part C: Chart axis label reading ---
    for lfs in label_font_sizes:
        for lrot in label_rotations:
            for i in range(n_per_config):
                n_cats = 5
                categories = random.sample(WORDS, n_cats)
                values = [random.randint(10, 90) for _ in range(n_cats)]

                fname = f"text_chart_lf{lfs}_lr{lrot}_{i}.png"
                fpath = os.path.join(out, fname)
                _draw_chart_with_labels(categories, values, lfs, lrot, fpath)

                # Ask about a specific category's value
                q_idx = random.randint(0, n_cats - 1)
                instances.extend(make_instances(
                    fpath, "chart_bar_value", values[q_idx],
                    subtask=f"label_font{lfs}_rot{lrot}",
                    metadata={
                        "chart_type": "text_stress",
                        "label_font_size": lfs, "label_rotation": lrot,
                        "categories": categories, "values": values,
                        "query_category": categories[q_idx],
                    },
                    category=categories[q_idx],
                ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, font_sizes=[36, 14], rotations=[0, 45],
                     contrasts=["high", "low"], label_font_sizes=[12, 7],
                     label_rotations=[0, 45])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} {inst.subtask:30s} -> {inst.ground_truth}")
