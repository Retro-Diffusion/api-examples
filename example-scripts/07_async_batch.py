"""Generate many images in parallel with async jobs.

Adding "async": true accepts the job immediately and returns a task_id; you poll
GET /v1/inferences/tasks/{task_id} for the result. This lets you fan out several
generations at once instead of waiting for each in turn — ideal for building a
set of assets.

    python 07_async_batch.py
"""
import concurrent.futures

from rd_client import generate_async, save_images

PROMPTS = [
    "A red health potion bottle",
    "A blue mana potion bottle",
    "A green poison flask",
    "A golden elixir vial",
]


def make_one(index_and_prompt: tuple[int, str]) -> str:
    index, prompt = index_and_prompt
    result = generate_async(
        {
            "prompt": prompt,
            "prompt_style": "rd_plus__mc_item",
            "width": 32,
            "height": 32,
            "num_images": 1,
            "remove_bg": True,  # transparent PNGs, ready to drop into a game
        }
    )
    paths = save_images(result, f"output_batch_{index}")
    return paths[0]


# Submit all jobs at once; each polls independently.
with concurrent.futures.ThreadPoolExecutor(max_workers=len(PROMPTS)) as pool:
    for path in pool.map(make_one, enumerate(PROMPTS)):
        print(f"Saved {path}")
