from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from workspace_memory.models import MemoryEntry


DEFAULT_MEMORY_DIR = Path(".memory")
VALID_ENTRY_STATUSES = {"new", "active", "done", "blocked"}


def normalize_entry_status(status: str | None, default: str = "new") -> str:
    value = (status or default).strip().lower()
    if not value:
        value = default
    if value not in VALID_ENTRY_STATUSES:
        valid = ", ".join(sorted(VALID_ENTRY_STATUSES))
        raise ValueError(f"Unsupported status: {status!r}. Valid statuses are: {valid}")
    return value


def normalize_entry_category(category: str | None, default: str) -> str:
    value = (category or default).strip()
    if not value:
        value = default
    return value


def normalize_entry_tags(tags: Iterable[str] | None) -> list[str]:
    return [tag.strip() for tag in (tags or []) if tag and tag.strip()]


def normalize_entry_datetime(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            f"Invalid {field_name}: {value!r}. Use ISO date or datetime values like YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ."
        ) from exc
    return value.strip()


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
            readme.write_text("# Memory\n\nThis directory stores the durable project memory for the workspace.\n", encoding="utf-8")
        return self.root

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    display_name TEXT,
                    role TEXT DEFAULT 'user',
                    bio TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    display_name TEXT,
                    role TEXT DEFAULT 'user',
                    bio TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    tags TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'new',
                    due_at TEXT,
                    reminder_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_status ON entries(user_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_due ON entries(user_id, due_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_category ON entries(user_id, category, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_kind ON entries(user_id, kind)")
            conn.commit()

            self._ensure_default_user(conn)

    def _ensure_default_user(self, conn: sqlite3.Connection) -> int:
        username = "workspace"
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if user is not None:
            return int(user["id"])

        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        password_hash = self._hash_password("workspace")
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, created_at, display_name, role, bio) VALUES (?, ?, ?, ?, ?, ?)",
            (username, password_hash, created, "Workspace User", "admin", "Default local workspace user."),
        )
        user_id = int(cursor.lastrowid)
        conn.execute(
            "INSERT INTO profiles (user_id, display_name, role, bio, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, "Workspace User", "admin", "Default local workspace user.", created),
        )
        conn.commit()
        return user_id

    def _hash_password(self, password: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), b"workspace-salt", 100_000).hex()

    def _default_user_id(self) -> int:
        with self._connect() as conn:
            return self._ensure_default_user(conn)

    @staticmethod
    def _coerce_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            try:
                return datetime.strptime(text, "%Y-%m-%d")
            except ValueError:
                return None

    def _is_overdue(self, entry: MemoryEntry) -> bool:
        if entry.status in {"done", "blocked"}:
            return False
        due_at = self._coerce_datetime(entry.due_at)
        if due_at is None:
            return False
        today = datetime.now(timezone.utc).date()
        due_date = due_at.date()
        return due_date < today

    def _is_upcoming(self, entry: MemoryEntry, days: int = 7) -> bool:
        if entry.status in {"done", "blocked"}:
            return False
        due_at = self._coerce_datetime(entry.due_at)
        if due_at is None:
            return False
        today = datetime.now(timezone.utc).date()
        due_date = due_at.date()
        cutoff = today + timedelta(days=days)
        return today <= due_date <= cutoff

    def create_user(self, username: str, password: str, display_name: str | None = None, role: str = "user", bio: str | None = None) -> dict[str, object]:
        if not username or not password:
            raise ValueError("Username and password are required.")
        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash, created_at, display_name, role, bio) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, self._hash_password(password), created, display_name or username, role, bio or ""),
                )
                user_id = int(cursor.lastrowid)
                conn.execute(
                    "INSERT INTO profiles (user_id, display_name, role, bio, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, display_name or username, role, bio or "", created),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("Username already exists.") from exc
        return {"id": user_id, "username": username, "display_name": display_name or username, "role": role, "bio": bio or ""}

    def verify_user(self, username: str, password: str) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, display_name, role, bio FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row is None:
                return None
            if row["password_hash"] != self._hash_password(password):
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "role": row["role"],
                "bio": row["bio"] or "",
            }

    def get_user_profile(self, user_id: int) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT u.id, u.username, COALESCE(p.display_name, u.display_name, u.username) as display_name, COALESCE(p.role, u.role, 'user') as role, COALESCE(p.bio, u.bio, '') as bio FROM users u LEFT JOIN profiles p ON p.user_id = u.id WHERE u.id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "role": row["role"],
                "bio": row["bio"],
            }

    def update_profile(self, user_id: int, *, display_name: str | None, role: str | None, bio: str | None) -> dict[str, object] | None:
        profile = self.get_user_profile(user_id)
        if profile is None:
            return None

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO profiles (user_id, display_name, role, bio, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET display_name = excluded.display_name, role = excluded.role, bio = excluded.bio, created_at = excluded.created_at",
                (
                    user_id,
                    display_name or profile["display_name"],
                    role or profile["role"],
                    bio if bio is not None else profile["bio"],
                    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                ),
            )
            conn.execute(
                "UPDATE users SET display_name = ?, role = ? WHERE id = ?",
                (display_name or profile["display_name"], role or profile["role"], user_id),
            )
            conn.commit()
        return self.get_user_profile(user_id)

    def _tags_to_text(self, tags: Iterable[str]) -> str:
        return ",".join(sorted({tag.strip().lower() for tag in normalize_entry_tags(tags) if tag and tag.strip()}))

    def add_note(self, text: str, category: str = "general", tags: Iterable[str] | None = None, status: str = "new", user_id: int | None = None, due_at: str | None = None, reminder_at: str | None = None) -> MemoryEntry:
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Text cannot be empty.")
        cleaned_category = normalize_entry_category(category, "general")
        cleaned_tags = normalize_entry_tags(tags)
        cleaned_status = normalize_entry_status(status)
        cleaned_due_at = normalize_entry_datetime(due_at, "due_at")
        cleaned_reminder_at = normalize_entry_datetime(reminder_at, "reminder_at")

        entry = MemoryEntry(
            kind="note",
            text=cleaned_text,
            category=cleaned_category,
            tags=cleaned_tags,
            status=cleaned_status,
            due_at=cleaned_due_at,
            reminder_at=cleaned_reminder_at,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self._insert(entry, user_id=user_id)
        return entry

    def add_task(self, text: str, category: str = "todo", tags: Iterable[str] | None = None, status: str = "new", user_id: int | None = None, due_at: str | None = None, reminder_at: str | None = None) -> MemoryEntry:
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Text cannot be empty.")
        cleaned_category = normalize_entry_category(category, "todo")
        cleaned_tags = normalize_entry_tags(tags)
        cleaned_status = normalize_entry_status(status)
        cleaned_due_at = normalize_entry_datetime(due_at, "due_at")
        cleaned_reminder_at = normalize_entry_datetime(reminder_at, "reminder_at")

        entry = MemoryEntry(
            kind="task",
            text=cleaned_text,
            category=cleaned_category,
            tags=cleaned_tags,
            status=cleaned_status,
            due_at=cleaned_due_at,
            reminder_at=cleaned_reminder_at,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self._insert(entry, user_id=user_id)
        return entry

    def _insert(self, entry: MemoryEntry, *, user_id: int | None = None) -> None:
        owner_id = user_id if user_id is not None else self._default_user_id()
        now = entry.created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO entries (user_id, kind, text, category, tags, status, due_at, reminder_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    owner_id,
                    entry.kind,
                    entry.text,
                    normalize_entry_category(entry.category, "general"),
                    self._tags_to_text(entry.normalized_tags),
                    normalize_entry_status(entry.status),
                    normalize_entry_datetime(entry.due_at, "due_at"),
                    normalize_entry_datetime(entry.reminder_at, "reminder_at"),
                    now,
                    now,
                ),
            )
            conn.commit()
            entry.id = int(cursor.lastrowid)

    def list_entries(
        self,
        kind: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        text_query: str | None = None,
        status: str | None = None,
        user_id: int | None = None,
        due_before: str | None = None,
        due_after: str | None = None,
        reminder_before: str | None = None,
        reminder_after: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[MemoryEntry]:
        sql = "SELECT id, user_id, kind, text, category, tags, status, due_at, reminder_at, created_at, updated_at FROM entries WHERE 1 = 1"
        params: list[str] = []

        if user_id is not None:
            sql += " AND user_id = ?"
            params.append(str(user_id))
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
        if status:
            sql += " AND LOWER(status) = LOWER(?)"
            params.append(normalize_entry_status(status))
        if due_before:
            sql += " AND due_at IS NOT NULL AND due_at <= ?"
            params.append(due_before)
        if due_after:
            sql += " AND due_at IS NOT NULL AND due_at >= ?"
            params.append(due_after)
        if reminder_before:
            sql += " AND reminder_at IS NOT NULL AND reminder_at <= ?"
            params.append(reminder_before)
        if reminder_after:
            sql += " AND reminder_at IS NOT NULL AND reminder_at >= ?"
            params.append(reminder_after)

        valid_sort = {"created_at": "created_at", "category": "category", "status": "status", "kind": "kind", "updated_at": "updated_at", "due_at": "due_at"}
        sort_field = valid_sort.get(sort_by, "created_at")
        order_sql = "DESC" if str(order).lower() == "desc" else "ASC"
        sql += f" ORDER BY {sort_field} {order_sql}"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        entries: list[MemoryEntry] = []
        for row in rows:
            tags = [item.strip() for item in (row["tags"] or "").split(",") if item.strip()]
            entry = MemoryEntry(
                id=row["id"],
                kind=row["kind"],
                text=row["text"],
                category=row["category"],
                tags=tags,
                status=row["status"],
                due_at=row["due_at"],
                reminder_at=row["reminder_at"],
                created_at=row["created_at"],
            )
            entries.append(entry)
        return entries

    def list_overdue_tasks(self, user_id: int | None = None) -> list[MemoryEntry]:
        entries = self.list_entries(user_id=user_id, sort_by="due_at", order="asc")
        return [entry for entry in entries if entry.kind == "task" and self._is_overdue(entry)]

    def list_upcoming_tasks(self, user_id: int | None = None, days: int = 7) -> list[MemoryEntry]:
        entries = self.list_entries(user_id=user_id, sort_by="due_at", order="asc")
        return [entry for entry in entries if entry.kind == "task" and self._is_upcoming(entry, days=days)]

    def task_summary(self, user_id: int | None = None) -> dict[str, object]:
        entries = self.list_entries(user_id=user_id)
        tasks = [entry for entry in entries if entry.kind == "task"]
        counts = {status: 0 for status in sorted(VALID_ENTRY_STATUSES)}
        for entry in tasks:
            counts[entry.status] = counts.get(entry.status, 0) + 1
        return {
            "total_tasks": len(tasks),
            "overdue": len(self.list_overdue_tasks(user_id=user_id)),
            "upcoming": len(self.list_upcoming_tasks(user_id=user_id, days=7)),
            "status_counts": counts,
        }

    def update_entry(self, entry_id: int, *, user_id: int | None = None, text: str | None = None, category: str | None = None, tags: Iterable[str] | None = None, status: str | None = None, due_at: str | None = None, reminder_at: str | None = None) -> MemoryEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, kind, text, category, tags, status, due_at, reminder_at, created_at FROM entries WHERE id = ? AND (? IS NULL OR user_id = ?)",
                (entry_id, user_id, user_id),
            ).fetchone()
            if row is None:
                return None

            updated_text = (text or row["text"]).strip()
            if not updated_text:
                raise ValueError("Text cannot be empty.")

            updated_category = normalize_entry_category(category, row["category"])
            updated_tags = normalize_entry_tags(tags if tags is not None else [item.strip() for item in (row["tags"] or "").split(",") if item.strip()])
            updated_status = normalize_entry_status(status or row["status"])
            updated_due = normalize_entry_datetime(due_at if due_at is not None else row["due_at"], "due_at")
            updated_reminder = normalize_entry_datetime(reminder_at if reminder_at is not None else row["reminder_at"], "reminder_at")
            updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            conn.execute(
                "UPDATE entries SET text = ?, category = ?, tags = ?, status = ?, due_at = ?, reminder_at = ?, updated_at = ? WHERE id = ?",
                (updated_text, updated_category, self._tags_to_text(updated_tags), updated_status, updated_due, updated_reminder, updated_at, entry_id),
            )
            conn.commit()

        return MemoryEntry(
            id=entry_id,
            kind=row["kind"],
            text=updated_text,
            category=updated_category,
            tags=updated_tags,
            status=updated_status,
            due_at=updated_due,
            reminder_at=updated_reminder,
            created_at=row["created_at"],
        )

    def delete_entry(self, entry_id: int, user_id: int | None = None) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM entries WHERE id = ? AND (? IS NULL OR user_id = ?)",
                (entry_id, user_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_categories(self, user_id: int | None = None) -> list[str]:
        with self._connect() as conn:
            sql = "SELECT DISTINCT category FROM entries"
            params: list[str] = []
            if user_id is not None:
                sql += " WHERE user_id = ?"
                params.append(str(user_id))
            sql += " ORDER BY category ASC"
            rows = conn.execute(sql, params).fetchall()
        return [row["category"] for row in rows]

    def search_by_tag(self, tag: str, user_id: int | None = None) -> list[MemoryEntry]:
        return self.list_entries(tag=tag, user_id=user_id)

    def search(self, query: str, user_id: int | None = None) -> list[MemoryEntry]:
        return self.list_entries(text_query=query, user_id=user_id)

    def status(self, user_id: int | None = None) -> dict[str, object]:
        with self._connect() as conn:
            if user_id is None:
                note_row = conn.execute("SELECT COUNT(*) AS total FROM entries WHERE kind = 'note'").fetchone()
                task_row = conn.execute("SELECT COUNT(*) AS total FROM entries WHERE kind = 'task'").fetchone()
            else:
                note_row = conn.execute("SELECT COUNT(*) AS total FROM entries WHERE user_id = ? AND kind = 'note'", (user_id,)).fetchone()
                task_row = conn.execute("SELECT COUNT(*) AS total FROM entries WHERE user_id = ? AND kind = 'task'", (user_id,)).fetchone()
            note_count = int(note_row["total"])
            task_count = int(task_row["total"])
        return {
            "root": str(self.root),
            "notes": note_count,
            "tasks": task_count,
            "categories": self.list_categories(user_id=user_id),
        }

    def _markdown_entry_pattern(self) -> re.Pattern[str]:
        return re.compile(
            r"^-\s+\[(?P<kind>note|task)\]\s+\[(?P<created>[^\]]+)\]\s+\[(?P<category>[^\]]+)\]\s+\[(?P<status>[^\]]+)\](?P<rest>.*)$",
            flags=re.IGNORECASE,
        )

    def _legacy_markdown_entry_pattern(self) -> re.Pattern[str]:
        return re.compile(
            r"^-\s+\[(?P<created>[^\]]+)\]\s+\[(?P<category>[^\]]+)\]\s+\[(?P<status>[^\]]+)\](?P<rest>.*)$",
            flags=re.IGNORECASE,
        )

    def _parse_markdown_entry(self, line: str) -> tuple[str, str, str, list[str], str | None, str | None, str] | None:
        value = line.strip()
        if not value.startswith("- "):
            return None
        content = value[2:].strip()

        alt = re.match(r"^\*\*(?P<kind>note|task)\*\*:\s*(?P<text>.+)$", content, flags=re.IGNORECASE)
        if alt:
            kind = alt.group("kind").lower()
            return kind, "general", "new", [], None, None, alt.group("text").strip()

        match = self._markdown_entry_pattern().match(content)
        if match is None:
            match = self._legacy_markdown_entry_pattern().match(content)
            if match is None:
                return None
            kind = "note"
            created_at = match.group("created")
            category = match.group("category")
            status = match.group("status")
            rest = match.group("rest")
        else:
            kind = match.group("kind").lower()
            created_at = match.group("created")
            category = match.group("category")
            status = match.group("status")
            rest = match.group("rest")

        due_at = None
        reminder_at = None
        tags: list[str] = []
        text = rest.strip()

        while text:
            if text.startswith(" [due:"):
                due_end = text.find("]")
                if due_end == -1:
                    break
                due_at = text[6:due_end].strip()
                text = text[due_end + 1 :].strip()
                continue
            if text.startswith(" [reminder:"):
                reminder_end = text.find("]")
                if reminder_end == -1:
                    break
                reminder_at = text[11:reminder_end].strip()
                text = text[reminder_end + 1 :].strip()
                continue
            if text.startswith(" ["):
                bracket_end = text.find("]")
                if bracket_end == -1:
                    break
                tag_value = text[2:bracket_end].strip()
                if tag_value:
                    tags.extend([item.strip() for item in tag_value.split(",") if item.strip()])
                text = text[bracket_end + 1 :].strip()
                continue
            break

        text = text.strip()
        if not text and kind == "note":
            text = created_at

        return kind, category, status, sorted(set(tags)), due_at, reminder_at, text

    def _list_for_export(self, user_id: int | None = None) -> list[MemoryEntry]:
        return self.list_entries(user_id=user_id)

    def export_markdown(self, file_path: str | Path, user_id: int | None = None) -> Path:
        target = Path(file_path)
        lines: list[str] = ["# WORKSPACE Memory Export\n"]
        for entry in self._list_for_export(user_id=user_id):
            lines.append(f"{entry.to_line()}\n")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(lines), encoding="utf-8")
        return target

    def export_csv(self, file_path: str | Path, user_id: int | None = None) -> Path:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "kind", "text", "category", "tags", "status", "due_at", "reminder_at", "created_at"])
            writer.writeheader()
            for entry in self._list_for_export(user_id=user_id):
                writer.writerow({
                    "id": entry.id or "",
                    "kind": entry.kind,
                    "text": entry.text,
                    "category": entry.category,
                    "tags": ",".join(entry.tags),
                    "status": getattr(entry, "status", "new"),
                    "due_at": entry.due_at or "",
                    "reminder_at": entry.reminder_at or "",
                    "created_at": entry.created_at,
                })
        return target

    def export_json(self, file_path: str | Path, user_id: int | None = None) -> Path:
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "id": entry.id,
                "kind": entry.kind,
                "text": entry.text,
                "category": entry.category,
                "tags": entry.tags,
                "status": getattr(entry, "status", "new"),
                "due_at": entry.due_at,
                "reminder_at": entry.reminder_at,
                "created_at": entry.created_at,
            }
            for entry in self._list_for_export(user_id=user_id)
        ]
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    def import_markdown(self, file_path: str | Path, user_id: int | None = None) -> int:
        source = Path(file_path)
        if not source.exists():
            raise FileNotFoundError(f"Markdown file not found: {source}")

        imported = 0
        for line in source.read_text(encoding="utf-8").splitlines():
            parsed = self._parse_markdown_entry(line)
            if parsed is None:
                continue

            kind, category, status, tags, due_at, reminder_at, text = parsed
            if not text:
                continue
            if kind == "task":
                self.add_task(text, category=category, tags=tags, status=status, user_id=user_id, due_at=due_at, reminder_at=reminder_at)
            else:
                self.add_note(text, category=category, tags=tags, status=status, user_id=user_id, due_at=due_at, reminder_at=reminder_at)
            imported += 1
        return imported

    def import_csv(self, file_path: str | Path, user_id: int | None = None) -> int:
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
                status = (row.get("status") or "new").strip()
                due_at = (row.get("due_at") or "").strip() or None
                reminder_at = (row.get("reminder_at") or "").strip() or None
                tags = [item.strip() for item in (row.get("tags") or "").split(",") if item.strip()]
                if kind == "task":
                    self.add_task(text, category=category, tags=tags, status=status, user_id=user_id, due_at=due_at, reminder_at=reminder_at)
                else:
                    self.add_note(text, category=category, tags=tags, status=status, user_id=user_id, due_at=due_at, reminder_at=reminder_at)
                imported += 1
        return imported

    def import_json(self, file_path: str | Path, user_id: int | None = None) -> int:
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
            status = item.get("status") or "new"
            due_at = item.get("due_at") or None
            reminder_at = item.get("reminder_at") or None
            tags = item.get("tags") or []
            if kind == "task":
                self.add_task(text, category=category, tags=tags, status=status, user_id=user_id, due_at=due_at, reminder_at=reminder_at)
            else:
                self.add_note(text, category=category, tags=tags, status=status, user_id=user_id, due_at=due_at, reminder_at=reminder_at)
            imported += 1
        return imported

    def import_any(self, file_path: str | Path, file_format: str | None = None, user_id: int | None = None) -> int:
        path = Path(file_path)
        fmt = (file_format or path.suffix.lower().lstrip(".") or "markdown").lower()
        if fmt in {"md", "markdown"}:
            return self.import_markdown(path, user_id=user_id)
        if fmt == "csv":
            return self.import_csv(path, user_id=user_id)
        if fmt in {"json", "jsn"}:
            return self.import_json(path, user_id=user_id)
        raise ValueError(f"Unsupported import format: {fmt}")

    def export_any(self, file_path: str | Path, file_format: str | None = None, user_id: int | None = None) -> Path:
        path = Path(file_path)
        fmt = (file_format or path.suffix.lower().lstrip(".") or "markdown").lower()
        if fmt in {"md", "markdown"}:
            return self.export_markdown(path, user_id=user_id)
        if fmt == "csv":
            return self.export_csv(path, user_id=user_id)
        if fmt in {"json", "jsn"}:
            return self.export_json(path, user_id=user_id)
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


__all__ = [
    "MemoryStore",
    "DEFAULT_MEMORY_DIR",
    "VALID_ENTRY_STATUSES",
    "ensure_workspace",
    "normalize_entry_category",
    "normalize_entry_datetime",
    "normalize_entry_status",
    "normalize_entry_tags",
]


# Batch A: task lifecycle and reminder automation helpers.
