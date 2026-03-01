"""Adapter for the VLMs-are-Blind benchmark dataset.

HuggingFace: https://huggingface.co/datasets/XAI/vlmsareblind
Paper: arXiv:2407.06581

Loads the HF dataset and converts rows to TaskInstance objects
that plug directly into the existing eval harness.
"""

from __future__ import annotations

import json
import os

from datasets import load_dataset
from tqdm import tqdm

from data.common import parse_bracketed_answer
from generate.base import TaskInstance

DATASET_ID = "XAI/vlmsareblind"

# Map HF dataset task names → our task_type names (for scorer compatibility)
TASK_MAP = {
    "Olympic Counting - Circles": "counting_circles",
    "Olympic Counting - Pentagons": "counting_pentagons",
    "Line Plot Intersections": "line_intersection",
    "Nested Squares": "nested_squares",
    "Touching Circles": "touching_circles",
    "Circled Letter": "circled_letter",
    "Counting Grid - Blank Grids": "grid_counting",
    "Counting Grid - Word Grids": "grid_counting",
    "Subway Connections": "path_following",
}


def load_blind(
    cache_dir: str = "data/cache/blind",
    image_dir: str = "data/images/blind",
    tasks: list[str] | None = None,
    max_per_task: int | None = None,
) -> list[TaskInstance]:
    """Load the VLMs-are-Blind dataset and return TaskInstances.

    Args:
        cache_dir: where HF caches the download.
        image_dir: where to save images to disk for the eval harness.
        tasks: optional filter — only load these task_type names
               (use our names like "counting_circles", not the HF names).
        max_per_task: cap instances per task (useful for quick sweeps).
    """
    os.makedirs(image_dir, exist_ok=True)

    ds = load_dataset(DATASET_ID, split="valid", cache_dir=cache_dir)

    task_counts: dict[str, int] = {}
    instances: list[TaskInstance] = []

    for row in tqdm(ds, desc="Loading VLMs-are-Blind"):
        hf_task = row["task"]
        task_type = TASK_MAP.get(hf_task)
        if task_type is None:
            # Unknown task in the dataset — keep it with raw name
            task_type = hf_task.lower().replace(" ", "_")

        # Filter by task if requested
        if tasks and task_type not in tasks:
            continue

        # Cap per task if requested
        if max_per_task:
            task_counts[task_type] = task_counts.get(task_type, 0) + 1
            if task_counts[task_type] > max_per_task:
                continue

        # Parse metadata
        meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
        meta["source"] = "hf_blind"
        meta["hf_task_name"] = hf_task

        # Save image to disk
        image_id = meta.get("image_id", f"{task_type}_{len(instances)}")
        image_path = os.path.join(image_dir, f"{image_id}.png")
        if not os.path.exists(image_path):
            row["image"].save(image_path)

        # Parse ground truth out of brackets
        gt = parse_bracketed_answer(row["groundtruth"])

        instances.append(TaskInstance(
            image_path=image_path,
            prompt=row["prompt"],
            ground_truth=gt,
            task_type=task_type,
            subtask=hf_task,
            metadata=meta,
        ))

    _print_summary(instances)
    return instances


def _print_summary(instances: list[TaskInstance]) -> None:
    print(f"Loaded {len(instances)} instances from VLMs-are-Blind")
    task_summary: dict[str, int] = {}
    for inst in instances:
        task_summary[inst.task_type] = task_summary.get(inst.task_type, 0) + 1
    for t, c in sorted(task_summary.items()):
        print(f"  {t}: {c}")


def list_tasks() -> list[str]:
    """Return available task names (in our naming convention)."""
    ds = load_dataset(DATASET_ID, split="valid", streaming=True)
    hf_tasks = set()
    for row in ds:
        hf_tasks.add(row["task"])
    return sorted(TASK_MAP.get(t, t.lower().replace(" ", "_")) for t in hf_tasks)
