# WORKSPACE Memory CLI

This project is a durable, text-first memory workspace for capturing notes, tasks, and operational context across sessions.

## Overview

The repository combines a persistent memory archive with a lightweight Python-based interface so you can keep structured project context without relying on a complex database or app stack.

## Features

- maintain durable notes and tasks in `.memory/`
- support categories and tags for organization
- expose commands through a Python CLI
- provide a small FastAPI-based web app for browsing memory state
- keep everything easy to back up and review in plain text
- export and import entries as Markdown for portability
- dashboard view with search and filtering

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
workspace-memory init
workspace-memory add-note "Review deployment checklist" --category ops --tag deployment --tag review
workspace-memory add-task "Draft the launch checklist" --category planning --tag launch
workspace-memory list --category ops
workspace-memory categories
workspace-memory export .memory/export.md
```

## Web app

```bash
workspace-web
```

Then open:

- http://localhost:8000/
- http://localhost:8000/api/status
- http://localhost:8000/api/entries

## Files and folders

- `.memory/` stores the archive
- `src/workspace_memory/` contains the Python package
- `docs/` contains project documentation and usage examples
- `tests/` contains pytest coverage for CLI and storage behavior

## Notes

This project remains intentionally lightweight and durable. It is designed for continuity, context retention, and operational knowledge, not for heavy production workload handling.
