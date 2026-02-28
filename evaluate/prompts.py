"""Standardized prompt templates for each task type."""

SYSTEM_PROMPT = (
    "You are a precise visual analyst. Examine the image carefully and answer "
    "the question. Put your final answer in curly braces like {answer}."
)

# Each task type maps to a prompt template string.
# Templates may contain {placeholders} for task-specific values.
PROMPTS = {
    # --- VLMs Are Blind tasks ---
    "counting_circles": (
        "How many circles are in the image? "
        "Answer with only the number in curly braces, e.g. {{5}}."
    ),
    "counting_pentagons": (
        "How many pentagons are in the image? "
        "Answer with only the number in curly braces, e.g. {{5}}."
    ),
    "line_intersection": (
        "How many times do the blue and red lines intersect? "
        "Answer with a number in curly braces, e.g. {{2}}."
    ),
    "nested_squares": (
        "How many squares are in the image? "
        "Answer with only the number in curly braces, e.g. {{3}}."
    ),
    "touching_circles": (
        "Are the two circles touching or overlapping each other? "
        "Answer {{Yes}} or {{No}}."
    ),
    "circled_letter": (
        "Which letter is circled in red? "
        "Answer with just the letter in curly braces, e.g. {{A}}."
    ),
    "grid_counting": (
        "How many rows and columns does this grid have? "
        "Answer in the format {{rows, columns}}, e.g. {{5, 6}}."
    ),
    "path_following": (
        "How many distinct colored paths connect station {start} to station {end}? "
        "Answer with a number in curly braces, e.g. {{3}}."
    ),
    # --- VLMs Are Biased tasks ---
    "patterned_grid": (
        "How many {shape_name} are in cell {cell_id}? "
        "Answer with a number in curly braces, e.g. {{3}}."
    ),
    "board_game_rows": (
        "How many rows does this {game_type} board have? "
        "Answer with a number in curly braces, e.g. {{8}}."
    ),
    "board_game_cols": (
        "How many columns does this {game_type} board have? "
        "Answer with a number in curly braces, e.g. {{8}}."
    ),
}


def get_prompt(task_type: str, **kwargs) -> str:
    """Return a formatted prompt for the given task type."""
    template = PROMPTS[task_type]
    return template.format(**kwargs) if kwargs else template
