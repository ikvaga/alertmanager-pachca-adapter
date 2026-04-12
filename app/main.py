from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from .formatting import format_message
from .metrics import (
    pachca_messages_total,
    pachca_send_seconds,
    webhook_alerts_total,
    webhook_requests_total,
)
from .models import AlertmanagerWebhook, RoutesConfig, route_alerts
from .pachca import PachcaClient
from .routes_loader import load_routes
from .settings import Settings


def create_app() -> FastAPI:
    settings = Settings()

    try:
        routes_cfg: RoutesConfig = load_routes(settings.routes_path)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Failed to load routes config from {settings.routes_path}: {e}") from e

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with httpx.AsyncClient(timeout=settings.pachca_timeout_seconds) as client:
            pachca = PachcaClient(
                base_url=settings.pachca_base_url,
                token=settings.pachca_token,
                client=client,
                max_attempts=settings.pachca_max_attempts,
            )
            app.state.settings = settings
            app.state.routes_cfg = routes_cfg
            app.state.pachca = pachca
            yield

    app = FastAPI(title="alertmanager-pachka-router", lifespan=lifespan)

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.post("/alertmanager/webhook")
    async def alertmanager_webhook(payload: AlertmanagerWebhook, request: Request):
        webhook_requests_total.inc()

        state_settings: Settings = request.app.state.settings
        routes_cfg: RoutesConfig = request.app.state.routes_cfg
        pachca: PachcaClient = request.app.state.pachca

        if state_settings.webhook_token:
            token = request.headers.get("X-Webhook-Token")
            if token != state_settings.webhook_token:
                raise HTTPException(status_code=401, detail="invalid webhook token")

        if not payload.alerts:
            return {"ok": True, "sent": 0, "reason": "no alerts"}

        webhook_alerts_total.inc(len(payload.alerts))
        mapping = route_alerts(routes_cfg, payload.alerts)
        if not mapping:
            return {"ok": True, "sent": 0, "reason": "no routes matched and no default"}

        sent = 0
        errors: list[str] = []

        for discussion_id, alerts in mapping.items():
            content = format_message(
                status=payload.status,
                alerts=alerts,
                max_alerts=state_settings.message_max_alerts,
            )
            try:
                with pachca_send_seconds.time():
                    await pachca.send_message(discussion_id=discussion_id, content=content)
                pachca_messages_total.labels(result="ok").inc()
                sent += 1
            except Exception as e:  # noqa: BLE001
                pachca_messages_total.labels(result="error").inc()
                errors.append(f"discussion_id={discussion_id}: {e}")

        if errors:
            raise HTTPException(status_code=502, detail={"sent": sent, "errors": errors})

        return {"ok": True, "sent": sent}

    return app


app = create_app()

