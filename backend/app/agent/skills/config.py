"""Skill package config loader (backend/skills/<skill_id>/config.json)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillConfig:
    skill_id: str
    raw: dict[str, Any]

    @property
    def render_modes(self) -> list[str]:
        v = self.raw.get("render_modes")
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        return ["table"]

    @property
    def default_render(self) -> str:
        v = self.raw.get("default_render")
        return str(v).strip() if isinstance(v, str) and v.strip() else "table"

    @property
    def prompt_template(self) -> str | None:
        v = self.raw.get("prompt_template")
        if isinstance(v, str) and v.strip():
            return v
        return None

    @property
    def name(self) -> str:
        v = self.raw.get("name")
        return str(v).strip() if isinstance(v, str) else ""

    @property
    def version(self) -> str:
        v = self.raw.get("version")
        return str(v).strip() if isinstance(v, str) else ""

    @property
    def description(self) -> str:
        v = self.raw.get("description")
        return str(v).strip() if isinstance(v, str) else ""


def _config_path(skill_id: str) -> Path:
    return settings.skills_dir / skill_id / "config.json"


def load_skill_config(skill_id: str) -> SkillConfig:
    path = _config_path(skill_id)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raw = {}
    except Exception:
        logger.debug("读取 skill config.json 失败: %s", path, exc_info=True)
        raw = {}
    return SkillConfig(skill_id=skill_id, raw=raw)

