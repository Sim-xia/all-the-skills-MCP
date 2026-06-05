from __future__ import annotations

from pathlib import Path

from all_the_skills.config import AppConfig
from all_the_skills.index_store import load_index, save_index
from all_the_skills.frontmatter import make_description_snapshot
from all_the_skills.models import SkillFrontmatter, SkillRecord
from all_the_skills.server import _extract_section, _refresh_index_payload, _skill_details_payload
from all_the_skills.scanner import scan_skills
from all_the_skills.tags_registry import TagsRegistry


def _write_skill(skill_dir: Path, title: str, description: str) -> Path:
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        f"---\ntitle: {title}\ndescription: {description}\ntags: [python]\n---\n",
        encoding="utf-8",
    )
    return skill_file


def test_refresh_index_payload_rescans_and_updates_cache(tmp_path: Path) -> None:
    root = tmp_path / ".skills"
    _write_skill(root / "alpha", "Alpha", "First skill")
    cache_path = tmp_path / "cache" / "index.json"
    config = AppConfig(roots=(root,), cache_path=cache_path, tags_path=tmp_path / "tags.md")
    state: dict[str, object] = {"scan": None, "registry": None}
    registry = TagsRegistry(allowed_tags=frozenset())

    payload = _refresh_index_payload(config, state, registry)

    assert payload == {
        "ok": True,
        "message": "Index refreshed",
        "count": 1,
        "roots": [str(root)],
    }
    assert state["scan"] is not None
    loaded = load_index(cache_path)
    assert loaded is not None
    assert len(loaded.skills) == 1


def test_refresh_index_payload_picks_up_new_skills(tmp_path: Path) -> None:
    root = tmp_path / ".skills"
    _write_skill(root / "alpha", "Alpha", "First skill")
    cache_path = tmp_path / "cache" / "index.json"
    config = AppConfig(roots=(root,), cache_path=cache_path, tags_path=tmp_path / "tags.md")
    registry = TagsRegistry(allowed_tags=frozenset())
    initial_scan = scan_skills(config.roots, tags_registry=registry)
    save_index(cache_path, initial_scan)
    state: dict[str, object] = {"scan": initial_scan, "registry": registry}

    _write_skill(root / "beta", "Beta", "Second skill")

    payload = _refresh_index_payload(config, state, registry)

    assert payload["count"] == 2
    assert len(state["scan"].skills) == 2


def test_extract_section_returns_matching_markdown_section() -> None:
    content = """---
title: Demo
description: Demo skill
tags: [python]
---

Intro body

## Instructions

Do the work.

## Examples

Example text.
"""

    assert _extract_section(content, "paragraph") == "Intro body\n\n## Instructions\n\nDo the work.\n\n## Examples\n\nExample text."


def test_extract_section_paragraph_uses_first_sentence() -> None:
    content = """---
title: Demo
description: Demo skill
tags: [python]
---

This is the first sentence. This is extra detail that should not be needed.

Another paragraph without punctuation but with many words that should be trimmed after a short preview for readability

## Usage

Follow these steps in order.

```
code sample
```

---

Final note.
"""

    assert _extract_section(content, "paragraph") == (
        "This is the first sentence.\n\n"
        "Another paragraph without punctuation but with many words that should be trimmed ...\n\n"
        "## Usage\n\n"
        "Follow these steps in order.\n\n"
        "```\ncode sample\n```\n\n"
        "Final note."
    )


def test_extract_section_returns_no_content_when_body_empty() -> None:
    content = """---
title: Demo
description: Demo skill
tags: [python]
---
"""

    assert _extract_section(content, "paragraph") == "[No content found]"


def test_extract_section_returns_hint_for_unsupported_section() -> None:
    content = """---
title: Demo
description: Demo skill
tags: [python]
---

# Demo Guide

Just body text.
"""

    assert _extract_section(content, "instructions") == (
        "[Section 'instructions' not supported. Use section='paragraph' or section='body']"
    )


def test_skill_details_payload_summary_omits_content(tmp_path: Path) -> None:
    skill_file = tmp_path / "skills" / "demo" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("", encoding="utf-8")
    frontmatter = SkillFrontmatter(
        title="Demo",
        description="Demo skill for reading",
        tags=("python",),
    )
    skill = SkillRecord(
        skill_id="skills:demo/SKILL.md",
        source_root=tmp_path / "skills",
        skill_path=skill_file,
        category_path=("demo",),
        frontmatter=frontmatter,
        description_snapshot=make_description_snapshot(frontmatter.description),
        tag_issues=(),
    )

    payload = _skill_details_payload(skill, "content", section="summary")

    assert payload["ok"] is True
    assert payload["section"] == "summary"
    assert payload["description_snapshot"] == "Demo skill for reading"
    assert payload["hint"].startswith("Use section='paragraph'")
    assert "content" not in payload


def test_skill_details_payload_supports_limits_and_body(tmp_path: Path) -> None:
    skill_file = tmp_path / "skills" / "demo" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("", encoding="utf-8")
    frontmatter = SkillFrontmatter(
        title="Demo",
        description="Demo skill for reading",
        tags=("python",),
    )
    skill = SkillRecord(
        skill_id="skills:demo/SKILL.md",
        source_root=tmp_path / "skills",
        skill_path=skill_file,
        category_path=("demo",),
        frontmatter=frontmatter,
        description_snapshot=make_description_snapshot(frontmatter.description),
        tag_issues=(),
    )
    content = """---
title: Demo
description: Demo skill
tags: [python]
---

line one
line two
line three
"""

    payload = _skill_details_payload(skill, content, section="body", max_lines=2, max_chars=20)

    assert payload["section"] == "body"
    assert payload["content"].startswith("line one\nline two")
    assert "truncated" in payload["content"]
