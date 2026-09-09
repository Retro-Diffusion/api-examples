"""Drive an assistant session end to end (beta).

Describe what you want in plain language; the assistant proposes a priced
plan, waits for your approval, generates, and reports back. Messages cost a
flat $0.01 (refunded automatically if the turn fails); decisions are free;
approved plans bill each generation at standard API rates. Full contract:
../ASSISTANT.md

    RD_API_KEY=... python 12_assistant_session.py
    RD_API_KEY=... python 12_assistant_session.py "A 16x16 potion bottle set"
    RD_API_KEY=... RD_AUTO_APPROVE=1.0 python 12_assistant_session.py   # no approval prompt
"""
import os
import sys
import time

import requests

from rd_client import get_api_key

ASSISTANT_BASE_URL = os.environ.get(
    "RD_ASSISTANT_BASE_URL",
    "https://api.retrodiffusion.ai/v1",
)
ASSISTANT = f"{ASSISTANT_BASE_URL}/assistant"
HEADERS = {"X-RD-Token": get_api_key()}
MESSAGE = sys.argv[1] if len(sys.argv) > 1 else (
    "Make me a 32x32 slime enemy sprite, then give it a bounce animation."
)


def api(method: str, path: str, payload: dict | None = None) -> dict:
    response = requests.request(
        method, f"{ASSISTANT}{path}", json=payload, headers=HEADERS, timeout=60
    )
    if response.status_code == 410:
        raise SystemExit("session expired (5 min idle) — run again to start fresh")
    response.raise_for_status()
    return response.json()


def poll_turn(session_id: str, turn_id: str) -> dict:
    """Poll a turn, printing each new event once, until it settles."""
    shown = 0
    while True:
        turn = api("GET", f"/sessions/{session_id}/turns/{turn_id}")
        for event in (turn.get("events") or [])[shown:]:
            shown += 1
            kind = event["type"]
            if kind == "message":
                print(f"assistant: {event['text']}")
            elif kind == "status" and event.get("text"):
                print(f"  … {event['text']}")
            elif kind == "plan":
                plan = event["plan"]
                print(f"\nPROPOSED PLAN — {plan['summary']}  (total ${plan['total']})")
                for step in plan["steps"]:
                    print(f"  [{step['model']}] {step['title']} · {step['detail']} · ${step['cost']}")
            elif kind == "plan_status":
                print(f"  plan: {event['status']}")
            elif kind == "image":
                print(f"  output {event['ref']} ({event['format']}): {event['url']}")
            elif kind == "note":
                print(f"  check: {event['answer'][:120]}")
            elif kind == "error":
                print(f"  ERROR: {event['message']}")
        if turn["status"] not in ("thinking", "executing"):
            return turn
        time.sleep(2)


settings = {}
auto_approve = os.environ.get("RD_AUTO_APPROVE")
if auto_approve:
    settings = {"settings": {"auto_approve_budget_usd": float(auto_approve)}}

session = api("POST", "/sessions", settings)
print(f"session {session['id']} (expires_at {session.get('expires_at')})\n")
print(f"you: {MESSAGE}")

accepted = api("POST", f"/sessions/{session['id']}/messages", {"message": MESSAGE})
print(f"  (charged ${accepted['charged_usd']}, balance ${accepted.get('remaining_balance')})")
turn = poll_turn(session["id"], accepted["turn_id"])

while turn["status"] == "awaiting_approval":
    answer = input("\napprove this plan? [y/N/feedback]: ").strip()
    if answer.lower() == "y":
        decision = {"decision": "approve"}
    elif answer:
        decision = {"decision": "deny", "feedback": answer}
    else:
        decision = {"decision": "deny"}
    accepted = api("POST", f"/sessions/{session['id']}/decision", decision)
    turn = poll_turn(session["id"], accepted["turn_id"])
    if decision["decision"] == "deny" and "feedback" not in decision:
        break

final = api("GET", f"/sessions/{session['id']}")
print(f"\nsession spend: ${final['spent_usd']} across {final['message_count']} message(s)")
print("images stay in the account history; event URLs are permanent.")
