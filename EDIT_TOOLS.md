# Canvas edit tools

Canvas edit tools modify an existing image. After reading this guide, you can
discover the enabled tools, estimate a request, run it, and save the returned
image.

Tool estimates and runs use the same API key as image generation:

```http
X-RD-Token: YOUR_API_KEY
```

Request fields use `snake_case`, matching the rest of the `/v1` API. Image
fields accept a raw base64 string or a `data:image/...;base64,...` data URI.

## Discover the current tools

Use the catalog to discover enabled tools, pricing, size metadata, defaults,
and input fields:

```python
import os
import requests

response = requests.get(
    "https://api.retrodiffusion.ai/v1/edit/tools",
    timeout=30,
)
response.raise_for_status()

for tool in response.json():
    print(tool["id"], tool["api_fields"])
```

Each item includes `balance_cost`, `credit_cost`, `is_free`,
`requires_minimum_balance`, `max_input_size`, and `api_fields`. The older
`fields` property describes the web canvas UI; API clients should use
`api_fields`.

## Estimate before running

An estimate validates the request and reports its cost without running the
tool:

```python
response = requests.post(
    "https://api.retrodiffusion.ai/v1/edit/tools/image_edit/estimate",
    headers={"X-RD-Token": os.environ["RD_API_KEY"]},
    json={
        "input_image": "<base64_png>",
        "prompt": "add a tiny wizard hat",
        "seed": 123,
    },
    timeout=60,
)
response.raise_for_status()
print(response.json())
```

The response includes `tool_id`, `balance_cost`, `credit_cost`, and
`estimate_seconds`.

## Run a tool

Send the same payload to the tool endpoint to execute it:

```python
response = requests.post(
    "https://api.retrodiffusion.ai/v1/edit/tools/image_edit",
    headers={"X-RD-Token": os.environ["RD_API_KEY"]},
    json={
        "input_image": "<base64_png>",
        "prompt": "add a tiny wizard hat",
        "seed": 123,
    },
    timeout=240,
)
response.raise_for_status()
result = response.json()
```

A successful response follows the regular inference API conventions:

```json
{
  "tool_id": "image_edit",
  "inference_id": "...",
  "balance_cost": 0.18,
  "credit_cost": 20,
  "charged": true,
  "remaining_balance": 10.82,
  "remaining_credits": null,
  "base64_images": [],
  "output_urls": ["..."]
}
```

At least one of `base64_images` or `output_urls` contains the result. The
deprecated camelCase response fields remain available for existing clients,
but new integrations should use the snake_case fields above.

## Tool inputs

Every tool requires `input_image`. The table lists its additional fields.
Optional defaults and current limits are returned by the catalog's
`api_fields` property.

Every tool also accepts an optional `custom_id` for correlating the run with
your queue. It is not an idempotency or deduplication key.

| Tool ID | Additional fields |
| --- | --- |
| `image_edit` | `prompt` (required), `seed` |
| `inpainting` | `mask_image` (required), `prompt` (required), `seed`, `soft_inpaint` |
| `outpainting` | `expand_left`, `expand_right`, `expand_top`, `expand_bottom`, `prompt`, `seed`, `soft_inpaint` |
| `background_remover` | `force_solid_pixels`, `transparency_threshold` |
| `color_reducer` | `color_count`, `dither_mode`, `dither_strength` |
| `pixel_correction` | None |
| `palette_converter` | `input_palette` (required), `dither_mode`, `dither_strength` |
| `color_style_transfer` | `extra_input_image` (required) |
| `k_centroid_downscale` | `width` (required), `height` (required) |
| `seam_tiling` | `tile_x`, `tile_y`, `seam_width`, `repair_window_size`, `seed` |
| `rotate` | `rotation_degrees` |

Supported `dither_mode` values are `none`, `bayer_2x2`, `bayer_4x4`, and
`bayer_8x8`. `dither_strength` ranges from `0` to `100`.

