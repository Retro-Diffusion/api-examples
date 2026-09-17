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
import uuid
from pathlib import Path
from typing import Any

import requests

API_VERSION = os.environ.get("RD_API_VERSION", "v2").strip().lower()
if API_VERSION not in {"v1", "v2"}:
    raise RuntimeError("RD_API_VERSION must be either v1 or v2.")
API_BASE_URL = f"https://api.retrodiffusion.ai/{API_VERSION}"


class RetroDiffusionAPIError(RuntimeError):
    """Safe typed representation of v1 and v2 API errors."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str | None,
        message: str,
        request_id: str | None,
        details: dict[str, Any] | None,
        retry_after: str | None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id
        self.details = details
        self.retry_after = retry_after
        metadata = [str(status_code)]
        if code:
            metadata.append(f"code={code}")
        if request_id:
            metadata.append(f"request_id={request_id}")
        if retry_after:
            metadata.append(f"retry_after={retry_after}")
        super().__init__(
            f"RetroDiffusion API request failed ({' '.join(metadata)}): {message}"
        )


def parse_api_error(
    *,
    status_code: int,
    body: Any,
    headers: Any = None,
) -> RetroDiffusionAPIError:
    response_headers = {
        str(key).lower(): str(value)
        for key, value in (headers.items() if headers is not None else [])
    }
    code = None
    message = None
    request_id = None
    details = None
    if isinstance(body, dict):
        source = body.get("error")
        if not isinstance(source, dict):
            detail = body.get("detail")
            if isinstance(detail, dict):
                source = detail
            elif isinstance(detail, list):
                source = next(
                    (item for item in detail if isinstance(item, dict)),
                    None,
                )
            elif isinstance(detail, str):
                message = detail
        if isinstance(source, dict):
            code = source.get("code") if isinstance(source.get("code"), str) else None
            if isinstance(source.get("message"), str):
                message = source["message"]
            elif isinstance(source.get("msg"), str):
                message = source["msg"]
            if source.get("request_id"):
                request_id = str(source["request_id"])
            if isinstance(source.get("details"), dict):
                details = source["details"]

    return RetroDiffusionAPIError(
        status_code=status_code,
        code=code,
        message=message or "The API request failed.",
        request_id=request_id or response_headers.get("x-request-id"),
        details=details,
        retry_after=response_headers.get("retry-after"),
    )


def raise_for_api_error(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        body = response.json()
    except ValueError:
        body = None
    raise parse_api_error(
        status_code=response.status_code,
        body=body,
        headers=response.headers,
    )


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


def _submit_inference(
    payload: dict[str, Any],
    api_key: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Submit one logical inference without replay or version fallback."""
    headers = _headers(api_key)
    use_idempotency = not payload.get("check_cost") and (
        API_VERSION == "v2" or payload.get("async") or payload.get("async_process")
    )
    if use_idempotency:
        key = idempotency_key or str(uuid.uuid4())
        headers["Idempotency-Key"] = key
        print(f"  admission key {key} (save it until task_id is received)")
    response = requests.post(
        f"{API_BASE_URL}/inferences",
        headers=headers,
        json=payload,
        timeout=300,
    )
    raise_for_api_error(response)
    return response.json()


def _poll_task(task_id: str, api_key: str, poll_seconds: float) -> dict[str, Any]:
    while True:
        task_response = requests.get(
            f"{API_BASE_URL}/inferences/tasks/{task_id}",
            headers=_headers(api_key),
            timeout=30,
        )
        raise_for_api_error(task_response)
        task = task_response.json()
        status = task["status"]
        if status in ("accepted", "pending", "running"):
            time.sleep(poll_seconds)
            continue
        if status == "succeeded":
            return task["result"]
        task_error = task.get("error")
        if isinstance(task_error, dict):
            raise parse_api_error(
                status_code=int(task_error.get("status_code", 500)),
                body={"error": task_error},
            )
        raise RuntimeError("The inference task failed without a valid error.")


def generate(
    payload: dict[str, Any],
    api_key: str | None = None,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Submit one inference and return its result; v2 polls the accepted task.

    Raises a helpful error if the request fails.
    """
    api_key = api_key or get_api_key()
    response = _submit_inference(payload, api_key, idempotency_key)
    if API_VERSION == "v2" and response.get("status") == "accepted":
        return _poll_task(str(response["task_id"]), api_key, 2.0)
    return response


def generate_async(
    payload: dict[str, Any],
    api_key: str | None = None,
    poll_seconds: float = 2.0,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Submit an async job and poll until it finishes, returning the final result.

    Use this for animations or large batches you'd rather not hold a connection
    open for.
    """
    api_key = api_key or get_api_key()
    accepted = _submit_inference(
        {**payload, "async": True}, api_key, idempotency_key
    )
    task_id = accepted["task_id"]
    print(f"  queued task {task_id}")
    return _poll_task(str(task_id), api_key, poll_seconds)


def check_cost(payload: dict[str, Any], api_key: str | None = None) -> float:
    """Return the price of a request without generating anything (free dry run)."""
    result = generate({**payload, "check_cost": True}, api_key)
    return float(result["balance_cost"])


def list_tasks(
    limit: int = 20,
    status: str | None = None,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """GET /v2/inferences/tasks — your most recent async jobs, newest first.

    Recovery fallback when the original idempotency key is unavailable: find
    the accepted task here instead of blindly re-submitting, then keep polling
    it via GET /v2/inferences/tasks/{task_id}.
    """
    api_key = api_key or get_api_key()
    params: dict[str, Any] = {"limit": max(1, min(limit, 100))}
    if status:
        params["status"] = status
    data = requests.get(
        f"{API_BASE_URL}/inferences/tasks",
        headers=_headers(api_key),
        params=params,
        timeout=30,
    )
    raise_for_api_error(data)
    return data.json()["tasks"]


def get_balance(api_key: str | None = None) -> float:
    """Return the account's current USD balance."""
    api_key = api_key or get_api_key()
    response = requests.get(
        f"{API_BASE_URL}/inferences/credits",
        headers=_headers(api_key),
        timeout=30,
    )
    raise_for_api_error(response)
    data = response.json()
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
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
        ):
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
    raise_for_api_error(response)
    return response.json()


def image_to_base64(path: str | Path) -> str:
    """Read an image file and return a raw base64 string (no data: URI prefix)."""
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def save_images(result: dict[str, Any], stem: str) -> list[str]:
    """Save every image in a response. PNG normally, .gif for animation styles.

    Handles both delivery modes: inline ``base64_images`` AND hosted
    ``output_urls`` — the image_edit, inpainting, and outpainting edit tools
    normally return an empty ``base64_images`` and deliver the result only as
    a URL. Returns the list of written file paths.
    """
    images = [base64.b64decode(b64) for b64 in result.get("base64_images") or []]
    if not images:
        for url in result.get("output_urls") or []:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            images.append(response.content)
    written: list[str] = []
    for index, data in enumerate(images):
        # Animation styles return GIFs; sniff the header to pick the extension.
        ext = "gif" if data[:3] == b"GIF" else "png"
        suffix = f"_{index + 1}" if len(images) > 1 else ""
        path = f"{stem}{suffix}.{ext}"
        Path(path).write_bytes(data)
        written.append(path)
    return written
