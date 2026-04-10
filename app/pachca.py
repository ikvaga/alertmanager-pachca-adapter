from __future__ import annotations

from dataclasses import dataclass

import asyncio
import httpx


@dataclass(frozen=True)
class PachcaClient:
    base_url: str
    token: str
    client: httpx.AsyncClient
    max_attempts: int = 3

    async def send_message(self, *, discussion_id: int, content: str) -> None:
        url = f"{self.base_url.rstrip('/')}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "message": {
                "entity_type": "discussion",
                "entity_id": discussion_id,
                "content": content,
            }
        }

        attempts = max(1, int(self.max_attempts))
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                resp = await self.client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
                last_exc = e
                if attempt >= attempts:
                    break

                retry_after = None
                if isinstance(e, httpx.HTTPStatusError):
                    ra = e.response.headers.get("Retry-After")
                    if ra and ra.isdigit():
                        retry_after = float(ra)

                # Basic exponential backoff with cap; honor Retry-After if present.
                backoff = min(8.0, 0.5 * (2 ** (attempt - 1)))
                await asyncio.sleep(retry_after if retry_after is not None else backoff)

        assert last_exc is not None
        raise last_exc

