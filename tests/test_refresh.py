from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from scripts.refresh import refresh_open_games


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload or {}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, games):
        self.games = games
        self.patch_calls = []

    async def get(self, url):
        assert url.endswith("/games/")
        return FakeResponse(self.games)

    async def patch(self, url, json=None, headers=None):
        self.patch_calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse({"ok": True})

    async def aclose(self):
        return None


class FakeRedis:
    def __init__(self, existing_keys=None):
        self.existing_keys = set(existing_keys or [])
        self.set_calls = []

    async def exists(self, key):
        return key in self.existing_keys

    async def set(self, key, value):
        self.existing_keys.add(key)
        self.set_calls.append((key, value))
        return True

    async def aclose(self):
        return None


@pytest.mark.anyio
async def test_refresh_marks_only_due_open_games_once(monkeypatch):
    now = datetime.now(timezone.utc)
    past_time = (now - timedelta(hours=2)).isoformat()
    future_time = (now + timedelta(hours=2)).isoformat()

    games = [
        {"id": 1, "scheduled_time": past_time, "status": "open"},
        {"id": 2, "scheduled_time": future_time, "status": "open"},
        {"id": 3, "scheduled_time": past_time, "status": "completed"},
        {"id": 4, "scheduled_time": past_time, "status": "open"},
    ]

    client = FakeAsyncClient(games)
    redis_client = FakeRedis(existing_keys={"game_processed_4"})

    processed = await refresh_open_games(client=client, redis_client=redis_client, token="admin-token")

    assert processed == 1
    assert len(client.patch_calls) == 1
    assert client.patch_calls[0]["url"].endswith("/games/1")
    assert client.patch_calls[0]["json"] == {"status": "completed"}
    assert client.patch_calls[0]["headers"] == {"Authorization": "Bearer admin-token"}
    assert redis_client.set_calls == [("game_processed_1", "1")]