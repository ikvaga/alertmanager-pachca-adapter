from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class PachcaClient:
    base_url: str
    token: str

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

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

