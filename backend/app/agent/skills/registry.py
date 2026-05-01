"""技能注册表：启动时扫描 backend/skills 并动态加载 skill.py。"""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.contracts.skill import BaseSkill
from app.schemas.skill import SkillMetaOut

logger = logging.getLogger(__name__)


class SkillPackageConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skill_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    enabled: bool = Field(...)
    default_render: str = Field(..., min_length=1)
    render_modes: list[str] = Field(..., min_length=1)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}
        self._meta: dict[str, SkillMetaOut] = {}

    def reload(self, skills_root: Path) -> None:
        self._skills.clear()
        self._meta.clear()

        if not skills_root.is_dir():
            logger.warning("技能目录不存在或不是目录: %s", skills_root)
            return

        for entry in sorted(skills_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("_") or entry.name.startswith("."):
                continue
            cfg_path = entry / "config.json"
            py_path = entry / "skill.py"
            if not cfg_path.is_file() or not py_path.is_file():
                logger.debug("跳过非技能目录: %s", entry.name)
                continue

            try:
                raw_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                cfg = SkillPackageConfig.model_validate(raw_cfg)
            except (OSError, json.JSONDecodeError, ValidationError) as e:
                logger.error("技能配置无效 %s: %s", cfg_path, e)
                continue

            if cfg.skill_id != entry.name:
                logger.error(
                    "技能目录名与 config.skill_id 不一致: dir=%s config=%s",
                    entry.name,
                    cfg.skill_id,
                )
                continue
            if not cfg.enabled:
                logger.info("技能已禁用，跳过注册: %s", cfg.skill_id)
                continue

            try:
                skill = _load_skill_module(cfg.skill_id, py_path)
            except Exception as e:
                logger.exception("加载技能失败 skill_id=%s: %s", cfg.skill_id, e)
                continue

            skill.set_skill_id(cfg.skill_id)
            if cfg.skill_id in self._skills:
                logger.error("检测到重复 skill_id，跳过后者: %s", cfg.skill_id)
                continue

            self._skills[cfg.skill_id] = skill
            self._meta[cfg.skill_id] = SkillMetaOut(
                skill_id=cfg.skill_id,
                name=cfg.name or skill.name,
                version=cfg.version or skill.version,
                description=cfg.description or skill.description,
                default_render=cfg.default_render,
                render_modes=cfg.render_modes,
            )
            logger.info("已注册技能: %s (%s)", cfg.skill_id, cfg.name)

    def get(self, skill_id: str) -> BaseSkill | None:
        return self._skills.get(skill_id)

    def list_meta(self) -> list[SkillMetaOut]:
        return [self._meta[k] for k in sorted(self._meta.keys())]

    def list_skill_ids(self) -> list[str]:
        return sorted(self._skills.keys())


def _load_skill_module(skill_id: str, py_path: Path) -> BaseSkill:
    """从文件路径动态加载 skill.py，要求模块内实现 build_skill() -> BaseSkill。"""
    module_name = f"_skillpkg_{skill_id.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, py_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法创建模块 spec: {py_path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    builder = getattr(mod, "build_skill", None)
    if not callable(builder):
        raise RuntimeError(f"{py_path} 必须定义 build_skill() -> BaseSkill")

    skill = builder()
    if not isinstance(skill, BaseSkill):
        raise RuntimeError("build_skill() 必须返回 BaseSkill 实例")
    return skill


_registry = SkillRegistry()


def get_skill_registry() -> SkillRegistry:
    return _registry

