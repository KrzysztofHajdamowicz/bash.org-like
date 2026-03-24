---
name: docs-sync
description: >
  Reminds Claude to check whether CLAUDE.md and README.md need updates after making code changes.
  Use this skill after ANY code modification in the project — including but not limited to: editing models,
  views, URLs, forms, templates, tests, settings, dependencies (pyproject.toml / uv.lock), Dockerfile,
  docker-compose.yml, CI workflows (.github/), migrations, static files, or project structure changes
  (adding/removing/renaming files or directories). Even small changes can affect documentation — a new
  view means a new URL pattern, a renamed file changes the project structure section, a new dependency
  changes the install instructions. Trigger this skill whenever you finish a task that touched any
  source file in the repository.
---

# Documentation Sync Reminder

After completing any code changes in this project, you must check whether **CLAUDE.md** and **README.md** need to be updated. These two files are the primary documentation for the project and must stay accurate.

## When to update

Review your changes and ask yourself: "Did I change anything that is described or referenced in CLAUDE.md or README.md?" If yes, update the relevant sections.

Here's a non-exhaustive list of what each file documents and what changes would require an update:

### CLAUDE.md covers

| Section | Update when you... |
|---|---|
| Quick commands | Change how to run, test, lint, or build the project |
| Project structure | Add, remove, rename, or move any file or directory |
| The Quote model | Change model fields, choices, or the model class itself |
| Views pattern | Add, remove, or change views or their decorators |
| Template filter | Modify or add template tags/filters |
| Frontend stack | Change CSS/JS frameworks, CDN links, or frontend approach |
| Database configuration | Change DB settings, add a new DB backend option |
| Static files | Change static file handling, dirs, or configuration |
| Testing | Add/remove test classes, change test count, modify test setup |
| CI/CD | Modify any GitHub Actions workflow |
| Deployment | Change Docker, gunicorn, or environment variable config |
| Gotchas | Discover or fix a gotcha, or introduce a new non-obvious behavior |
| Dependencies / pyproject.toml | Add, remove, or change any dependency or extra |
| Architecture and design | Change any architectural decision (package manager, DB driver, etc.) |

### README.md covers

| Section | Update when you... |
|---|---|
| Requirements | Change Python or Django version requirements |
| Getting started | Change installation steps, commands, or prerequisites |
| Production deployment | Change environment variables, deployment commands, or server config |

## How to update

1. Read the current content of both files (if you haven't already in this session).
2. Identify which sections are affected by your changes.
3. Update only the affected sections — keep the existing style and structure.
4. If you added something entirely new that doesn't fit any existing section, add a new subsection in the appropriate place.
5. Keep CLAUDE.md detailed and technical (it's for Claude/developers). Keep README.md concise and user-friendly (it's for humans setting up the project).

## Important

- Update the test count in CLAUDE.md's Testing section if you added or removed tests.
- Update the project structure tree if you added or removed files.
- Update the view/URL count if you added or removed views or URL patterns.
- If you changed `pyproject.toml`, check both the Quick Commands and the Dependencies sections.
- Don't forget to update the environment variables table if you added a new env var.
