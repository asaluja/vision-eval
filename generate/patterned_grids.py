"""Generate patterned grid images with anomalous cells (VLMs Are Biased).

Each cell in a grid contains a pattern of shapes (dice dots or tally marks)
following a spatial rule. One cell is modified (add/remove one shape) to
create an anomaly. The model must count the shapes in the anomalous cell.

Key bias: the surrounding pattern suggests a count, but the actual count
differs by 1. Models tend to report the pattern-suggested count.
"""

from __future__ import annotations

import os
import random

from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm

from generate.base import TaskInstance, ensure_dir
from evaluate.prompts import get_prompt


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        path = fm.findfont("DejaVu Sans")
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# Standard dice dot positions (relative to cell center, as fractions of cell size)
DICE_POSITIONS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5), (0.25, 0.75), (0.75, 0.75)],
}


def _cell_count(row: int, col: int, n_rows: int, n_cols: int) -> int:
    """Compute the pattern-based count for a cell.

    Rule: count = min(distance_to_nearest_vertical_edge, distance_to_nearest_horizontal_edge) + 1
    This creates a pattern that increases toward the center.
    """
    row_dist = min(row, n_rows - 1 - row)
    col_dist = min(col, n_cols - 1 - col)
    return min(row_dist, col_dist) + 1


def _draw_dice_dots(draw: ImageDraw, cx: int, cy: int, cell_size: int, count: int, dot_radius: int):
    """Draw dice-style dots in a cell."""
    if count <= 6:
        positions = DICE_POSITIONS.get(count, [])
    else:
        # Grid layout for counts > 6
        side = int(count ** 0.5) + 1
        positions = []
        for r in range(side):
            for c in range(side):
                if len(positions) < count:
                    positions.append(((c + 1) / (side + 1), (r + 1) / (side + 1)))

    for fx, fy in positions:
        x = cx + int((fx - 0.5) * cell_size * 0.7)
        y = cy + int((fy - 0.5) * cell_size * 0.7)
        draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
                     fill="black")


