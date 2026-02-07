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

## Check credit cost before generating

You can check how much a request will cost before actually generating images by adding the `check_cost` parameter set to `true`:

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
    "num_images": 1,
    "check_cost": true
}

response = requests.request(method, url, headers=headers, json=payload)
print(response.text)
```

The response will show the credit cost without generating any images:

```json
{
  "created_at": 1761299395,
  "credit_cost": 1,
  "output_images": [],
  "base64_images": [],
  "output_urls": [],
  "model": "check_cost",
  "remaining_credits": 0
}
```

Note: When using `check_cost`, the `remaining_credits` will always be `0` and no images will be generated.

## Using styles

### RD_PRO
- `RD_PRO` is our newest and most advanced model, it supports several styles, and it's passed as a parameter named `prompt_style`.

#### Available styles:
- rd_pro__default	`Clean modern pixel art style model that allows multiple reference images and extremely detailed prompting.`
- rd_pro__painterly	`Almost brush-like style with minimal outlines or anti-aliasing. Clean vibrant color palettes and beautiful details`
- rd_pro__fantasy	`Bright colors, soft transitions, detailed textures, light dithering, and outlines.`
- rd_pro__ui_panel	`Consistent arrangements of UI elements, split into buttons, sliders, panels, and knobs.`
- rd_pro__horror	`Dark, gritty style with chaotic details and harsh shapes and shading.`
- rd_pro__scifi	`High contrast with glowing details, clean outlines, and beautiful lighting.`
- rd_pro__simple	`Simple pixel art with minimal shading or texturing, but strong outlines and shapes.`
- rd_pro__isometric	`Pixel art rotated at a 45 degree angle. Clean lines and shapes.`
- rd_pro__topdown	`Pixel art viewed from a 2/3 downwards angle, with simple shapes and shading.`
- rd_pro__platformer	`Side-scroller style platformer perspective, with modern styling and outlines.`
- rd_pro__dungeon_map	`Dungeon-crawler style game levels with connected rooms filled with objects and enemies.`
- rd_pro__edit	`Upload an image and describe the changes you want. You can use up to 9 references.`
- rd_pro__pixelate	`Convert input images into pixel art.`
- rd_pro__spritesheet	`Collections of assets on a simple background with the same style.`
- rd_pro__typography	`Generate logos, buttons, or any other element using text as the central focus.`
- rd_pro__hexagonal_tiles	`Small collection of hexagonal tiles for game maps.`
- rd_pro__fps_weapon	`First person perspective weapons, items, and objects.`
- rd_pro__inventory_items	`Creates a spritesheet of grid aligned inventory items (like for Diablo or Path of Exile)`

#### Using reference images with RD_PRO
- You can use up to 9 reference images with RD_PRO by passing base64 encoded images in the `reference_images` parameter.

```json
{
	"width": 256,
	"height": 256,
	"prompt": "corgi",
	"num_images": 1,
	"prompt_style": "rd_pro__default",
	"check_cost": false,
	"reference_images": [
		"iVBORw0KGgoAAA..."
	]
}
```

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

**Default size range is 64x64 <-> 384x384 unless otherwise specified.**
#### Available styles:

- rd_fast__default	`Simple clean pixel art, with Anime illustration influences`
- rd_fast__retro	`A classic arcade game aesthetic inspired by early PC games`
- rd_fast__simple	`Simple shading with minimalist shapes and designs`
- rd_fast__detailed	`Pixel art with lots of shading and details`
- rd_fast__anime	`Simple clean pixel art, with Anime illustration influences`
- rd_fast__game_asset	`Distinct assets set on a simple background`
- rd_fast__portrait	`Character portrait focused images with high detail`
- rd_fast__texture	`Flat game textures like stones, bricks, or wood`
- rd_fast__ui	`User interface boxes and buttons`
- rd_fast__item_sheet	`Sheets of objects placed on a simple background`
- rd_fast__character_turnaround	`Character sprites viewed from different angles`
- rd_fast__1_bit	`Two color black and white only images`
- rd_fast__low_res	`(16x16 <-> 128x128)	General low resolution pixel art images`
- rd_fast__mc_item	`(16x16 <-> 128x128)	Minecraft-styled items with automatic transparency`
- rd_fast__mc_texture	`(16x16 <-> 128x128)	Minecraft-styled flat textures, like grass, stones, or wood`
- rd_fast__no_style	`Pixel art with no style influence applied`

### RD_PLUS
- `RD_PLUS` supports several styles, and it's passed as a parameter named `prompt_style`:
- `RD_PLUS` is more expensive than `RD_FAST`, please confirm the cost in our [web app](https://www.retrodiffusion.ai) selecting the model and style and settings you want to use.

#### Available styles:
- rd_plus__default	`Clean pixel art style with bold colors and outlines`
- rd_plus__retro	`Classic pixel art style inspired by PC98 games`
- rd_plus__watercolor	`Pixel art mixed with a watercolor painting aesthetic`
- rd_plus__textured	`Semi-realistic pixel art style with lots of shading and texture`
- rd_plus__cartoon	`Simple shapes and shading, with bold outlines`
- rd_plus__ui_element	`User interface boxes and buttons`
- rd_plus__item_sheet	`Sheets of objects placed on a simple background`
- rd_plus__character_turnaround	`Character sprites viewed from different angles`
- rd_plus__environment `One-point perspective scenes with outlines and strong shapes`
- rd_plus__topdown_map	`Video game map style pixel art with a 3/4 top down perspective`
- rd_plus__topdown_asset	`3/4 top down perspective game assets on a simple background`
- rd_plus__isometric	`45 degree isometric perspective, with consistent outlines`
- rd_plus__isometric_asset	`45 degree isometric objects or assets, on a neutral background`
- rd_plus__classic	`(32x32 <-> 192x192)	Strongly outlined medium-resolution pixel art with a focus on simple shading and clear design`
- rd_plus__low_res	`(16x16 <-> 128x128)	High quality, low resolution pixel art assets and backgrounds`
- rd_plus__mc_item	`(16x16 <-> 128x128)	High quality Minecraft-styled items and game assets`
- rd_plus__mc_texture	`(16x16 <-> 128x128)	Detailed Minecraft-style flat block textures, with enhanced prompt following`
- rd_plus__topdown_item	`(16x16 <-> 128x128)	Top-down view of items and objects, with a simple background`
- rd_plus__skill_icon  `(16x16 <-> 128x128)	Icons for skills, abilities, or spells`

### User Created Styles

- You can use your own custom created styles (or the ones you imported from other users) by passing their ID in the `prompt_style` parameter.
- You can find your style IDs (and generate sample code for different languages) by clicking the **Show API Code** button located at the top left corner of the canvas in the web app.

```python
import requests

