"""Generate color discrimination tasks.

Tests the ability to distinguish visually similar colors:
1. Similar-shade bar charts: bars in similar hues, match to legend
2. Color grid: identify which cell has a different shade
3. Bar charts with similar-color series: read the correct series value

This is a genuine gap — no paper systematically tests fine-grained color perception.
"""

from __future__ import annotations

import os
import random

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from generate.base import ensure_dir, make_instances

# Color families — pairs/triples of similar hues for discrimination testing
SIMILAR_COLOR_GROUPS = {
    "blues": [
        ("#1565C0", "dark blue"),
        ("#42A5F5", "medium blue"),
        ("#90CAF9", "light blue"),
    ],
    "reds": [
        ("#C62828", "dark red"),
        ("#EF5350", "medium red"),
        ("#EF9A9A", "light red"),
    ],
    "greens": [
        ("#2E7D32", "dark green"),
        ("#66BB6A", "medium green"),
        ("#A5D6A7", "light green"),
    ],
    "purples": [
        ("#6A1B9A", "dark purple"),
        ("#AB47BC", "medium purple"),
        ("#CE93D8", "light purple"),
    ],
    "oranges": [
        ("#E65100", "dark orange"),
        ("#FF9800", "medium orange"),
        ("#FFE0B2", "light orange"),
    ],
}

# Maximally distinct colors for easy-difficulty baseline
DISTINCT_COLORS = [
    ("#1565C0", "blue"),
    ("#C62828", "red"),
    ("#2E7D32", "green"),
    ("#FF9800", "orange"),
    ("#6A1B9A", "purple"),
]

CATEGORY_LABELS = ["A", "B", "C", "D", "E", "F"]

# Base hues for programmatic shade generation (H, S in HSL)
FAMILY_HUES = {
    "blues": (0.59, 0.80),    # H≈212°
    "reds": (0.0, 0.70),      # H≈0°
    "greens": (0.34, 0.45),   # H≈123°
    "purples": (0.79, 0.60),  # H≈284°
    "oranges": (0.07, 0.90),  # H≈25°
}


