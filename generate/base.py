"""Common types and utilities for image generators."""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class TaskInstance:
    """A single evaluation instance: image + question + ground truth."""
    image_path: str
    prompt: str
    ground_truth: Any  # int, str, tuple, etc.
    task_type: str
    subtask: str = ""
    metadata: dict = field(default_factory=dict)


def save_instances(instances: list[TaskInstance], output_path: str) -> None:
    """Write instances as JSONL."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for inst in instances:
            f.write(json.dumps(asdict(inst)) + "\n")


def load_instances(path: str) -> list[TaskInstance]:
    """Read JSONL back into TaskInstances."""
    instances = []
    with open(path) as f:
        for line in f:
            d = json.loads(line.strip())
            instances.append(TaskInstance(**d))
    return instances


def ensure_dir(path: str) -> str:
    """Create directory if needed, return path."""
    os.makedirs(path, exist_ok=True)
    return path
