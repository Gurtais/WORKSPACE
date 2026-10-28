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
