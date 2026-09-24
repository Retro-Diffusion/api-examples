"""Build a low-poly 3D model, animate it, and export it for a game engine.

Low-Poly turns a prompt and/or up to 4 reference images into a real low-poly 3D
model with pixel-art textures. Jobs take minutes, so every paid call returns a
task_id to poll. Prices depend on the cube size (16-256 texels, or "auto"):
generate $0.25-$3.00, revise $0.20-$1.50, animate $0.15-$1.00 (the first
animation rigs the model for free). Exports are free. Full contract:
../LOW_POLY.md

    RD_API_KEY=... python 13_lowpoly_model.py
    RD_API_KEY=... python 13_lowpoly_model.py "a mossy stone well with a wooden roof"
    RD_API_KEY=... RD_LOWPOLY_ANIMATE="a bouncy idle" python 13_lowpoly_model.py "a small frog"
"""
import os
import sys
import time
import uuid

import requests

from rd_client import API_BASE_URL, get_api_key

LOWPOLY = f"{API_BASE_URL}/lowpoly"
HEADERS = {"X-RD-Token": get_api_key()}
PROMPT = sys.argv[1] if len(sys.argv) > 1 else "a wooden treasure chest with iron bands"
ANIMATION = os.environ.get("RD_LOWPOLY_ANIMATE", "")


def api(method: str, path: str, payload: dict | None = None, *, paid: bool = False) -> dict:
    headers = dict(HEADERS)
    if paid:
        # Persist this key if you retry: the same key never charges twice.
        headers["Idempotency-Key"] = str(uuid.uuid4())
    response = requests.request(method, f"{LOWPOLY}{path}", json=payload, headers=headers, timeout=60)
    if response.status_code >= 400:
        raise SystemExit(f"{method} {path} failed ({response.status_code}): {response.text}")
    return response.json()


def wait(task_id: str) -> dict:
    """Poll a job until it finishes. 3D jobs usually take 1-5 minutes (up to ~15 at 256)."""
    started = time.monotonic()
    while True:
        task = api("GET", f"/tasks/{task_id}")
        if task["status"] == "succeeded":
            return task
        if task["status"] == "failed":
            raise SystemExit(f"job failed (refunded): {task.get('error')}")
        print(f"  {task['status']}… {int(time.monotonic() - started)}s")
        time.sleep(10)


def download(url: str, filename: str) -> None:
    path = f"output_{filename}"
    with open(path, "wb") as f:
        f.write(requests.get(url, timeout=120).content)
    print(f"Saved {path}")


estimate = api("POST", "/estimate", {"operation": "generate", "prompt": PROMPT, "size": "auto"})
print(f"Auto size {estimate['size']}³ costs ${estimate['cost']:.2f}")

job = api("POST", "/generate", {"prompt": PROMPT, "size": "auto", "style": "rd_lowpoly__detailed"}, paid=True)
print(f"Building '{PROMPT}' (task {job['task_id']}, ${job['cost']:.2f})")
asset = wait(job["task_id"])["result"]
version = asset["versions"][-1]
print(f"Model {asset['asset_id']} v{version['number']}: {version['stats']}")
download(version["render_url"], "lowpoly_render.png")

export = api("POST", f"/assets/{asset['asset_id']}/export", {"target": "godot"})
download(export["url"], export["filename"])

if ANIMATION:
    job = api("POST", f"/assets/{asset['asset_id']}/animate", {"prompt": ANIMATION}, paid=True)
    print(f"Animating: {ANIMATION} (task {job['task_id']}, ${job['cost']:.2f})")
    done = wait(job["task_id"])
    name = done["animation"]
    gif = api("POST", f"/assets/{asset['asset_id']}/export", {"target": "gif", "animation": name})
    download(gif["url"], gif["filename"])
