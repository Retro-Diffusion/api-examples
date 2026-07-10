"""Transform an existing image with a prompt (img2img).

Pass a base64 image in `input_image` plus a `strength` (0-1): low = a subtle
restyle that stays close to the input, high = loose inspiration.

Notes:
- input_image must be raw base64 with NO "data:image/png;base64," prefix.
- RGB without transparency works best.
- Do NOT send a "model" field — the model is inferred from prompt_style.

    python 03_img2img.py path/to/input.png
"""
import sys

from rd_client import generate, image_to_base64, save_images

input_path = sys.argv[1] if len(sys.argv) > 1 else "../input.png"

result = generate(
    {
        "prompt": "The same scene, now in deep winter with snow and a frozen lake",
        "prompt_style": "rd_plus__default",
        "width": 256,
        "height": 256,
        "num_images": 1,
        "input_image": image_to_base64(input_path),
        "strength": 0.8,  # 0 = barely change it, 1 = only loosely inspired by it
    }
)

print(f"Saved {save_images(result, 'output_img2img')}")
