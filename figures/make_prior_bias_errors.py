"""Generate composite error figure for prior bias override primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/board_games/chess_7x8_s512_0.png",
        "gt": "7 rows",
        "model": "8 (canonical)",
        "caption": "100% bias alignment: always outputs 8\u00d78",
    },
    {
        "image": "generate/images/patterned_grid/pgrid_dice_add_g6_s768_0.png",
        "gt": "1 (cell has extra dot)",
        "model": "4",
        "caption": "Add-anomaly: 0% \u2014 extra dot is invisible",
    },
    {
        "image": "data/images/biased/Ebbinghaus_001_Q1_notitle_px384.png",
        "gt": "Same size (Yes)",
        "model": "No",
        "caption": "Ebbinghaus illusion: 50% = pure chance",
    },
]

make_error_composite(cases, "figures/prior_bias_override_errors.png")
