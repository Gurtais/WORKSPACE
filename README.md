# WORKSPACE Memory

A lightweight, durable memory workspace for notes, tasks, deadlines, and operational context.

## What it does

WORKSPACE Memory is designed for text-first context retention. It stores information in a local `.memory/` directory so notes, tasks, and reminders remain easy to review, export, and reconstruct across sessions.

Included functionality:
- durable notes and tasks in `.memory/`
- category and tag organization
- task status tracking (`new`, `active`, `done`, `blocked`)
- optional `due_at` and `reminder_at` timestamps
- CLI commands for common operations
- FastAPI web dashboard for browsing and editing memory entries
- Markdown, CSV, and JSON import/export for portability

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
```

Initialize a workspace:

```bash
workspace-memory init
```

Create an item:

```bash
workspace-memory add-note "Review deployment checklist" --category ops --tag deployment --tag review
workspace-memory add-task "Draft the launch checklist" --category planning --tag launch --status active --due 2026-11-01
```

List entries:

```bash
workspace-memory list --category ops
workspace-memory categories
workspace-memory status
```

Export memory:

```bash
workspace-memory export .memory/export.md
workspace-memory export .memory/export.json --format json
```

## Web app

Start the dashboard:

```bash
workspace-web
```

Then open:
- http://localhost:8000/
- http://localhost:8000/api/status
- http://localhost:8000/api/entries

The dashboard supports:
- creating notes and tasks
- filtering by category, kind, and status
- editing entries inline
- deleting entries
- exporting to Markdown, JSON, or CSV
- importing from a selected path

## Local development workflow

```bash
source .venv/bin/activate
pytest
workspace-web
```

If you want to test the package directly without installing globally:

```bash
python -m workspace_memory
```

## Folder layout

- `.memory/` stores the persistent memory archive
- `src/workspace_memory/` contains the Python package
- `tests/` covers storage and import/export behavior
- `docs/` contains release and smoke-test notes

## Suggested smoke test

Before tagging a release, confirm the following:

1. `workspace-memory init` creates the workspace structure.
2. `workspace-memory add-note` stores a note with tags and category metadata.
3. `workspace-memory add-task` stores a task with status and due date metadata.
4. `workspace-memory export .memory/export.md` writes a readable markdown file.
5. `workspace-web` loads the dashboard without auth errors when using a valid session.
6. Importing a generated markdown export restores the same metadata.

## Notes

This project is intentionally lightweight and durable. It favors plain-text storage, fast local workflows, and easy review over heavy production infrastructure.
