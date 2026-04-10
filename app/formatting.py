from __future__ import annotations

from .models import Alert


def _pick(labels: dict[str, str], *keys: str) -> str | None:
    for k in keys:
        v = labels.get(k)
        if v:
            return v
    return None


def format_alert_line(a: Alert) -> str:
    name = _pick(a.labels, "alertname") or "alert"
    severity = _pick(a.labels, "severity")
    instance = _pick(a.labels, "instance", "pod", "node")
    summary = a.annotations.get("summary") or a.annotations.get("message") or a.annotations.get("description")

    bits: list[str] = [name]
    if severity:
        bits.append(f"sev={severity}")
    if instance:
        bits.append(f"at={instance}")
    if summary:
        bits.append(f"- {summary}")
    return " ".join(bits)


def format_message(*, status: str, alerts: list[Alert], max_alerts: int) -> str:
    shown = alerts[: max(0, max_alerts)]
    extra = len(alerts) - len(shown)

    lines: list[str] = []
    lines.append(f"[{status.upper()}] alerts={len(alerts)}")

    for a in shown:
        lines.append(f"- {format_alert_line(a)}")
        if a.generatorURL:
            lines.append(f"  {a.generatorURL}")

    if extra > 0:
        lines.append(f"... and {extra} more")

    return "\n".join(lines)

