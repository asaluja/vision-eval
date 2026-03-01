"""Answer extraction and scoring for evaluation results."""

from __future__ import annotations

import re
from typing import Any


def extract_number(response: str) -> int | None:
    """Extract a number — first try curly braces, then first integer in text."""
    # Try {N} format
    m = re.search(r"\{(\d+)\}", response)
    if m:
        return int(m.group(1))
    # Fallback: first standalone integer
    m = re.search(r"\b(\d+)\b", response)
    if m:
        return int(m.group(1))
    return None


def extract_yes_no(response: str) -> str | None:
    """Extract Yes or No from response."""
    text = response.strip().lower()
    if text.startswith("yes") or text.startswith("{yes"):
        return "Yes"
    if text.startswith("no") or text.startswith("{no"):
        return "No"
    if re.search(r"\byes\b", text):
        return "Yes"
    if re.search(r"\bno\b", text):
        return "No"
    return None


def extract_letter(response: str) -> str | None:
    """Extract a single letter answer."""
    text = response.strip()
    # {X} format
    m = re.search(r"\{([A-Za-z])\}", text)
    if m:
        return m.group(1).upper()
    # Just the letter
    if len(text) == 1 and text.isalpha():
        return text.upper()
    # "The letter is X" pattern
    m = re.search(r"(?:letter|character)\s+(?:is\s+)?[\"']?([A-Za-z])[\"']?", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Quoted single letter
    m = re.search(r"[\"']([A-Za-z])[\"']", text)
    if m:
        return m.group(1).upper()
    return None


def extract_row_col(response: str) -> tuple[int, int] | None:
    """Extract (rows, cols) from grid counting response."""
    # Try {R, C} format
    m = re.search(r"\{(\d+)\s*,\s*(\d+)\}", response)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    # Try rows={R} columns={C}
    m = re.search(r"rows?\s*[=:]\s*\{?(\d+)\}?.*?col(?:umn)?s?\s*[=:]\s*\{?(\d+)\}?", response, re.IGNORECASE)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    # Try (R, C)
    m = re.search(r"\((\d+)\s*,\s*(\d+)\)", response)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return None


def extract_text_answer(response: str) -> str | None:
    """Extract a text answer from curly braces, e.g. {January} -> January."""
    m = re.search(r"\{([^{}]+)\}", response)
    if m:
        return m.group(1).strip()
    # Fallback: return first line stripped (often the model just says the answer)
    first_line = response.strip().split("\n")[0].strip()
    if first_line and len(first_line) < 50:
        return first_line
    return None


def extract_trend(response: str) -> str | None:
    """Extract increasing/decreasing from response."""
    text = response.lower()
    # Try braces first
    m = re.search(r"\{(increasing|decreasing)\}", text)
    if m:
        return m.group(1)
    if "increasing" in text and "decreasing" not in text:
        return "increasing"
    if "decreasing" in text and "increasing" not in text:
        return "decreasing"
    # Both present — take the one in braces or first occurrence
    if "increasing" in text:
        return "increasing"
    if "decreasing" in text:
        return "decreasing"
    return None


def score_instance(task_type: str, ground_truth: Any, response: str, metadata: dict | None = None) -> dict:
    """Score a single response. Returns dict with extracted answer, correctness, etc.

    If metadata contains 'expected_bias', also checks whether the model's error
    is bias-aligned (gave the memorized canonical answer instead of the correct one).
    """
    result = {"ground_truth": ground_truth, "response": response, "extracted": None, "correct": False}

    # Numeric tasks
    if task_type in ("counting_circles", "counting_pentagons", "line_intersection",
                     "nested_squares", "path_following", "patterned_grid",
                     "board_game_rows", "board_game_cols", "board_game",
                     "chart_bar_value", "chart_bar_count", "chart_grouped_value",
                     "chart_line_value", "chart_line_count",
                     "table_cell_lookup", "table_row_count",
                     "diagram_node_count",
                     "text_number_reading"):
        extracted = extract_number(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted == int(ground_truth))

    # Yes/No tasks
    elif task_type in ("touching_circles", "optical_illusion"):
        extracted = extract_yes_no(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted.lower() == str(ground_truth).lower())

    # Letter tasks
    elif task_type == "circled_letter":
        extracted = extract_letter(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted.upper() == str(ground_truth).upper())

    # Grid tasks
    elif task_type == "grid_counting":
        extracted = extract_row_col(response)
        result["extracted"] = extracted
        if extracted is not None:
            gt = ground_truth
            if isinstance(gt, str):
                parts = gt.split(",")
                gt = (int(parts[0].strip()), int(parts[1].strip()))
            elif isinstance(gt, list):
                gt = tuple(gt)
            result["correct"] = (extracted == gt)

    # Trend tasks (increasing/decreasing)
    elif task_type == "chart_line_trend":
        extracted = extract_trend(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted.lower() == str(ground_truth).lower())

    # Text-answer tasks (category names, step names, etc.)
    elif task_type in ("chart_bar_compare", "table_max",
                       "diagram_next_step", "diagram_decision",
                       "text_word_reading", "color_grid_odd"):
        extracted = extract_text_answer(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted.lower().strip() == str(ground_truth).lower().strip())

    # Fallback: generic string match
    else:
        extracted = _extract_bracketed_or_full(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted.lower().strip() == str(ground_truth).lower().strip())

    # Bias alignment check (for DPO data)
    if metadata and "expected_bias" in metadata and not result["correct"]:
        expected_bias = str(metadata["expected_bias"]).lower().strip()
        extracted_str = str(result["extracted"]).lower().strip() if result["extracted"] is not None else ""
        result["bias_aligned"] = (extracted_str == expected_bias)

    return result


def _extract_bracketed_or_full(response: str) -> str | None:
    """Extract {bracketed} answer or return stripped response."""
    m = re.search(r"\{([^}]+)\}", response)
    if m:
        return m.group(1).strip()
    return response.strip() if response.strip() else None
