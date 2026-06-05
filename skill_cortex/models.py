from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class SkillFrontmatter:
	title: str
	description: str
	tags: tuple[str, ...]
	author: Optional[str] = None
	version: Optional[str] = None
	license: Optional[str] = None


@dataclass(frozen=True)
class SkillSource:
	type: str  # "github", "local", "marketplace"
	url: Optional[str] = None
	repo: Optional[str] = None
	path: Optional[str] = None
	branch: Optional[str] = None
	commit: Optional[str] = None


@dataclass(frozen=True)
class SkillRecord:
	skill_id: str
	source_root: Path
	skill_path: Path
	category_path: tuple[str, ...]
	frontmatter: SkillFrontmatter
	description_snapshot: str
	tag_issues: tuple[str, ...]
	source: Optional[SkillSource] = None
	installed_at: Optional[datetime] = None
	updated_at: Optional[datetime] = None


@dataclass
class TreeNode:
	name: str
	path: tuple[str, ...]
	children: dict[str, TreeNode] = field(default_factory=dict)
	skills: list[SkillRecord] = field(default_factory=list)


@dataclass(frozen=True)
class ScanResult:
	skills: tuple[SkillRecord, ...]
	tree: TreeNode


@dataclass(frozen=True)
class IDEConfig:
	name: str
	skill_path: Path
	enabled: bool = True


@dataclass(frozen=True)
class SkillRegistry:
	skills: dict[str, SkillRecord] = field(default_factory=dict)
	ides: list[IDEConfig] = field(default_factory=list)