url = "https://api.retrodiffusion.ai/v1/inferences"
method = "POST"

headers = {
    "X-RD-Token": "YOUR_API_KEY",
}

payload = {
    "prompt": "life and mana flasks",
    "width": 256,
    "height": 256,
    "num_images": 4,
    "seed": 1105683575,
    "prompt_style": "user__flasks_586",
    "tile_x": False,
    "tile_y": False,
    "remove_bg": True
}

response = requests.request(method, url, headers=headers, json=payload)
print(response.text)
```

## Animations

We support the following animation styles:
- rd_animation__any_animation	`(64x64 only)	Describe an animation and bring pixel art to life`
- rd_animation__8_dir_rotation	`(80x80 only)	 Create 8 direction rotations of anything`
- rd_animation__four_angle_walking	`(48x48 only)	Consistent 4 direction, 4 frame long walking animations of humanoid characters`
- rd_animation__walking_and_idle	`(48x48 only)	Consistent 4 direction walking and idle animations of humanoid characters`
- rd_animation__small_sprites `(32x32 only)	Consistent 4 direction walking, arm movement, looking, surprised, and laying down animations`
- rd_animation__battle_sprites `(48x48 only)	Characters with walking, jumping, attacking, and idle animations`
- rd_animation__vfx	`(24x24 <-> 96x96, 1:1 aspect ratio)	Eye-catching animations for fire, explosions, lightning, or other simple effects`
- rd_animation__any_animation  `(64x64 only)	General purpose custom animation sheets with optional first frame input`

Some important notes:

- `animation__four_angle_walking` and `animation__walking_and_idle` currently only support 48x48 resolution. (Bigger or smaller resolutions will be ignored and default to 48x48)
- `animation__small_sprites` only supports 32x32 resolution.
- `animation__vfx` supports sizes between 24x24 and 96x96, square aspect ratios only.
- Animations only support generating one image at a time.
- Outputs are transparent GIF images encoded in base64.
bypass_prompt_expansion
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

<img width="896" height="1024" alt="Idle_example" src="https://github.com/user-attachments/assets/b38c0770-5e41-4066-89e2-c0e226f984f9" />

### Small sprites format

The small sprites animation sheets are broken down like the example below:

<img width="768" height="768" alt="Small_example" src="https://github.com/user-attachments/assets/07e9c827-7495-4a7e-9d6a-a104c777126e" />

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

### Tips for using any_animation

Due to `animation__any_animation`'s open-ended nature, its a good idea to include a detailed prompt about the content and action in the sequence.
It can also be used for more general sprite sheet objectives, like creating variations of character portraits, sprite sheets of items, and many more creative uses.

Use a 64x64 input image to get near perfect subject adherence.

## Tilesets
<img src="resources/tileset.png" style="display: block; margin-left: auto; margin-right: auto; max-width: 50%;" />

### All tileset styles
- rd_tile__tileset `(16x16 <-> 32x32)	Create full tilesets from a simple prompt describing the textures or environment, using a simple set of "wang" style combinations`
- rd_tile__tileset_advanced `(16x16 <-> 32x32)	Full tilesets from two prompts and/or textures, using a simple set of "wang" style combinations`
- rd_tile__single_tile `(16x16 <-> 64x64)	Detailed single tile texture for creating full tilesets or surfaces`
- rd_tile__tile_variation `(16x16 <-> 128x128)	Texture variations of the provided tile image`
- rd_tile__tile_object `(16x16 <-> 96x96)	Small assets for placing on sections of tiles`
- rd_tile__scene_object `(64x64 <-> 384x384) Large assets for placing on tileset maps`

### Full tilesets
- You can generate full tilesets using the following styles:
  - rd_tile__tileset
  - rd_tile__tileset_advanced

- `rd_tile__tileset` supports an inspiration image via the `input_image` parameter
- `rd_tile__tileset_advanced` supports inside and outside textures via the `input_image` and `extra_input_image` parameters. Advanced tilesets require the inside texture description in the `prompt` parameter and the outside texture description in the `extra_prompt` parameter.
- The `width` and `height` parameters specify the size of each tile in the tileset. Values can range between 16 and 32.

Advanced tileset example payload:

```python
{
  "width": 32,
  "height": 32,
  "prompt": "grey stones with gravel and dirt",
  "extra_prompt": "lush green grass",
  "num_images": 1,
  "prompt_style": "rd_tile__tileset_advanced",
  "seed": 123,
  "input_image": "iVBORw0KGgoAAAANSUhEUgAAAUA... ... ...",
  "extra_input_image": "iVBORw0KGgoAAAANSUhEUgAAAUA... ... ..."
}
```
### Tileset format:
<img src="https://github.com/user-attachments/assets/ada60887-e11d-479f-83fe-9f888b0bbf25" style="display: block; margin-left: auto; margin-right: auto; max-width: 50%;" />

### Single tiles
<img src="resources/single_tile.png" style="display: block; margin-left: auto; margin-right: auto; max-width: 50%;" />

- You can generate single tiles using the `rd_tile__single_tile` style.
- The `width` and `height` parameters specify the size of the tile and can range between 16 and 64.

Example:

```python
{
  "width": 32,
  "height": 32,
  "prompt": "volcanic rock with cracks",
  "num_images": 1,
  "prompt_style": "rd_tile__single_tile"
}
```

### Tile variation
- You can generate variations of a tile using the `rd_tile__tile_variation` style.
- The `input_image` parameter is **required** and should be a base64 encoded image of the tile you want to create variations from.
- Use the `prompt` parameter to describe the changes you want to see in the variations.

Example:

```python
{
  "width": 32,
  "height": 32,
  "prompt": "add moss and cracks",
  "num_images": 1,
  "prompt_style": "rd_tile__tile_variation",
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

- Optionally, you can also receive the original image before palette is applied by setting `return_pre_palette` to `true`:

```python
{
  "prompt": "a raven with a glowing green eye",
  "width": 256,
  "height": 256,
  "num_images": 1,
  "seed": 1234,
  "input_palette": "iVBORw0KGgoAAAANSUhEUgAAAUA... ... ...",
  "return_pre_palette": true
}
```

When `return_pre_palette` is enabled, the response will include an additional string in the `base64_images` array, which is the original image before the palette is applied.

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

- Optionally, you can also receive the original image before background removal by setting `return_non_bg_removed` to `true`:

```python
payload = {
    "prompt": "a raven with a glowing green eye",
    "width": 128,
    "height": 128,
    "remove_bg": True,
    "return_non_bg_removed": True
}
```

When `return_non_bg_removed` is enabled, the response will include an additional string in the `base64_images` array, which is the original image before background removal.

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

## Ignoring prompt expansion
- You can use the `bypass_prompt_expansion` parameter to disable prompt expansion for your request.
```python
payload = {
    "prompt": "a raven with a glowing green eye",
    "width": 128,
    "height": 128,
    "bypass_prompt_expansion": True
}
```

## Image editing
![Progressive editing](https://github.com/user-attachments/assets/c787cd05-b464-4a66-a3e8-423aadf1ee1f)

- You can use the `https://api.retrodiffusion.ai/v1/edit` endpoint to edit images.
- The request should be a POST request with the following parameters:

```json
{
    "prompt": "add a hat",
    "inputImageBase64": "iVBORw0KGgoAAAANSUhEUgAAAUA...",
}
```

- We support sizes between 16x16 and 256x256
- You can send any image within the size limits to be edited
- Progressive editing is possible by sending the response you get from one task as the input for a new task
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
    These formulas can be used as a guide for automated cost calculations:
    **Standard image model pricing**
    All costs are rounded to three decimal places.
	`rd_fast` styles:

	Balance cost = `max(0.015, ((width * height) + 100000) / 6000000) * number of images`
	
	`rd_plus` styles:

	Balance cost = `max(0.025, ((width * height) + 50000) / 2000000) * number of images`
	
	**Low resolution model pricing**
	`rd_plus__mc_texture`, `rd_plus__mc_item`, `rd_plus__low_res`, `rd_plus__classic`, `rd_plus__topdown_item`, `rd_plus__skill_icon`, `rd_tile__tile_variation`, `rd_tile__single_tile`, `rd_tile__tile_object`:

	Balance cost = `max(0.02, ((width * height) + 13700) / 600000) * number of images`

	`rd_pro` styles:

	Balance cost = `0.22 * number of images`

	**Editing class styles**
	`rd_pro__pixelate`

	Balance cost = `0.25 * number of images`
	
	**Unique model pricing:**
	`animation__four_angle_walking`, `animation__walking_and_idle`, `animation__small_sprites`, `animation__vfx`:

	Balance cost = `0.07`

	`rd_tile__tileset`, `rd_tile__tileset_advanced`:

	Balance cost = `0.10`

	`animation__any_animation`, `animation__8_dir_rotation`:

	Balance cost = `0.25`



	
- **How can I check my remaining credits?**
  - You can make a GET request to the `https://api.retrodiffusion.ai/v1/inferences/credits` endpoint, with the header `X-RD-Token` set to your API key. The response will include the remaining credits in the following format:

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
