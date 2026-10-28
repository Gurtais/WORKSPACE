from pathlib import Path

from workspace_memory.storage import MemoryStore


def test_memory_store_init(tmp_path):
    store = MemoryStore(tmp_path / ".memory")
    assert (tmp_path / ".memory").exists()
    assert (tmp_path / ".memory" / "notes").exists()
    assert (tmp_path / ".memory" / "tasks").exists()


def test_add_note_and_task_with_tags(tmp_path):
    store = MemoryStore(tmp_path / ".memory")

    note = store.add_note("Review the changelog", category="ops", tags=["release", "docs"])
    task = store.add_task("Draft migration steps", category="planning", tags=["migration", "ops"])

    assert note.category == "ops"
    assert "release" in note.normalized_tags
    assert task.category == "planning"
    assert "migration" in task.normalized_tags

    entries = store.list_entries()
    assert any("Review the changelog" in e.text for e in entries)
    assert any("Draft migration steps" in e.text for e in entries)


def test_categories_and_tag_filter(tmp_path):
    store = MemoryStore(tmp_path / ".memory")
    store.add_note("Note 1", category="ops", tags=["release"])
    store.add_note("Note 2", category="planning", tags=["release"])
    store.add_task("Task 1", category="ops", tags=["docs"])

    categories = store.list_categories()
    assert "ops" in categories
    assert "planning" in categories

    release_matches = store.search_by_tag("release")
    assert len(release_matches) == 2

    ops_entries = store.list_entries(category="ops")
    assert len(ops_entries) >= 2


def test_markdown_round_trip_keeps_kind_metadata(tmp_path):
    source_store = MemoryStore(tmp_path / ".memory-source")
    task = source_store.add_task(
        "Ship release candidate",
        category="ops",
        tags=["release", "qa"],
        status="active",
        due_at="2026-11-01",
        reminder_at="2026-10-30T09:00:00Z",
    )

    export_path = tmp_path / "memory.md"
    source_store.export_markdown(export_path)
    content = export_path.read_text(encoding="utf-8")

    assert "[task]" in content
    assert "[due:2026-11-01]" in content
    assert "[reminder:2026-10-30T09:00:00Z]" in content

    imported_store = MemoryStore(tmp_path / ".memory-import")
    count = imported_store.import_markdown(export_path)
    assert count == 1

    imported = imported_store.list_entries()
    assert len(imported) == 1
    assert imported[0].kind == "task"
    assert imported[0].text == task.text
    assert imported[0].category == "ops"
    assert imported[0].status == "active"
    assert imported[0].due_at == "2026-11-01"
    assert imported[0].reminder_at == "2026-10-30T09:00:00Z"
    assert "release" in imported[0].tags
    assert "qa" in imported[0].tags


__all__ = [
    "test_memory_store_init",
    "test_add_note_and_task_with_tags",
    "test_categories_and_tag_filter",
    "test_markdown_round_trip_keeps_kind_metadata",
]


# This keeps the file focused on the storage behavior used by the app and export/import round-trips.