Outpainting requires at least one positive expansion value. Seam tiling
requires at least one of `tile_x` or `tile_y` to be `true`.

## Inpainting mask format

For `inpainting`, `mask_image` must be the same pixel dimensions as
`input_image`. The recommended format is an RGBA PNG:

- Alpha `0` means protect this pixel and copy it unchanged to the result.
- Alpha values greater than `12` mean replace this pixel using the prompt.
- The mask's visible RGB color does not matter; the alpha channel controls the
  editable area.

An `L`-mode grayscale PNG is also accepted. Values from `0` through `12` are
protected, and values greater than `12` are replaced.

Do not use an ordinary fully opaque RGB image as the mask. Converting it to
RGBA gives every pixel alpha `255`, which selects the entire image. Export an
RGBA image with transparent protected pixels, or export a true grayscale
image with black protected pixels.

This example creates a transparent RGBA mask with one opaque editable region:

```python
from PIL import Image, ImageDraw

with Image.open("input.png") as source:
    mask = Image.new("RGBA", source.size, (0, 0, 0, 0))

# Replace only this rectangle. The red color is for human visibility; alpha
# 255 is what marks these pixels as editable.
box = (mask.width // 4, mask.height // 4, mask.width * 3 // 4, mask.height * 3 // 4)
ImageDraw.Draw(mask).rectangle(box, fill=(255, 0, 0, 255))
mask.save("mask.png")
```

A ready-to-run RGBA example mask is included at
`resources/inpainting-mask-rgba.png`; it matches
`resources/single_tile.png`.

The inpainting request then sends both files as base64:

```json
{
  "input_image": "<base64 input.png>",
  "mask_image": "<base64 mask.png>",
  "prompt": "replace the masked area with a red gem",
  "seed": 123,
  "soft_inpaint": false
}
```

With `soft_inpaint` set to `false`, pixels outside the selected mask are
restored exactly. Set it to `true` only when the edit may blend through a
bounded transition immediately around the mask edge.

Animated GIF input is supported by `color_reducer`, `palette_converter`,
`color_style_transfer`, and `k_centroid_downscale`. Other tools accept static
images only.

Example payloads for every tool are available in
[09_edit_tools.py](example-scripts/09_edit_tools.py). The script defaults to
the free `pixel_correction` tool and estimates the cost before executing:

```bash
RD_API_KEY=YOUR_API_KEY python example-scripts/09_edit_tools.py
RD_API_KEY=YOUR_API_KEY RD_EDIT_TOOL=rotate python example-scripts/09_edit_tools.py
RD_API_KEY=YOUR_API_KEY RD_EDIT_TOOL=inpainting \
  INPUT_IMAGE_PATH=resources/single_tile.png \
  MASK_IMAGE_PATH=resources/inpainting-mask-rgba.png \
  python example-scripts/09_edit_tools.py
```

Set `INPUT_IMAGE_PATH` to use an image other than `input.png`. Inpainting also
requires `MASK_IMAGE_PATH`; the script verifies its dimensions, mode, and
selected pixels before sending it. Palette conversion requires
`PALETTE_IMAGE_PATH`; color style transfer requires `REFERENCE_IMAGE_PATH`.

## Errors and retries

Stable application errors use the same shape as the generation API:

```json
{
  "detail": {
    "code": "missing_prompt",
    "message": "A prompt is required for this tool."
  }
}
```

- `400` means the request is semantically invalid or the account cannot cover
  the operation.
- `401` means the API token is invalid or expired.
- `404` means the tool is unknown or disabled.
- `422` means the JSON does not match the request schema or a required header
  is missing.
- `500` means the tool failed temporarily on the server.

Runs are non-idempotent `POST` requests, and paid runs are charged. Some free
tools still require a minimum account value; check `is_free` and
`requires_minimum_balance` in the catalog. If a request times out, check your
inference history before submitting it again.
