from __future__ import annotations

import logging
import re
import shutil
import sys
import threading
from pathlib import Path
from typing import Any

from skill_cortex.config import AppConfig, load_config
from skill_cortex.downloader import SkillDownloader
from skill_cortex.frontmatter import normalize_tags
from skill_cortex.index_store import load_index, save_index
from skill_cortex.models import IDEConfig, SkillRecord, SkillSource
from skill_cortex.registry import RegistryManager
from skill_cortex.scanner import scan_skills
from skill_cortex.skill_manager import delete_skill
from skill_cortex.tags_registry import TagsRegistry, load_tags_registry

_logger = logging.getLogger("skill_cortex")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _refresh_scan(config: AppConfig, state: dict[str, object], registry: TagsRegistry) -> Any:
    scan = scan_skills(config.roots, tags_registry=registry)
    save_index(config.cache_path, scan)
    state["scan"] = scan
    return scan


def _roots_payload(config: AppConfig) -> list[str]:
    return [str(path) for path in config.roots]


def _refresh_index_payload(
    config: AppConfig,
    state: dict[str, object],
    registry: TagsRegistry,
) -> dict:
    scan = _refresh_scan(config, state, registry)
    return {
        "ok": True,
        "message": "Index refreshed",
        "count": len(scan.skills),
        "roots": _roots_payload(config),
    }


def _ensure_state_loaded(
    config: AppConfig,
    state: dict[str, object],
    state_lock: threading.Lock,
) -> None:
    with state_lock:
        if state.get("registry") is not None and state.get("scan") is not None:
            return

        registry = load_tags_registry(config.tags_path)
        scan = load_index(config.cache_path)
        if scan is None:
            scan = _refresh_scan(config, state, registry)

        state["registry"] = registry
        state["scan"] = scan


def _parse_path_arg(path: str | None) -> tuple[str, ...]:
    if not path:
        return ()
    return tuple(p for p in path.split("/") if p)


def _find_node(tree, path: tuple[str, ...]):
    node = tree
    for part in path:
        node = node.children.get(part)
        if node is None:
            return None
    return node


def _summarize_skill(skill: SkillRecord) -> dict:
    return {
        "skill_id": skill.skill_id,
        "title": skill.frontmatter.title,
        "description_snapshot": skill.description_snapshot,
        "tags": list(skill.frontmatter.tags),
        "tag_issues": list(skill.tag_issues),
        "category_path": list(skill.category_path),
        "author": skill.frontmatter.author,
        "version": skill.frontmatter.version,
        "license": skill.frontmatter.license,
    }


def _format_tags_inline(tags: tuple[str, ...]) -> str:
    return "[" + ", ".join(tags) + "]"


def _lookup_skill(scan: Any, skill_id: str) -> SkillRecord | None:
    for skill in scan.skills:
        if skill.skill_id == skill_id:
            return skill
    return None


def _apply_content_limits(
    text: str,
    max_lines: int | None = None,
    max_chars: int | None = None,
) -> str:
    limited = text
    if max_lines is not None and max_lines > 0:
        lines = limited.splitlines()
        if len(lines) > max_lines:
            limited = "\n".join(lines[:max_lines]) + f"\n... [truncated, {len(lines) - max_lines} more lines]"

    if max_chars is not None and max_chars > 0 and len(limited) > max_chars:
        limited = limited[:max_chars].rstrip() + f"\n... [truncated, {len(text) - max_chars} more chars]"

    return limited


def _body_start_index(lines: list[str]) -> int:
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return 0


def _trim_words(text: str, max_words: int = 12) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip() + " ..."


