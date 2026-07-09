"""Generate a game-ready tileset from a prompt.

rd_tile__tileset builds a full "wang"-style tileset (a grid of tiles that connect
seamlessly) from one prompt. Tile size is 16-32px (the width/height is the size
of a single tile). One tileset per request.

rd_tile__tileset_advanced takes two textures — an inside and an outside — via
`prompt`/`extra_prompt` (and optional `input_image`/`extra_input_image`).

    python 06_tileset.py
"""
from rd_client import generate, save_images

# Simple single-prompt tileset.
tileset = generate(
    {
        "prompt": "Grass and dirt path with small stones",
        "prompt_style": "rd_tile__tileset",
        "width": 16,   # tile size, 16-32
        "height": 16,
        "num_images": 1,
        "seed": 12,
    }
)
print(f"Saved {save_images(tileset, 'output_tileset')}")

# Advanced: two textures (inside = stone, outside = grass).
advanced = generate(
    {
        "prompt": "grey stones with gravel and dirt",   # inside texture
        "extra_prompt": "lush green grass",              # outside texture
        "prompt_style": "rd_tile__tileset_advanced",
        "width": 32,
        "height": 32,
        "num_images": 1,
        "seed": 12,
    }
)
print(f"Saved {save_images(advanced, 'output_tileset_advanced')}")
