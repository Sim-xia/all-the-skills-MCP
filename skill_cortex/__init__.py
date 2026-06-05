"""
All The Skills - Skill Manager

A powerful skill manager MCP server for downloading, managing, and deploying Claude Code Skills across IDEs.
"""

__version__ = "0.2.0"
__author__ = "All The Skills Contributors"

from skill_cortex.models import (
    ScanResult, SkillFrontmatter, SkillRecord, TreeNode,
    IDEConfig, SkillRegistry, SkillSource
)
from skill_cortex.config import AppConfig, load_config
from skill_cortex.scanner import scan_skills
from skill_cortex.tags_registry import TagsRegistry, load_tags_registry
from skill_cortex.index_store import load_index, save_index
from skill_cortex.frontmatter import ParsedFrontmatter, parse_skill_markdown, normalize_tags
from skill_cortex.registry import RegistryManager
from skill_cortex.downloader import SkillDownloader

__all__ = [
    "__version__",
    # Models
    "ScanResult",
    "SkillFrontmatter", 
    "SkillRecord",
    "TreeNode",
    "IDEConfig",
    "SkillRegistry",
    "SkillSource",
    # Config
    "AppConfig",
    "load_config",
    # Scanner
    "scan_skills",
    # Tags
    "TagsRegistry",
    "load_tags_registry",
    # Index
    "load_index",
    "save_index",
    # Frontmatter
    "ParsedFrontmatter",
    "parse_skill_markdown",
    "normalize_tags",
    # Registry
    "RegistryManager",
    # Downloader
    "SkillDownloader",
]
