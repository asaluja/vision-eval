"""Generate composite error figure for line/path following primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/path_following/paths_6_s512_lw4.0_0.png",
        "gt": "6 paths A\u2192B",
        "model": "5",
        "caption": "Loses track of overlapping colored paths",
    },
    {
        "image": "generate/images/line_intersection/lines_p5_int0_s512_lw3.0_0.png",
        "gt": "0 intersections",
        "model": "2",
        "caption": "Hallucinates crossings from visual proximity",
    },
    {
        "image": "generate/images/charts/line_3x10_g1_v0_0.png",
        "gt": "Online: increasing",
        "model": "decreasing",
        "caption": "Can't isolate named series in 10-line chart",
    },
]

make_error_composite(cases, "figures/line_path_following_errors.png")