def _hsl_to_hex(h, s, l):
    """Convert HSL (h in [0,1], s in [0,1], l in [0,1]) to hex color."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def _make_color_bar_chart(categories, values, colors, color_labels, output_path):
    """Bar chart where each bar has a specific color from a family."""
    fig, ax = plt.subplots(figsize=(8, 5))
    hex_colors = [c[0] for c in colors]
    bars = ax.bar(categories, values, color=hex_colors, width=0.6, edgecolor="black", linewidth=0.5)

    # Legend mapping color names to bars
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c[0], edgecolor="black", label=c[1])
                       for c in colors]
    ax.legend(handles=legend_elements, loc="upper right")

    ax.set_ylabel("Value")
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(values) * 1.15)
    fig.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def _make_color_grid(grid_colors, odd_pos, cell_size, output_path):
    """Grid of colored cells where one cell is a different shade."""
    from PIL import Image, ImageDraw
    rows, cols = len(grid_colors), len(grid_colors[0])
    margin = 10
    img_w = 2 * margin + cols * cell_size
    img_h = 2 * margin + rows * cell_size

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    for r in range(rows):
        for c in range(cols):
            x0 = margin + c * cell_size
            y0 = margin + r * cell_size
            draw.rectangle([x0, y0, x0 + cell_size, y0 + cell_size],
                           fill=grid_colors[r][c], outline="black", width=1)

    img.save(output_path)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    n_bars_list: list[int] | None = None,
    difficulties: list[str] | None = None,
    grid_sizes: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate color discrimination tasks.

    Part A: Bar charts with similar-color bars + legend matching questions.
    Part B: Color grids with one odd-shade cell.
    """
    if n_bars_list is None:
        n_bars_list = [3, 4, 5]
    if difficulties is None:
        difficulties = ["easy", "hard"]  # distinct vs similar colors
    if grid_sizes is None:
        grid_sizes = [4, 6]

    out = ensure_dir(os.path.join(output_dir, "color_discrimination"))
    instances = []

    # --- Part A: Color-legend matching bar charts ---
    for n_bars in n_bars_list:
        for difficulty in difficulties:
            # For hard difficulty, sweep all color families explicitly
            if difficulty == "hard":
                families_to_use = list(SIMILAR_COLOR_GROUPS.keys())
            else:
                families_to_use = [None]  # single pass for easy

            for family in families_to_use:
                for i in range(n_per_config):
                    categories = CATEGORY_LABELS[:n_bars]
                    values = [random.randint(15, 90) for _ in range(n_bars)]

                    if difficulty == "easy":
                        colors = random.sample(DISTINCT_COLORS, min(n_bars, len(DISTINCT_COLORS)))
                        family_name = "mixed"
                    else:  # hard — similar shades from specified family
                        family_colors = SIMILAR_COLOR_GROUPS[family]
                        colors = []
                        while len(colors) < n_bars:
                            colors.extend(family_colors)
                        colors = colors[:n_bars]
                        random.shuffle(colors)
                        family_name = family

                    fname = f"color_bar_{n_bars}_{difficulty}_{family_name}_{i}.png"
                    fpath = os.path.join(out, fname)
                    _make_color_bar_chart(categories, values, colors, [c[1] for c in colors], fpath)

                    # Question: "What is the value of the [color_name] bar?"
                    q_idx = random.randint(0, n_bars - 1)
                    q_color_name = colors[q_idx][1]
                    q_value = values[q_idx]

                    instances.extend(make_instances(
                        fpath, "chart_legend_match", q_value,
                        subtask=f"color_{difficulty}_n{n_bars}",
                        metadata={
                            "chart_type": "color_discrimination",
                            "n_bars": n_bars, "difficulty": difficulty,
                            "query_color": q_color_name,
                            "color_family": family_name,
                            "categories": categories, "values": values,
                        },
                        color=q_color_name,
                    ))

    # --- Part B: Color grid — find the odd cell ---
    # Four difficulty levels by lightness delta (ΔL in HSL space):
    #   "easy"      = darkest vs lightest (ΔL≈30-40)
    #   "hard"      = dark vs medium (ΔL≈16-23)
    #   "very_hard" = ΔL≈10 (programmatic)
    #   "extreme"   = ΔL≈5 (programmatic)
    grid_difficulties = ["easy", "hard", "very_hard", "near_threshold", "extreme"]
    for grid_size in grid_sizes:
        for family_name, family_colors in SIMILAR_COLOR_GROUPS.items():
            for grid_diff in grid_difficulties:
                for i in range(n_per_config):
                    if grid_diff == "easy":
                        base_color = family_colors[0][0]  # darkest shade
                        odd_color = family_colors[-1][0]  # lightest shade
                        base_name = family_colors[0][1]
                        odd_name = family_colors[-1][1]
                    elif grid_diff == "hard":
                        base_color = family_colors[0][0]  # darkest shade
                        odd_color = family_colors[1][0]  # medium shade
                        base_name = family_colors[0][1]
                        odd_name = family_colors[1][1]
                    else:
                        # Programmatic: generate base at L=0.40, odd at L=0.40+delta
                        h, s = FAMILY_HUES[family_name]
                        base_l = 0.40
                        delta_map = {"very_hard": 0.10, "near_threshold": 0.07, "extreme": 0.05}
                        delta = delta_map[grid_diff]
                        base_color = _hsl_to_hex(h, s, base_l)
                        odd_color = _hsl_to_hex(h, s, base_l + delta)
                        base_name = f"{family_name} L={base_l:.0%}"
                        odd_name = f"{family_name} L={base_l + delta:.0%}"

                    odd_r = random.randint(0, grid_size - 1)
                    odd_c = random.randint(0, grid_size - 1)

                    grid = [[base_color] * grid_size for _ in range(grid_size)]
                    grid[odd_r][odd_c] = odd_color

                    fname = f"color_grid_{grid_size}_{family_name}_{grid_diff}_{i}.png"
                    fpath = os.path.join(out, fname)
                    cell_size = max(40, 400 // grid_size)
                    _make_color_grid(grid, (odd_r, odd_c), cell_size, fpath)

                    # Row/col labels (1-indexed for rows, letters for cols)
                    cell_id = f"{chr(ord('A') + odd_c)}{odd_r + 1}"

                    instances.extend(make_instances(
                        fpath, "color_grid_odd", cell_id,
                        subtask=f"grid_{grid_size}_{family_name}_{grid_diff}",
                        metadata={
                            "grid_size": grid_size, "color_family": family_name,
                            "grid_difficulty": grid_diff,
                            "base_color": base_name, "odd_color": odd_name,
                            "base_hex": base_color, "odd_hex": odd_color,
                            "odd_row": odd_r, "odd_col": odd_c,
                            "odd_cell_id": cell_id,
                        },
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_bars_list=[4], difficulties=["easy", "hard"],
                     grid_sizes=[5])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} {inst.subtask:25s} -> {inst.ground_truth}")
