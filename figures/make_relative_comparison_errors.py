"""Generate composite error figure for relative comparison primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/relative_comparison/comp_bar_4_d1_g1_2.png",
        "gt": "D taller (diff=1)",
        "model": "B",
        "caption": "1-unit bar diff is below resolution",
    },
    {
        "image": "generate/images/touching_circles/touch_d0.1_r0.1_ahorizontal_s512_0.png",
        "gt": "Not touching (10px gap)",
        "model": "Yes, touching",
        "caption": "r=0.10: always-touching bias up to 10px",
    },
    {
        "image": "generate/images/touching_circles/touch_d0.05_r0.2_ahorizontal_s512_0.png",
        "gt": "Not touching (5px gap)",
        "model": "Yes, touching",
        "caption": "r=0.20: gap below 12px threshold",
    },
]

make_error_composite(cases, "figures/relative_comparison_errors.png")
