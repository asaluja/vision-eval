"""Thin wrapper around the Anthropic API for vision calls."""

from __future__ import annotations

import base64
import time
from pathlib import Path

import anthropic

import config


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.API_KEY)


def encode_image(image_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_data, media_type)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "image/png")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def query_model(
    image_path: str,
    prompt: str,
    system: str | None = None,
    thinking: bool = False,
    thinking_budget: int = 4096,
    max_retries: int = 3,
) -> str:
    """Send an image + prompt to Haiku 4.5 and return the text response.

    Args:
        thinking: Enable extended thinking. When True, the model reasons
                  step-by-step before answering (may improve counting/spatial tasks).
        thinking_budget: Max tokens for the thinking phase (not counted in max_tokens).
    """
    client = get_client()
    img_data, media_type = encode_image(image_path)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img_data,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    for attempt in range(max_retries):
        try:
            kwargs = dict(
                model=config.MODEL_ID,
                max_tokens=config.MAX_TOKENS,
                messages=messages,
                temperature=0,
            )
            if system:
                kwargs["system"] = system
            if thinking:
                # temperature must be 1 for extended thinking
                kwargs.pop("temperature")
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                }
                # thinking requires max_tokens to cover both thinking + response
                kwargs["max_tokens"] = thinking_budget + config.MAX_TOKENS
            response = client.messages.create(**kwargs)
            # With thinking enabled, response has multiple blocks —
            # extract the text block (skip thinking blocks)
            for block in response.content:
                if block.type == "text":
                    return block.text
            return response.content[-1].text
        except anthropic.RateLimitError:
            wait = 2 ** attempt
            time.sleep(wait)
        except anthropic.APIError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)

    raise RuntimeError(f"Failed after {max_retries} retries")
