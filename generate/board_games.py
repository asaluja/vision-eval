"""Generate board game images with modified dimensions (VLMs Are Biased).

Creates chess and Go boards with non-standard dimensions to test if
models report actual dimensions vs. canonical ones (8x8 for chess,
19x19 for Go).
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

from generate.base import TaskInstance, ensure_dir
from evaluate.prompts import get_prompt

# Standard board game colors
CHESS_LIGHT = "#f0d9b5"
CHESS_DARK = "#b58863"
GO_BOARD = "#DCB35C"
GO_LINE = "#000000"


def _draw_chess_board(rows: int, cols: int, image_size: int, output_path: str):
    """Draw a chess-style alternating color board."""
    img = Image.new("RGB", (image_size, image_size), "white")
    draw = ImageDraw.Draw(img)

    margin = int(image_size * 0.05)
    board_size = image_size - 2 * margin
    cell_w = board_size / cols
    cell_h = board_size / rows

    for r in range(rows):
        for c in range(cols):
            color = CHESS_LIGHT if (r + c) % 2 == 0 else CHESS_DARK
            x0 = margin + int(c * cell_w)
            y0 = margin + int(r * cell_h)
            x1 = margin + int((c + 1) * cell_w)
            y1 = margin + int((r + 1) * cell_h)
            draw.rectangle([x0, y0, x1, y1], fill=color)

    # Border
    draw.rectangle([margin, margin, margin + board_size, margin + board_size],
                   outline="black", width=2)

    img.save(output_path)


def _draw_go_board(rows: int, cols: int, image_size: int, output_path: str):
    """Draw a Go-style grid board with star points."""
    img = Image.new("RGB", (image_size, image_size), GO_BOARD)
    draw = ImageDraw.Draw(img)

    margin = int(image_size * 0.08)
    board_w = image_size - 2 * margin
    board_h = image_size - 2 * margin
    cell_w = board_w / (cols - 1) if cols > 1 else board_w
    cell_h = board_h / (rows - 1) if rows > 1 else board_h

    # Draw grid lines
    line_width = max(1, image_size // 500)
    for r in range(rows):
        y = margin + int(r * cell_h)
        draw.line([(margin, y), (margin + board_w, y)], fill=GO_LINE, width=line_width)
    for c in range(cols):
        x = margin + int(c * cell_w)
        draw.line([(x, margin), (x, margin + board_h)], fill=GO_LINE, width=line_width)

    # Star points (hoshi) — only if standard 19x19
    star_radius = max(3, image_size // 150)
    if rows == 19 and cols == 19:
        star_positions = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15),
                          (15, 3), (15, 9), (15, 15)]
    elif rows == 9 and cols == 9:
        star_positions = [(2, 2), (2, 6), (4, 4), (6, 2), (6, 6)]
    else:
        star_positions = []

    for sr, sc in star_positions:
        if sr < rows and sc < cols:
            x = margin + int(sc * cell_w)
            y = margin + int(sr * cell_h)
            draw.ellipse([x - star_radius, y - star_radius,
                          x + star_radius, y + star_radius], fill=GO_LINE)

    img.save(output_path)


GAME_CONFIGS = {
    "chess": {
        "canonical": (8, 8),
        "variants": [(7, 8), (9, 8), (8, 7), (8, 9)],
        "draw_fn": _draw_chess_board,
    },
    "go": {
        "canonical": (19, 19),
        "variants": [(18, 19), (20, 19), (19, 18), (19, 20)],
        "draw_fn": _draw_go_board,
    },
}


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    game_types: list[str] | None = None,
    image_sizes: list[int] | None = None,
    include_canonical: bool = True,
) -> list[TaskInstance]:
    """Generate board game images with standard and modified dimensions."""
    if game_types is None:
        game_types = ["chess", "go"]
    if image_sizes is None:
        image_sizes = [384, 768]

    out = ensure_dir(os.path.join(output_dir, "board_games"))
    instances = []

    for game in game_types:
        cfg = GAME_CONFIGS[game]
        draw_fn = cfg["draw_fn"]
        canon_r, canon_c = cfg["canonical"]

        # Build list of (rows, cols) to generate
        dims_list = list(cfg["variants"])
        if include_canonical:
            dims_list.append(cfg["canonical"])

        for rows, cols in dims_list:
            for img_size in image_sizes:
                for i in range(n_per_config):
                    # Generate for both row and column questions
                    fname = f"{game}_{rows}x{cols}_s{img_size}_{i}.png"
                    fpath = os.path.join(out, fname)
                    draw_fn(rows, cols, img_size, fpath)

                    # Row-counting question
                    prompt_r = get_prompt("board_game_rows", game_type=game)
                    instances.append(TaskInstance(
                        image_path=os.path.abspath(fpath),
                        prompt=prompt_r,
                        ground_truth=rows,
                        task_type="board_game_rows",
                        subtask=f"{game}_{rows}x{cols}",
                        metadata={
                            "game_type": game, "rows": rows, "cols": cols,
                            "image_size": img_size,
                            "canonical_rows": canon_r, "canonical_cols": canon_c,
                            "expected_bias": canon_r,
                            "is_canonical": (rows, cols) == (canon_r, canon_c),
                        },
                    ))

                    # Column-counting question
                    prompt_c = get_prompt("board_game_cols", game_type=game)
                    instances.append(TaskInstance(
                        image_path=os.path.abspath(fpath),
                        prompt=prompt_c,
                        ground_truth=cols,
                        task_type="board_game_cols",
                        subtask=f"{game}_{rows}x{cols}",
                        metadata={
                            "game_type": game, "rows": rows, "cols": cols,
                            "image_size": img_size,
                            "canonical_rows": canon_r, "canonical_cols": canon_c,
                            "expected_bias": canon_c,
                            "is_canonical": (rows, cols) == (canon_r, canon_c),
                        },
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, image_sizes=[512])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        meta = inst.metadata
        print(f"  {os.path.basename(inst.image_path)} | {inst.task_type} -> "
              f"{inst.ground_truth} (bias={meta['expected_bias']}, "
              f"canonical={meta['is_canonical']})")
