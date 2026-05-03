import base64
import os
from pathlib import Path
from typing import Any

import requests


API_BASE_URL = "https://api.retrodiffusion.ai/v1"


def image_to_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def save_base64_image(image_base64: str, path: str) -> None:
    Path(path).write_bytes(base64.b64decode(image_base64))


def run_edit_tool(api_key: str, tool_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/edit/tools/{tool_id}",
        headers={"X-RD-Token": api_key},
        json=payload,
        timeout=120,
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


def main() -> None:
    api_key = os.environ["RD_API_KEY"]
    input_image = image_to_base64("input.png")

    examples: list[tuple[str, dict[str, Any], str]] = [
        (
            "image_edit",
            {
                "inputImageBase64": input_image,
                "prompt": "add a tiny wizard hat",
                "seed": 123,
            },
            "output_image_edit.png",
        ),
        (
            "background_remover",
            {
                "inputImageBase64": input_image,
            },
            "output_background_removed.png",
        ),
        (
            "color_reducer",
            {
                "inputImageBase64": input_image,
                "colorCount": 16,
                "dithering": True,
            },
            "output_color_reduced.png",
        ),
        (
            "palette_converter",
            {
                "inputImageBase64": input_image,
                "paletteImageBase64": input_image,
                "dithering": True,
            },
            "output_palette_converted.png",
        ),
        (
            "color_style_transfer",
            {
                "inputImageBase64": input_image,
                "referenceImageBase64": input_image,
            },
            "output_color_style_transfer.png",
        ),
        (
            "k_centroid_downscale",
            {
                "inputImageBase64": input_image,
                "width": 64,
                "height": 64,
            },
            "output_k_centroid_downscale.png",
        ),
    ]

    for tool_id, payload, output_path in examples:
        result = run_edit_tool(api_key, tool_id, payload)
        save_base64_image(result["outputImageBase64"], output_path)
        print(f"{tool_id}: saved {output_path}")


if __name__ == "__main__":
    main()
