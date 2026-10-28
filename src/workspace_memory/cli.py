from __future__ import annotations

import argparse
import sys
from pathlib import Path

from workspace_memory.storage import DEFAULT_MEMORY_DIR, MemoryStore


def _project_root() -> Path:
    return Path.cwd()


def _store() -> MemoryStore:
    return MemoryStore(_project_root() / DEFAULT_MEMORY_DIR)


def cmd_init(args: argparse.Namespace) -> int:
    store = _store()
    print(f"Initialized memory workspace at {store.root}")
    return 0


def cmd_add_note(args: argparse.Namespace) -> int:
    store = _store()
    store.add_note(args.text, category=args.category, tags=args.tags)
    print(f"Saved note in {store.notes_path()}")
    return 0


def cmd_add_task(args: argparse.Namespace) -> int:
    store = _store()
    store.add_task(args.text, category=args.category, tags=args.tags)
    print(f"Saved task in {store.tasks_path()}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    store = _store()
    info = store.status()
    print(f"Memory workspace: {info['root']}")
    print(f"Notes: {info['notes']}")
    print(f"Tasks: {info['tasks']}")
    print(f"Categories: {', '.join(info['categories']) if info['categories'] else 'none'}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = _store()
    entries = store.list_entries(category=args.category, tag=args.tag)
    if not entries:
        print("No matching entries found.")
        return 0
    for entry in entries:
        print(entry.to_line())
    return 0


def cmd_categories(args: argparse.Namespace) -> int:
    store = _store()
    categories = store.list_categories()
    if not categories:
        print("No categories found.")
        return 0
    for category in categories:
        print(category)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the WORKSPACE memory archive.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create the memory workspace structure")
    init_parser.set_defaults(func=cmd_init)

    note_parser = subparsers.add_parser("add-note", help="Add a categorized note to the memory archive")
    note_parser.add_argument("text", help="The note text to persist")
    note_parser.add_argument("--category", default="general")
    note_parser.add_argument("--tag", dest="tags", action="append", default=[])
    note_parser.set_defaults(func=cmd_add_note)

    task_parser = subparsers.add_parser("add-task", help="Add a categorized task to the active workflow list")
    task_parser.add_argument("text", help="The task description to persist")
    task_parser.add_argument("--category", default="todo")
    task_parser.add_argument("--tag", dest="tags", action="append", default=[])
    task_parser.set_defaults(func=cmd_add_task)

    status_parser = subparsers.add_parser("status", help="Show memory workspace status")
    status_parser.set_defaults(func=cmd_status)

    list_parser = subparsers.add_parser("list", help="List memory entries")
    list_parser.add_argument("--category")
    list_parser.add_argument("--tag")
    list_parser.set_defaults(func=cmd_list)

    categories_parser = subparsers.add_parser("categories", help="List all categories used")
    categories_parser.set_defaults(func=cmd_categories)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
