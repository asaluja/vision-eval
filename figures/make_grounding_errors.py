"""Generate composite error figure for text-visual consistency (grounding) primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/text_visual_conflict/value_label_n6_1.png",
        "gt": "Product D = 89 (bar height)",
        "model": "56 (reads wrong label)",
        "caption": "0% accuracy: always trusts text over visual",
    },
    {
        "image": "generate/images/text_visual_conflict/annotation_n3_1.png",
        "gt": "Product C (highest bar)",
        "model": "Product B",
        "caption": "\"Highest\" arrow fools model at small gap",
    },
    {
        "image": "generate/images/text_visual_conflict/title_trend_n3_0.png",
        "gt": "Decreasing",
        "model": "Decreasing \u2713",
        "caption": "100%: ignores \"Rising Sales\" title correctly",
    },
]

make_error_composite(cases, "figures/text_visual_consistency_errors.png", fontsize=7)
