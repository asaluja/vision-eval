"""Generate composite error figure for prior bias override primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "data/images/biased/car_001_notitle_Q1_px768.png",
        "gt": "4 (points + ring)",
        "model": "3 (canonical star)",
        "caption": "Car logos: 0% — retrieves canonical, never counts",
    },
    {
        "image": "data/images/biased/flag_stars_001_notitle_Q1_px768.png",
        "gt": "13",
        "model": "12 (canonical EU)",
        "caption": "Flags: 40% — 83% of errors are exact biased answer",
    },
    {
        "image": "generate/images/text_visual_conflict/value_label_n6_1.png",
        "gt": "89 (bar height)",
        "model": "56 (reads wrong label)",
        "caption": "Value labels: 0% — always trusts text over visual",
    },
]

make_error_composite(cases, "figures/prior_bias_override_errors.png", figsize=(10, 3.8))
