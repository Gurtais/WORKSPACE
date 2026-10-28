from __future__ import annotations

from pathlib import Path
from typing import Iterable

from workspace_memory.models import MemoryEntry


DEFAULT_MEMORY_DIR = Path(".memory")


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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

    def list_entries(self, kind: str | None = None, category: str | None = None, tag: str | None = None) -> list[MemoryEntry]:
        entries: list[MemoryEntry] = []
        for target_kind, path in (("note", self.notes_path()), ("task", self.tasks_path())):
            if kind is not None and target_kind != kind:
                continue
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip() or line.startswith("#") or not line.startswith("-"):
                    continue
                entry = self._parse_line(target_kind, line)
                if category and entry.category != category:
                    continue
                if tag and tag.lower() not in {value.lower() for value in entry.tags}:
                    continue
                entries.append(entry)
        return entries

    def list_categories(self) -> list[str]:
        categories: set[str] = set()
        for entry in self.list_entries():
            categories.add(entry.category)
        return sorted(categories)

    def search_by_tag(self, tag: str) -> list[MemoryEntry]:
        return self.list_entries(tag=tag)

    def _parse_line(self, kind: str, line: str) -> MemoryEntry:
        text = line.lstrip("-").strip()
        if "[" in text and "]" in text:
            # rough extraction for tags/category metadata
            marker_end = text.find("]")
            if marker_end > 0:
                rest = text[marker_end + 1 :].strip()
                if rest.startswith("["):
                    end = rest.find("]")
                    if end > 0:
                        category = rest[1:end]
                        rest = rest[end + 1 :].strip()
                    else:
                        category = "general"
                else:
                    category = "general"
            else:
                category = "general"
            rest = rest.strip()
            if rest.startswith("["):
                tags_part = rest[1 : rest.find("]")]
                rest = rest[rest.find("]") + 1 :].strip()
                tags = [item.strip() for item in tags_part.split(",") if item.strip()]
            else:
                tags = []
        else:
            category = "general"
            tags = []
            rest = text

        return MemoryEntry(kind=kind, text=rest, category=category, tags=tags)

    def status(self) -> dict[str, object]:
        notes = self.list_entries(kind="note")
        tasks = self.list_entries(kind="task")
        return {
            "root": str(self.root),
            "notes": len(notes),
            "tasks": len(tasks),
            "categories": self.list_categories(),
        }


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
