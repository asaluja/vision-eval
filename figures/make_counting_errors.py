"""Generate composite error figure for counting/enumeration primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/counting_circles/circle_10_ov0.3_cmono_s512_lw2.0_0.png",
        "gt": "10 circles",
        "model": "15",
        "caption": "Large shapes + overlap \u2192 overcounting",
    },
    {
        "image": "data/images/blind/counting_circles_20.png",
        "gt": "7 circles",
        "model": "5",
        "caption": "Small shapes on large canvas \u2192 undercounting",
    },
    {
        "image": "generate/images/counting_pentagons/pentagon_6_ov0.3_cmono_s512_lw2.0_0.png",
        "gt": "6 pentagons",
        "model": "8",
        "caption": "Complex shapes compound overlap errors",
    },
]

make_error_composite(cases, "figures/counting_enumeration_errors.png",
                     figsize=(9, 3.8), fontsize=8, cmap="gray")
