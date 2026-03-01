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
        "image": "generate/images/patterned_grid/pgrid_dice_add_g6_s768_0.png",
        "gt": "1 (cell has extra dot)",
        "model": "4 (canonical count)",
        "caption": "Patterned grid add-anomaly: 0% — extra shape invisible",
    },
]

make_error_composite(cases, "figures/prior_bias_override_errors.png")
