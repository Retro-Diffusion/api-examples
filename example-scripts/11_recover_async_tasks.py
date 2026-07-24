"""Recover async jobs after a lost submission response.

Submitting with "async": true returns a task_id you poll. If that first response
never arrives (edge timeout, disconnect, crash) the job was still accepted and
charged — re-submitting would charge you twice. Instead of guessing, list your
recent jobs with GET /v1/inferences/tasks and pick up where you left off:

    python 11_recover_async_tasks.py
"""

from rd_client import list_tasks, save_images

# 1. Your submission response was lost — you never saw a task_id, but the
#    balance went down. List your most recent jobs (newest first):
recent = list_tasks(limit=5)
for task in recent:
    print(f"  {task['task_id']}  {task['status']:9s}  {task['created_at']}")

if not recent:
    raise SystemExit("No async jobs yet — run 07_async_batch.py first.")

# 2. Identify the lost job (here: the newest one) and poll it by id.
import time

task_id = recent[0]["task_id"]
print(f"\nRecovering task {task_id} ...")
while True:
    task = next(t for t in list_tasks(limit=5) if t["task_id"] == task_id)
    # Equivalent: GET /v1/inferences/tasks/{task_id} directly.
    if task["status"] in ("pending", "running"):
        time.sleep(2)
        continue
    if task["status"] == "succeeded":
        paths = save_images(task["result"], "output_recovered")
        print(f"Saved {paths[0]}")
    else:
        print("failed:", task["error"])
    break

# Tip: `generate(...)` posts the submission; pair it with list_tasks() to make
# retries safe — check whether the previous attempt already created a job
# before sending another one.
