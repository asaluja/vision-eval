"""Tests for evaluate/score.py extractors and scorer."""

from __future__ import annotations

import pytest

from evaluate.score import (
    extract_letter,
    extract_number,
    extract_row_col,
    extract_text_answer,
    extract_trend,
    extract_yes_no,
    score_instance,
)


# ---------------------------------------------------------------------------
# extract_number
# ---------------------------------------------------------------------------

class TestExtractNumber:
    def test_braces_integer(self):
        assert extract_number("{7}") == 7

    def test_braces_takes_priority_over_other_numbers(self):
        # "3 items, answer is {12}" — should return 12, not 3
        assert extract_number("I see 3 items but the count is {12}") == 12

    def test_braces_zero(self):
        assert extract_number("{0}") == 0

    def test_fallback_first_integer(self):
        assert extract_number("There are 5 circles") == 5

    def test_fallback_multiword(self):
        assert extract_number("I counted about 3 or 4 shapes") == 3

    def test_no_number_returns_none(self):
        assert extract_number("no numbers here") is None

    def test_empty_string(self):
        assert extract_number("") is None

    def test_error_response(self):
        assert extract_number("ERROR: FileNotFoundError") is None

    def test_braces_no_float(self):
        # {7.5} — only \d+ inside braces, so no match; falls back to "7"
        assert extract_number("{7.5}") == 7

    def test_large_number(self):
        assert extract_number("{100}") == 100


# ---------------------------------------------------------------------------
# extract_yes_no
# ---------------------------------------------------------------------------

class TestExtractYesNo:
    def test_yes_start(self):
        assert extract_yes_no("Yes, the circles are touching") == "Yes"

    def test_no_start(self):
        assert extract_yes_no("No, they are separated") == "No"

    def test_yes_uppercase(self):
        assert extract_yes_no("YES!") == "Yes"

    def test_no_uppercase(self):
        assert extract_yes_no("NO") == "No"

    def test_braces_yes(self):
        assert extract_yes_no("{yes}") == "Yes"

    def test_braces_no(self):
        assert extract_yes_no("{no}") == "No"

    def test_yes_in_body(self):
        assert extract_yes_no("Based on the image, yes") == "Yes"

    def test_no_in_body(self):
        assert extract_yes_no("The answer is no") == "No"

    def test_neither_returns_none(self):
        assert extract_yes_no("I cannot determine") is None

    def test_empty_returns_none(self):
        assert extract_yes_no("") is None

    def test_no_not_matched_in_word(self):
        # "know" contains "no" but \bno\b should not match
        assert extract_yes_no("I know the shapes are touching") is None

    def test_yes_precedence_over_no(self):
        # "yes" appears before "no" in a contradictory response
        assert extract_yes_no("Yes, no wait, maybe") == "Yes"


# ---------------------------------------------------------------------------
# extract_letter
# ---------------------------------------------------------------------------

class TestExtractLetter:
    def test_braces(self):
        assert extract_letter("{A}") == "A"

    def test_braces_lowercase_uppercased(self):
        assert extract_letter("{q}") == "Q"

    def test_single_char(self):
        assert extract_letter("B") == "B"

    def test_single_char_lowercase(self):
        assert extract_letter("m") == "M"

    def test_letter_is_pattern(self):
        assert extract_letter("The letter is X") == "X"

    def test_character_is_pattern(self):
        assert extract_letter("The character is Z") == "Z"

    def test_quoted_single_letter(self):
        assert extract_letter('"M"') == "M"

    def test_single_quoted(self):
        assert extract_letter("'K'") == "K"

    def test_multi_char_no_braces_no_pattern_returns_none(self):
        assert extract_letter("ABC") is None

    def test_braces_takes_priority(self):
        assert extract_letter('The letter is X, but {Y} is the answer') == "Y"

    def test_digit_string_returns_none(self):
        assert extract_letter("5") is None


# ---------------------------------------------------------------------------
# extract_row_col
# ---------------------------------------------------------------------------

