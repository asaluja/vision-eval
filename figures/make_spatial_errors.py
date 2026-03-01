"""Generate composite error figure for spatial localization primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/charts/line_3x10_g0_v1_0.png",
        "gt": "83 (correct series)",
        "model": "56 (wrong series)",
        "caption": "10-series line chart: reads wrong line at correct x",
    },
    {
        "image": "generate/images/diagrams/flow_multi_decision_n3_4.png",
        "gt": "Next after Run Tests: Complete?",
        "model": "Notify Team",
        "caption": "Arrow tracing fails in multi-decision DAG",
    },
    {
        "image": "data/images/blind/circled_letter_205.png",
        "gt": "t (circled, pos 0)",
        "model": "H",
        "caption": "Lowercase invisible next to uppercase",
    },
]

make_error_composite(cases, "figures/spatial_localization_errors.png")
