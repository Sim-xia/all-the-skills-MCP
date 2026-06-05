---
title: Fetch Skills Into ATS
description: Help an agent import, move, or back up an existing skills folder into All The Skills so ATS can index and serve it.
tags: [skills, migration, filesystem, mcp]
---

## Instructions

Use this skill when the user wants All The Skills (ATS) to read an existing IDE or local skills folder without manually editing paths.

The preferred target is `.all_the_skills/fetched/<source-name>` inside the ATS project. Move or copy the complete source folder there, then make sure `SKILL_CORTEX_ROOTS` includes that fetched folder or its parent.

Follow this workflow:

1. Identify the source skills folder from the user's request or from common locations such as `~/.claude/skills`, `~/.cursor/skills`, `~/.windsurf/skills`, `~/.config/opencode/skills`, or `.skills`.
2. Verify the source folder exists and contains one or more `SKILL.md` files before moving anything.
3. Create `.all_the_skills/fetched` in the ATS project if it does not exist.
4. Choose a lowercase hyphenated destination name based on the source path, for example `cursor-skills`, `claude-skills`, or `project-skills`.
5. Copy the complete source folder to `.all_the_skills/fetched/<destination-name>` when preserving the original IDE setup is safer.
6. Move the source folder only when the user explicitly wants ATS to take ownership of that folder.
7. Update `SKILL_CORTEX_ROOTS` or the MCP configuration so the fetched destination is scanned.
8. Call the `refresh_index` MCP tool after the filesystem change.
9. Use `search_skills` or `list_skill_tree` to verify that ATS can see the imported skills.

## Safety Rules

Never delete the original source folder unless the user explicitly asks for a move instead of a copy.

When moving a folder, create a backup first unless the destination itself is the backup requested by the user.

Do not treat a directory as a skill unless it contains a valid `SKILL.md` file.

If the source path contains spaces, quote it in shell commands.

## Example

For a Cursor skills folder:

```bash
mkdir -p .all_the_skills/fetched
cp -R ~/.cursor/skills .all_the_skills/fetched/cursor-skills
```

Then configure ATS with a root like:

```bash
SKILL_CORTEX_ROOTS=.all_the_skills/fetched/cursor-skills,~/.claude/skills,./.skills
```

Finally call `refresh_index` and verify with `search_skills`.
