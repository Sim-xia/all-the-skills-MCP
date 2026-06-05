from __future__ import annotations

from pathlib import Path

from skill_cortex.skill_manager import create_skill, delete_skill


def test_create_and_delete_user_skill(tmp_path: Path) -> None:
    root = tmp_path / ".skills"
    result = create_skill(
        roots=(root,),
        path="coding/python-helper",
        description="Helpful Python workflow",
        tags=["python"],
    )

    assert result["ok"] is True
    skill_path = Path(result["skill_path"])
    assert skill_path.exists()

    preview = delete_skill(skill_path=skill_path, roots=(root,), confirm=False)
    assert preview["ok"] is False
    assert preview["error"] == "confirmation_required"
    assert skill_path.exists()

    deleted = delete_skill(skill_path=skill_path, roots=(root,), confirm=True)
    assert deleted["ok"] is True
    assert not skill_path.exists()


def test_delete_skill_rejects_installed_manager_skill(tmp_path: Path) -> None:
    installed_root = tmp_path / ".all_the_skills" / "installed"
    skill_dir = installed_root / "github__owner__repo__skill"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(
        "---\ntitle: Installed\ndescription: managed skill\ntags: [python]\n---\n",
        encoding="utf-8",
    )

    result = delete_skill(skill_path=skill_path, roots=(tmp_path / ".skills", installed_root), confirm=True)

    assert result["ok"] is False
    assert result["error"] == "not_deletable"
