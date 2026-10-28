from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryEntry:
    kind: str
    text: str
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    status: str = "new"
    due_at: str | None = None
    reminder_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    @property
    def normalized_tags(self) -> list[str]:
        return sorted({tag.strip().lower() for tag in self.tags if tag and tag.strip()})

    def to_line(self) -> str:
        tags = ",".join(self.normalized_tags)
        due = f" [due:{self.due_at}]" if self.due_at else ""
        reminder = f" [reminder:{self.reminder_at}]" if self.reminder_at else ""
        if tags:
            return f"- [{self.kind.lower()}] [{self.created_at}] [{self.category}] [{self.status}]{due}{reminder} [{tags}] {self.text}"
        return f"- [{self.kind.lower()}] [{self.created_at}] [{self.category}] [{self.status}]{due}{reminder} {self.text}"

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "text": self.text,
            "category": self.category,
            "tags": self.normalized_tags,
            "status": self.status,
            "due_at": self.due_at,
            "reminder_at": self.reminder_at,
            "created_at": self.created_at,
        }
