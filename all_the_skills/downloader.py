from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from all_the_skills.frontmatter import parse_skill_markdown
from all_the_skills.models import SkillSource


class SkillDownloader:
    """从各种来源下载和安装技能"""

    def __init__(self, install_root: Path):
        self.install_root = install_root
        self.install_root.mkdir(parents=True, exist_ok=True)

    def _validate_skill_dir(self, skill_dir: Path) -> tuple[bool, Optional[str]]:
        """验证技能目录的基本质量"""
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return False, "SKILL.md not found"

        try:
            content = skill_md.read_text(encoding="utf-8")
            parse_skill_markdown(content)
        except Exception as e:
            return False, f"Invalid SKILL.md: {str(e)}"

        return True, None

    def _resolve_skill_dir(self, repo_root: Path, skill_path: str) -> Optional[Path]:
        requested = repo_root / skill_path
        if requested.exists():
            if requested.is_file():
                requested = requested.parent
            if (requested / "SKILL.md").exists():
                return requested

        current = repo_root
        for part in Path(skill_path).parts:
            current = current / part
            if (current / "SKILL.md").exists():
                return current

        return None

    def download_from_github(
        self,
        repo: str,
        skill_path: str,
        branch: Optional[str] = None,
    ) -> tuple[bool, Optional[Path], Optional[str], Optional[SkillSource]]:
        """
        从 GitHub 仓库下载单个技能

        repo: 格式 "owner/repo"
        skill_path: 仓库内技能的路径
        branch: 可选的分支/标签
        """
        repo_url = f"https://github.com/{repo}.git"
        source = SkillSource(
            type="github",
            url=repo_url,
            repo=repo,
            path=skill_path,
            branch=branch,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # 浅克隆仓库
                clone_args = ["git", "clone", "--depth", "1", repo_url, str(temp_path)]
                if branch:
                    clone_args.extend(["--branch", branch])

                subprocess.run(
                    clone_args,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # 获取 commit hash
                commit_hash = (
                    subprocess.check_output(
                        ["git", "rev-parse", "HEAD"],
                        cwd=temp_path,
                        text=True,
                    )
                    .strip()
                )
                source = SkillSource(
                    type=source.type,
                    url=source.url,
                    repo=source.repo,
                    path=source.path,
                    branch=source.branch,
                    commit=commit_hash,
                )

                # 查找技能目录
                skill_dir = self._resolve_skill_dir(temp_path, skill_path)
                if skill_dir is None:
                    return False, None, f"Skill not found at {skill_path}", None

                # 验证技能
                valid, error_msg = self._validate_skill_dir(skill_dir)
                if not valid:
                    return False, None, error_msg, None

                # 安装技能
                dest_name = f"github__{repo.replace('/', '__')}__{skill_path.replace('/', '__')}"
                dest_path = self.install_root / dest_name

                if dest_path.exists():
                    shutil.rmtree(dest_path)

                shutil.copytree(skill_dir, dest_path)

                return True, dest_path, None, source

            except subprocess.CalledProcessError as e:
                return False, None, f"Git command failed: {e.stderr}", None
            except Exception as e:
                return False, None, f"Download failed: {str(e)}", None

    def install_local(
        self,
        local_path: Path,
    ) -> tuple[bool, Optional[Path], Optional[str], Optional[SkillSource]]:
        """从本地路径安装技能"""
        if not local_path.exists():
            return False, None, "Path does not exist", None

        # 如果是文件，查找父目录
        if local_path.is_file():
            local_path = local_path.parent

        valid, error_msg = self._validate_skill_dir(local_path)
        if not valid:
            return False, None, error_msg, None

        source = SkillSource(
            type="local",
            path=str(local_path),
        )

        dest_name = f"local__{local_path.name}"
        dest_path = self.install_root / dest_name

        if dest_path.exists():
            shutil.rmtree(dest_path)

        shutil.copytree(local_path, dest_path)

        return True, dest_path, None, source
