"""Common types and utilities for image generators."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any

from PIL import ImageFont
import matplotlib.font_manager as fm


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a reliable font. Tries DejaVu Sans (ships with matplotlib), then Helvetica, then default."""
    try:
        path = fm.findfont("DejaVu Sans")
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:
            return ImageFont.load_default()


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


def make_instances(
    image_path: str,
    task_type: str,
    ground_truth: Any,
    subtask: str = "",
    metadata: dict | None = None,
    **prompt_kwargs,
) -> list[TaskInstance]:
    """Create one TaskInstance per prompt variant for a given task.

    Returns a list with one entry per variant defined in PROMPTS[task_type].
    Each instance is identical except for the prompt text and a
    'prompt_variant' key in metadata (0, 1, 2, ...).

    Usage:
        instances.extend(make_instances(
            fpath, "chart_bar_value", 42,
            subtask="bar_n5", metadata={...}, category="Jan",
        ))
    """
    from evaluate.prompts import PROMPTS

    templates = PROMPTS.get(task_type, [])
    if not templates:
        raise ValueError(f"No prompts registered for task_type={task_type!r}")

    abs_path = os.path.abspath(image_path)
    meta = dict(metadata or {})
    results = []

    for variant_idx, template in enumerate(templates):
        prompt = template.format(**prompt_kwargs) if prompt_kwargs else template
        inst_meta = dict(meta, prompt_variant=variant_idx)
        results.append(TaskInstance(
            image_path=abs_path,
            prompt=prompt,
            ground_truth=ground_truth,
            task_type=task_type,
            subtask=subtask,
            metadata=inst_meta,
        ))

    return results
