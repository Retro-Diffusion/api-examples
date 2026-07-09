"""Post-process an image by chaining edit tools.

Edit tools take one image and return one edited image. NOTE: these endpoints use
camelCase field names (inputImageBase64), unlike /v1/inferences.

GET  /v1/edit/tools                 lists the currently available tools + costs
POST /v1/edit/tools/{tool_id}       runs one tool

Tools include: image_edit ($0.18, input <=256px), inpainting ($0.18),
outpainting ($0.18), seam_tiling ($0.18), background_remover ($0.01),
color_style_transfer ($0.01), and the free color_reducer / palette_converter /
k_centroid_downscale (free tools still need >= $0.01 balance). GET /v1/edit/tools
is authoritative for what's available and each tool's fields.

Chain tools by feeding each outputImageBase64 into the next call's
inputImageBase64. This script turns a large image into a clean pixel-art asset:
k_centroid_downscale (shrink to pixel art) -> image_edit -> reduce colors.

Other useful tools you can slot into the same chain (see GET /v1/edit/tools):
    background_remover  -> transparent PNG          {"inputImageBase64": img}
    palette_converter   -> map to a palette image   {"inputImageBase64": img, "paletteImageBase64": pal}
    seam_tiling         -> make a texture tile       {"inputImageBase64": img, "seamTileHorizontal": True}

    python 09_edit_tools.py path/to/input.png
"""
import sys

import requests

from rd_client import API_BASE_URL, get_api_key, image_to_base64, save_images

api_key = get_api_key()
input_path = sys.argv[1] if len(sys.argv) > 1 else "../input.png"


def run_tool(tool_id: str, payload: dict) -> str:
    """Run one edit tool and return its output image (base64)."""
    response = requests.post(
        f"{API_BASE_URL}/edit/tools/{tool_id}",
        headers={"X-RD-Token": api_key},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["outputImageBase64"]


# List available tools (handy for discovering fields and live costs).
tools = requests.get(f"{API_BASE_URL}/edit/tools", headers={"X-RD-Token": api_key}, timeout=30).json()
print("Available tools:", ", ".join(t["id"] for t in tools))

# 1. Downscale any-size input to 128px pixel art (free; image_edit needs <=256px).
image = run_tool("k_centroid_downscale", {"inputImageBase64": image_to_base64(input_path), "width": 128, "height": 128})

# 2. Edit it with a prompt.
image = run_tool("image_edit", {"inputImageBase64": image, "prompt": "add a tiny wizard hat", "seed": 123})

# 3. Reduce to 16 colors with dithering (a free tool).
image = run_tool("color_reducer", {"inputImageBase64": image, "colorCount": 16, "dithering": True})

# save_images expects an inference-style response, so wrap the final image.
print(f"Saved {save_images({'base64_images': [image]}, 'output_edited')}")
