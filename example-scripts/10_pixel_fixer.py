"""Restore an enlarged or softened image to its native pixel grid.

Usage:
    export RD_API_KEY="rdpk-..."
    python 10_pixel_fixer.py path/to/image.png
    python 10_pixel_fixer.py path/to/image.jpg --engine neural --width 32 --height 32

The neural endpoint accepts optional target width and height values.
"""

import argparse
from pathlib import Path

from rd_client import fix_pixel_art, image_to_base64, save_images


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="PNG or JPEG image to fix")
    parser.add_argument(
        "--engine",
        choices=("standard", "neural"),
        default="standard",
        help="Pixel Fixer engine (default: standard)",
    )
    parser.add_argument("--width", type=int, help="Neural target width")
    parser.add_argument("--height", type=int, help="Neural target height")
    parser.add_argument("--output", default="pixel_fixer_output", help="Output path without extension")
    args = parser.parse_args()
    if args.engine == "standard" and (args.width is not None or args.height is not None):
        parser.error("--width and --height are accepted only with --engine neural")
    return args


def main() -> None:
    args = parse_args()
    result = fix_pixel_art(
        image_to_base64(args.image),
        engine=args.engine,
        width=args.width,
        height=args.height,
    )
    written = save_images(result, args.output)
    if len(written) != 1:
        raise RuntimeError("Pixel Fixer returned an unexpected number of images")
    print(f"Saved {written[0]}")


if __name__ == "__main__":
    main()
