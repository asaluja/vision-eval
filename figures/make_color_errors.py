"""Generate composite error figure for color discrimination primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/color_discrimination/color_grid_4_blues_extreme_1.png",
        "gt": "A2 (odd cell)",
        "model": "C1",
        "caption": "Blues at \u0394L\u22485: shade invisible",
    },
    {
        "image": "generate/images/color_discrimination/color_grid_4_greens_near_threshold_4.png",
        "gt": "A4 (odd cell)",
        "model": "B4",
        "caption": "Greens hardest family (10% at \u0394L\u22487)",
    },
    {
        "image": "generate/images/color_discrimination/color_bar_5_hard_blues_3.png",
        "gt": "43 (medium blue bar)",
        "model": "56",
        "caption": "5 same-family bars: color confusion + misread",
    },
]

make_error_composite(cases, "figures/color_discrimination_errors.png")
