from __future__ import annotations

import argparse
from pathlib import Path

from workspace_memory.storage import (
    DEFAULT_MEMORY_DIR,
    append_line,
    ensure_workspace,
    list_memory_files,
    now_iso,
    read_text,
    summarize_entries,
)


def _project_root() -> Path:
    return Path.cwd()


def cmd_init(args: argparse.Namespace) -> int:
    root = ensure_workspace(_project_root() / DEFAULT_MEMORY_DIR)
    print(f"Initialized memory workspace at {root}")
    return 0


def cmd_add_note(args: argparse.Namespace) -> int:
    root = ensure_workspace(_project_root() / DEFAULT_MEMORY_DIR)
    note_path = root / "notes" / "notes.md"
    entry = f"[{now_iso()}] {args.text}"
    append_line(note_path, entry)
    print(f"Saved note to {note_path}")
    return 0


def cmd_add_task(args: argparse.Namespace) -> int:
    root = ensure_workspace(_project_root() / DEFAULT_MEMORY_DIR)
    task_path = root / "tasks" / "active-tasks.md"
    entry = f"- [{now_iso()}] {args.text}"
    if not task_path.exists():
        task_path.write_text("# Active Tasks\n\n", encoding="utf-8")
    append_line(task_path, entry)
    print(f"Saved task to {task_path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = _project_root() / DEFAULT_MEMORY_DIR
    if not root.exists():
        print("No workspace memory initialized yet.")
        return 1

    files = list_memory_files(root)
    print(f"Memory workspace: {root}")
    print(f"Tracked files: {len(files)}")
    for file_path in files[:10]:
        print(f"- {file_path.relative_to(root.parent)}")
    if len(files) > 10:
        print("- ...")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    root = _project_root() / DEFAULT_MEMORY_DIR
    if not root.exists():
        print("No workspace memory initialized yet.")
        return 1

    files = list_memory_files(root)
    for file_path in summarize_entries(files):
        print(file_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the WORKSPACE memory archive.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create the memory workspace structure")
    init_parser.set_defaults(func=cmd_init)

    note_parser = subparsers.add_parser("add-note", help="Add a note to the memory archive")
    note_parser.add_argument("text", help="The note text to persist")
    note_parser.set_defaults(func=cmd_add_note)

    task_parser = subparsers.add_parser("add-task", help="Add a task to the active task list")
    task_parser.add_argument("text", help="The task description to persist")
    task_parser.set_defaults(func=cmd_add_task)

    status_parser = subparsers.add_parser("status", help="Show memory workspace status")
    status_parser.set_defaults(func=cmd_status)

    list_parser = subparsers.add_parser("list", help="List files stored in the memory workspace")
    list_parser.set_defaults(func=cmd_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
