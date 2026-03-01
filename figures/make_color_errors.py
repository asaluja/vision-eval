"""Generate composite error figure for color discrimination primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/color_discrimination/color_grid_4_blues_extreme_0.png",
        "gt": "A1 (odd cell)",
        "model": "C1",
        "caption": "Blues at \u0394L\u22485: shade invisible",
    },
    {
        "image": "generate/images/color_discrimination/color_bar_4_hard_blues_4.png",
        "gt": "23 (queried bar)",
        "model": "30",
        "caption": "4 same-family blue bars: wrong shade matched",
    },
    {
        "image": "generate/images/heatmap/heatmap_4x4_viridis_0to100_1.png",
        "gt": "8",
        "model": "0",
        "caption": "Heatmap: color-to-value interpolation error",
    },
]

make_error_composite(cases, "figures/color_discrimination_errors.png")
