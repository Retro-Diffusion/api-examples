<p align="center">
  <img src="resources/wordmark.png" style="display: block; margin-left: auto; margin-right: auto; max-width: 50%;" />
</p>

> **ℹ️ Info:**  
> We just migrated to a new server infrastructure!  
> All current workflows should continue to work with the existing endpoint and no changes are needed from you.  
> If you experience any issues, you can temporarily use our legacy endpoint at `https://api.retrodiffusion.ai/v1/inferences/legacy`.


## How to generate images

1. First you need to generate an API Key directly from your [RetroDiffusion account](https://www.retrodiffusion.ai/app/devtools)
2. Make sure you have available credits in your account
   Take in mind that each model supports different styles.
3. Prepare your request, in this example we will use Python and make simple request to generate one image with RD_FAST model and no styles:

```python
import requests

url = "https://api.retrodiffusion.ai/v1/inferences"
method = "POST"

headers = {
    "X-RD-Token": "YOUR_API_KEY",
}

payload = {
    "width": 256,
    "height": 256,
    "prompt": "A really cool corgi",
    "num_images": 1
}

response = requests.request(method, url, headers=headers, json=payload)
print(response.text)
```

5. The response should look like this:

```json
{
  "created_at": 1733425519,
  "credit_cost": 1,
  "base64_images": ["..."],
  "type": "txt2img",
  "remaining_credits": 999
}
```

## Using styles

### RD_FAST

- `RD_FAST` only support one style at a time, and it's passed as a parameter named `prompt_style`:

```python
payload = {
    "width": 256,
    "height": 256,
    "prompt": "A really cool corgi wearing sunglasses and a party hat",
    "num_images": 1,
    "prompt_style": "rd_fast__simple"
}
```

**Default size range is 64x64 <-> 512x512 unless otherwise specified.**
#### Available styles:

- rd_fast__default
- rd_fast__retro
- rd_fast__simple
- rd_fast__detailed
- rd_fast__anime
- rd_fast__game_asset
- rd_fast__portrait
- rd_fast__texture
- rd_fast__ui
- rd_fast__item_sheet
- rd_fast__character_turnaround
- rd_fast__1_bit
- rd_fast__low_res (16x16 <-> 128x128)
- rd_fast__mc_item (16x16 <-> 128x128)
- rd_fast__mc_texture (16x16 <-> 128x128)
- rd_fast__no_style

### RD_PLUS
- `RD_PLUS` supports several styles, and it's passed as a parameter named `prompt_style`:
- `RD_PLUS` is more expensive than `RD_FAST`, please confirm the cost in our [web app](https://www.retrodiffusion.ai) selecting the model and style and settings you want to use.

#### Available styles:
- rd_plus__default
- rd_plus__retro
- rd_plus__watercolor
- rd_plus__textured
- rd_plus__cartoon
- rd_plus__ui_element
- rd_plus__item_sheet
- rd_plus__character_turnaround
- rd_plus__topdown_map
- rd_plus__topdown_asset
- rd_plus__isometric
- rd_plus__isometric_asset
- rd_plus__classic (32x32 <-> 192x192)
- rd_plus__low_res (16x16 <-> 128x128)
- rd_plus__mc_item (16x16 <-> 128x128)
- rd_plus__mc_texture (16x16 <-> 128x128)

## Animations

We support the following animation styles:
- animation__four_angle_walking (48x48 only)
- animation__walking_and_idle (48x48 only)
- animation__vfx (32x32 <-> 96x96, 1:1 aspect ratio)

Some important notes:

- `animation__four_angle_walking` and `animation__walking_and_idle` currently only support 48x48 resolution. (Bigger or smaller resolutions will be ignored and default to 48x48)
- `animation__vfx` supports sizes between 32x32 and 96x96, square aspect ratios only.
- Animations only support generating one image at a time.
- Outputs are transparent GIF images encoded in base64.

Example payload:

> This payload will generate a 48x48 transparent GIF, if you want the spritesheet, look below

```python
{
	"prompt": "corgi wearing a party hat",
	"width": 48,
	"height": 48,
	"num_images": 1,
	"seed": 123,
	"prompt_style": "animation__four_angle_walking"
}
```

Spritesheet output payload:

> Just add the **return_spritesheet** property set to `true`, this will output a transparent PNG with the spritesheet

```python
{
	"prompt": "corgi wearing a party hat",
	"width": 48,
	"height": 48,
	"num_images": 1,
	"seed": 123,
	"prompt_style": "animation__four_angle_walking",
	"return_spritesheet": true
}
```

### Walking and Idle format

The walking and idle animation format is similar to the four angle walking format, but has some changes. Below is an example:

<img src="resources/walk_idle_format.png" style="display: block; margin-left: auto; margin-right: auto; max-width: 50%;" />

### Image reference for animations

You can use the parameter `input_image` in your payload to let the model know what image to use as a reference.
The `input_image` should be a base64 encoded RGB image with no transparency.
In your prompt you can include a brief description of your reference image.

**Don't** include the `data:image/png;base64,` in the base64 image.

```python
{
	"prompt": "robot",
	"width": 48,
	"height": 48,
	"num_images": 1,
	"seed": 1234,
	"prompt_style": "animation__four_angle_walking",
	"return_spritesheet": true,
	"input_image": "iVBORw0KGgoAAAANSUhEUgAAAUA... ... ..."
}
```

## Using img2img

- Just send a **base64** image in the `input_image` parameter and adjust `strength` to your likinng. Strength is a value between 0 and 1 and represents how much the image should be modified.
- No need to include `data:image/png;base64,` in the base64 image.
- Send your image as a base64 string, it should be a RGB image with no transparency.

```python
with Image.open(input_image_path) as img:
    rgb_img = img.convert('RGB')
    buffer = BytesIO()
    rgb_img.save(buffer, format='PNG')
    base64_input_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

payload = {
    "prompt": "A really cool corgi wearing sunglasses and a party hat",
    "width": 256,
    "height": 256,
    "input_image": base64_input_image,
    "strength": 0.8
}
```

## Using a palette for reference

- You can use the `input_palette` parameter to let the model know what palette to use as a reference.
- Just send a **base64** image in the `input_palette` parameter.
- The `input_palette` should be a base64 encoded image with no transparency.
- Keep your palette image small, below 1mb is recommended 200k characters or less.
- No need to include `data:image/png;base64,` in the base64 image.

```python
{
  "prompt": "a raven with a glowing green eye",
  "width": 256,
  "height": 256,
  "num_images": 1,
  "seed": 1234,
  "input_palette": "iVBORw0KGgoAAAANSUhEUgAAAUA... ... ..."
}
```

## Using background removal for transparent images

- Simply `remove_bg` as a boolean

```python
payload = {
    "prompt": "a raven with a glowing green eye",
    "width": 128,
    "height": 128,
    "remove_bg": True
}
```

## Using seamless tiling

- Simply add `tile_x` and `tile_y` both as booleans

```python
payload = {
    "prompt": "Stone bricks",
    "width": 128,
    "height": 128,
    "tile_x": true,
    "tile_y": true
}
```

## Image editing
- You can use the `/v1/edit` endpoint to edit images.
- The request should be a POST request with the following parameters:

```json
{
    "prompt": "add a hat",
    "inputImageBase64": "iVBORw0KGgoAAAANSUhEUgAAAUA...",
}
```

- We support sizes between 32x32 and 256x256
- The cost is 5 credits per image edit
- We have the following response format:

```json
{
  "outputImageBase64": "iVBORw0KGgoAAAANSUhEUgAAAUA...",
  "remaining_credits": 999
}
```

## FAQ

- **How much does it cost?**
  - Cost is calculated based on the model and resolution you choose. You can check the cost of each request in our [web app](https://www.retrodiffusion.ai/)
- **How can I check my remaining credits?**
  - You can make a GET request to the `/v1/inferences/credits` endpoint, with the header `X-RD-Token` set to your API key. The response will include the remaining credits in the following format:

```json
{
  "credits": 999
}
```

- **Can I buy credits from the API?**
  - No, but to ensure you always have enough credits for your requests, you can set up **auto refills** in the [Payment Methods section](https://www.retrodiffusion.ai/app/payment-methods)
- **What happened to RD_CLASSIC?**
  - We just dropped support for RD_CLASSIC
- **What happened to RD_FLUX?**
  - We just renamed RD_FLUX to RD_FAST, so you can use it as before.
- **What happened to the model parameter**
  - `model` is no longer required, as the model is determined by the `prompt_style` parameter.
- **How to get images at native resolution?**
  - You can use the `upscale_output_factor` parameter to get images at native resolution. Set it to 1 for native resolution, or `null` for regular size.
