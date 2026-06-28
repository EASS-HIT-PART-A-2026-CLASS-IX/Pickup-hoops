import asyncio
import os
from datetime import datetime, timezone
from typing import Any

import httpx
import redis.asyncio as redis
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed


API_URL = os.getenv("API_URL", "http://localhost:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
SEM = asyncio.Semaphore(3)


def build_auth_headers(token: str | None = None) -> dict[str, str]:
    access_token = token or ADMIN_TOKEN
    if not access_token:
        return {}
    return {"Authorization": f"Bearer {access_token}"}


def parse_game_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        game_time = value
    else:
        game_time = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    if game_time.tzinfo is None:
        return game_time.replace(tzinfo=timezone.utc)
    return game_time.astimezone(timezone.utc)


def is_game_ready(game: dict[str, Any], now: datetime | None = None) -> bool:
    current_time = now or datetime.now(timezone.utc)
    game_time = parse_game_time(game["scheduled_time"])
    return game.get("status") == "open" and game_time < current_time


@retry(
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True,
)
async def fetch_games(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    response = await client.get(f"{API_URL}/games/")
    response.raise_for_status()
    return response.json()


@retry(
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True,
)
async def mark_game_completed(
    client: httpx.AsyncClient,
    game_id: int,
    token: str | None = None,
) -> None:
    response = await client.patch(
        f"{API_URL}/games/{game_id}",
        json={"status": "completed"},
        headers=build_auth_headers(token),
    )
    response.raise_for_status()


async def process_game(
    game: dict[str, Any],
    client: httpx.AsyncClient,
    redis_client: redis.Redis,
    token: str | None = None,
) -> bool:
    game_id = int(game["id"])
    redis_key = f"game_processed_{game_id}"

    if await redis_client.exists(redis_key):
        return False

    async with SEM:
        if await redis_client.exists(redis_key):
            return False

        await mark_game_completed(client, game_id, token=token)
        await redis_client.set(redis_key, "1")
        return True


async def refresh_open_games(
    client: httpx.AsyncClient | None = None,
    redis_client: redis.Redis | None = None,
    token: str | None = None,
) -> int:
    own_client = client is None
    own_redis = redis_client is None
    processed_count = 0

    async with httpx.AsyncClient(timeout=10) as http_client:
        active_client = client or http_client
        active_redis = redis_client or redis.from_url(REDIS_URL, decode_responses=True)

        try:
            games = await fetch_games(active_client)
            eligible_games = [game for game in games if is_game_ready(game)]

            results = await asyncio.gather(
                *(process_game(game, active_client, active_redis, token=token) for game in eligible_games)
            )
            processed_count = sum(1 for result in results if result)
            return processed_count
        finally:
            if own_redis:
                await active_redis.aclose()
            if own_client:
                await active_client.aclose()


async def main() -> None:
    count = await refresh_open_games()
    print(f"Processed {count} game(s).")


if __name__ == "__main__":
    asyncio.run(main())