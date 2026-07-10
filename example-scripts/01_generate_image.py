"""Generate a single pixel-art image from a text prompt.

The simplest possible request: a prompt, a style, a size, and how many images.
Prompts describe the SUBJECT only — never write "pixel art"; the styling comes
from prompt_style.

    python 01_generate_image.py
"""
from rd_client import generate, save_images

result = generate(
    {
        "prompt": "A cozy wizard's tower on a hill at sunset, warm window light",
        "prompt_style": "rd_plus__default",  # see 08_list_styles.py for all ids
        "width": 256,
        "height": 256,
        "num_images": 1,
        "seed": 42,  # optional — omit for a random result each run
    }
)

paths = save_images(result, "output_generate")
print(f"Saved {paths}")
print(f"Cost: ${result['balance_cost']}   Remaining balance: ${result['remaining_balance']}")
