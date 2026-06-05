# All The Skills

All The Skills is a third-party MCP server for discovering, indexing, reading, installing, and managing local Claude Code Skills.

## Features

- Scan multiple skill roots for `SKILL.md` files.
- Browse skills as a directory tree.
- Search skills by text and tags.
- Read skill summaries, compact paragraph previews, body content, or full files with size limits.
- Install skills from GitHub repositories or local directories.
- Create, delete, list, uninstall, and sync skills across configured IDE paths.

## Quick Start

Requirements: Python 3.11+, `pip`, and `git` if installing skills from GitHub.

```bash
pip install -e .
source config/examples/ats.env.example
all-the-skills
```

Before running in your own environment, edit `SKILL_CORTEX_ROOTS` in `config/examples/ats.env.example` or set it in your MCP client config so it points to the skill directories you want to scan.

## MCP Config Example

```json
{
  "mcpServers": {
    "all-the-skills": {
      "command": "all-the-skills",
      "args": [],
      "env": {
        "SKILL_CORTEX_ROOTS": "/path/to/.claude/skills,/path/to/project/.skills,/path/to/project/.all_the_skills/installed",
        "SKILL_CORTEX_CACHE_PATH": "/path/to/project/.skill_cortex_cache/index.json",
        "SKILL_CORTEX_TAGS_PATH": "/path/to/project/tags.md"
      }
    }
  }
}
```

## Common Tools

- `refresh_index`: rescan configured skill roots.
- `list_skill_tree`: browse indexed skills by folder path.
- `search_skills`: search indexed skills by query and tags.
- `get_skill_details`: read a skill section such as `summary`, `paragraph`, `body`, or `full`.
- `install_from_github`: install a skill from a GitHub repository.
- `install_local`: install a skill from a local directory.
- `create_new_skill`: create a new user skill.
- `delete_existing_skill`: delete a user-created skill after confirmation.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License
