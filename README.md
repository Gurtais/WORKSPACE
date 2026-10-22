# WORKSPACE
NOTHING SPECIAL 
git clone https://github.com/Gurtais/WORKSPACE.git
cd WORKSPACE

git checkout -b gurtais-memory

mkdir -p .memory .github/workflows

cat > README.md <<'EOF'
# WORKSPACE

Personal memory and continuity workspace.

This repository is used as a persistent memory layer for personal development, context retention, and long-term project continuity.

## Branches

- `gurtais-memory` — active personal memory branch
- `main` — clean baseline archive

## Purpose

- preserve personal context
- store ideas and tasks
- maintain session continuity
- recover from reset or reinitialization
- keep a durable long-term knowledge base

## Memory folder

The `.memory/` directory is the main persistence layer.
It stores:
- current session state
- personal notes
- ideas
- tasks
- recovery instructions
- growth reflections
EOF

cat > .gitignore <<'EOF'
.DS_Store
EOF

cat > .memory/README.md <<'EOF'
# Memory workspace

This directory is the persistent memory layer for the personal workspace.

Purpose:
- keep personal context
- store ideas and tasks
- preserve session continuity
- restore state after resets or reinitialization
- maintain a stable personal knowledge base

Files in this folder:
- project-context.yaml
- session-memory.md
- restore-steps.md
- chat-history.txt
- project-summary.md
- current-task.md
- last-session-state.md
- personal-growth.md
- ideas-bank.md
- tasks.md
- daily-log.md
EOF

cat > .memory/project-context.yaml <<'EOF'
repository:
  owner: Gurtais
  name: WORKSPACE
  branch: gurtais-memory

memory:
  folder: .memory
  purpose: "personal continuity, knowledge retention, and restore layer"

files:
  - README.md
  - project-context.yaml
  - session-memory.md
  - restore-steps.md
  - chat-history.txt
  - project-summary.md
  - current-task.md
  - last-session-state.md
  - personal-growth.md
  - ideas-bank.md
  - tasks.md
  - daily-log.md

rules:
  - "keep .memory in the repository root"
  - "never delete it"
  - "restore it after cleanup or reset"
  - "keep the personal context alive"
EOF

cat > .memory/session-memory.md <<'EOF'
# Session memory

Repository: WORKSPACE
Branch: gurtais-memory

This file stores the current personal and project state so work can continue after reset or reinitialization.

The goal:
- preserve context
- maintain personal continuity
- keep ideas and tasks alive
- restore quickly after wipe or cleanup
EOF

cat > .memory/restore-steps.md <<'EOF'
# Restore steps

If the repository is reset or recreated:

1. Open WORKSPACE
2. Check `.memory/`
3. Restore the files from backup or local disk
4. Reopen `session-memory.md`
5. Resume from the last stable state
6. Keep `.memory/` untouched unless intentionally clearing memory
EOF

cat > .memory/chat-history.txt <<'EOF'
Personal memory snapshot
Repository: WORKSPACE
Branch: gurtais-memory

Use this file to keep:
- conversation summary
- core ideas
- current tasks
- decisions
- personal growth notes
EOF

cat > .memory/project-summary.md <<'EOF'
# Project summary

Repository: WORKSPACE
Branch: gurtais-memory

This is a personal continuity workspace for:
- ideas
- tasks
- growth
- long-term memory
- project context

The main objective is to keep personal context alive outside the active session.
EOF

cat > .memory/current-task.md <<'EOF'
# Current task

Repository: WORKSPACE
Branch: gurtais-memory

Current focus:
- build a stable personal memory system
- preserve context over time
- keep a working knowledge layer

Next step:
- continue from the last stable state
- restore from `.memory/` if needed
EOF

cat > .memory/last-session-state.md <<'EOF'
# Last session state

Repository: WORKSPACE
Branch: gurtais-memory

Last known state:
- memory folder exists
- context is stored in `.memory/`
- restoration path is defined
- continuity is preserved

This is a short checkpoint for recovery.
EOF

cat > .memory/personal-growth.md <<'EOF'
# Personal growth

This file stores progress, insights, reflections, and patterns for personal development.

Focus:
- skill growth
- self-knowledge
- emotional balance
- life direction
- long-term learning
EOF

cat > .memory/ideas-bank.md <<'EOF'
# Ideas bank

Store ideas here:
- projects
- experiments
- business ideas
- research topics
- creative concepts
- future opportunities
EOF

cat > .memory/tasks.md <<'EOF'
# Tasks

Keep current and future tasks here.

- maintain memory system
- preserve personal context
- improve understanding
- expand knowledge and skills
- build durable personal infrastructure
EOF

cat > .memory/daily-log.md <<'EOF'
# Daily log

Use this file for:
- daily reflections
- what was learned
- what happened
- what to improve
- what to continue tomorrow
EOF

cat > .github/workflows/memory-guard.yml <<'EOF'
name: Memory Guard
on:
  push:
    branches: [main, gurtais-memory]
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: gurtais-memory
          fetch-depth: 0

      - name: Check .memory exists and is complete
        run: |
          test -d .memory || { echo ".memory missing"; exit 1; }

          for f in \
            README.md \
            project-context.yaml \
            session-memory.md \
            restore-steps.md \
            chat-history.txt \
            project-summary.md \
            current-task.md \
            last-session-state.md \
            personal-growth.md \
            ideas-bank.md \
            tasks.md \
            daily-log.md
          do
            test -s ".memory/$f" || { echo ".memory/$f missing or empty"; exit 1; }
          done
EOF

cat > .github/workflows/memory-auto-save.yml <<'EOF'
name: Memory Auto Save
on:
  workflow_dispatch:
  schedule:
    - cron: '0 20 * * *'

jobs:
  autosave:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: gurtais-memory
          fetch-depth: 0

      - name: Ensure memory files exist
        run: |
          test -d .memory || { echo ".memory missing"; exit 1; }

      - name: Commit memory snapshot
        run: |
          git config user.name "Gurtais"
          git config user.email "gurtais@users.noreply.github.com"
          git add .
          if git diff --cached --quiet; then
            echo "No changes to commit"
          else
            git commit -m "memory: auto-save $(date -u +%Y-%m-%dT%H:%M:%SZ)"
            git push origin gurtais-memory
          fi
EOF

git add .
git commit -m "Initialize WORKSPACE memory layer"
git push -u origin gurtais-memory