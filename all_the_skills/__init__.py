"""
All The Skills - Skill Manager

A powerful skill manager MCP server for downloading, managing, and deploying Claude Code Skills across IDEs.
"""

__version__ = "0.2.0"
__author__ = "All The Skills Contributors"

from all_the_skills.models import (
    ScanResult, SkillFrontmatter, SkillRecord, TreeNode,
    IDEConfig, SkillRegistry, SkillSource
)
from all_the_skills.config import AppConfig, load_config
from all_the_skills.scanner import scan_skills
from all_the_skills.tags_registry import TagsRegistry, load_tags_registry
from all_the_skills.index_store import load_index, save_index
from all_the_skills.frontmatter import ParsedFrontmatter, parse_skill_markdown, normalize_tags
from all_the_skills.registry import RegistryManager
from all_the_skills.downloader import SkillDownloader

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
