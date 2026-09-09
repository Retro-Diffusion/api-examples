# Assistant sessions (beta)

The assistant API is a conversation, not a one-shot tool: you describe what
you want in plain language, the assistant works out the best model, style,
size, and settings, proposes a **plan with an exact price**, and — once you
approve it — generates everything, checks the results, and reports back
honestly. It handles multi-step work on its own: base sprite then animation,
sets of items, variants of one image, edits chained onto earlier outputs.

It is the same assistant that powers the chat widget on
[retrodiffusion.ai](https://www.retrodiffusion.ai), exposed for programs.

Auth is the usual API key header on every request:

```http
X-RD-Token: YOUR_API_KEY
```

Base URL: `https://api.retrodiffusion.ai/v1/assistant`

Same host, same key, same conventions as the rest of the `/v1` API; every
path in this guide is relative to the base above.

## The loop at a glance

```
POST /sessions                        create a session
POST /sessions/{id}/messages          say what you want      -> 202 {turn_id}
GET  /sessions/{id}/turns/{turn_id}   poll the turn's events
POST /sessions/{id}/decision          approve or deny the proposed plan
GET  /sessions/{id}                   session state, image bank, pending plan
POST /sessions/{id}/keepalive         keep an idle session alive
GET  /sessions/{id}/turns             recent turns (newest first)
DELETE /sessions/{id}                 end the session
```

Nothing generates and nothing beyond the flat message fee is charged until
you approve a plan (or opt in to auto-approval, below).

## Pricing

- **Messages: $0.01 each**, charged when the message is accepted. If the
  turn fails for any reason, the fee is refunded automatically.
- **Decisions are free** — approving, denying, and denying with feedback
  cost nothing.
- **Generations and edits bill at standard API rates** when an approved plan
  executes — exactly what `/v1/inferences` and `/v1/edit/tools` would
  charge, shown per step on the plan before you approve. Failed steps are
  refunded automatically.

There is no message cap; the standard per-key rate limits apply
(30 messages+decisions/min, 60 keepalives/min).

## Sessions

A session is a short-lived working context: the conversation, an image bank
of everything uploaded or generated (referenced as `img_1`, `img_2`, …), and
at most one pending plan. It expires after **5 minutes idle** — any
authenticated call on the session refreshes the clock, and
`POST .../keepalive` exists purely as a cheap ping (send one every couple of
minutes if the human went to lunch). An expired session returns
**410 Gone**; start a new one. Generated results are never lost to expiry —
every generation is saved to the account's history and `/v1/inferences`
activity like any other API call, and output URLs in events are permanent
hosted URLs.

Create with optional settings:

```json
POST /v1/assistant/sessions
{"settings": {"auto_approve_budget_usd": 1.0}}
```

`auto_approve_budget_usd` (0–1000, off by default): plans totalling at or
under the budget execute immediately without the approval round-trip — the
plan still appears in the turn's events (with `plan_status:
"auto_approved"`) so nothing is hidden, and the budget is a hard per-plan
ceiling. This is the setting that makes fully unattended automation work.

## Sending messages

```json
POST /v1/assistant/sessions/{id}/messages
{"message": "Make me a 32x32 knight sprite, then give it an idle animation"}
```

Returns **202** immediately:

```json
{"session_id": "ases_...", "turn_id": "turn_...", "status": "thinking",
 "charged_usd": 0.01, "remaining_balance": 12.49}
```

Optional fields:

- `images`: up to 4 attachments as `data:image/png;base64,...` or
  `data:image/gif;base64,...` URLs (≤ 2 MB each). The assistant looks at
  them, stores them in the bank, and can use them as inputs or references.
- `supersede: true` — required to send a message while a plan is awaiting a
  decision; the pending plan is discarded ("superseded") and the new
  message proceeds. Without it you get **409**.

One turn runs at a time per session; sending while a turn is live returns
**409** — poll it first.

## Polling a turn

`GET /v1/assistant/sessions/{id}/turns/{turn_id}` every ~2 seconds. A turn
moves `thinking` → (`awaiting_approval` | `executing`) → `completed` |
`failed`, and accumulates an append-only `events` list you can render as a
chat:

| Event `type` | Payload | Meaning |
| --- | --- | --- |
| `message` | `text` | Assistant said something. |
| `status` | `text` | Transient progress ("Pricing the plan…"). |
| `plan` | `plan` | A priced plan was proposed (shape below). |
| `plan_status` | `status` | `executing`, `completed`, `partial`, `failed`, `denied`, `superseded`, `auto_approved`. |
| `image` | `ref`, `url`, `format`, `width`, `height`, `title`, `cost` | A finished output (hosted URL; `format` is `png` or `gif`). |
| `note` | `label`, `question`, `answer` | An automatic quality-check note about a result. |
| `error` | `message` | Something went wrong (the turn will end `failed`). |

Every event carries an `at` timestamp. The turn also reports `charged_usd`
(the message fee; `0` after a refund) and `spent_usd` (generation spend).

## Plans and decisions

When the turn parks at `awaiting_approval`, the `plan` event (also on the
turn's `plan` field) holds the full card:

```json
{"id": "plan_...", "summary": "A 32x32 knight sprite, then an idle animation of it",
 "total": 0.267,
 "steps": [
   {"kind": "generate", "title": "Knight sprite", "model": "RD Pro",
    "detail": "Default · 32×32", "cost": 0.017, "style": "rd_pro__default",
    "width": 32, "height": 32, "num_images": 1, "input": null, "refs": []},
   {"kind": "generate", "title": "Idle animation", "model": "Advanced Animation",
    "detail": "Idle · 32×32 · 8 frames", "cost": 0.25, "input": "step_1"}
 ]}
```

Steps reference each other (`step_N`) and bank images (`img_N`);
independent steps run in parallel. Decide with:

```json
POST /v1/assistant/sessions/{id}/decision
{"decision": "approve"}
{"decision": "deny", "feedback": "make it red and 48x48"}
```

Both return **202** with a new `turn_id` to poll. Approve executes the plan
(images arrive as `image` events, then a closing summary `message`); deny
with feedback usually produces a revised plan in the same turn. Denying is
free either way.

## Failure behavior

- A failed **turn** refunds its $0.01 automatically (a `status` event says
  so and `charged_usd` drops to 0). This includes turns interrupted by a
  server restart — they surface as `failed` with an explanatory error on
  your next poll.
- A failed **generation step** refunds that step's charge automatically;
  the rest of the plan continues where dependencies allow, the assistant
  reports honestly what succeeded and what didn't (`plan_status:
  "partial"`), and follow-up plans reuse the finished work from the bank
  instead of regenerating it.

## Minimal client

See [example-scripts/12_assistant_session.py](example-scripts/12_assistant_session.py)
for a complete runnable version.

```python
import requests, time

BASE = "https://api.retrodiffusion.ai/v1/assistant"
H = {"X-RD-Token": "YOUR_API_KEY"}

sid = requests.post(f"{BASE}/sessions", json={}, headers=H).json()["id"]

def turn(turn_id):
    while True:
        t = requests.get(f"{BASE}/sessions/{sid}/turns/{turn_id}", headers=H).json()
        if t["status"] not in ("thinking", "executing"):
            return t
        time.sleep(2)

t = turn(requests.post(f"{BASE}/sessions/{sid}/messages",
                       json={"message": "A 32x32 slime enemy with a bounce animation"},
                       headers=H).json()["turn_id"])

while t["status"] == "awaiting_approval":
    print("plan:", t["plan"]["summary"], "->", f"${t['plan']['total']}")
    t = turn(requests.post(f"{BASE}/sessions/{sid}/decision",
                           json={"decision": "approve"}, headers=H).json()["turn_id"])

for e in t["events"]:
    if e["type"] == "image":
        print("output:", e["ref"], e["url"])
    elif e["type"] == "message":
        print("assistant:", e["text"])
```

## Errors

Standard API status codes, `detail` in the usual shapes:

- `400` — empty/oversized message, bad attachment, or not enough balance.
- `401` — missing or invalid `X-RD-Token`.
- `402` — outstanding payment debt on the account.
- `409` — a turn is already running, a plan awaits a decision (send
  `supersede: true` or a decision), or no plan is awaiting one.
- `410` — the session expired (5 minutes idle). Start a new session.
- `422` — the request body failed validation.
- `429` — rate limited; respect `Retry-After`.
