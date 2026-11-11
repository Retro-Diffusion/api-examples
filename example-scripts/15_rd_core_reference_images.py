"""Keep a character consistent across images with RD Core reference images.

RD Core ($0.10/image at any size, about 4x faster than RD Pro) accepts up
to 9 `reference_images`. Unlike an input_image (which is redrawn), references guide
the style and content WITHOUT being redrawn — perfect for putting the same
character in new scenes, or matching your game's art.

The recipe: generate the character once, then pass that output back as a
reference in follow-up prompts. RD Core sizes run 12-512 px per side in any
aspect ratio (e.g. 480x270) and take up to 4 images per request.

    python 15_rd_core_reference_images.py
"""
from rd_client import generate, save_images

STYLE = "rd_core__default"
SIZE = {"width": 128, "height": 128, "num_images": 1}

# 1. Generate the base character.
base = generate(
    {
        "prompt": "A goblin merchant with a huge backpack of trinkets, green skin, red cloak, standing pose",
        "prompt_style": STYLE,
        "seed": 55,
        **SIZE,
    }
)
save_images(base, "output_core_base")
character_b64 = base["base64_images"][0]  # already base64 — reuse directly

# 2. Put that same character into new scenes by passing it as a reference.
for prompt, stem in [
    ("The same goblin merchant sitting by a campfire counting gold coins at night", "output_core_campfire"),
    ("The same goblin merchant haggling at a bustling medieval market stall", "output_core_market"),
]:
    variation = generate(
        {
            "prompt": prompt,
            "prompt_style": STYLE,
            "reference_images": [character_b64],  # up to 9
            **SIZE,
        }
    )
    print(f"Saved {save_images(variation, stem)}")
