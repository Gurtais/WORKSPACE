from __future__ import annotations

from pathlib import Path
from typing import Iterable

from workspace_memory.models import MemoryEntry


DEFAULT_MEMORY_DIR = Path(".memory")


class MemoryStore:
    def __init__(self, root: Path | str = DEFAULT_MEMORY_DIR):
        self.root = Path(root)
        self.ensure_workspace()

    def ensure_workspace(self) -> Path:
        required = [
            self.root,
            self.root / "state",
            self.root / "tasks",
            self.root / "reflections",
            self.root / "recovery",
            self.root / "tools",
            self.root / "notes",
        ]
        for directory in required:
            directory.mkdir(parents=True, exist_ok=True)

        readme = self.root / "README.md"
        if not readme.exists():
            readme.write_text(
                "# Memory\n\nThis directory stores the durable project memory for the workspace.\n",
                encoding="utf-8",
            )

        return self.root

    def notes_path(self) -> Path:
        return self.root / "notes" / "notes.md"

    def tasks_path(self) -> Path:
        return self.root / "tasks" / "active-tasks.md"

    def add_note(self, text: str, category: str = "general", tags: Iterable[str] | None = None) -> MemoryEntry:
        entry = MemoryEntry(kind="note", text=text, category=category, tags=list(tags or []))
        self._append_entry(self.notes_path(), entry)
        return entry

    def add_task(self, text: str, category: str = "todo", tags: Iterable[str] | None = None) -> MemoryEntry:
        entry = MemoryEntry(kind="task", text=text, category=category, tags=list(tags or []))
        self._append_entry(self.tasks_path(), entry)
        return entry

    def _append_entry(self, path: Path, entry: MemoryEntry) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            header = "# Memory Entries\n\n" if "notes" in str(path) else "# Active Tasks\n\n"
            path.write_text(header, encoding="utf-8")

        with path.open("a", encoding="utf-8") as handle:
            handle.write(entry.to_line() + "\n")

    def _load_entries_from_file(self, path: Path, kind: str) -> list[MemoryEntry]:
        if not path.exists():
            return []

        entries: list[MemoryEntry] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#") or not line.startswith("-"):
                continue
            entries.append(self._parse_line(kind, line))
        return entries

    def list_entries(
        self,
        kind: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        text_query: str | None = None,
    ) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for target_kind, path in (("note", self.notes_path()), ("task", self.tasks_path())):
            if kind is not None and target_kind != kind:
                continue
            entries.extend(self._load_entries_from_file(path, target_kind))

        filtered: list[MemoryEntry] = []
        for entry in entries:
            if category and entry.category.lower() != category.lower():
                continue
            if tag and tag.lower() not in {value.lower() for value in entry.tags}:
                continue
            if text_query and text_query.lower() not in entry.text.lower():
                continue
            filtered.append(entry)
        return filtered

    def list_categories(self) -> list[str]:
        categories: set[str] = set()
        for entry in self.list_entries():
            categories.add(entry.category)
        return sorted(categories)

    def search_by_tag(self, tag: str) -> list[MemoryEntry]:
        return self.list_entries(tag=tag)

    def search(self, query: str) -> list[MemoryEntry]:
        return self.list_entries(text_query=query)

    def _parse_line(self, kind: str, line: str) -> MemoryEntry:
        text = line.lstrip("-").strip()
        category = "general"
        tags: list[str] = []

        i = text.find("]")
        if i != -1:
            # format: [timestamp] [category] [tag1,tag2] text
            rest = text[i + 1 :].strip()
            if rest.startswith("["):
                category_end = rest.find("]")
                if category_end != -1:
                    category = rest[1:category_end].strip() or "general"
                    rest = rest[category_end + 1 :].strip()
            else:
                category = "general"

            if rest.startswith("["):
                tags_end = rest.find("]")
                if tags_end != -1:
                    tags_str = rest[1:tags_end]
                    tags = [item.strip() for item in tags_str.split(",") if item.strip()]
                    rest = rest[tags_end + 1 :].strip()

            text_body = rest
        else:
            text_body = text

        return MemoryEntry(kind=kind, text=text_body, category=category, tags=tags)

    def status(self) -> dict[str, object]:
        notes = self.list_entries(kind="note")
        tasks = self.list_entries(kind="task")
        return {
            "root": str(self.root),
            "notes": len(notes),
            "tasks": len(tasks),
            "categories": self.list_categories(),
        }

    def export_markdown(self, file_path: str | Path) -> Path:
        target = Path(file_path)
        lines = ["# WORKSPACE Memory Export\n"]
        for category in self.list_categories():
            lines.append(f"## {category}\n")
            for entry in self.list_entries(category=category):
                lines.append(f"- **{entry.kind}**: {entry.text}\n")
                if entry.tags:
                    lines.append(f"  Tags: {', '.join(entry.tags)}\n")
                lines.append(f"  Created: {entry.created_at}\n")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(lines), encoding="utf-8")
        return target

    def import_markdown(self, file_path: str | Path) -> int:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"Markdown file not found: {source}")

        imported = 0
        for line in source.read_text(encoding="utf-8").splitlines():
            if not line.startswith("- "):
                continue

            content = line[2:].strip()
            if not content:
                continue
            if "**note**:" in content.lower():
                text = content.split(":", 1)[1].strip()
                self.add_note(text)
                imported += 1
            elif "**task**:" in content.lower():
                text = content.split(":", 1)[1].strip()
                self.add_task(text)
                imported += 1
        return imported


def ensure_workspace(memory_dir: Path | str = DEFAULT_MEMORY_DIR) -> Path:
    return MemoryStore(memory_dir).root


def append_line(file_path: Path | str, content: str) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content.rstrip() + "\n")
    return path


def read_text(file_path: Path | str) -> str:
    path = Path(file_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def list_memory_files(memory_dir: Path | str = DEFAULT_MEMORY_DIR) -> list[Path]:
    root = Path(memory_dir)
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file())


def summarize_entries(paths: Iterable[Path]) -> list[str]:
    return [str(path) for path in paths]
