"""Keep a character consistent across images with RD Pro reference images.

RD Pro styles accept up to 9 `reference_images`. Unlike an input_image (which is
redrawn), references guide the style and content WITHOUT being redrawn — perfect
for putting the same character in new scenes, or matching your game's art.

The recipe: generate the character once, then pass that output back as a
reference in follow-up prompts.

    python 04_reference_images.py
"""
import base64

from rd_client import generate, save_images

STYLE = "rd_pro__default"
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
save_images(base, "output_ref_base")
character_b64 = base["base64_images"][0]  # already base64 — reuse directly

# 2. Put that same character into new scenes by passing it as a reference.
for prompt, stem in [
    ("The same goblin merchant sitting by a campfire counting gold coins at night", "output_ref_campfire"),
    ("The same goblin merchant haggling at a bustling medieval market stall", "output_ref_market"),
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
