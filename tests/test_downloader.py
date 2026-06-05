from __future__ import annotations

from pathlib import Path

from skill_cortex.downloader import SkillDownloader


def test_resolve_skill_dir_supports_nested_paths(tmp_path: Path) -> None:
    downloader = SkillDownloader(tmp_path / "installed")
    repo_root = tmp_path / "repo"
    skill_dir = repo_root / "collection" / "python" / "helper"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\ntitle: Helper\ndescription: nested skill\ntags: [python]\n---\n",
        encoding="utf-8",
    )

    resolved = downloader._resolve_skill_dir(repo_root, "collection/python/helper/extra/file.txt")

    assert resolved == skill_dir


def test_resolve_skill_dir_accepts_direct_skill_file_path(tmp_path: Path) -> None:
    downloader = SkillDownloader(tmp_path / "installed")
    repo_root = tmp_path / "repo"
    skill_dir = repo_root / "helper"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\ntitle: Helper\ndescription: direct file\ntags: [python]\n---\n",
        encoding="utf-8",
    )

    resolved = downloader._resolve_skill_dir(repo_root, "helper/SKILL.md")

    assert resolved == skill_dir
