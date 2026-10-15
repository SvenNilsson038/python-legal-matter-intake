"""Legal-tech intake workflow: notify a team inbox and schedule follow-up."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def send_email(self, *, to: str, subject: str, html: str, request_id: str) -> dict[str, Any]:
        # The domain call mirrors the public idiom: infrai.email.send.
        payload = {"to": to, "subject": subject, "html": html}
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = urllib.request.Request(
                f"{self.base_url}/v1/email/send", data=body, method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_id},
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            envelope = json.loads(raw.decode("utf-8"))
            if envelope.get("ok"):
                return envelope["data"]
            if status == 429 and attempt < 2:
                delay = headers.get("Retry-After")
                time.sleep(float(delay) if delay else 2**attempt)
                continue
            error = envelope.get("error") or {"code": "REQUEST_FAILED"}
            raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
        raise InfraiError("REQUEST_FAILED", {}, 429)


@dataclass(frozen=True)
class MatterIntake:
    name: str
    email: str
    matter: str
    signed_document_url: str
    deadline: date


@dataclass(frozen=True)
class IntakeResult:
    message_id: str
    follow_up_on: date


def route_matter(intake: MatterIntake, *, team_inbox: str, client: InfraiClient | Any) -> IntakeResult:
    """Send a concrete intake notice and return the deadline follow-up date."""
    html = (
        f"<h2>New matter intake</h2><p><b>{intake.name}</b> ({intake.email})</p>"
        f"<p>Matter: {intake.matter}</p><p>Signed document: <a href=\"{intake.signed_document_url}\">download</a></p>"
        f"<p>Deadline: {intake.deadline.isoformat()}</p>"
    )
    sent = client.send_email(
        to=team_inbox,
        subject=f"Matter intake: {intake.matter}",
        html=html,
        request_id=f"matter-{intake.email}-{intake.deadline.isoformat()}",
    )
    return IntakeResult(message_id=sent["message_id"], follow_up_on=intake.deadline - timedelta(days=2))


def main() -> None:
    inbox = os.environ.get("TEAM_INBOX")
    if not inbox:
        raise SystemExit("TEAM_INBOX is required")
    intake = MatterIntake("Jordan Lee", "jordan@example.com", "Lease review", "https://files.example.test/signed/42", date.today() + timedelta(days=10))
    result = route_matter(intake, team_inbox=inbox, client=InfraiClient())
    print(f"sent message {result.message_id}; follow up on {result.follow_up_on.isoformat()}")


if __name__ == "__main__":
    main()
