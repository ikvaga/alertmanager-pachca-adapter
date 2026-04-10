from __future__ import annotations

from typing import Literal, Optional, Dict, List

from pydantic import BaseModel, Field


class Alert(BaseModel):
    status: Literal["firing", "resolved"]
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

    startsAt: Optional[str] = None
    endsAt: Optional[str] = None

    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None


class AlertmanagerWebhook(BaseModel):
    receiver: Optional[str] = None
    status: Literal["firing", "resolved"]
    alerts: List[Alert] = Field(default_factory=list)

    groupLabels: Dict[str, str] = Field(default_factory=dict)
    commonLabels: Dict[str, str] = Field(default_factory=dict)
    commonAnnotations: Dict[str, str] = Field(default_factory=dict)

    externalURL: Optional[str] = None
    version: Optional[str] = None
    groupKey: Optional[str] = None
    truncatedAlerts: Optional[int] = None

    # allow extra fields (Alertmanager can add more over time)
    class Config:
        extra = "allow"


class RouteTarget(BaseModel):
    discussion_id: int


class RouteRule(BaseModel):
    name: str
    match: Dict[str, str] = Field(default_factory=dict)
    target: RouteTarget


class RoutesConfig(BaseModel):
    version: int = 1
    default: Optional[RouteTarget] = None
    routes: List[RouteRule] = Field(default_factory=list)

    class Config:
        extra = "forbid"


def labels_match(selector: Dict[str, str], labels: Dict[str, str]) -> bool:
    for k, v in selector.items():
        if labels.get(k) != v:
            return False
    return True


def route_alerts(cfg: RoutesConfig, alerts: List[Alert]) -> Dict[int, List[Alert]]:
    by_discussion: Dict[int, List[Alert]] = {}

    for alert in alerts:
        matched = False
        for rule in cfg.routes:
            if labels_match(rule.match, alert.labels):
                by_discussion.setdefault(rule.target.discussion_id, []).append(alert)
                matched = True
        if not matched and cfg.default is not None:
            by_discussion.setdefault(cfg.default.discussion_id, []).append(alert)

    return by_discussion

