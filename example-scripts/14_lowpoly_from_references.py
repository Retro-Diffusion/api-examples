"""Turn reference photos into a blocky low-poly model, revise it, and export it for Blockbench and Minecraft.

Reference images (up to 4, several views of the same object work best) can replace the
prompt or add to it. The blocky style builds only from rectangular boxes (tilted where
the design needs it, like a windshield), which maps 1:1 onto Blockbench and Minecraft.
Full contract: ../LOW_POLY.md

    RD_API_KEY=... python 14_lowpoly_from_references.py front.png side.png
    RD_API_KEY=... python 14_lowpoly_from_references.py car.jpg --prompt "a red sports car" --revise "add a roof rack"
"""
import argparse
import base64
import time
import uuid
from pathlib import Path

import requests

from rd_client import API_BASE_URL, get_api_key

LOWPOLY = f"{API_BASE_URL}/lowpoly"


def api(method: str, path: str, payload: dict | None = None, *, paid: bool = False) -> dict:
    headers = {"X-RD-Token": get_api_key()}
    if paid:
        headers["Idempotency-Key"] = str(uuid.uuid4())  # persist it if you retry: the same key never charges twice
    response = requests.request(method, f"{LOWPOLY}{path}", json=payload, headers=headers, timeout=60)
    if response.status_code >= 400:
        raise SystemExit(f"{method} {path} failed ({response.status_code}): {response.text}")
    return response.json()


def wait(task_id: str) -> dict:
    """3D jobs take minutes: poll every 10-20 seconds."""
    started = time.monotonic()
    while True:
        task = api("GET", f"/tasks/{task_id}")
        if task["status"] == "succeeded":
            return task
        if task["status"] == "failed":
            raise SystemExit(f"job failed (refunded): {task.get('error')}")
        print(f"  {task['status']}… {int(time.monotonic() - started)}s")
        time.sleep(15)


def download(url: str, filename: str) -> None:
    Path(filename).write_bytes(requests.get(url, timeout=120).content)
    print(f"Saved {filename}")


def data_uri(path: str) -> str:
    kind = {".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}.get(Path(path).suffix.lower(), "png")
    return f"data:image/{kind};base64," + base64.b64encode(Path(path).read_bytes()).decode()


parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("images", nargs="+", help="1-4 reference images (PNG, JPEG or WEBP, up to 8 MB each)")
parser.add_argument("--prompt", default="", help="optional: what it is, or what to change about the references")
parser.add_argument("--size", default="64", help='16, 32, 64, 128, 256 or "auto" (image-only requests default to 64)')
parser.add_argument("--revise", default="", help="optional: a change to make after the first version")
args = parser.parse_args()

request = {
    "reference_images": [data_uri(p) for p in args.images[:4]],
    "size": args.size if args.size == "auto" else int(args.size),
    "style": "rd_lowpoly__blocky",
}
if args.prompt:
    request["prompt"] = args.prompt

job = api("POST", "/generate", request, paid=True)
print(f"Building from {len(request['reference_images'])} reference image(s): {job['size']}³, ${job['cost']:.2f}")
asset = wait(job["task_id"])["result"]
asset_id = asset["asset_id"]
download(asset["versions"][-1]["turntable_url"], "output_turntable_v1.png")

if args.revise:
    # Revisions save a new version; the earlier one stays available (send "version" to use it).
    job = api("POST", f"/assets/{asset_id}/revise", {"prompt": args.revise}, paid=True)
    print(f"Revising: {args.revise} (${job['cost']:.2f})")
    asset = wait(job["task_id"])["result"]
    download(asset["versions"][-1]["turntable_url"], f"output_turntable_v{len(asset['versions'])}.png")

# Exports are free and cached, so asking again for the same target is instant.
for target in ("blockbench", "minecraft"):
    export = api("POST", f"/assets/{asset_id}/export", {"target": target})
    download(export["url"], export["filename"])
