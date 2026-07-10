"""Run one canvas edit tool through the public RetroDiffusion API.

Set RD_API_KEY and optionally RD_EDIT_TOOL. The default tool is the free
pixel_correction operation. Some tools also need MASK_IMAGE_PATH,
PALETTE_IMAGE_PATH, or REFERENCE_IMAGE_PATH.
"""

import base64
import os
from pathlib import Path
from typing import Any

import requests


API_BASE_URL = "https://api.retrodiffusion.ai/v1"
SUPPORTED_TOOL_IDS = (
    "image_edit",
    "inpainting",
    "outpainting",
    "background_remover",
    "color_reducer",
    "pixel_correction",
    "palette_converter",
    "color_style_transfer",
    "k_centroid_downscale",
    "seam_tiling",
    "rotate",
)


def image_to_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def save_base64_image(image_base64: str, path_stem: str) -> Path:
    if image_base64.startswith("data:"):
        image_base64 = image_base64.split(",", 1)[1]
    image_bytes = base64.b64decode(image_base64)
    if image_bytes.startswith(b"GIF8"):
        suffix = ".gif"
    elif image_bytes.startswith(b"\xff\xd8\xff"):
        suffix = ".jpg"
    elif image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        suffix = ".webp"
    else:
        suffix = ".png"
    output_path = Path(path_stem).with_suffix(suffix)
    output_path.write_bytes(image_bytes)
    return output_path


def request_edit_tool(
    api_key: str,
    tool_id: str,
    payload: dict[str, Any],
    *,
    estimate: bool = False,
) -> dict[str, Any]:
    suffix = "/estimate" if estimate else ""
    response = requests.post(
        f"{API_BASE_URL}/edit/tools/{tool_id}{suffix}",
        headers={"X-RD-Token": api_key},
        json=payload,
        timeout=60 if estimate else 240,
    )
    response.raise_for_status()
    return response.json()


def list_edit_tools(api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{API_BASE_URL}/edit/tools",
        headers={"X-RD-Token": api_key},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_payload(tool_id: str) -> dict[str, Any]:
    if tool_id not in SUPPORTED_TOOL_IDS:
        available = ", ".join(SUPPORTED_TOOL_IDS)
        raise ValueError(f"Unknown RD_EDIT_TOOL {tool_id!r}. Choose one of: {available}")

    input_image = image_to_base64(os.getenv("INPUT_IMAGE_PATH", "input.png"))
    common = {"input_image": input_image}

    if tool_id == "inpainting":
        return {
            **common,
            "mask_image": image_to_base64(os.environ["MASK_IMAGE_PATH"]),
            "prompt": "replace the masked area with a red gem",
            "seed": 123,
            "soft_inpaint": False,
        }
    if tool_id == "palette_converter":
        return {
            **common,
            "input_palette": image_to_base64(os.environ["PALETTE_IMAGE_PATH"]),
            "dither_mode": "none",
        }
    if tool_id == "color_style_transfer":
        return {
            **common,
            "extra_input_image": image_to_base64(
                os.environ["REFERENCE_IMAGE_PATH"]
            ),
        }

    payloads: dict[str, dict[str, Any]] = {
        "image_edit": {
            **common,
            "prompt": "add a tiny wizard hat",
            "seed": 123,
        },
        "outpainting": {
            **common,
            "expand_right": 32,
            "prompt": "continue the forest path",
            "seed": 123,
            "soft_inpaint": False,
        },
        "background_remover": {
            **common,
            "force_solid_pixels": True,
            "transparency_threshold": 190,
        },
        "color_reducer": {
            **common,
            "color_count": 16,
            "dither_mode": "bayer_4x4",
            "dither_strength": 50,
        },
        "pixel_correction": common,
        "k_centroid_downscale": {
            **common,
            "width": 64,
            "height": 64,
        },
        "seam_tiling": {
            **common,
            "tile_x": True,
            "tile_y": False,
            "seam_width": 32,
            "repair_window_size": 256,
            "seed": 123,
        },
        "rotate": {
            **common,
            "rotation_degrees": 45,
        },
    }

    return payloads[tool_id]


def main() -> None:
    api_key = os.environ["RD_API_KEY"]
    tool_id = os.getenv("RD_EDIT_TOOL", "pixel_correction")
    payload = build_payload(tool_id)

    catalog = {tool["id"]: tool for tool in list_edit_tools(api_key)}
    if tool_id not in catalog:
        raise RuntimeError(f"{tool_id} is not enabled in the public API catalog")

    estimate = request_edit_tool(api_key, tool_id, payload, estimate=True)
    print(
        f"Estimate: {estimate['balance_cost']} balance / "
        f"{estimate['credit_cost']} credits"
    )

    result = request_edit_tool(api_key, tool_id, payload)
    if result["base64_images"]:
        output_path = save_base64_image(
            result["base64_images"][0], f"output_{tool_id}"
        )
        print(f"Saved {output_path}; inference ID: {result['inference_id']}")
    elif result["output_urls"]:
        print(
            f"Output URL: {result['output_urls'][0]}; "
            f"inference ID: {result['inference_id']}"
        )
    else:
        raise RuntimeError("The API returned no image output")


if __name__ == "__main__":
    main()
