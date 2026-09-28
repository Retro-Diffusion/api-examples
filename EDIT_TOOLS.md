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

# The result may arrive inline OR as a hosted URL — handle both.
if result["base64_images"]:
    image_bytes = base64.b64decode(result["base64_images"][0])
else:
    image_bytes = requests.get(result["output_urls"][0], timeout=60).content
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

**At least one of `base64_images` or `output_urls` contains the result — do
not assume it is `base64_images`.** `image_edit`, `inpainting`, and
`outpainting` normally return an **empty** `base64_images` and deliver the
image only as a hosted URL in `output_urls` (as in the sample above); the
other tools return inline base64. An integration that only reads
`base64_images` will silently drop those tools' results while still being
charged for the run. Always check `base64_images` first, then fall back to
downloading `output_urls[0]`. The deprecated camelCase response fields remain
available for existing clients, but new integrations should use the
snake_case fields above.

Every run, synchronous or task, appears in API Activity, and its output stays
retrievable for 24 hours. The synchronous response carries an
`X-RD-Request-ID` header: `GET /v2/inferences/requests/{request_id}` returns
that run's status, cost, and fresh signed output URLs, even if your client
timed out before reading the response. Without the id,
`GET /v2/inferences/requests?limit=20&cursor=...&status=...` lists your recent
calls newest first as `{"items": [...], "next_cursor": "..."}`; edit runs have
`"operation": "edit_tool"` and the tool in `request.tool_id`. See
[API Activity](README.md#api-activity-every-calls-result-for-24-hours).

## Run a tool as a task (no long-held connection)

`POST /edit/tools/{tool_id}` keeps the connection open until the image is
ready. `inpainting`, `outpainting`, and `image_edit` usually take 20-40
seconds. If your HTTP client, proxy, or gateway closes requests sooner, the
run still completes and is charged, but you never receive the result. Use the
task endpoints instead whenever your request timeout is under about 60
seconds, and for every `inpainting` or `outpainting` call:

- `POST /edit/tools/{tool_id}/tasks` takes the same body as the run endpoint
  and returns `202` with a `task_id` right away.
- `GET /edit/tasks/{task_id}` returns the task's `status`: `pending`,
  `running`, `succeeded`, or `failed`.

Input, size, and balance are checked before the job is queued. A bad request
fails immediately with the same `4xx` error as the run endpoint, and nothing
is charged. The charge is taken when the job starts and refunded
automatically if it fails.

On the task endpoint, `custom_id` works as an idempotency key. Sending the
same `custom_id` again returns the original `task_id` without running or
charging a second time, so a retry after a dropped connection is safe. Store
the `custom_id` with your job before submitting it, and give every distinct
job its own `custom_id` (also when retrying one that failed).

```python
import os
import time
import uuid

import requests

API = "https://api.retrodiffusion.ai/v1"
HEADERS = {"X-RD-Token": os.environ["RD_API_KEY"]}

custom_id = str(uuid.uuid4())  # save it with your job so a retry reuses it
start = requests.post(
    f"{API}/edit/tools/inpainting/tasks",
    headers=HEADERS,
    json={
        "input_image": "<base64_png>",
        "mask_image": "<base64_mask_png>",
        "prompt": "replace the masked area with a red gem",
        "custom_id": custom_id,
    },
    timeout=30,
)
start.raise_for_status()  # 202 Accepted
task_id = start.json()["task_id"]

while True:
    response = requests.get(f"{API}/edit/tasks/{task_id}", headers=HEADERS, timeout=30)
    response.raise_for_status()
    task = response.json()
    if task["status"] not in ("pending", "running"):
        break
    time.sleep(3)

if task["status"] == "succeeded":
    image_bytes = requests.get(task["result"]["output_urls"][0], timeout=60).content
else:
    print("failed:", task["error"])
```

The accepted response:

```json
{
  "status": "accepted",
  "task_id": "3f0c9b2e-...",
  "request_id": "3f0c9b2e-...",
  "message": "Edit accepted. Poll GET /v1/edit/tasks/{task_id} for status."
}
```

A finished task. `created_at` and `updated_at` are Unix seconds, and `result`
has the same fields as the run endpoint's response. Task results always come
back as a hosted URL in `output_urls`, and `base64_images` is empty for every
tool:

```json
{
  "status": "succeeded",
  "task_id": "3f0c9b2e-...",
  "created_at": 1790611200,
  "updated_at": 1790611229,
  "result": {
    "tool_id": "inpainting",
    "inference_id": "...",
    "balance_cost": 0.18,
    "credit_cost": 20,
    "charged": true,
    "remaining_balance": 10.82,
    "base64_images": [],
    "output_urls": ["..."]
  }
}
```

A failed task is still returned with HTTP `200` and has an `error` object instead
of `result`. On `/v2` that object is `{"status_code", "code", "message",
"request_id"}`. On `/v1` it is the stored
`{"status_code", "detail": {"code", "message", "request_id"}}`. An unknown
`task_id`, or one that belongs to another account, returns `404
edit_task_not_found`. Both endpoints are also available under `/v2`, which
uses the canonical error envelope described in [V2_MIGRATION.md](V2_MIGRATION.md).

## A workflow worth knowing: consistent variants via `image_edit`

To get the *same* image in several versions (seasons, day/night, weather, palettes,
damaged/pristine), do **not** generate each variant from scratch — independent generations
come out as unrelated compositions. Generate the base once, then derive each variant with
`image_edit` and an imperative prompt that pins the layout:

```
"Turn this summer scene into deep winter — snow blankets the ground, bare frosted
trees, cold grey-blue light — keep the exact same composition, layout, and every
structure in place."
```

Each derivation costs the same as a generation but keeps the set visually consistent, and
all variants can be derived from the one base in parallel.

## Tool inputs

Every tool requires `input_image`. The table lists its additional fields.
Optional defaults and current limits are returned by the catalog's
`api_fields` property.

Every tool also accepts an optional `custom_id` for correlating the run with
your queue. On `POST /edit/tools/{tool_id}` it is not an idempotency or
deduplication key. On the [task endpoint](#run-a-tool-as-a-task-no-long-held-connection)
it is.

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
`bayer_8x8`. `dither_strength` ranges from `0` to `10` (`0` disables
dithering, default `5`), matching the Pixel Fixer's dither scale. Values
above `10` are treated as the deprecated `0`-`100` scale and divided by 10.

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

`POST /edit/tools/{tool_id}` runs are non-idempotent, and paid runs are
charged. Some free tools still require a minimum account value; check
`is_free` and `requires_minimum_balance` in the catalog. If a run times out on
your side, the server may still finish it and charge for it. Look it up in
API Activity (`GET /v2/inferences/requests`) before submitting it again; its
output stays retrievable there for 24 hours. Alternatively, use the
[task endpoints](#run-a-tool-as-a-task-no-long-held-connection) with a
`custom_id`, which makes retries safe.
