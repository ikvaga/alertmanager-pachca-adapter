from __future__ import annotations

from prometheus_client import Counter, Histogram

webhook_requests_total = Counter(
    "am_pachca_router_webhook_requests_total",
    "Incoming Alertmanager webhook requests",
)

webhook_alerts_total = Counter(
    "am_pachca_router_webhook_alerts_total",
    "Incoming Alertmanager alerts",
)

pachca_messages_total = Counter(
    "am_pachca_router_pachca_messages_total",
    "Pachca messages attempted",
    ["result"],
)

pachca_send_seconds = Histogram(
    "am_pachca_router_pachca_send_seconds",
    "Time spent sending messages to Pachca",
)

