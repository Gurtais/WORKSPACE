# WORKSPACE

## Overview

This repository serves as a persistent personal memory layer for long-term context retention, continuity, and recovery across development sessions, toolchains, AI workflows, and autonomous execution loops.

It is intentionally lightweight and durable, designed to preserve knowledge that is easy to lose during resets, environment rebuilds, tool migrations, or reinitialization. The repository acts as a structured archive for human context, system memory, and autonomous operational learning.

## Purpose

WORKSPACE is intended to support the following goals:

- preserve personal context over time
- maintain continuity across sessions, repos, and tools
- store ideas, notes, and task state
- record decisions, lessons learned, and operational knowledge
- support recovery after system resets or environment changes
- maintain a durable long-term knowledge base for AI and human workflows
- organize tool-specific context and execution memory
- support automatic tool learning, installation, and idle-state knowledge acquisition
- provide automated memory capture via `auto memory_save`

## Branches

- `gurtais-memory` — active personal memory branch
- `main` — clean baseline archive

## Core Memory Model

The `.memory/` directory is the primary persistence layer. It stores information that should survive across time and sessions, including:

- current session state
- personal notes
- ideas and concepts
- task tracking
- recovery instructions
- growth reflections
- operational context for future work
- learned tool knowledge and workflows
- installation and setup history
- auto-saved memory snapshots

## Auto Tool Learning and Installation

This workspace is designed to support an autonomous tooling loop:

- learn tools and workflows from use patterns
- retain discovered commands, configuration details, and setup steps
- track tool capabilities and operational assumptions
- auto-install or prepare missing tooling when needed
- maintain a local record of tool provenance, usage, and context
- reduce the need to rediscover or reconfigure known systems

This allows the environment to become more self-aware over time, learning what is useful and reusing that information in future sessions.

## Auto Memory Save

`auto memory_save` is the mechanism for continuously persisting important context to the workspace memory layer.

This includes:
- saving session state
- recording working decisions and findings
- persisting tool usage patterns
- capturing recovery context for future re-entry
- retaining relevant environment and workflow knowledge
- creating durable snapshots of important memory artifacts

The goal is to reduce the risk of losing critical continuity data during interruption, reset, or reinitialization.

## Idle Learning

The repository also supports an idle-learning model, where the system can passively accumulate knowledge while inactive or between active tasks. This includes:

- recording observed environment state
- capturing useful patterns and shell behavior
- noting stalled or recurring tasks
- storing context that becomes valuable later
- preserving learnings gathered during low-activity periods

Idle learning is useful for long-running continuity, especially in environments where valuable context is generated outside active user interaction.

## External Ecosystem

This workspace is designed to work with available plugin and tool ecosystems that extend runtime capability and automation.

Relevant references:
- DSH plugin directory: https://dsh-plugin.org/plugins
- Awesome DSH plugins repository: https://github.com/awesome-dsh-plugin/awesome-dsh-plugin
- DeepSeek plugin directory: https://deepseekplugin.com/plugins

These sources provide access to tools, integrations, and extension patterns that can be evaluated, installed, and adapted into the workspace as needed.

## Repository Structure

```text
WORKSPACE/
├── .memory/
│   ├── state/
│   │   └── current-session.md
│   ├── notes/
│   │   └── personal-notes/
│   ├── ideas/
│   │   └── brainstorms/
│   ├── tasks/
│   │   └── active-tasks.md
│   ├── reflections/
│   │   └── growth-log.md
│   ├── recovery/
│   │   └── reset-instructions.md
│   ├── tools/
│   │   └── learned-tooling.md
│   ├── idle/
│   │   └── idle-learning-log.md
│   ├── autosave/
│   │   └── memory-snapshots/
│   └── README.md
├── dsh/
│   └── shell-state/
├── dsh-dream/
│   ├── dreams/
│   ├── prompts/
│   ├── states/
│   └── artifacts/
├── memories/
│   ├── personal/
│   ├── project/
│   └── runtime/
├── plugins/
│   ├── integrations/
│   └── extensions/
├── jobs/
│   ├── active/
│   ├── completed/
│   └── recurring/
├── multibots/
│   ├── configs/
│   ├── workflows/
│   └── sessions/
├── deepmin/
│   ├── configs/
│   ├── tasks/
│   └── notes/
├── agents/
│   ├── prompts/
│   ├── workflows/
│   └── memory/
├── grok/
│   ├── notes/
│   ├── prompts/
│   └── outputs/
├── deepseek/
│   ├── notes/
│   ├── prompts/
│   └── outputs/
├── README.md
├── .gitignore
└── LICENSE
