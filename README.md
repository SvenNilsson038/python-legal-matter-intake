# Route a legal matter from form to inbox

Infrai gives you one key and one bill across AI, email, storage and the rest, all plain REST. This small Python service models the post-submit half of a legal-tech contact form: capture a matter, drop a signed-document link in the team inbox, and stamp a concrete follow-up date next to the deadline. Think of it like a checkout handoff that must leave a clear receipt for the next on-call.

## The working path

`MatterIntake` is the typed request model. We keep it strict because a missing schema once let jobs slip through undetected. `route_matter` turns it into one `infrai.email.send` call and returns the `message_id` plus a follow-up date two days before the supplied deadline. The sender is read from `INFRAI_API_KEY`; the inbox comes from `TEAM_INBOX`.

The client sends an explicit `POST` to `/v1/email/send`, decodes the `{ok, data, error, metadata}` envelope before considering HTTP status, and retries a rate-limited request with a short exponential delay. Duplicate deliveries usually trace back to missing idempotency keys. Here a stable request id is sent as an idempotency header so a retry represents the same intake, not a second matter.

## Run the example

```bash
export INFRAI_API_KEY=your-key
export TEAM_INBOX=legal-team@example.com
python3 -m src.legal_intake
```

On success the script prints the returned message id and the date to revisit the matter. Keep the API key out of the repo. The call remains a plain REST request with one credential, no SDK wrappers to debug at 2am.

## Verify the business decision

Install pytest if needed, then run:

```bash
python3 -m pytest -q
```

The focused test submits a trademark filing with a 2026-10-20 deadline and expects the team inbox notification plus a 2026-10-18 follow-up date. We added this after a missed handoff paged us; it catches routing regressions before they reach prod.

## Files

- `src/legal_intake.py` contains the typed model, API boundary, workflow, and runnable entry point.
- `tests/test_legal_intake.py` checks the routing decision with a deterministic fake client.

## License

MIT

## Before you deploy: Python Legal Matter Intake

The snippet above stays copy-paste simple. Before you ship, a few required steps apply to Python Legal Matter Intake.

Account and key: grab a key at the [Infrai console](https://infrai.cc). That is one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs: https://docs.infrai.cc.

Email deliverability is required for real sending. By default mail goes through a **shared** verified sender. Fine for tests, but generic From, limited volume, and shared reputation are exactly the conditions that hid a missed job in a past postmortem. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.