"""Standardized prompt templates for each task type.

Following VLMs Are Blind methodology, each task has two semantically equivalent
prompt variants (A and B) to test robustness to prompt phrasing.
"""

SYSTEM_PROMPT = (
    "You are a precise visual analyst. Examine the image carefully and answer "
    "the question. Put your final answer in curly braces like {answer}."
)

# Each task type maps to a list of semantically equivalent prompt templates.
# Variant A = index 0, Variant B = index 1.
PROMPTS = {
    # --- VLMs Are Blind tasks ---
    "counting_circles": [
        "How many circles are in the image? "
        "Answer with only the number in curly braces, e.g. {{5}}.",

        "Count the total number of circles shown. "
        "Put your answer as a number in curly braces, e.g. {{5}}.",
    ],
    "counting_pentagons": [
        "How many pentagons are in the image? "
        "Answer with only the number in curly braces, e.g. {{5}}.",

        "Count the total number of pentagons shown. "
        "Put your answer as a number in curly braces, e.g. {{5}}.",
    ],
    "line_intersection": [
        "How many times do the blue and red lines intersect? "
        "Answer with a number in curly braces, e.g. {{2}}.",

        "Count the intersection points where the blue and red lines cross. "
        "Put your answer in curly braces, e.g. {{2}}.",
    ],
    "nested_squares": [
        "How many squares are in the image? "
        "Answer with only the number in curly braces, e.g. {{3}}.",

        "Count the total number of squares, including nested ones. "
        "Put your answer in curly braces, e.g. {{3}}.",
    ],
    "touching_circles": [
        "Are the two circles touching or overlapping each other? "
        "Answer {{Yes}} or {{No}}.",

        "Do the two circles make contact with each other? "
        "Answer {{Yes}} or {{No}}.",
    ],
    "circled_letter": [
        "Which letter is circled in red? "
        "Answer with just the letter in curly braces, e.g. {{A}}.",

        "Identify the character that has a red circle around it. "
        "Answer with the letter in curly braces, e.g. {{A}}.",
    ],
    "grid_counting": [
        "How many rows and columns does this grid have? "
        "Answer in the format {{rows, columns}}, e.g. {{5, 6}}.",

        "Count the rows and columns in this grid. "
        "Respond in the format {{rows, columns}}, e.g. {{5, 6}}.",
    ],
    "path_following": [
        "How many distinct colored paths connect station {start} to station {end}? "
        "Answer with a number in curly braces, e.g. {{3}}.",

        "Count the number of separate colored routes from station {start} to station {end}. "
        "Put your answer in curly braces, e.g. {{3}}.",
    ],
    # --- VLMs Are Biased tasks ---
    "patterned_grid": [
        "How many {shape_name} are in cell {cell_id}? "
        "Answer with a number in curly braces, e.g. {{3}}.",

        "Count the {shape_name} inside cell {cell_id}. "
        "Put your answer in curly braces, e.g. {{3}}.",
    ],
    "board_game_rows": [
        "How many rows does this {game_type} board have? "
        "Answer with a number in curly braces, e.g. {{8}}.",

        "Count the number of rows on this {game_type} board. "
        "Put your answer in curly braces, e.g. {{8}}.",
    ],
    "board_game_cols": [
        "How many columns does this {game_type} board have? "
        "Answer with a number in curly braces, e.g. {{8}}.",

        "Count the number of columns on this {game_type} board. "
        "Put your answer in curly braces, e.g. {{8}}.",
    ],
    # --- Business-critical: Charts ---
    "chart_bar_value": [
        "What is the value for {category}? "
        "Answer with a number in curly braces, e.g. {{42}}.",

        "Read the value of the bar labeled {category}. "
        "Put your answer in curly braces, e.g. {{42}}.",
    ],
    "chart_bar_compare": [
        "Which category has the highest value? "
        "Answer with the category name in curly braces, e.g. {{January}}.",

        "Which bar is the tallest? "
        "Answer with its label in curly braces, e.g. {{January}}.",
    ],
    "chart_bar_count": [
        "How many bars are shown in this chart? "
        "Answer with a number in curly braces, e.g. {{5}}.",

        "Count the total number of bars in this chart. "
        "Put your answer in curly braces, e.g. {{5}}.",
    ],
    "chart_series_count": [
        "How many different colored bar groups are shown in each category? "
        "Answer with a number in curly braces, e.g. {{3}}.",

        "How many data series are represented in this grouped bar chart? "
        "Answer with a number in curly braces, e.g. {{3}}.",
    ],
    "chart_bar_count_total": [
        "How many individual bars are shown in total in this chart? "
        "Answer with a number in curly braces, e.g. {{12}}.",

        "Count every single bar in this chart. "
        "Put the total in curly braces, e.g. {{12}}.",
    ],
    "chart_grouped_value": [
        "What is the value of {series} for {category}? "
        "Answer with a number in curly braces, e.g. {{42}}.",

        "Read the {series} bar for {category}. "
        "Put the value in curly braces, e.g. {{42}}.",
    ],
    "chart_line_value": [
        "What is the value of {series} at {x_label}? "
        "Answer with a number in curly braces, e.g. {{42}}.",

        "Read the {series} data point at {x_label}. "
        "Put the value in curly braces, e.g. {{42}}.",
    ],
    "chart_line_trend": [
        "Is the overall trend increasing or decreasing? "
        "Answer with {{increasing}} or {{decreasing}}.",

        "Does the line go up or down overall? "
        "Answer with {{increasing}} or {{decreasing}}.",
    ],
    "chart_line_count": [
        "How many lines are shown in this chart? "
        "Answer with a number in curly braces, e.g. {{3}}.",

        "Count the distinct lines plotted in this chart. "
        "Put your answer in curly braces, e.g. {{3}}.",
    ],
    # --- Business-critical: Tables ---
    "table_cell_lookup": [
        "What is the value in the {row_header} row and {col_header} column? "
        "Answer in curly braces, e.g. {{42}}.",

        "What is {row_header}'s {col_header}? "
        "Answer in curly braces, e.g. {{42}}.",
    ],
    "table_row_count": [
        "How many data rows does this table have (excluding the header row)? "
        "Answer with a number in curly braces, e.g. {{5}}.",

        "Count the rows of data in this table, not including the header. "
        "Put your answer in curly braces, e.g. {{5}}.",
    ],
    "table_max": [
        "Which {entity_type} has the highest {metric}? "
        "Answer with the name in curly braces, e.g. {{USA}}.",

        "Looking at the {metric} column, which {entity_type} has the largest value? "
        "Answer with its name in curly braces, e.g. {{USA}}.",
    ],
    # --- Business-critical: Diagrams ---
    "diagram_node_count": [
        "How many steps or boxes are in this flowchart (excluding Start and End)? "
        "Answer with a number in curly braces, e.g. {{4}}.",

        "Count the process and decision nodes in this flowchart, not counting Start or End. "
        "Put your answer in curly braces, e.g. {{4}}.",
    ],
    "diagram_next_step": [
        "What step comes directly after \"{node_label}\"? "
        "Answer with the step name in curly braces, e.g. {{Review Data}}.",

        "In this flowchart, what is the next step after \"{node_label}\"? "
        "Put the step name in curly braces, e.g. {{Review Data}}.",
    ],
    "diagram_decision": [
        "In this flowchart, if \"{condition}\" is {answer}, what is the next step? "
        "Answer with the step name in curly braces, e.g. {{Send Email}}.",

        "Following the \"{condition}\" decision, if the answer is {answer}, "
        "which step comes next? Put the step name in curly braces, e.g. {{Send Email}}.",
    ],
}


def get_prompt(task_type: str, variant: int = 0, **kwargs) -> str:
    """Return a formatted prompt for the given task type.

    Args:
        task_type: Key into PROMPTS dict.
        variant: 0 for prompt A, 1 for prompt B.
        **kwargs: Format variables (e.g., category, series, start, end).
    """
    templates = PROMPTS[task_type]
    template = templates[variant % len(templates)]
    return template.format(**kwargs) if kwargs else template
