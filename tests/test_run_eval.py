"""Tests for evaluate/run_eval.py — validate_instances and _load_completed."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from evaluate.run_eval import validate_instances, _load_completed
from generate.base import TaskInstance


def _inst(image_path, prompt="p", task_type="counting_circles", ground_truth=1):
    return TaskInstance(
        image_path=image_path,
        prompt=prompt,
        ground_truth=ground_truth,
        task_type=task_type,
        subtask="",
        metadata={},
    )


# ---------------------------------------------------------------------------
# validate_instances — image existence
# ---------------------------------------------------------------------------

class TestValidateInstancesImages:
    def test_existing_image_not_flagged(self, tmp_path):
        img = tmp_path / "img.png"
        img.write_bytes(b"x")
        issues = validate_instances([_inst(str(img))])
        assert issues["missing_images"] == []

    def test_missing_image_flagged(self, tmp_path):
        inst = _inst(str(tmp_path / "nonexistent.png"))
        issues = validate_instances([inst])
        assert issues["missing_images"] == [inst]

    def test_mixed_returns_only_missing(self, tmp_path):
        good = tmp_path / "good.png"
        good.write_bytes(b"x")
        bad_inst = _inst(str(tmp_path / "bad.png"))
        good_inst = _inst(str(good))
        issues = validate_instances([good_inst, bad_inst])
        assert issues["missing_images"] == [bad_inst]


# ---------------------------------------------------------------------------
# validate_instances — stale prompt check
# ---------------------------------------------------------------------------

FAKE_PROMPTS = {"counting_circles": ["current prompt A", "current prompt B"]}


class TestValidateInstancesPrompts:
    def test_current_prompt_not_flagged(self, tmp_path):
        img = tmp_path / "img.png"
        img.write_bytes(b"x")
        inst = _inst(str(img), prompt="current prompt A")
        with patch("evaluate.run_eval.PROMPTS", FAKE_PROMPTS):
            issues = validate_instances([inst])
        assert issues["stale_prompts"] == []

    def test_stale_prompt_flagged(self, tmp_path):
        img = tmp_path / "img.png"
        img.write_bytes(b"x")
        inst = _inst(str(img), prompt="old prompt that changed")
        with patch("evaluate.run_eval.PROMPTS", FAKE_PROMPTS):
            issues = validate_instances([inst])
        assert issues["stale_prompts"] == [inst]

    def test_task_type_not_in_prompts_skipped(self, tmp_path):
        # HF-style task or any task_type not managed by PROMPTS
        img = tmp_path / "img.png"
        img.write_bytes(b"x")
        inst = _inst(str(img), task_type="hf_only_task", prompt="any prompt")
        with patch("evaluate.run_eval.PROMPTS", FAKE_PROMPTS):
            issues = validate_instances([inst])
        assert issues["stale_prompts"] == []

    def test_both_variants_accepted(self, tmp_path):
        img = tmp_path / "img.png"
        img.write_bytes(b"x")
        inst_a = _inst(str(img), prompt="current prompt A")
        inst_b = _inst(str(img), prompt="current prompt B")
        with patch("evaluate.run_eval.PROMPTS", FAKE_PROMPTS):
            issues = validate_instances([inst_a, inst_b])
        assert issues["stale_prompts"] == []

    def test_missing_image_and_stale_prompt_both_reported(self, tmp_path):
        inst = _inst(str(tmp_path / "missing.png"), prompt="old prompt")
        with patch("evaluate.run_eval.PROMPTS", FAKE_PROMPTS):
            issues = validate_instances([inst])
        assert len(issues["missing_images"]) == 1
        assert len(issues["stale_prompts"]) == 1

    def test_empty_instances(self):
        with patch("evaluate.run_eval.PROMPTS", FAKE_PROMPTS):
            issues = validate_instances([])
        assert issues["missing_images"] == []
        assert issues["stale_prompts"] == []


# ---------------------------------------------------------------------------
# _load_completed
# ---------------------------------------------------------------------------

class TestLoadCompleted:
    def test_empty_file_returns_empty_set(self, tmp_path):
        f = tmp_path / "results.jsonl"
        f.write_text("")
        assert _load_completed(str(f)) == set()

    def test_nonexistent_file_returns_empty_set(self, tmp_path):
        assert _load_completed(str(tmp_path / "missing.jsonl")) == set()

    def test_loads_completed_keys(self, tmp_path):
        f = tmp_path / "results.jsonl"
        f.write_text(json.dumps({"image_path": "a.png", "prompt": "p1", "correct": True}) + "\n")
        done = _load_completed(str(f))
        assert "a.png|p1" in done

    def test_multiple_entries(self, tmp_path):
        f = tmp_path / "results.jsonl"
        lines = [
            json.dumps({"image_path": "a.png", "prompt": "p1"}),
            json.dumps({"image_path": "b.png", "prompt": "p2"}),
        ]
        f.write_text("\n".join(lines) + "\n")
        done = _load_completed(str(f))
        assert "a.png|p1" in done
        assert "b.png|p2" in done

    def test_skips_malformed_lines(self, tmp_path):
        f = tmp_path / "results.jsonl"
        f.write_text("not json\n" + json.dumps({"image_path": "a.png", "prompt": "p"}) + "\n")
        done = _load_completed(str(f))
        assert "a.png|p" in done
        assert len(done) == 1

    def test_skips_lines_missing_keys(self, tmp_path):
        f = tmp_path / "results.jsonl"
        f.write_text(json.dumps({"image_path": "a.png"}) + "\n")  # no prompt key
        done = _load_completed(str(f))
        assert len(done) == 0
