from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from all_the_skills.models import (
    IDEConfig,
    SkillRecord,
    SkillRegistry,
    SkillSource,
)


class RegistryManager:
    """管理技能注册表和 IDE 配置"""

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self._registry: Optional[SkillRegistry] = None

    def _ensure_dir(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> SkillRegistry:
        """从磁盘加载注册表"""
        if not self.registry_path.exists():
            self._registry = SkillRegistry(skills={}, ides=[])
            return self._registry

        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            skills = {}
            for skill_id, skill_data in data.get("skills", {}).items():
                # 重建 SkillRecord
                source_data = skill_data.get("source")
                source = None
                if source_data:
                    source = SkillSource(
                        type=source_data["type"],
                        url=source_data.get("url"),
                        repo=source_data.get("repo"),
                        path=source_data.get("path"),
                        branch=source_data.get("branch"),
                        commit=source_data.get("commit"),
                    )
                # 其他字段暂时简化处理
                skills[skill_id] = skill_data

            ides = []
            for ide_data in data.get("ides", []):
                ides.append(
                    IDEConfig(
                        name=ide_data["name"],
                        skill_path=Path(ide_data["skill_path"]),
                        enabled=ide_data.get("enabled", True),
                    )
                )

            self._registry = SkillRegistry(skills=skills, ides=ides)
            return self._registry
        except Exception:
            self._registry = SkillRegistry(skills={}, ides=[])
            return self._registry

    def save(self) -> None:
        """保存注册表到磁盘"""
        self._ensure_dir()
        if self._registry is None:
            return

        data = {
            "skills": self._registry.skills,
            "ides": [
                {
                    "name": ide.name,
                    "skill_path": str(ide.skill_path),
                    "enabled": ide.enabled,
                }
                for ide in self._registry.ides
            ],
        }
        self.registry_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def register_skill(self, skill: SkillRecord, source: SkillSource) -> None:
        """注册一个已安装的技能"""
        if self._registry is None:
            self.load()

        skill_data = {
            "skill_id": skill.skill_id,
            "skill_path": str(skill.skill_path),
            "source_root": str(skill.source_root),
            "source": asdict(source),
            "installed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._registry.skills[skill.skill_id] = skill_data
        self.save()

    def unregister_skill(self, skill_id: str) -> bool:
        """注销一个技能"""
        if self._registry is None:
            self.load()

        if skill_id not in self._registry.skills:
            return False

        del self._registry.skills[skill_id]
        self.save()
        return True

    def get_installed_skills(self) -> list[str]:
        """获取所有已安装的技能 ID 列表"""
        if self._registry is None:
            self.load()
        return list(self._registry.skills.keys())

    def is_installed(self, skill_id: str) -> bool:
        """检查技能是否已安装"""
        if self._registry is None:
            self.load()
        return skill_id in self._registry.skills

    def add_ide(self, ide: IDEConfig) -> None:
        """添加一个 IDE 配置"""
        if self._registry is None:
            self.load()

        # 移除同名的现有配置
        self._registry.ides = [
            i for i in self._registry.ides if i.name != ide.name
        ]
        self._registry.ides.append(ide)
        self.save()

    def remove_ide(self, ide_name: str) -> bool:
        """移除一个 IDE 配置"""
        if self._registry is None:
            self.load()

        original_len = len(self._registry.ides)
        self._registry.ides = [
            i for i in self._registry.ides if i.name != ide_name
        ]
        self.save()
        return len(self._registry.ides) < original_len

    def get_ides(self) -> list[IDEConfig]:
        """获取所有 IDE 配置"""
        if self._registry is None:
            self.load()
        return self._registry.ides

    def sync_to_ides(self, skill_path: Path, skill_id: str) -> list[tuple[str, bool]]:
        """将技能同步到所有启用的 IDE"""
        if self._registry is None:
            self.load()

        results = []
        for ide in self._registry.ides:
            if not ide.enabled:
                continue

            try:
                dest_path = ide.skill_path / skill_path.relative_to(skill_path.parent.parent)
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                if skill_path.is_dir():
                    shutil.copytree(skill_path, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(skill_path, dest_path)

                results.append((ide.name, True))
            except Exception:
                results.append((ide.name, False))

        return results
