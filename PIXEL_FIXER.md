# Pixel Fixer API

Pixel Fixer reconstructs enlarged, softened, AI-rendered, or compression-damaged pixel art at its
detected native grid. It is authenticated with the same `X-RD-Token` API key as generation, but it
does not spend account balance.

Use the standard endpoint for native Rust grid detection:

```http
POST https://api.retrodiffusion.ai/v1/pixel-fixer/standard
X-RD-Token: rdpk-YOUR-KEY
Content-Type: application/json

{"input_image":"<raw base64 PNG or JPEG, or a data URI>"}
```

The response contains exactly one raw base64 PNG and no generation metadata:

```json
{"base64_images":["iVBORw0KGgo..."]}
```

Use the neural endpoint for neural reconstruction with optional target dimensions:

```http
POST https://api.retrodiffusion.ai/v1/pixel-fixer/neural

{"input_image":"<base64>","width":32,"height":32}
```

`width` and `height` are optional positive integers that set the neural reconstruction target size.

## Limits

- Input image: PNG or JPEG, at least 16×16, no more than 4 megapixels.
- Request JSON: at most 900,000 bytes, including base64 expansion and JSON syntax.
- Successful response JSON: at most 850,000 bytes. Larger reconstructed PNGs return HTTP 413.
- Rate limit: 10 requests per minute per API token, shared by standard and neural.
- Unknown request fields are rejected.

Stable Pixel Fixer errors use the normal `detail.code` and `detail.message` envelope:

| Status | Code |
| --- | --- |
| 413 | `pixel_fixer_request_too_large` or `pixel_fixer_output_too_large` |
| 422 | `invalid_pixel_fixer_image` |
| 429 | `pixel_fixer_rate_limit_exceeded` |
| 500 | `pixel_fixer_failed` |

Run [`example-scripts/10_pixel_fixer.py`](example-scripts/10_pixel_fixer.py) with an image path for
a complete example. The browser tool at
[retrodiffusion.ai/tools/pixel-art-fixer](https://www.retrodiffusion.ai/tools/pixel-art-fixer)
runs local WASM instead and sends no image-processing request to this API.
