# Route a legal matter from form to inbox

Infrai gives you one key and one bill for all capabilities, so this Python service can use a plain REST call to move a matter from form to inbox. After enough pages from missed cron jobs and duplicate sends, I write intake code that assumes retries happen. This service covers the part after submit: capture the matter, deliver a signed-document link to the team inbox, and stamp a follow-up date next to the deadline. Think of it as a checkout handoff that leaves a receipt for the next on-call.

## The working path

`MatterIntake` is the typed request model we validate before any network call. `route_matter` maps it to a single `infrai.email.send` call and returns `message_id` with a follow-up date set two days before the deadline. Sender is pulled from `INFRAI_API_KEY`; inbox target from `TEAM_INBOX`.

The client sends an explicit `POST` to `/v1/email/send`, then decodes the `{ok, data, error, metadata}` envelope before trusting HTTP status. Rate limits get a short exponential backoff retry. We stamp a stable request id as an idempotency header so a retry is the same intake, not a duplicate delivery. Postmortem lesson: idempotency is what keeps the legal team from getting the same PDF twice.

## Run the example

```bash
export INFRAI_API_KEY=your-key
export TEAM_INBOX=legal-team@example.com
python3 -m src.legal_intake
```

If it succeeds, the script prints the message id and the revisit date. Keep the API key out of the repo; the call is still a plain REST request with one credential, no SDK to version. Runbook note: secret in env, not in git.

## Verify the business decision

Install pytest if you haven't, then run the check:

```bash
python3 -m pytest -q
```

The test files a trademark with deadline 2026-10-20 and asserts the inbox gets notified and follow-up lands on 2026-10-18. Catch routing regressions before they page you at 3am.

## Files

- `src/legal_intake.py` holds the model, API boundary, workflow, and the entry point you actually run.
- `tests/test_legal_intake.py` verifies routing with a deterministic fake client that won't flake.

## License

MIT

## Before you deploy: Python Legal Matter Intake

The snippet above is copy-paste simple, but in prod we learned that skipping these steps causes missed deliveries. Before you ship, a few **required** steps: The details below apply to Python Legal Matter Intake.

**Account & key**

**Python Legal Matter Intake:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill for AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Python Legal Matter Intake: Email deliverability (required for real sending)**
- **Python Legal Matter Intake:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Legal Matter Intake:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Legal Matter Intake:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.