def _first_sentence(text: str) -> str | None:
    match = re.match(r"(.+?[.!?。！？])(?:\s|$)", text.strip(), flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _paragraph_preview(block: str) -> str:
    stripped = block.strip()
    if not stripped or stripped == "---":
        return ""
    if stripped.startswith("#"):
        return stripped
    sentence = _first_sentence(stripped)
    if sentence:
        return sentence
    return _trim_words(stripped)


def _extract_section(content: str, section: str) -> str:
    section_lower = section.lower()
    if section_lower != "paragraph":
        return f"[Section '{section}' not supported. Use section='paragraph' or section='body']"

    body = _strip_frontmatter(content)
    if not body:
        return "[No content found]"

    blocks = re.split(r"\n\s*\n", body)
    previews = [_paragraph_preview(block) for block in blocks]
    previews = [preview for preview in previews if preview]
    return "\n\n".join(previews) or "[No content found]"


def _strip_frontmatter(content: str) -> str:
    lines = content.splitlines()
    return "\n".join(lines[_body_start_index(lines) :]).strip()


def _skill_details_payload(
    skill: SkillRecord,
    content: str,
    section: str | None = "summary",
    max_lines: int | None = None,
    max_chars: int | None = None,
    include_frontmatter: bool = True,
) -> dict:
    section_lower = (section or "summary").strip().lower()
    result = {
        "ok": True,
        "skill_id": skill.skill_id,
        "message": "Skill details loaded",
        "title": skill.frontmatter.title,
        "description": skill.frontmatter.description,
        "tags": list(skill.frontmatter.tags),
        "author": skill.frontmatter.author,
        "version": skill.frontmatter.version,
        "license": skill.frontmatter.license,
        "skill_path": str(skill.skill_path),
        "section": section_lower,
    }

    if section_lower == "summary":
        result["description_snapshot"] = skill.description_snapshot
        result["hint"] = "Use section='paragraph' for a compact preview, section='body' for the main content, or section='full' for the complete file"
        return result

    if section_lower == "full":
        selected = content if include_frontmatter else _strip_frontmatter(content)
    elif section_lower == "body":
        selected = _strip_frontmatter(content)
    else:
        selected = _extract_section(content, section_lower)

    result["content"] = _apply_content_limits(selected, max_lines=max_lines, max_chars=max_chars)
    return result


def main() -> None:
    _setup_logging()
    try:
        sys.stdout.reconfigure(line_buffering=True, write_through=True)
    except Exception:
        pass

    try:
        sys.stderr.reconfigure(line_buffering=True, write_through=True)
    except Exception:
        pass

    config = load_config()
    _logger.info("Starting All The Skills - Skill Manager")
    _logger.info("roots=%s", ",".join(str(p) for p in config.roots))

    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        _logger.error("Missing dependency 'mcp': %s", exc)
        print(
            "Missing dependency 'mcp'. Install dependencies first, e.g. `pip install -e .`\n"
            + f"Import error: {exc}",
            file=sys.stderr,
        )
        raise

    mcp = FastMCP("All The Skills - Skill Manager")

    state_lock = threading.Lock()
    state: dict[str, object] = {
        "registry": None,
        "scan": None,
    }

    # 初始化管理器
    project_root = Path.cwd()
    registry_mgr = RegistryManager(project_root / ".all_the_skills" / "registry.json")
    downloader = SkillDownloader(project_root / ".all_the_skills" / "installed")

    @mcp.tool()
    def list_skill_tree(path: str | None = None) -> dict:
        """浏览技能树结构"""
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]
        parts = _parse_path_arg(path)
        node = _find_node(scan.tree, parts)
        if node is None:
            return {"ok": False, "error": "path_not_found", "path": list(parts)}
        return {
            "ok": True,
            "path": list(parts),
            "roots": _roots_payload(config),
            "categories": sorted(node.children.keys()),
            "count": len(node.skills),
            "skills": [_summarize_skill(s) for s in node.skills],
        }

    @mcp.tool()
    def search_skills(query: str | None = None, tags: list[str] | None = None) -> dict:
        """搜索技能"""
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]
        q = (query or "").strip().lower()
        filter_tags = normalize_tags(tags or [])
        results = []
        for s in scan.skills:
            if q:
                hay = " ".join(
                    [
                        s.skill_id,
                        s.frontmatter.title,
                        s.description_snapshot,
                        "/".join(s.category_path),
                    ]
                ).lower()
                if q not in hay:
                    continue
            if filter_tags:
                if not set(filter_tags).issubset(set(s.frontmatter.tags)):
                    continue
            results.append(_summarize_skill(s))
        return {
            "ok": True,
            "count": len(results),
            "roots": _roots_payload(config),
            "results": results,
        }

    @mcp.tool()
    def get_skill_details(
        skill_id: str,
        section: str = "summary",
        max_lines: int | None = None,
        max_chars: int | None = None,
        include_frontmatter: bool = True,
    ) -> dict:
        """获取技能详细信息，支持按 section 压缩读取"""
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]
        s = _lookup_skill(scan, skill_id)
        if s is None:
            return {"ok": False, "error": "skill_not_found", "skill_id": skill_id}
        try:
            content = s.skill_path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            registry = state["registry"]
            scan = _refresh_scan(config, state, registry)
            s = _lookup_skill(scan, skill_id)
            if s is None:
                return {
                    "ok": False,
                    "error": "stale_index",
                    "skill_id": skill_id,
                    "message": "Skill disappeared after index refresh",
                }
            try:
                content = s.skill_path.read_text(encoding="utf-8")
            except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
                return {
                    "ok": False,
                    "error": "skill_unreadable",
                    "skill_id": skill_id,
                    "detail": str(exc),
                }
        return _skill_details_payload(
            s,
            content,
            section=section,
            max_lines=max_lines,
            max_chars=max_chars,
            include_frontmatter=include_frontmatter,
        )

    @mcp.tool()
    def install_from_github(repo: str, skill_path: str, branch: str | None = None) -> dict:
        """
        从 GitHub 安装技能

        repo: "owner/repo" 格式
        skill_path: 仓库内技能的路径
        branch: 可选的分支/标签
        """
        success, path, error, source = downloader.download_from_github(
            repo, skill_path, branch
        )
        if not success:
            return {"ok": False, "error": error}

        # 重新扫描并更新索引
        _ensure_state_loaded(config, state, state_lock)
        registry = state["registry"]
        scan = _refresh_scan(config, state, registry)

        # 找到新安装的技能并注册
        skill_record = None
        for s in scan.skills:
            if s.skill_path.is_relative_to(path):
                skill_record = s
                break

        if skill_record and source:
            registry_mgr.register_skill(skill_record, source)
            # 同步到 IDEs
            sync_results = registry_mgr.sync_to_ides(path, skill_record.skill_id)
            return {
                "ok": True,
                "skill_id": skill_record.skill_id,
                "title": skill_record.frontmatter.title,
                "installed_path": str(path),
                "sync_results": [
                    {"ide": ide, "success": ok} for ide, ok in sync_results
                ],
            }

        return {"ok": True, "installed_path": str(path), "warning": "Skill registered but not found in scan"}

    @mcp.tool()
    def install_local(local_path: str) -> dict:
        """从本地路径安装技能"""
        path_obj = Path(local_path).expanduser()
        success, path, error, source = downloader.install_local(path_obj)
        if not success:
            return {"ok": False, "error": error}

        # 重新扫描并更新索引
        _ensure_state_loaded(config, state, state_lock)
        registry = state["registry"]
        scan = _refresh_scan(config, state, registry)

        # 找到新安装的技能并注册
        skill_record = None
        for s in scan.skills:
            if s.skill_path.is_relative_to(path):
                skill_record = s
                break

        if skill_record and source:
            registry_mgr.register_skill(skill_record, source)
            # 同步到 IDEs
            sync_results = registry_mgr.sync_to_ides(path, skill_record.skill_id)
            return {
                "ok": True,
                "skill_id": skill_record.skill_id,
                "title": skill_record.frontmatter.title,
                "installed_path": str(path),
                "sync_results": [
                    {"ide": ide, "success": ok} for ide, ok in sync_results
                ],
            }

        return {"ok": True, "installed_path": str(path), "warning": "Skill registered but not found in scan"}

    @mcp.tool()
    def uninstall_skill(skill_id: str) -> dict:
        """卸载技能"""
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]

        skill_record = None
        for s in scan.skills:
            if s.skill_id == skill_id:
                skill_record = s
                break

        if not skill_record:
            return {"ok": False, "error": "skill_not_found", "skill_id": skill_id}

        # 检查是否是我们管理的安装技能
        skill_dir = skill_record.skill_path.parent
        if not str(skill_dir).startswith(str(project_root / ".all_the_skills" / "installed")):
            return {
                "ok": False,
                "error": "cannot_uninstall",
                "reason": "This skill was not installed via All The Skills manager",
            }

        # 删除目录
        try:
            shutil.rmtree(skill_dir)
        except Exception as e:
            return {"ok": False, "error": f"Failed to delete skill: {str(e)}"}

        # 更新注册表
        registry_mgr.unregister_skill(skill_id)

        # 重新扫描
        registry = state["registry"]
        _refresh_scan(config, state, registry)

        return {"ok": True, "skill_id": skill_id}

    @mcp.tool()
    def list_installed() -> dict:
        """列出所有已安装的技能"""
        installed = registry_mgr.get_installed_skills()
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]

        skills = []
        for skill_id in installed:
            for s in scan.skills:
                if s.skill_id == skill_id:
                    skills.append(_summarize_skill(s))
                    break

        return {
            "ok": True,
            "count": len(skills),
            "message": "Installed skills loaded",
            "skills": skills,
        }

    @mcp.tool()
    def add_ide_config(name: str, skill_path: str, enabled: bool = True) -> dict:
        """添加 IDE 配置"""
        path_obj = Path(skill_path).expanduser()
        ide_config = IDEConfig(name=name, skill_path=path_obj, enabled=enabled)
        registry_mgr.add_ide(ide_config)
        return {"ok": True, "ide": name, "skill_path": str(path_obj)}

    @mcp.tool()
    def remove_ide_config(name: str) -> dict:
        """移除 IDE 配置"""
        removed = registry_mgr.remove_ide(name)
        return {"ok": True, "removed": removed, "ide": name}

    @mcp.tool()
    def list_ide_configs() -> dict:
        """列出所有 IDE 配置"""
        ides = registry_mgr.get_ides()
        return {
            "ok": True,
            "ides": [
                {"name": ide.name, "skill_path": str(ide.skill_path), "enabled": ide.enabled}
                for ide in ides
            ],
        }

    @mcp.tool()
    def refresh_index() -> dict:
        """强制刷新技能索引"""
        _ensure_state_loaded(config, state, state_lock)
        registry = state["registry"]
        return _refresh_index_payload(config, state, registry)

    @mcp.tool()
    def sync_skill_to_ides(skill_id: str) -> dict:
        """手动同步技能到所有已配置的 IDE"""
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]

        skill_record = None
        for s in scan.skills:
            if s.skill_id == skill_id:
                skill_record = s
                break

        if not skill_record:
            return {"ok": False, "error": "skill_not_found", "skill_id": skill_id}

        sync_results = registry_mgr.sync_to_ides(
            skill_record.skill_path.parent, skill_id
        )
        return {
            "ok": True,
            "skill_id": skill_id,
            "sync_results": [
                {"ide": ide, "success": ok} for ide, ok in sync_results
            ],
        }

    # 保留原始功能作为兼容接口
    @mcp.tool()
    def create_new_skill(
        path: str,
        description: str,
        tags: list[str] | None = None,
        instructions: str | None = None,
    ) -> dict:
        """创建新技能（兼容接口）"""
        # 为简化，委托给 skill_manager（需要确保它仍存在）
        from skill_cortex.skill_manager import create_skill

        _ensure_state_loaded(config, state, state_lock)
        result = create_skill(
            roots=config.roots,
            path=path,
            description=description,
            tags=tags,
            instructions=instructions,
        )
        if result.get("ok"):
            registry = state["registry"]
            _refresh_scan(config, state, registry)
        return result

    @mcp.tool()
    def delete_existing_skill(
        skill_id: str,
        confirm: bool = False,
    ) -> dict:
        """删除技能（兼容接口）"""
        _ensure_state_loaded(config, state, state_lock)
        scan = state["scan"]
        skill_record = _lookup_skill(scan, skill_id)
        if skill_record is None:
            return {"ok": False, "error": "skill_not_found", "skill_id": skill_id}

        result = delete_skill(
            skill_path=skill_record.skill_path,
            roots=config.roots,
            confirm=confirm,
        )
        if result.get("ok"):
            registry = state["registry"]
            _refresh_scan(config, state, registry)
        return result

    mcp.run()


if __name__ == "__main__":
    main()
