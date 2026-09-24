# Low-Poly 3D models

Low-Poly builds real low-poly 3D models with hand-painted pixel-art textures from a
prompt, up to 4 reference images, or both. Every texture pixel is the same size on
every face, so models look like pixel art from any angle. You can revise a model,
animate it, and export it for your engine or modeling tool.

Base URL: `https://api.retrodiffusion.ai/v2/lowpoly` (also `/v1/lowpoly`). Authenticate
with the `X-RD-Token` header, like every other endpoint.

Runnable client: [`example-scripts/13_lowpoly_model.py`](example-scripts/13_lowpoly_model.py).

## Sizes and prices

A model's size is its largest dimension in texels. Pick a size or send `"auto"`:
auto reads the prompt and picks the size that fits the object (a coin is small, a
castle is large). Requests with only reference images default to 64.

| Size | Typical subject | Generate | Revise | Animate |
| --- | --- | --- | --- | --- |
| 16 | small item: coin, potion, key | $0.25 | $0.20 | $0.15 |
| 32 | prop or handheld: sword, chair, chest | $0.50 | $0.35 | $0.25 |
| 64 | character, creature or vehicle | $0.85 | $0.65 | $0.35 |
| 128 | building or large vehicle | $1.20 | $0.90 | $0.50 |
| 256 | landmark or scene | $3.00 | $1.50 | $1.00 |

Rigging is free: it happens automatically with a model's first animation. Size
suggestions, estimates, reads and exports are free. A failed job is refunded
automatically. `GET /lowpoly/pricing` returns this table, the styles, the limits and
the export targets as JSON.

## Styles and modes

- `rd_lowpoly__detailed` (default): free-form low-poly shapes (boxes, cylinders,
  spheres, extrusions).
- `rd_lowpoly__blocky`: boxes only, like a Minecraft model. Best for Blockbench and
  Minecraft exports.

The style list can grow; `GET /lowpoly/pricing` returns the current styles (`id`, `name`,
`description`, `appearance`). Sending a Low-Poly style to `/inferences` returns
`400 lowpoly_style_not_supported`.

`mode` is `quality` (default) or `fast` (about 3x quicker, simpler shapes). Both cost
the same.

## Jobs take minutes

Generate, revise and animate are asynchronous. Each returns `202 Accepted` with a
`task_id` and the model's `asset_id`; poll `GET /lowpoly/tasks/{task_id}` every 10-20
seconds. Jobs usually take 1-5 minutes and can take up to 15 at size 256. Send an
`Idempotency-Key` header (or `custom_id` in the body) on paid calls so a retried
request returns the same job instead of charging again. A model runs one job at a
time, and an account runs a few at once (`429 lowpoly_too_many_jobs` otherwise).

```text
POST /lowpoly/generate          {prompt?, size?, style?, mode?, reference_images?, custom_id?}
POST /lowpoly/assets/{id}/revise   {prompt, version?, mode?, reference_images?, custom_id?}
POST /lowpoly/assets/{id}/animate  {prompt, version?, mode?, animation?, custom_id?}
GET  /lowpoly/tasks/{task_id}   -> {status: pending|running|succeeded|failed, result?, animation?, error?}
```

Prompts are at most 250 characters. `reference_images` are base64 PNG, JPEG or WEBP
(data URIs are fine), at most 4 and 8 MB each; several views of the same object
work best.

## Versions and animations

A model starts at version 1. Each revision saves a new version, and you can revise
or animate any version (`version`, default the newest). Animations attach to the
version they were made on and never create a version.

To change an existing animation instead of adding one, send its name as `animation`
with a prompt describing the change (`{"prompt": "slower, with a bigger hop",
"animation": "hop"}`). It is updated in place, keeps its name, and costs the same
as a new animation. An unknown name returns `404 lowpoly_animation_not_found`. A succeeded task's `result`
is the model:

```json
{
  "asset_id": "5b0c...",
  "status": "ready",
  "prompt": "a wooden treasure chest with iron bands",
  "style": "rd_lowpoly__detailed",
  "size": 32,
  "size_source": "auto",
  "versions": [
    {
      "number": 1,
      "kind": "generate",
      "render_url": "https://.../render.png",
      "turntable_url": "https://.../turntable.png",
      "scene_url": "https://.../scene.json",
      "animations": ["idle"],
      "rigged": true,
      "stats": {"size_px": [30.0, 24.0, 22.0], "triangles": 412}
    }
  ]
}
```

`GET /lowpoly/assets` lists your models (newest first, `limit`, `before_id`) and
`GET /lowpoly/assets/{id}` returns one. `scene_url` is the payload for Retro
Diffusion's interactive web viewer; use exports for your own tools.

## Exports

`POST /lowpoly/assets/{id}/export {target, version?, animation?}` returns a hosted
download URL. Exports are built on first request and reused after that.

| target | File |
| --- | --- |
| `godot`, `unity`, `unreal`, `web`, `blender` | `.glb` (glTF 2.0, one node per part, nearest-filtered atlas) |
| `blockbench` | `.bbmodel` Blockbench project |
| `obj` | zip of `.obj` + `.mtl` + atlas `.png` |
| `minecraft` | Java resource-pack zip (box parts only; best with the blocky style) |
| `atlas` | texture atlas `.png` |
| `turntable` | 8-view turntable sprite sheet `.png` |
| `gif`, `sheet` | an animation as a GIF or sprite sheet (needs `animation`) |

## Errors

Low-Poly errors use the standard `{"error": {"code", "message", "request_id"}}` shape.
The ones you will see most:

| Status | Code | Meaning |
| --- | --- | --- |
| 400 | `lowpoly_prompt_required` | Send a prompt, reference images, or both |
| 400 | `lowpoly_invalid_reference_image` | A reference image is not a readable PNG/JPEG/WEBP |
| 400 | `not_enough_balance` | Top up, or wait for your running jobs to finish |
| 404 | `lowpoly_asset_not_found` | Unknown `asset_id` (or not yours) |
| 409 | `lowpoly_asset_busy` | The model already has a job running |
| 429 | `lowpoly_too_many_jobs` | Too many 3D jobs at once; retry when one finishes |
| task | `lowpoly_generate_failed` / `lowpoly_revise_failed` / `lowpoly_animate_failed` | The job failed and was refunded |
| task | `lowpoly_timeout` | The job ran too long and was refunded |
