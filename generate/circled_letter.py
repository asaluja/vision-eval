"""Generate circled-letter identification images.

Renders a word and draws a red circle/ellipse around one letter.
Uses PIL for text rendering and ellipse drawing.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as fm

from generate.base import TaskInstance, ensure_dir, make_instances
from evaluate.prompts import get_prompt


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a reliable font. Try DejaVu Sans (ships with matplotlib), fallback to system."""
    try:
        path = fm.findfont("DejaVu Sans")
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:
            return ImageFont.load_default()


def _char_bboxes(word: str, font: ImageFont.FreeTypeFont):
    """Compute bounding boxes for each character in the word.

    Returns list of (x_left, y_top, x_right, y_bottom) for each char.
    """
    bboxes = []
    # Measure character by character using cumulative widths
    x_offset = 0
    for i, ch in enumerate(word):
        left = int(font.getlength(word[:i]))
        right = int(font.getlength(word[:i + 1]))
        # Use font's getbbox for vertical extent
        bbox = font.getbbox(ch)
        y_top = bbox[1]
        y_bottom = bbox[3]
        bboxes.append((left, y_top, right, y_bottom))
    return bboxes


WORDS = [
    "Acknowledgement",
    "Subdermatoglyphic",
    "tHyUiKaRbNqWeOpXcZvM",
    "PERPLEXITY",
    "Foundation",
    "Juxtaposed",
    "Complexity",
    "Wavelength",
]


def generate(
    n_per_config: int = 1,
    output_dir: str = "generate/images",
    words: list[str] | None = None,
    font_sizes: list[int] | None = None,
    canvas_size: int = 512,
    circle_thicknesses: list[int] | None = None,
) -> list[TaskInstance]:
    """Generate images with one letter circled in red."""
    # Deterministic generator — replicates produce identical images, so cap at 1
    n_per_config = 1

    if words is None:
        words = WORDS
    if font_sizes is None:
        font_sizes = [44]  # low-signal: fixed (paper: "font does not vary performance")
    if circle_thicknesses is None:
        circle_thicknesses = [4]  # low-signal: fixed (analogous to line width)

    task_type = "circled_letter"
    out = ensure_dir(os.path.join(output_dir, task_type))
    instances = []

    for word in words:
        for fs in font_sizes:
            for ct in circle_thicknesses:
                # Circle a subset of letters (spread across the word)
                indices = [0, len(word) // 4, len(word) // 2, 3 * len(word) // 4, len(word) - 1]
                indices = sorted(set(min(idx, len(word) - 1) for idx in indices))

                for target_idx in indices:
                    for i in range(n_per_config):
                        fname = f"circled_{word[:8]}_f{fs}_t{ct}_i{target_idx}_{i}.png"
                        fpath = os.path.join(out, fname)

                        font = _get_font(fs)
                        bboxes = _char_bboxes(word, font)

                        # Compute text dimensions
                        text_width = int(font.getlength(word))
                        text_bbox = font.getbbox(word)
                        text_height = text_bbox[3] - text_bbox[1]

                        # Center text on canvas
                        img = Image.new("RGB", (canvas_size, canvas_size), "white")
                        draw = ImageDraw.Draw(img)

                        x_start = (canvas_size - text_width) // 2
                        y_start = (canvas_size - text_height) // 2

                        # Draw the word
                        draw.text((x_start, y_start - text_bbox[1]), word,
                                  fill="black", font=font)

                        # Draw red ellipse around target character
                        cb = bboxes[target_idx]
                        char_w = cb[2] - cb[0]
                        char_h = cb[3] - cb[1]
                        pad_x = max(8, char_w * 0.5)
                        pad_y = max(8, char_h * 0.6)
                        ellipse_box = [
                            x_start + cb[0] - pad_x,
                            y_start + cb[1] - pad_y,
                            x_start + cb[2] + pad_x,
                            y_start + cb[3] + pad_y,
                        ]
                        draw.ellipse(ellipse_box, outline="red", width=ct)

                        img.save(fpath)

                        target_letter = word[target_idx]
                        instances.extend(make_instances(
                            fpath, task_type, target_letter.upper(),
                            subtask=f"word={word[:8]}",
                            metadata={
                                "word": word, "target_index": target_idx,
                                "target_letter": target_letter,
                                "font_size": fs, "circle_thickness": ct,
                            },
                        ))

    return instances


if __name__ == "__main__":
    insts = generate(n_per_config=1, words=["Foundation"], font_sizes=[36],
                     circle_thicknesses=[4])
    print(f"Generated {len(insts)} instances")
    for inst in insts:
        print(f"  {os.path.basename(inst.image_path)} -> '{inst.ground_truth}' "
              f"(letter {inst.metadata['target_index']} of '{inst.metadata['word']}')")
