"""Generate table images for cell lookup, row counting, and extremum tasks.

Creates data tables with row/column headers, borders, and cell values
using PIL (consistent with grid_counting.py pattern).
"""

from __future__ import annotations

import os
import random

from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm

from generate.base import TaskInstance, ensure_dir, make_instances

# Entity pools for row headers
ROW_POOLS = {
    "countries": ["USA", "UK", "Germany", "France", "Japan", "Brazil", "India", "Canada",
                  "Australia", "Mexico"],
    "products": ["Widget A", "Widget B", "Widget C", "Widget D", "Widget E",
                 "Widget F", "Widget G", "Widget H"],
    "months": ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October"],
    "teams": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon",
              "Zeta", "Eta", "Theta"],
}

COL_METRICS = ["Revenue", "Units", "Score", "Growth", "Rating", "Cost", "Margin", "Users"]

HEADER_BG_COLOR = "#4472C4"
HEADER_TEXT_COLOR = "white"
ALT_ROW_COLOR = "#D9E2F3"


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        path = fm.findfont("DejaVu Sans")
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _draw_table(
    row_headers: list[str],
    col_headers: list[str],
    data: list[list[int]],
    header_style: str,
    image_width: int,
    output_path: str,
):
    """Draw a data table with headers and cell values."""
    n_rows = len(row_headers)
    n_cols = len(col_headers)

    # Layout calculations
    margin = 20
    # First column is wider (for row headers)
    header_col_width = max(100, image_width // (n_cols + 2))
    data_col_width = (image_width - 2 * margin - header_col_width) // n_cols
    row_height = max(35, min(50, 400 // n_rows))
    header_row_height = row_height + 5

    total_height = 2 * margin + header_row_height + n_rows * row_height
    total_width = 2 * margin + header_col_width + n_cols * data_col_width

    img = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(img)

    font_size = max(11, min(16, data_col_width // 6))
    font = _get_font(font_size)
    header_font = _get_font(font_size + 1)

    x0 = margin
    y0 = margin

    # Draw header row
    if header_style == "shaded":
        # Empty top-left corner
        draw.rectangle([x0, y0, x0 + header_col_width, y0 + header_row_height],
                       fill=HEADER_BG_COLOR, outline="black")
        for c, col_h in enumerate(col_headers):
            cx = x0 + header_col_width + c * data_col_width
            draw.rectangle([cx, y0, cx + data_col_width, y0 + header_row_height],
                           fill=HEADER_BG_COLOR, outline="black")
            bbox = header_font.getbbox(col_h)
            tw = bbox[2] - bbox[0]
            draw.text((cx + (data_col_width - tw) // 2, y0 + 8),
                      col_h, fill=HEADER_TEXT_COLOR, font=header_font)
    else:
        draw.rectangle([x0, y0, x0 + header_col_width, y0 + header_row_height],
                       outline="black")
        for c, col_h in enumerate(col_headers):
            cx = x0 + header_col_width + c * data_col_width
            draw.rectangle([cx, y0, cx + data_col_width, y0 + header_row_height],
                           outline="black")
            bbox = font.getbbox(col_h)
            tw = bbox[2] - bbox[0]
            draw.text((cx + (data_col_width - tw) // 2, y0 + 8),
                      col_h, fill="black", font=font)

    # Draw data rows
    for r, row_h in enumerate(row_headers):
        ry = y0 + header_row_height + r * row_height
        bg = ALT_ROW_COLOR if (header_style == "shaded" and r % 2 == 1) else "white"

        # Row header
        rh_bg = ALT_ROW_COLOR if header_style == "shaded" else "white"
        if header_style == "shaded":
            rh_bg = bg
        draw.rectangle([x0, ry, x0 + header_col_width, ry + row_height],
                       fill=rh_bg, outline="black")
        bbox = font.getbbox(row_h)
        tw = bbox[2] - bbox[0]
        draw.text((x0 + 8, ry + (row_height - font_size) // 2),
                  row_h, fill="black", font=font)

        # Data cells
        for c in range(n_cols):
            cx = x0 + header_col_width + c * data_col_width
            draw.rectangle([cx, ry, cx + data_col_width, ry + row_height],
                           fill=bg, outline="black")
            val_str = str(data[r][c])
            bbox = font.getbbox(val_str)
            tw = bbox[2] - bbox[0]
            draw.text((cx + (data_col_width - tw) // 2, ry + (row_height - font_size) // 2),
                      val_str, fill="black", font=font)

    img.save(output_path)


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    n_rows_list: list[int] | None = None,
    n_cols_list: list[int] | None = None,
    header_styles: list[str] | None = None,
    image_width: int = 800,
) -> list[TaskInstance]:
    """Generate table images with multiple questions per table."""
    if n_rows_list is None:
        n_rows_list = [3, 5, 7, 10]
    if n_cols_list is None:
        n_cols_list = [2, 3, 5]
    if header_styles is None:
        header_styles = ["plain", "shaded"]

    out = ensure_dir(os.path.join(output_dir, "tables"))
    instances = []

    for n_rows in n_rows_list:
        for n_cols in n_cols_list:
            for hstyle in header_styles:
                for i in range(n_per_config):
                    # Pick entity type and headers
                    entity_type = random.choice(list(ROW_POOLS.keys()))
                    row_headers = random.sample(ROW_POOLS[entity_type],
                                                min(n_rows, len(ROW_POOLS[entity_type])))
                    # Pad if needed
                    while len(row_headers) < n_rows:
                        row_headers.append(f"Item {len(row_headers) + 1}")

                    col_headers = random.sample(COL_METRICS, min(n_cols, len(COL_METRICS)))
                    data = [[random.randint(10, 999) for _ in range(n_cols)]
                            for _ in range(n_rows)]

                    fname = f"table_{n_rows}x{n_cols}_{hstyle}_{i}.png"
                    fpath = os.path.join(out, fname)
                    _draw_table(row_headers, col_headers, data, hstyle, image_width, fpath)

                    # Q1: cell lookup (random cell)
                    q_row = random.randint(0, n_rows - 1)
                    q_col = random.randint(0, n_cols - 1)
                    instances.extend(make_instances(
                        fpath, "table_cell_lookup", data[q_row][q_col],
                        subtask=f"{n_rows}x{n_cols}_{hstyle}",
                        metadata={"n_rows": n_rows, "n_cols": n_cols,
                                  "header_style": hstyle, "entity_type": entity_type,
                                  "row_headers": row_headers, "col_headers": col_headers,
                                  "query_row": row_headers[q_row],
                                  "query_col": col_headers[q_col]},
                        row_header=row_headers[q_row],
                        col_header=col_headers[q_col],
                    ))

                    # Q2: row count
                    instances.extend(make_instances(
                        fpath, "table_row_count", n_rows,
                        subtask=f"{n_rows}x{n_cols}",
                        metadata={"n_rows": n_rows, "n_cols": n_cols},
                    ))

                    # Q3: which entity has highest value in a random column
                    q_metric_idx = random.randint(0, n_cols - 1)
                    col_vals = [data[r][q_metric_idx] for r in range(n_rows)]
                    max_row = row_headers[col_vals.index(max(col_vals))]
                    instances.extend(make_instances(
                        fpath, "table_max", max_row,
                        subtask=f"{n_rows}x{n_cols}_{hstyle}",
                        metadata={"n_rows": n_rows, "n_cols": n_cols,
                                  "header_style": hstyle,
                                  "query_metric": col_headers[q_metric_idx],
                                  "max_entity": max_row},
                        entity_type=entity_type.rstrip("s"),
                        metric=col_headers[q_metric_idx],
                    ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, n_rows_list=[4], n_cols_list=[3],
                     header_styles=["shaded"])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {inst.task_type:25s} -> {inst.ground_truth}")
