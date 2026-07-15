"""Tiny shared helper for the Retro Diffusion API example scripts.

Every script in this folder imports from here so the examples can stay short and
focused on the task rather than on HTTP boilerplate.

Full reference: https://www.retrodiffusion.ai/app/guide/api

Set your API key once, in the environment:
    export RD_API_KEY="rdpk-..."      # macOS / Linux
    setx    RD_API_KEY  "rdpk-..."    # Windows (new terminals)

Create a key at https://www.retrodiffusion.ai/app/devtools
"""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

import requests

API_BASE_URL = "https://api.retrodiffusion.ai/v1"


def get_api_key() -> str:
    """Read the API key from the RD_API_KEY environment variable."""
    key = os.environ.get("RD_API_KEY")
    if not key:
        raise SystemExit(
            "Set the RD_API_KEY environment variable to your API key "
            "(create one at https://www.retrodiffusion.ai/app/devtools)."
        )
    return key


def _headers(api_key: str) -> dict[str, str]:
    return {"X-RD-Token": api_key}


def generate(payload: dict[str, Any], api_key: str | None = None) -> dict[str, Any]:
    """POST /v1/inferences and return the parsed JSON response.

    Raises a helpful error if the request fails.
    """
    api_key = api_key or get_api_key()
    response = requests.post(
        f"{API_BASE_URL}/inferences",
        headers=_headers(api_key),
        json=payload,
        timeout=300,
    )
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
    return response.json()


def generate_async(payload: dict[str, Any], api_key: str | None = None, poll_seconds: float = 2.0) -> dict[str, Any]:
    """Submit an async job and poll until it finishes, returning the final result.

    Use this for animations or large batches you'd rather not hold a connection
    open for.
    """
    api_key = api_key or get_api_key()
    accepted = generate({**payload, "async": True}, api_key)
    task_id = accepted["task_id"]
    print(f"  queued task {task_id}")
    while True:
        task = requests.get(
            f"{API_BASE_URL}/inferences/tasks/{task_id}",
            headers=_headers(api_key),
            timeout=30,
        ).json()
        status = task["status"]
        if status in ("pending", "running"):
            time.sleep(poll_seconds)
            continue
        if status == "succeeded":
            return task["result"]
        raise RuntimeError(f"task failed: {task.get('error')}")


def check_cost(payload: dict[str, Any], api_key: str | None = None) -> float:
    """Return the price of a request without generating anything (free dry run)."""
    result = generate({**payload, "check_cost": True}, api_key)
    return float(result["balance_cost"])


def get_balance(api_key: str | None = None) -> float:
    """Return the account's current USD balance."""
    api_key = api_key or get_api_key()
    data = requests.get(
        f"{API_BASE_URL}/inferences/credits",
        headers=_headers(api_key),
        timeout=30,
    ).json()
    return float(data["balance"])


def fix_pixel_art(
    input_image: str | None = None,
    *,
    image_url: str | None = None,
    engine: str = "standard",
    width: int | None = None,
    height: int | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Reconstruct an image at its native pixel grid and return one base64 PNG."""
    if engine not in {"standard", "neural"}:
        raise ValueError("engine must be 'standard' or 'neural'")
    if engine == "standard" and (width is not None or height is not None):
        raise ValueError("width and height are accepted only by the neural endpoint")
    if (input_image is None) == (image_url is None):
        raise ValueError("provide exactly one of input_image or image_url")
    for name, value in (("width", width), ("height", height)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value <= 0):
            raise ValueError(f"{name} must be a positive integer when provided")

    payload: dict[str, Any] = (
        {"input_image": input_image}
        if input_image is not None
        else {"image_url": image_url}
    )
    if width is not None:
        payload["width"] = width
    if height is not None:
        payload["height"] = height

    response = requests.post(
        f"{API_BASE_URL}/pixel-fixer/{engine}",
        headers=_headers(api_key or get_api_key()),
        json=payload,
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
    return response.json()


def image_to_base64(path: str | Path) -> str:
    """Read an image file and return a raw base64 string (no data: URI prefix)."""
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def save_images(result: dict[str, Any], stem: str) -> list[str]:
    """Save every image in a response. PNG normally, .gif for animation styles.

    Returns the list of written file paths.
    """
    images = result.get("base64_images") or []
    written: list[str] = []
    for index, b64 in enumerate(images):
        data = base64.b64decode(b64)
        # Animation styles return GIFs; sniff the header to pick the extension.
        ext = "gif" if data[:3] == b"GIF" else "png"
        suffix = f"_{index + 1}" if len(images) > 1 else ""
        path = f"{stem}{suffix}.{ext}"
        Path(path).write_bytes(data)
        written.append(path)
    return written
