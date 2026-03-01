"""Adapter for the VLMs-are-Biased benchmark dataset.

HuggingFace: https://huggingface.co/datasets/anvo25/vlms-are-biased
Paper: VLMs are Biased (ICLR 2026)

Loads the HF dataset and converts rows to TaskInstance objects.
Preserves the expected_bias field in metadata for DPO pair generation.
"""

from __future__ import annotations

import json
import os

from datasets import load_dataset
from tqdm import tqdm

from data.common import parse_bracketed_answer
from generate.base import TaskInstance

DATASET_ID = "anvo25/vlms-are-biased"

AVAILABLE_SPLITS = [
    "main",
    "identification",
    "withtitle",
    "original",
    "remove_background_q1q2",
    "remove_background_q3",
]


def load_biased(
    split: str = "main",
    cache_dir: str = "data/cache/biased",
    image_dir: str = "data/images/biased",
    topics: list[str] | None = None,
    max_per_topic: int | None = None,
) -> list[TaskInstance]:
    """Load the VLMs-are-Biased dataset and return TaskInstances.

    Args:
        split: which split to load (default "main").
        cache_dir: where HF caches the download.
        image_dir: where to save images to disk.
        topics: optional filter — only load these topic names.
        max_per_topic: cap instances per topic.
    """
    os.makedirs(image_dir, exist_ok=True)

    ds = load_dataset(DATASET_ID, split=split, cache_dir=cache_dir)

    topic_counts: dict[str, int] = {}
    instances: list[TaskInstance] = []

    for row in tqdm(ds, desc=f"Loading VLMs-are-Biased ({split})"):
        topic = row["topic"]
        sub_topic = row["sub_topic"]

        if topics and topic not in topics:
            continue

        if max_per_topic:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            if topic_counts[topic] > max_per_topic:
                continue

        # Parse metadata and enrich with top-level fields
        meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
        meta["source"] = "hf_biased"
        meta["topic"] = topic
        meta["sub_topic"] = sub_topic
        meta["with_title"] = row.get("with_title", False)
        meta["type_of_question"] = row.get("type_of_question", "")
        meta["pixel"] = row.get("pixel", 0)

        # Preserve expected_bias — this is gold for DPO rejected responses
        bias_raw = row.get("expected_bias", "")
        if bias_raw:
            meta["expected_bias"] = parse_bracketed_answer(bias_raw)

        # Save image to disk
        row_id = row["ID"]
        image_path = os.path.join(image_dir, f"{row_id}.png")
        if not os.path.exists(image_path):
            row["image"].save(image_path)

        gt = parse_bracketed_answer(row["ground_truth"])

        # Map topic to a task_type the scorer can handle.
        # These are new task types — scorer will need extending.
        task_type = _topic_to_task_type(topic, sub_topic)

        instances.append(TaskInstance(
            image_path=image_path,
            prompt=row["prompt"],
            ground_truth=gt,
            task_type=task_type,
            subtask=sub_topic,
            metadata=meta,
        ))

    _print_summary(instances)
    return instances


def _topic_to_task_type(topic: str, sub_topic: str) -> str:
    """Map Biased dataset topics to task_type strings."""
    mapping = {
        "Game Board": "board_game",
        "Patterned Grid": "patterned_grid",
        "Optical Illusion": "optical_illusion",
        "Chess Board": "board_game",
    }
    return mapping.get(topic, topic.lower().replace(" ", "_"))


def _print_summary(instances: list[TaskInstance]) -> None:
    print(f"Loaded {len(instances)} instances from VLMs-are-Biased")
    task_summary: dict[str, int] = {}
    for inst in instances:
        key = f"{inst.task_type}/{inst.subtask}"
        task_summary[key] = task_summary.get(key, 0) + 1
    for t, c in sorted(task_summary.items()):
        print(f"  {t}: {c}")


def list_topics(split: str = "main") -> list[str]:
    """Return available topic names."""
    ds = load_dataset(DATASET_ID, split=split, streaming=True)
    topics = set()
    for row in ds:
        topics.add(row["topic"])
    return sorted(topics)
