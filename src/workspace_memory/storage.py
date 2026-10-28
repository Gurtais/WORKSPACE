from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable


DEFAULT_MEMORY_DIR = Path(".memory")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_workspace(memory_dir: Path | str = DEFAULT_MEMORY_DIR) -> Path:
    root = Path(memory_dir)
    required = [
        root,
        root / "state",
        root / "tasks",
        root / "reflections",
        root / "recovery",
        root / "tools",
        root / "notes",
    ]
    for directory in required:
        directory.mkdir(parents=True, exist_ok=True)

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Memory\n\nThis directory stores the durable project memory for the workspace.\n",
            encoding="utf-8",
        )

    return root


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
    rows: list[str] = []
    for path in paths:
        rows.append(f"{path}")
    return rows
