"""Discover every style available to your account.

GET /v1/styles/selector returns the live catalog with each style's exact size
limits, batch cap, and whether it needs an input image or supports reference
images. Always the source of truth for valid prompt_style values — call this
before generating if you're unsure what a style supports.

    python 08_list_styles.py                 # all styles
    python 08_list_styles.py rd_pro          # filter by model
    python 08_list_styles.py rd_plus tab:image
"""
import sys

import requests

from rd_client import API_BASE_URL, get_api_key

params = {}
for arg in sys.argv[1:]:
    if arg.startswith("tab:"):
        params["tab"] = arg
    else:
        params["model"] = arg  # rd_fast | rd_plus | rd_pro | rd_mini

response = requests.get(
    f"{API_BASE_URL}/styles/selector",
    headers={"X-RD-Token": get_api_key()},
    params=params,
    timeout=30,
)
response.raise_for_status()
data = response.json()

print(f"{len(data['styles'])} styles  (models: {', '.join(data['models'])})\n")
for style in data["styles"]:
    flags = []
    if style.get("require_input_image"):
        flags.append("needs input image")
    if style.get("supports_reference_images"):
        flags.append("reference images")
    detail = f"  [{', '.join(flags)}]" if flags else ""
    print(
        f"{style['prompt_style']:<34} "
        f"{style['min_width']}-{style['max_width']}px  "
        f"batch<={style['max_number_of_images']}{detail}"
    )
