from __future__ import annotations

from pathlib import Path

import yaml

from .models import RoutesConfig


def load_routes(path: str) -> RoutesConfig:
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if raw is None:
        raw = {}
    return RoutesConfig.parse_obj(raw)

