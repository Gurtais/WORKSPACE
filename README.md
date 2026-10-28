# WORKSPACE

WORKSPACE is a durable personal memory and operational context project designed to preserve knowledge across sessions, tools, and environment resets. It began as a plain-text memory archive for notes, tasks, and reflections, and it now includes a small Python-based CLI to make that workflow usable as a real project.

## What this project is

This repository combines two things:

- a long-term knowledge base for notes, tasks, reflections, and recovery instructions
- a lightweight software project for managing that memory in a structured and repeatable way

It is intentionally simple, durable, and text-first.

## Features

- persistent memory storage under `.memory/`
- task tracking and note capture
- lightweight command-line interface for managing memory entries
- easy recovery workflow after resets or environment rebuilds
- plain-text project structure for portability and clarity

## Project structure

```text
WORKSPACE/
├── .memory/
│   ├── README.md
│   ├── state/
│   ├── tasks/
│   ├── reflections/
│   ├── recovery/
│   └── tools/
├── agents/
├── assets/
├── deepseek/
├── docs/
├── dsh-dream/
├── grok/
├── jobs/
├── multibots/
├── plugins/
├── src/
│   └── workspace_memory/
├── .editorconfig
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
└── .github/
```

## Getting started

### Prerequisites

- Python 3.10 or newer

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Use the CLI

```bash
workspace-memory init
workspace-memory add-note "Review deployment checklist and capture any missing steps."
workspace-memory add-task "Draft a recovery plan for the new environment."
workspace-memory status
workspace-memory list
```

The CLI stores notes and task entries in the `.memory/` directory, preserving project context in a durable format.

## Memory model

The repository's memory layer is organized around:

- session continuity
- task tracking
- personal notes and reflections
- operational knowledge and recovery instructions
- tool learning and environment context

This is designed to reduce context loss and accelerate re-entry into ongoing work.

## Commands

```bash
workspace-memory init
workspace-memory add-note "Your note here"
workspace-memory add-task "Your task here"
workspace-memory status
workspace-memory list
```

## Development

To run the package directly:

```bash
python -m workspace_memory.cli --help
```

## Why it matters

This project is not meant to be a large production application. It is a durable workspace for continuity, learning, and context retention. The included CLI gives it a usable software layer so it functions as a real project instead of only a folder of notes.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
