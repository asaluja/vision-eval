"""Generate composite error figure for text reading primitive."""
from figures.error_composite import make_error_composite

cases = [
    {
        "image": "generate/images/text_reading/text_word_f10_r90_chigh_1.png",
        "gt": "Forecast",
        "model": "Forrest",
        "caption": "Lexical prior fills in degraded 10px/90\u00b0 text",
    },
    {
        "image": "generate/images/text_reading/text_num_f10_r90_2.png",
        "gt": "256",
        "model": "325",
        "caption": "No lexical rescue for numbers: 0% at 10px/90\u00b0",
    },
    {
        "image": "generate/images/text_reading/text_num_f20_r45_1.png",
        "gt": "518",
        "model": "5128",
        "caption": "Phantom digit insertion at 20px/45\u00b0",
    },
]

make_error_composite(cases, "figures/text_reading_errors.png")