class TestExtractRowCol:
    def test_braces_format(self):
        assert extract_row_col("{3, 4}") == (3, 4)

    def test_braces_with_spaces(self):
        # Regex requires digits immediately after { — extra padding returns None
        assert extract_row_col("{  5 ,  7  }") is None

    def test_rows_cols_keyword(self):
        assert extract_row_col("rows: 5, columns: 7") == (5, 7)

    def test_rows_equals_cols(self):
        assert extract_row_col("rows=5 cols=7") == (5, 7)

    def test_parentheses_format(self):
        assert extract_row_col("(6, 8)") == (6, 8)

    def test_no_match_returns_none(self):
        assert extract_row_col("no grid info") is None

    def test_empty_returns_none(self):
        assert extract_row_col("") is None


# ---------------------------------------------------------------------------
# extract_text_answer
# ---------------------------------------------------------------------------

class TestExtractTextAnswer:
    def test_braces_simple(self):
        assert extract_text_answer("{January}") == "January"

    def test_braces_with_spaces(self):
        assert extract_text_answer("{Product A}") == "Product A"

    def test_braces_strips_whitespace(self):
        assert extract_text_answer("{  Revenue  }") == "Revenue"

    def test_fallback_short_first_line(self):
        assert extract_text_answer("January") == "January"

    def test_fallback_long_line_returns_none(self):
        long = "A" * 51
        assert extract_text_answer(long) is None

    def test_fallback_multiline_uses_first(self):
        assert extract_text_answer("April\nsome explanation") == "April"

    def test_braces_takes_priority_over_fallback(self):
        assert extract_text_answer("The answer is {March}") == "March"

    def test_empty_returns_none(self):
        assert extract_text_answer("") is None


# ---------------------------------------------------------------------------
# extract_trend
# ---------------------------------------------------------------------------

class TestExtractTrend:
    def test_braces_increasing(self):
        assert extract_trend("{increasing}") == "increasing"

    def test_braces_decreasing(self):
        assert extract_trend("{decreasing}") == "decreasing"

    def test_only_increasing(self):
        assert extract_trend("The trend is increasing over time") == "increasing"

    def test_only_decreasing(self):
        assert extract_trend("Values are decreasing") == "decreasing"

    def test_both_present_defaults_increasing(self):
        # Ambiguous: both full words present; we default to "increasing"
        assert extract_trend("Revenue is increasing but costs are decreasing") == "increasing"

    def test_inflected_forms_not_matched(self):
        # "increased"/"decreased" are NOT substrings of "increasing"/"decreasing"
        assert extract_trend("The trend increased then decreased") is None

    def test_braces_overrides_body(self):
        assert extract_trend("it seems increasing but {decreasing}") == "decreasing"

    def test_uppercase_handled(self):
        assert extract_trend("INCREASING trend") == "increasing"

    def test_none_when_absent(self):
        assert extract_trend("no trend information") is None

    def test_empty_returns_none(self):
        assert extract_trend("") is None


# ---------------------------------------------------------------------------
# score_instance
# ---------------------------------------------------------------------------

