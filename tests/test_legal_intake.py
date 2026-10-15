from datetime import date

from src.legal_intake import MatterIntake, route_matter


class FakeClient:
    def __init__(self):
        self.call = None

    def send_email(self, **kwargs):
        self.call = kwargs
        return {"message_id": "msg_test_42"}


def test_routes_intake_and_sets_two_day_follow_up():
    fake = FakeClient()
    intake = MatterIntake("Ava Chen", "ava@example.com", "Trademark filing", "https://files.test/doc", date(2026, 10, 20))
    result = route_matter(intake, team_inbox="legal@example.com", client=fake)
    assert result.message_id == "msg_test_42"
    assert result.follow_up_on == date(2026, 10, 18)
    assert fake.call["to"] == "legal@example.com"
    assert "Trademark filing" in fake.call["html"]
