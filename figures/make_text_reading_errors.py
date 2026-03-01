"""Generate composite error figure for text reading primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/text_reading/text_word_f8_r30_clow_2.png",
        "gt": "Marketing",
        "model": "Morocco",
        "caption": "Lexical hallucination at 8px/30\u00b0",
    },
    {
        "image": "generate/images/text_reading/text_num_f10_r45_2.png",
        "gt": "518",
        "model": "528",
        "caption": "Single digit substitution at 10px/45\u00b0",
    },
    {
        "image": "generate/images/text_reading/text_num_f8_r45_0.png",
        "gt": "2048",
        "model": "2024",
        "caption": "Year prior substitution at 8px/45\u00b0",
    },
]

make_error_composite(cases, "figures/text_reading_errors.png")
