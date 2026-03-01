"""Main evaluation orchestrator: generate images, query model, score, save results."""

from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

import config
from evaluate.api import query_model
from evaluate.prompts import SYSTEM_PROMPT
from evaluate.score import score_instance
from generate.base import TaskInstance


def _load_completed(results_path: str) -> set[str]:
    """Load already-evaluated image paths for resume support."""
    done = set()
    if os.path.exists(results_path):
        with open(results_path) as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    done.add(r["image_path"] + "|" + r["prompt"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def _make_eval_fn(thinking: bool = False, thinking_budget: int = 4096):
    """Return an eval function with thinking config baked in (for thread pool)."""
    def _eval_one(inst: TaskInstance) -> dict:
        try:
            response = query_model(
                inst.image_path, inst.prompt,
                system=SYSTEM_PROMPT,
                thinking=thinking,
                thinking_budget=thinking_budget,
            )
        except Exception as e:
            response = f"ERROR: {e}"

        scored = score_instance(inst.task_type, inst.ground_truth, response, metadata=inst.metadata)
        return {
            "task_type": inst.task_type,
            "subtask": inst.subtask,
            "image_path": inst.image_path,
            "prompt": inst.prompt,
            "thinking_enabled": thinking,
            **scored,
            "metadata": inst.metadata,
        }
    return _eval_one


def run_evaluation(
    instances: list[TaskInstance],
    results_path: str,
    max_workers: int = 10,
    thinking: bool = False,
    thinking_budget: int = 4096,
) -> list[dict]:
    """Evaluate a list of TaskInstances against Haiku 4.5.

    Args:
        instances: Generated task instances to evaluate.
        results_path: Path to JSONL file for results (append mode, supports resume).
        max_workers: Number of concurrent API calls.
        thinking: Enable extended thinking for step-by-step reasoning.
        thinking_budget: Max tokens for the thinking phase.

    Returns:
        List of result dicts.
    """
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    completed = _load_completed(results_path)

    # Filter to only pending instances
    pending = [inst for inst in instances
               if (inst.image_path + "|" + inst.prompt) not in completed]

    if not pending:
        print(f"  All {len(instances)} instances already evaluated, skipping.")
        with open(results_path) as f:
            return [json.loads(line) for line in f if line.strip()]

    print(f"  {len(pending)} pending ({len(instances) - len(pending)} already done)")

    results = []
    write_lock = threading.Lock()
    eval_fn = _make_eval_fn(thinking=thinking, thinking_budget=thinking_budget)

    with open(results_path, "a") as f:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(eval_fn, inst): inst for inst in pending}

            for future in tqdm(as_completed(futures), total=len(futures), desc="Evaluating"):
                result = future.result()
                with write_lock:
                    f.write(json.dumps(result, default=str) + "\n")
                    f.flush()
                results.append(result)

    return results


def print_summary(results: list[dict]) -> None:
    """Print accuracy breakdown by task_type and subtask."""
    from collections import defaultdict

    by_task = defaultdict(lambda: {"correct": 0, "total": 0})
    by_subtask = defaultdict(lambda: {"correct": 0, "total": 0})

    for r in results:
        task = r["task_type"]
        subtask = r.get("subtask", "")
        by_task[task]["total"] += 1
        by_task[task]["correct"] += int(r["correct"])
        if subtask:
            key = f"{task}/{subtask}"
            by_subtask[key]["total"] += 1
            by_subtask[key]["correct"] += int(r["correct"])

    print("\n=== Results by Task ===")
    for task, counts in sorted(by_task.items()):
        acc = counts["correct"] / counts["total"] if counts["total"] else 0
        print(f"  {task:30s}  {acc:6.1%}  ({counts['correct']}/{counts['total']})")

    if by_subtask:
        print("\n=== Results by Subtask ===")
        for key, counts in sorted(by_subtask.items()):
            acc = counts["correct"] / counts["total"] if counts["total"] else 0
            print(f"  {key:40s}  {acc:6.1%}  ({counts['correct']}/{counts['total']})")

    total_c = sum(c["correct"] for c in by_task.values())
    total_n = sum(c["total"] for c in by_task.values())
    if total_n:
        print(f"\n  {'OVERALL':30s}  {total_c/total_n:6.1%}  ({total_c}/{total_n})")
