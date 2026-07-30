# Migrating from v1 to v2

V1 remains supported and unchanged. Existing clients can keep using
`https://api.retrodiffusion.ai/v1` without a code change.

V2 is an explicit opt-in at `https://api.retrodiffusion.ai/v2`. It preserves
successful route/status/response contracts for carried operations and
standardizes every JSON error:

```json
{
  "error": {
    "code": "invalid_token",
    "message": "Invalid or expired API token.",
    "request_id": "request-id",
    "details": {}
  }
}
```

`details` is optional. `X-Request-ID` matches the body request ID.
`Retry-After` is preserved for rate limits and temporary failures. Branch on
`code`, never on `message`.

Important corrections:

- missing/invalid credentials are `401 invalid_token`;
- insufficient balance is `402 not_enough_balance`;
- upstream failures use 502/503/504 semantics;
- framework 404, 405, 422, and 500 responses use the canonical envelope;
- failed async task reads remain HTTP 200 and embed
  `status_code`, `code`, `message`, and `request_id`.

Not carried into v2:

- `/inferences/legacy`
- `/external-credits/*` pending an authenticated ownership decision

The exact artifacts are checked in under `contracts/`. Python and JavaScript
examples select a version with `RD_API_VERSION`; they default to v1. Never
retry a failed paid v2 request on v1. Rollback by setting the version back to
v1.

This documentation introduces no redirect, deprecation header, sunset date, or
removal. Eventual v1 deprecation requires a separate approved lifecycle plan.
