from __future__ import annotations

from pathlib import Path

from all_the_skills.config import load_config


def test_load_config_defaults_include_common_skill_roots(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("SKILL_CORTEX_ROOTS", raising=False)
    monkeypatch.delenv("SKILL_CORTEX_CACHE_PATH", raising=False)
    monkeypatch.delenv("SKILL_CORTEX_TAGS_PATH", raising=False)

    config = load_config()

    assert Path(tmp_path / "home" / ".claude" / "skills") in config.roots
    assert Path(tmp_path / "home" / ".cursor" / "skills") in config.roots
    assert Path(tmp_path / "home" / ".windsurf" / "skills") in config.roots
    assert Path(tmp_path / "home" / ".config" / "opencode" / "skills") in config.roots
    assert tmp_path / ".skills" in config.roots
    assert tmp_path / ".all_the_skills" / "installed" in config.roots


def test_load_config_dedupes_roots(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "SKILL_CORTEX_ROOTS",
        f"{tmp_path}/skills,{tmp_path}/skills,{tmp_path}/other",
    )

    config = load_config()

    assert config.roots == (tmp_path / "skills", tmp_path / "other")
