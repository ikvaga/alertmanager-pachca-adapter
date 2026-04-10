from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .formatting import format_message
from .models import AlertmanagerWebhook, RoutesConfig, route_alerts
from .pachca import PachcaClient
from .routes_loader import load_routes
from .settings import Settings


def create_app() -> FastAPI:
    app = FastAPI(title="alertmanager-pachka-router")

    try:
        settings = Settings()
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(
            "Missing/invalid settings. Ensure PACHCA_TOKEN (env var pachca_token) is set."
        ) from e

    try:
        routes_cfg: RoutesConfig = load_routes(settings.routes_path)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Failed to load routes config from {settings.routes_path}: {e}") from e

    pachca = PachcaClient(base_url=settings.pachca_base_url, token=settings.pachca_token)

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.post("/alertmanager/webhook")
    async def alertmanager_webhook(payload: AlertmanagerWebhook):
        if not payload.alerts:
            return {"ok": True, "sent": 0, "reason": "no alerts"}

        mapping = route_alerts(routes_cfg, payload.alerts)
        if not mapping:
            return {"ok": True, "sent": 0, "reason": "no routes matched and no default"}

        sent = 0
        errors: list[str] = []

        for discussion_id, alerts in mapping.items():
            content = format_message(
                status=payload.status,
                alerts=alerts,
                max_alerts=settings.message_max_alerts,
            )
            try:
                await pachca.send_message(discussion_id=discussion_id, content=content)
                sent += 1
            except Exception as e:  # noqa: BLE001
                errors.append(f"discussion_id={discussion_id}: {e}")

        if errors:
            raise HTTPException(status_code=502, detail={"sent": sent, "errors": errors})

        return {"ok": True, "sent": sent}

    return app


app = create_app()