class TestScoreInstance:

    # --- numeric exact match ---

    def test_numeric_correct(self):
        r = score_instance("counting_circles", 5, "{5}")
        assert r["correct"] is True
        assert r["extracted"] == 5

    def test_numeric_wrong(self):
        r = score_instance("counting_circles", 5, "{7}")
        assert r["correct"] is False

    def test_numeric_error_response(self):
        r = score_instance("counting_circles", 5, "ERROR: something went wrong")
        assert r["correct"] is False
        assert r["extracted"] is None

    def test_numeric_none_extracted_not_correct(self):
        r = score_instance("nested_squares", 3, "I cannot determine the count")
        assert r["correct"] is False

    # --- tolerance scoring ---

    def test_tolerance_within(self):
        # gt=100, tolerance=max(2, 5)=5, extracted=104 → within
        r = score_instance("chart_bar_value", 100, "{104}")
        assert r["correct"] is True
        assert r["error"] == 4

    def test_tolerance_outside(self):
        r = score_instance("chart_bar_value", 100, "{106}")
        assert r["correct"] is False
        assert r["error"] == 6

    def test_tolerance_small_gt_uses_min_2(self):
        # gt=10, tolerance=max(2, 0.5)=2, error=2 → correct (<=)
        r = score_instance("chart_bar_value", 10, "{12}")
        assert r["correct"] is True

    def test_tolerance_small_gt_just_outside(self):
        r = score_instance("chart_bar_value", 10, "{13}")
        assert r["correct"] is False

    # --- yes/no ---

    def test_yes_no_correct(self):
        r = score_instance("touching_circles", "Yes", "Yes, they are touching")
        assert r["correct"] is True

    def test_yes_no_case_insensitive(self):
        r = score_instance("touching_circles", "yes", "{Yes}")
        assert r["correct"] is True

    def test_yes_no_wrong(self):
        r = score_instance("touching_circles", "No", "Yes")
        assert r["correct"] is False

    # --- letter ---

    def test_letter_correct(self):
        r = score_instance("circled_letter", "K", "{K}")
        assert r["correct"] is True

    def test_letter_case_insensitive(self):
        r = score_instance("circled_letter", "k", "{K}")
        assert r["correct"] is True

    def test_letter_wrong(self):
        r = score_instance("circled_letter", "A", "{B}")
        assert r["correct"] is False

    # --- trend ---

    def test_trend_correct(self):
        r = score_instance("chart_line_trend", "increasing", "{increasing}")
        assert r["correct"] is True

    def test_trend_wrong(self):
        r = score_instance("chart_line_trend", "decreasing", "The trend is increasing")
        assert r["correct"] is False

    # --- text answer ---

    def test_text_correct(self):
        r = score_instance("table_max", "Product A", "{Product A}")
        assert r["correct"] is True

    def test_text_case_insensitive(self):
        r = score_instance("table_max", "product a", "{Product A}")
        assert r["correct"] is True

    def test_text_wrong(self):
        r = score_instance("table_max", "Product A", "{Product B}")
        assert r["correct"] is False

    # --- grid counting ---

    def test_grid_string_gt(self):
        r = score_instance("grid_counting", "5, 3", "{5, 3}")
        assert r["correct"] is True

    def test_grid_list_gt(self):
        r = score_instance("grid_counting", [5, 3], "{5, 3}")
        assert r["correct"] is True

    def test_grid_wrong(self):
        r = score_instance("grid_counting", "5, 3", "{4, 3}")
        assert r["correct"] is False

    # --- metadata: text_reliant flag ---

    def test_text_reliant_true(self):
        r = score_instance(
            "conflict_value_label", 52, "{36}",
            metadata={"text_answer": "36"},
        )
        assert r["text_reliant"] is True

    def test_text_reliant_false(self):
        r = score_instance(
            "conflict_value_label", 52, "{52}",
            metadata={"text_answer": "36"},
        )
        assert r["text_reliant"] is False

    def test_text_reliant_not_set_when_no_metadata(self):
        r = score_instance("conflict_value_label", 52, "{36}")
        assert "text_reliant" not in r

    # --- metadata: bias_aligned flag ---

    def test_bias_aligned_true(self):
        # wrong answer that matches the expected bias
        r = score_instance(
            "board_game_rows", 7, "{8}",
            metadata={"expected_bias": "8"},
        )
        assert r["bias_aligned"] is True

    def test_bias_aligned_false(self):
        # wrong answer that does NOT match the expected bias
        r = score_instance(
            "board_game_rows", 7, "{9}",
            metadata={"expected_bias": "8"},
        )
        assert r["bias_aligned"] is False

    def test_bias_aligned_not_set_when_correct(self):
        # bias_aligned only set on wrong answers
        r = score_instance(
            "board_game_rows", 8, "{8}",
            metadata={"expected_bias": "8"},
        )
        assert "bias_aligned" not in r

    # --- fallback task_type ---

    def test_unknown_task_type_bracketed(self):
        r = score_instance("some_new_task", "foo", "{foo}")
        assert r["correct"] is True

    def test_unknown_task_type_unbracketed(self):
        r = score_instance("some_new_task", "foo", "foo")
        assert r["correct"] is True
