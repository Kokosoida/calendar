import unittest.mock

from sqlalchemy.orm.session import Session
from starlette.testclient import TestClient

from app.core.config import settings
from tests.factories import EventInviteFactory
from tests.utils import get_jwt_header


class TestGetEvents:
    def test_get_events_not_logged_in(self, client: TestClient):
        resp = client.get(
            settings.API_PATH + "/events",
            params={"after": "2022-01-01T00:00Z", "before": "2022-01-01T00:00Z"},
        )
        assert resp.status_code == 401

    def test_get_events(self, db: Session, client: TestClient, user, event):
        jwt_header = get_jwt_header(user)
        resp = client.get(
            settings.API_PATH + "/events",
            headers=jwt_header,
            params={"after": "2022-01-01T00:00Z", "before": "2022-01-01T00:00Z"},
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "events_with_occurrences": [
                {
                    "start": "2022-01-01T00:00:00+00:00",
                    "name": unittest.mock.ANY,
                    "duration_minutes": 120,
                    "recurrence": None,
                    "id": event.id,
                    "owner_id": str(user.id),
                    "invites": [],
                    "occurrences": ["2022-01-01T00:00:00+00:00"],
                }
            ],
            "offset": None,
        }

    def test_offset(self, db: Session, client: TestClient, user, event):
        EventInviteFactory(user=user)
        jwt_header = get_jwt_header(user)
        resp = client.get(
            settings.API_PATH + "/events",
            headers=jwt_header,
            params={
                "after": "2022-01-01T00:00Z",
                "before": "2022-01-01T00:00Z",
                "limit": 1,
            },
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "events_with_occurrences": [
                {
                    "start": "2022-01-01T00:00:00+00:00",
                    "name": unittest.mock.ANY,
                    "duration_minutes": 120,
                    "recurrence": None,
                    "id": event.id,
                    "owner_id": str(user.id),
                    "invites": [],
                    "occurrences": ["2022-01-01T00:00:00+00:00"],
                }
            ],
            "offset": event.id,
        }


class TestGetSingleEvent:
    def test_get_single_event(self, db: Session, client: TestClient, user, event):
        jwt_header = get_jwt_header(user)
        resp = client.get(settings.API_PATH + f"/events/{event.id}", headers=jwt_header)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == event.id
        assert data["name"] == event.name


class TestCreateEvent:
    def test_create_event(self, db: Session, client: TestClient, user):
        jwt_header = get_jwt_header(user)

        resp = client.post(
            settings.API_PATH + "/events",
            headers=jwt_header,
            json={
                "start": "2022-10-08T13:35Z",
                "name": "event_test",
                "duration_minutes": 1440,
                "recurrence": {
                    "description": {
                        "interval": 1,
                        "count": 2,
                        "until": "2022-10-08T13:35:39.925Z",
                        "type": "monthly",
                        "mode": "by_day",
                    }
                },
                "invitee_ids": [],
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["id"]


class TestDeleteEvent:
    def test_delete_event(self, db: Session, client: TestClient, user, event):
        jwt_header = get_jwt_header(user)

        resp = client.delete(
            settings.API_PATH + f"/events/{event.id}", headers=jwt_header
        )
        assert resp.status_code == 200

    def test_delete_event_does_not_exist(self, db: Session, client: TestClient, user):
        jwt_header = get_jwt_header(user)

        resp = client.delete(settings.API_PATH + f"/events/{10**6}", headers=jwt_header)
        assert resp.status_code == 404, resp.text


class TestAcceptInvitation:
    def test_update_event(self, db: Session, client: TestClient, event_invite):
        jwt_header = get_jwt_header(event_invite.user)

        resp = client.patch(
            settings.API_PATH + f"/events/{event_invite.event_id}/invite",
            headers=jwt_header,
            json={"is_accepted": True},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_accepted"] is True