def _draw_tally_marks(draw: ImageDraw, cx: int, cy: int, cell_size: int, count: int, line_width: int = 2):
    """Draw tally marks in a cell."""
    mark_height = int(cell_size * 0.5)
    mark_spacing = max(4, int(cell_size * 0.08))
    group_spacing = max(6, int(cell_size * 0.15))

    # Compute total width to center the marks
    n_groups = count // 5
    n_remaining = count % 5
    total_marks_width = (n_groups * (4 * mark_spacing + group_spacing) +
                         n_remaining * mark_spacing)
    start_x = cx - total_marks_width // 2

    x = start_x
    marks_drawn = 0
    y_top = cy - mark_height // 2
    y_bot = cy + mark_height // 2

    for g in range(n_groups):
        # Draw 4 vertical lines
        for _ in range(4):
            draw.line([(x, y_top), (x, y_bot)], fill="black", width=line_width)
            x += mark_spacing
            marks_drawn += 1
        # Draw diagonal strike-through
        x_start = x - 4 * mark_spacing
        draw.line([(x_start, y_bot - int(mark_height * 0.1)),
                    (x - mark_spacing + 2, y_top + int(mark_height * 0.1))],
                   fill="black", width=line_width)
        x += group_spacing

    # Draw remaining vertical lines
    for _ in range(n_remaining):
        draw.line([(x, y_top), (x, y_bot)], fill="black", width=line_width)
        x += mark_spacing
        marks_drawn += 1


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    grid_sizes: list[int] | None = None,
    image_sizes: list[int] | None = None,
    grid_types: list[str] | None = None,
    anomaly_types: list[str] | None = None,
) -> list[TaskInstance]:
    """Generate patterned grid images with anomalous cells."""
    if grid_sizes is None:
        grid_sizes = [6, 8, 10]
    if image_sizes is None:
        image_sizes = [768, 1152]
    if grid_types is None:
        grid_types = ["dice", "tally"]
    if anomaly_types is None:
        anomaly_types = ["remove", "add"]

    task_type = "patterned_grid"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    label_font_size = 12

    for grid_size in grid_sizes:
        for img_size in image_sizes:
            for gtype in grid_types:
                for anomaly in anomaly_types:
                    for i in range(n_per_config):
                        fname = f"pgrid_{gtype}_{anomaly}_g{grid_size}_s{img_size}_{i}.png"
                        fpath = os.path.join(out, fname)

                        # Pick a non-edge cell for the anomaly
                        valid_cells = [
                            (r, c) for r in range(1, grid_size - 1)
                            for c in range(1, grid_size - 1)
                            if _cell_count(r, c, grid_size, grid_size) >= 2  # need count >= 2 for remove
                        ]
                        if not valid_cells:
                            valid_cells = [(grid_size // 2, grid_size // 2)]
                        anom_r, anom_c = random.choice(valid_cells)

                        # Compute grid
                        margin = int(img_size * 0.06)
                        label_space = int(img_size * 0.04)
                        grid_area = img_size - 2 * margin - label_space
                        cell_size = grid_area // grid_size

                        img = Image.new("RGB", (img_size, img_size), "white")
                        draw = ImageDraw.Draw(img)
                        font = _get_font(label_font_size)

                        x_offset = margin + label_space
                        y_offset = margin + label_space

                        # Draw cells
                        for r in range(grid_size):
                            for c in range(grid_size):
                                cx = x_offset + c * cell_size + cell_size // 2
                                cy = y_offset + r * cell_size + cell_size // 2
                                x0 = x_offset + c * cell_size
                                y0 = y_offset + r * cell_size

                                # Cell border
                                draw.rectangle([x0, y0, x0 + cell_size, y0 + cell_size],
                                               outline="black", width=1)

                                # Compute count for this cell
                                count = _cell_count(r, c, grid_size, grid_size)
                                if r == anom_r and c == anom_c:
                                    canonical_count = count
                                    if anomaly == "remove":
                                        count = max(0, count - 1)
                                    else:  # add
                                        count = count + 1

                                # Draw pattern
                                dot_radius = max(2, cell_size // 12)
                                if gtype == "dice":
                                    _draw_dice_dots(draw, cx, cy, cell_size, count, dot_radius)
                                else:
                                    _draw_tally_marks(draw, cx, cy, cell_size, count)

                        # Draw row/column labels
                        for r in range(grid_size):
                            label = str(r + 1)
                            y = y_offset + r * cell_size + cell_size // 2
                            draw.text((margin, y - 6), label, fill="black", font=font)
                        for c in range(grid_size):
                            label = chr(ord("A") + c)
                            x = x_offset + c * cell_size + cell_size // 2 - 4
                            draw.text((x, margin), label, fill="black", font=font)

                        img.save(fpath)

                        # Cell ID for prompt
                        cell_id = f"{chr(ord('A') + anom_c)}{anom_r + 1}"
                        shape_name = "circles" if gtype == "dice" else "lines"
                        actual_count = count  # post-anomaly

                        prompt = get_prompt(task_type, shape_name=shape_name, cell_id=cell_id)
                        instances.append(TaskInstance(
                            image_path=os.path.abspath(fpath),
                            prompt=prompt,
                            ground_truth=actual_count,
                            task_type=task_type,
                            subtask=f"{gtype}_{anomaly}",
                            metadata={
                                "grid_type": gtype, "anomaly_type": anomaly,
                                "grid_size": grid_size, "image_size": img_size,
                                "anomaly_cell": cell_id,
                                "canonical_count": canonical_count,
                                "actual_count": actual_count,
                                "expected_bias": canonical_count,
                            },
                        ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, grid_sizes=[6], image_sizes=[768],
                     grid_types=["dice", "tally"], anomaly_types=["remove"])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {os.path.basename(inst.image_path)} -> "
              f"actual={inst.ground_truth}, bias={inst.metadata['expected_bias']}, "
              f"cell={inst.metadata['anomaly_cell']}")
