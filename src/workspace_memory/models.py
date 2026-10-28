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
    store.add_note(args.text, category=args.category, tags=args.tags, status=args.status)
    print(f"Saved note in {store.notes_path()}")
    return 0


def cmd_add_task(args: argparse.Namespace) -> int:
    store = _store()
    store.add_task(args.text, category=args.category, tags=args.tags, status=args.status)
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
    entries = store.list_entries(category=args.category, tag=args.tag, text_query=args.query, status=args.status, sort_by=args.sort_by, order=args.order)
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


def cmd_export(args: argparse.Namespace) -> int:
    store = _store()
    target = store.export_any(args.output, args.format)
    print(f"Exported data to {target}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    store = _store()
    count = store.import_any(args.input, args.format)
    print(f"Imported {count} entries from {args.input}")
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
    note_parser.add_argument("--status", choices=["new", "active", "done", "blocked"], default="new")
    note_parser.set_defaults(func=cmd_add_note)

    task_parser = subparsers.add_parser("add-task", help="Add a categorized task to the active workflow list")
    task_parser.add_argument("text", help="The task description to persist")
    task_parser.add_argument("--category", default="todo")
    task_parser.add_argument("--tag", dest="tags", action="append", default=[])
    task_parser.add_argument("--status", choices=["new", "active", "done", "blocked"], default="new")
    task_parser.set_defaults(func=cmd_add_task)

    status_parser = subparsers.add_parser("status", help="Show memory workspace status")
    status_parser.set_defaults(func=cmd_status)

    list_parser = subparsers.add_parser("list", help="List memory entries")
    list_parser.add_argument("--category")
    list_parser.add_argument("--tag")
    list_parser.add_argument("--query", help="Text search within entries")
    list_parser.add_argument("--status", choices=["new", "active", "done", "blocked"])
    list_parser.add_argument("--sort-by", choices=["created_at", "category", "status", "kind"], default="created_at")
    list_parser.add_argument("--order", choices=["asc", "desc"], default="desc")
    list_parser.set_defaults(func=cmd_list)

    categories_parser = subparsers.add_parser("categories", help="List all categories used")
    categories_parser.set_defaults(func=cmd_categories)

    export_parser = subparsers.add_parser("export", help="Export entries to a file")
    export_parser.add_argument("output", help="Output path")
    export_parser.add_argument("--format", choices=["markdown", "md", "csv", "json"], default=None)
    export_parser.set_defaults(func=cmd_export)

    import_parser = subparsers.add_parser("import", help="Import entries from a file")
    import_parser.add_argument("input", help="Input path")
    import_parser.add_argument("--format", choices=["markdown", "md", "csv", "json"], default=None)
    import_parser.set_defaults(func=cmd_import)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
