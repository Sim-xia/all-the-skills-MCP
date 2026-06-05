from __future__ import annotations

from pathlib import Path

from skill_cortex.frontmatter import make_description_snapshot
from skill_cortex.index_store import load_index, save_index
from skill_cortex.models import ScanResult, SkillFrontmatter, SkillRecord, TreeNode


def _make_scan(skill_file: Path) -> ScanResult:
    frontmatter = SkillFrontmatter(
        title="Example Skill",
        description="Useful example skill",
        tags=("python",),
    )
    skill = SkillRecord(
        skill_id="skills:example/SKILL.md",
        source_root=skill_file.parent.parent,
        skill_path=skill_file,
        category_path=("example",),
        frontmatter=frontmatter,
        description_snapshot=make_description_snapshot(frontmatter.description),
        tag_issues=(),
    )
    tree = TreeNode(name="/", path=())
    child = TreeNode(name="example", path=("example",), skills=[skill])
    tree.children["example"] = child
    return ScanResult(skills=(skill,), tree=tree)


def test_load_index_returns_none_when_skill_file_missing(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "example"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\ntitle: Example\ndescription: test\ntags: [python]\n---\n",
        encoding="utf-8",
    )
    cache_path = tmp_path / "cache" / "index.json"
    save_index(cache_path, _make_scan(skill_file))

    skill_file.unlink()

    assert load_index(cache_path) is None


def test_load_index_returns_none_when_skill_file_changes(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "example"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\ntitle: Example\ndescription: test\ntags: [python]\n---\n",
        encoding="utf-8",
    )
    cache_path = tmp_path / "cache" / "index.json"
    save_index(cache_path, _make_scan(skill_file))

    skill_file.write_text(
        "---\ntitle: Example\ndescription: changed\ntags: [python]\n---\n",
        encoding="utf-8",
    )

    assert load_index(cache_path) is None
