# Canvas edit tools

Canvas edit tools modify an existing image. After reading this guide, you can
discover the enabled tools, estimate a request, run it, and save the returned
image.

Tool estimates, runs, and scheduled jobs use the same API key as image
generation:

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
`estimate_seconds`. Inpainting and outpainting estimates may also include a
`region_plan` and `scheduled_region_summary`.

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
| `inpainting` | `mask_image` (required), `prompt` (required), `seed`, `soft_inpaint`, `scheduled_region_mode`, `scheduled_region_quality` |
| `outpainting` | `expand_left`, `expand_right`, `expand_top`, `expand_bottom`, `prompt`, `seed`, `soft_inpaint`, `scheduled_region_mode`, `scheduled_region_quality` |
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

Animated GIF input is supported by `color_reducer`, `palette_converter`,
`color_style_transfer`, and `k_centroid_downscale`. Other tools accept static
images only.

Example payloads for every tool are available in [edit_tools.py](edit_tools.py).
The script defaults to the free `pixel_correction` tool and estimates the cost
before executing:

```bash
RD_API_KEY=YOUR_API_KEY python edit_tools.py
RD_API_KEY=YOUR_API_KEY RD_EDIT_TOOL=rotate python edit_tools.py
```

Set `INPUT_IMAGE_PATH` to use an image other than `input.png`. Inpainting also
requires `MASK_IMAGE_PATH`; palette conversion requires `PALETTE_IMAGE_PATH`;
and color style transfer requires `REFERENCE_IMAGE_PATH`.

## Scheduled inpainting and outpainting

Large inpainting and outpainting requests can be planned and reserved as
scheduled-region jobs. Set `scheduled_region_mode` to `true` and choose
`scheduled_region_quality` as `fast` or `quality`.

Start a job:

```http
POST /v1/edit/tools/{tool_id}/scheduled-region-jobs
```

The response includes the authoritative `region_plan` and a
`scheduled_region_job_id`. Pass that ID in the normal tool request's optional
`scheduled_region_job_id` field to claim and execute the reservation. You can
inspect or cancel it with:

```http
GET  /v1/edit/scheduled-region-jobs/{job_id}
POST /v1/edit/scheduled-region-jobs/{job_id}/cancel
```

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
