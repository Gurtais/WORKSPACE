from __future__ import annotations

from fastapi.testclient import TestClient

from workspace_memory import web_app
from workspace_memory.storage import MemoryStore


def _fresh_client(tmp_path, monkeypatch):
    memory_dir = tmp_path / ".memory"
    monkeypatch.setattr(web_app, "DEFAULT_MEMORY_DIR", memory_dir)
    monkeypatch.setattr(web_app, "_user_store", lambda: MemoryStore(memory_dir))
    return TestClient(web_app.app)


def test_register_login_and_me(tmp_path, monkeypatch):
    client = _fresh_client(tmp_path, monkeypatch)

    register = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret", "display_name": "Alice"},
    )
    assert register.status_code == 200, register.text
    assert register.json()["user"]["username"] == "alice"

    me = client.get("/api/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["username"] == "alice"


def test_create_note_and_task_and_list_filters(tmp_path, monkeypatch):
    client = _fresh_client(tmp_path, monkeypatch)
    client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "secret", "display_name": "Bob"},
    )

    note = client.post(
        "/api/notes",
        json={
            "text": "review logs",
            "category": "ops",
            "tags": ["release", "ops"],
            "status": "active",
            "due_at": "2026-11-01",
        },
    )
    assert note.status_code == 200, note.text

    task = client.post(
        "/api/tasks",
        json={
            "text": "ship release",
            "category": "ops",
            "tags": ["release"],
            "status": "new",
            "due_at": "2026-11-02",
        },
    )
    assert task.status_code == 200, task.text

    active_entries = client.get("/api/entries?status=active")
    assert active_entries.status_code == 200, active_entries.text
    assert any(item["text"] == "review logs" for item in active_entries.json())

    status = client.get("/api/status")
    assert status.status_code == 200, status.text
    payload = status.json()
    assert payload["notes"] >= 1
    assert payload["tasks"] >= 1


def test_export_and_import_round_trip(tmp_path, monkeypatch):
    client = _fresh_client(tmp_path, monkeypatch)
    client.post(
        "/api/auth/register",
        json={"username": "charlie", "password": "secret", "display_name": "Charlie"},
    )

    note = client.post(
        "/api/notes",
        json={"text": "migration checklist", "category": "ops", "tags": ["release"], "status": "done"},
    )
    assert note.status_code == 200, note.text

    export_path = tmp_path / "export.md"
    export = client.post("/api/export", json={"path": str(export_path), "format": "markdown"})
    assert export.status_code == 200, export.text
    assert export_path.exists()

    import_response = client.post("/api/import", json={"path": str(export_path), "format": "markdown"})
    assert import_response.status_code == 200, import_response.text
    assert import_response.json()["count"] >= 1

    entries = client.get("/api/entries")
    assert entries.status_code == 200, entries.text
    assert any(item["text"] == "migration checklist" for item in entries.json())
