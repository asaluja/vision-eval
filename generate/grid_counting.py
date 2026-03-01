"""Generate grid images for row/column counting.

Creates empty grids and text-filled grids. The key insight from VLMs Are Blind:
models do much better with text-filled grids (they use OCR cues, not vision).
"""

from __future__ import annotations

import os
import random

from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm

from generate.base import TaskInstance, ensure_dir, make_instances
from evaluate.prompts import get_prompt

WORD_LIST = [
    "apple", "brick", "crane", "delta", "eagle", "flame", "grape", "house",
    "ivory", "joker", "knife", "lemon", "maple", "nerve", "ocean", "pearl",
    "queen", "river", "stone", "tiger", "umbra", "voice", "wheat", "xenon",
    "yacht", "zebra", "bloom", "clash", "drift", "frost", "globe", "haste",
    "inbox", "jewel", "knack", "lunar", "minor", "noble", "orbit", "plume",
]


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        path = fm.findfont("DejaVu Sans")
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _draw_grid(
    rows: int,
    cols: int,
    image_size: int,
    line_width: int,
    with_text: bool,
    output_path: str,
):
    """Draw a grid image with optional text in cells."""
    img = Image.new("RGB", (image_size, image_size), "white")
    draw = ImageDraw.Draw(img)

    margin = int(image_size * 0.05)
    grid_w = image_size - 2 * margin
    grid_h = image_size - 2 * margin
    cell_w = grid_w / cols
    cell_h = grid_h / rows

    # Draw grid lines
    for r in range(rows + 1):
        y = margin + int(r * cell_h)
        draw.line([(margin, y), (margin + grid_w, y)], fill="black", width=line_width)
    for c in range(cols + 1):
        x = margin + int(c * cell_w)
        draw.line([(x, margin), (x, margin + grid_h)], fill="black", width=line_width)

    # Fill cells with text if requested
    if with_text:
        font_size = max(8, int(min(cell_w, cell_h) * 0.25))
        font = _get_font(font_size)
        for r in range(rows):
            for c in range(cols):
                word = random.choice(WORD_LIST)
                cx = margin + int((c + 0.5) * cell_w)
                cy = margin + int((r + 0.5) * cell_h)
                bbox = font.getbbox(word)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((cx - tw // 2, cy - th // 2), word, fill="black", font=font)

    img.save(output_path)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    grid_sizes: list[tuple[int, int]] | None = None,
    image_sizes: list[int] | None = None,
    line_widths: list[int] | None = None,
    text_modes: list[bool] | None = None,
) -> list[TaskInstance]:
    """Generate grid counting images."""
    if grid_sizes is None:
        # high-signal: square and near-square grids across difficulty range
        grid_sizes = [(r, c) for r in [3, 5, 7, 9, 11] for c in [r, r + 1]]
    if image_sizes is None:
        image_sizes = [768]  # low-signal: fixed
    if line_widths is None:
        line_widths = [3]  # low-signal: fixed
    if text_modes is None:
        text_modes = [False, True]  # HIGH-SIGNAL: text dramatically helps VLMs

    task_type = "grid_counting"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    for rows, cols in grid_sizes:
        for img_size in image_sizes:
            for lw in line_widths:
                for with_text in text_modes:
                    for i in range(n_per_config):
                        text_tag = "text" if with_text else "empty"
                        fname = f"grid_{rows}x{cols}_{text_tag}_s{img_size}_lw{lw}_{i}.png"
                        fpath = os.path.join(out, fname)

                        _draw_grid(rows, cols, img_size, lw, with_text, fpath)

                        gt = f"{rows}, {cols}"
                        instances.extend(make_instances(
                            fpath, task_type, gt,
                            subtask=f"{rows}x{cols}_{text_tag}",
                            metadata={
                                "rows": rows, "cols": cols, "image_size": img_size,
                                "line_width": lw, "with_text": with_text,
                            },
                        ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, grid_sizes=[(4, 5), (8, 8)],
                     image_sizes=[600], line_widths=[3], text_modes=[False, True])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {os.path.basename(inst.image_path)} -> {inst.ground_truth}")
