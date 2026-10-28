from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from workspace_memory.models import MemoryEntry


DEFAULT_MEMORY_DIR = Path(".memory")


class MemoryStore:
    def __init__(self, root: Path | str = DEFAULT_MEMORY_DIR):
        self.root = Path(root)
        self.db_path = self.root / "workspace.db"
        self.ensure_workspace()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    tags TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def notes_path(self) -> Path:
        return self.root / "notes" / "notes.md"

    def tasks_path(self) -> Path:
        return self.root / "tasks" / "active-tasks.md"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _tags_to_text(self, tags: Iterable[str]) -> str:
        return ",".join(sorted({tag.strip().lower() for tag in tags if tag and tag.strip()}))

    def add_note(self, text: str, category: str = "general", tags: Iterable[str] | None = None) -> MemoryEntry:
        entry = MemoryEntry(kind="note", text=text, category=category, tags=list(tags or []), created_at=self._now_iso())
        self._insert(entry)
        return entry

    def add_task(self, text: str, category: str = "todo", tags: Iterable[str] | None = None) -> MemoryEntry:
        entry = MemoryEntry(kind="task", text=text, category=category, tags=list(tags or []), created_at=self._now_iso())
        self._insert(entry)
        return entry

    def _insert(self, entry: MemoryEntry) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO entries (kind, text, category, tags, created_at) VALUES (?, ?, ?, ?, ?)",
                (entry.kind, entry.text, entry.category, self._tags_to_text(entry.normalized_tags), entry.created_at),
            )
            conn.commit()

    def list_entries(
        self,
        kind: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        text_query: str | None = None,
    ) -> list[MemoryEntry]:
        sql = "SELECT id, kind, text, category, tags, created_at FROM entries WHERE 1 = 1"
        params: list[str] = []

        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if category:
            sql += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        if tag:
            sql += " AND LOWER(tags) LIKE ?"
            params.append(f"%{tag.lower()}%")
        if text_query:
            sql += " AND LOWER(text) LIKE ?"
            params.append(f"%{text_query.lower()}%")

        sql += " ORDER BY created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        entries: list[MemoryEntry] = []
        for row in rows:
            tags = [item.strip() for item in row["tags"].split(",") if item.strip()] if row["tags"] else []
            entries.append(
                MemoryEntry(
                    kind=row["kind"],
                    text=row["text"],
                    category=row["category"],
                    tags=tags,
                    created_at=row["created_at"],
                )
            )
        return entries

    def update_entry(self, entry_id: int, *, text: str | None = None, category: str | None = None, tags: Iterable[str] | None = None) -> MemoryEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, kind, text, category, tags, created_at FROM entries WHERE id = ?",
                (entry_id,),
            ).fetchone()
            if row is None:
                return None

            updated_text = text if text is not None else row["text"]
            updated_category = category if category is not None else row["category"]
            updated_tags = self._tags_to_text(tags if tags is not None else [item.strip() for item in (row["tags"] or "").split(",") if item.strip()])

            conn.execute(
                "UPDATE entries SET text = ?, category = ?, tags = ? WHERE id = ?",
                (updated_text, updated_category, updated_tags, entry_id),
            )
            conn.commit()

        return MemoryEntry(
            kind=row["kind"],
            text=updated_text,
            category=updated_category,
            tags=[item.strip() for item in updated_tags.split(",") if item.strip()],
            created_at=row["created_at"],
        )

    def delete_entry(self, entry_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_categories(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT category FROM entries ORDER BY category ASC").fetchall()
        return [row["category"] for row in rows]

    def search_by_tag(self, tag: str) -> list[MemoryEntry]:
        return self.list_entries(tag=tag)

    def search(self, query: str) -> list[MemoryEntry]:
        return self.list_entries(text_query=query)

    def status(self) -> dict[str, object]:
        with self._connect() as conn:
            notes = conn.execute("SELECT COUNT(*) as total FROM entries WHERE kind = 'note'").fetchone()["total"]
            tasks = conn.execute("SELECT COUNT(*) as total FROM entries WHERE kind = 'task'").fetchone()["total"]
        return {
            "root": str(self.root),
            "notes": notes,
            "tasks": tasks,
            "categories": self.list_categories(),
        }

    def export_markdown(self, file_path: str | Path) -> Path:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# WORKSPACE Memory Export\n"]
        for category in self.list_categories():
            lines.append(f"## {category}\n")
            for entry in self.list_entries(category=category):
                lines.append(f"- **{entry.kind}**: {entry.text}\n")
                if entry.tags:
                    lines.append(f"  Tags: {', '.join(entry.tags)}\n")
                lines.append(f"  Created: {entry.created_at}\n")
        target.write_text("".join(lines), encoding="utf-8")
        return target

    def export_csv(self, file_path: str | Path) -> Path:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "kind", "text", "category", "tags", "created_at"])
            writer.writeheader()
            for entry in self.list_entries():
                writer.writerow({
                    "id": "",
                    "kind": entry.kind,
                    "text": entry.text,
                    "category": entry.category,
                    "tags": ",".join(entry.tags),
                    "created_at": entry.created_at,
                })
        return target

    def export_json(self, file_path: str | Path) -> Path:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "kind": entry.kind,
                "text": entry.text,
                "category": entry.category,
                "tags": entry.tags,
                "created_at": entry.created_at,
            }
            for entry in self.list_entries()
        ]
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
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
            if "**note**:" in content.lower():
                self.add_note(content.split(":", 1)[1].strip())
                imported += 1
            elif "**task**:" in content.lower():
                self.add_task(content.split(":", 1)[1].strip())
                imported += 1
        return imported

    def import_csv(self, file_path: str | Path) -> int:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")

        imported = 0
        with source.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                text = (row.get("text") or "").strip()
                if not text:
                    continue
                kind = (row.get("kind") or "note").strip()
                category = (row.get("category") or "general").strip()
                tags = [item.strip() for item in (row.get("tags") or "").split(",") if item.strip()]
                if kind == "task":
                    self.add_task(text, category=category, tags=tags)
                else:
                    self.add_note(text, category=category, tags=tags)
                imported += 1
        return imported

    def import_json(self, file_path: str | Path) -> int:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"JSON file not found: {source}")

        payload = json.loads(source.read_text(encoding="utf-8"))
        imported = 0
        for item in payload:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            kind = item.get("kind", "note")
            category = item.get("category") or "general"
            tags = item.get("tags") or []
            if kind == "task":
                self.add_task(text, category=category, tags=tags)
            else:
                self.add_note(text, category=category, tags=tags)
            imported += 1
        return imported

    def import_any(self, file_path: str | Path, file_format: str | None = None) -> int:
        path = Path(file_path)
        fmt = (file_format or path.suffix.lower().lstrip(".") or "markdown").lower()
        if fmt in {"md", "markdown"}:
            return self.import_markdown(path)
        if fmt == "csv":
            return self.import_csv(path)
        if fmt in {"json", "jsn"}:
            return self.import_json(path)
        raise ValueError(f"Unsupported import format: {fmt}")

    def export_any(self, file_path: str | Path, file_format: str | None = None) -> Path:
        path = Path(file_path)
        fmt = (file_format or path.suffix.lower().lstrip(".") or "markdown").lower()
        if fmt in {"md", "markdown"}:
            return self.export_markdown(path)
        if fmt == "csv":
            return self.export_csv(path)
        if fmt in {"json", "jsn"}:
            return self.export_json(path)
        raise ValueError(f"Unsupported export format: {fmt}")


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


__all__ = ["MemoryStore", "DEFAULT_MEMORY_DIR", "ensure_workspace"]
