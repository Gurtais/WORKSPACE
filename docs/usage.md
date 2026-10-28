# WORKSPACE Memory Usage Guide

## CLI usage

### Initialize the memory workspace

```bash
workspace-memory init
```

### Add a note

```bash
workspace-memory add-note "Document the rollout steps" --category operations --tag deployment --tag rollout
```

### Add a task

```bash
workspace-memory add-task "Prepare release notes" --category planning --tag release --tag docs
```

### List entries with filtering

```bash
workspace-memory list
workspace-memory list --category operations
workspace-memory list --tag release
workspace-memory list --query rollout
```

### Show category inventory

```bash
workspace-memory categories
```

### Export and import Markdown

```bash
workspace-memory export .memory/export.md
workspace-memory import .memory/export.md
```

## Web app usage

Start the web server:

```bash
workspace-web
```

Then visit:

- http://localhost:8000/
- http://localhost:8000/api/status
- http://localhost:8000/api/entries

## Data model

Entries are stored as plain text under `.memory/` with a lightweight structure:

- notes are appended to `.memory/notes/notes.md`
- tasks are appended to `.memory/tasks/active-tasks.md`
- categories and tags are included in the formatted text lines for easy review

## Example

```text
- [2026-10-28T10:00:00Z] [operations] [deployment,rollout] Document the rollout steps
- [2026-10-28T10:05:00Z] [planning] [release,docs] Prepare release notes
```
