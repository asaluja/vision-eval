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


def score_instance(task_type: str, ground_truth: Any, response: str) -> dict:
    """Score a single response. Returns dict with extracted answer, correctness, etc."""
    result = {"ground_truth": ground_truth, "response": response, "extracted": None, "correct": False}

    if task_type in ("counting_circles", "counting_pentagons", "line_intersection",
                     "nested_squares", "path_following", "patterned_grid",
                     "board_game_rows", "board_game_cols"):
        extracted = extract_number(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted == int(ground_truth))

    elif task_type == "touching_circles":
        extracted = extract_yes_no(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted == str(ground_truth))

    elif task_type == "circled_letter":
        extracted = extract_letter(response)
        result["extracted"] = extracted
        if extracted is not None:
            result["correct"] = (extracted.upper() == str(ground_truth).upper())

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

    return result
