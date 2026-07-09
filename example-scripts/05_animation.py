"""Bring a still pixel-art image to life with Advanced Animations.

Advanced animation styles (rd_advanced_animation__*) animate an uploaded start
frame. They REQUIRE an input_image, work at 32-256px matching that frame, and
return an animated GIF.

Actions: walking, idle, jump, crouch, attack, destroy, custom_action (describe
any motion), subtle_motion (ambient life for scenes). frames_duration accepts
4, 6, 8, 10, 12, or 16.

This script generates a start frame, then animates it. Because animation can
take a little longer, it uses the async submit-and-poll flow.

    python 05_animation.py
"""
from rd_client import generate, generate_async, save_images

# 1. Make a neutral standing character to animate (side profile works best).
print("Generating a start frame...")
frame = generate(
    {
        "prompt": "A knight in armor standing in a neutral pose, side profile facing right, full body, plain background",
        "prompt_style": "rd_plus__low_res",
        "width": 64,
        "height": 64,
        "num_images": 1,
        "seed": 31,
    }
)
save_images(frame, "output_anim_frame")
start_frame_b64 = frame["base64_images"][0]

# 2. Animate it. input_image is required; width/height match the start frame.
print("Animating (walking)...")
walk = generate_async(
    {
        "prompt": "Confident, steady steps",
        "prompt_style": "rd_advanced_animation__walking",
        "width": 64,
        "height": 64,
        "num_images": 1,
        "frames_duration": 8,
        "input_image": start_frame_b64,
    }
)
print(f"Saved {save_images(walk, 'output_anim_walk')}  (an animated GIF)")

# Tip: add "return_spritesheet": True to get a PNG spritesheet instead of a GIF.
