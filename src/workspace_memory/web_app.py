from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from workspace_memory.storage import DEFAULT_MEMORY_DIR, MemoryStore


app = FastAPI(title="WORKSPACE Memory", version="0.2.0")


class MemoryPayload(BaseModel):
    text: str = Field(..., min_length=1)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    kind: str = "note"


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <html>
      <head><title>WORKSPACE Memory</title></head>
      <body>
        <h1>WORKSPACE Memory</h1>
        <p>Store notes and tasks in a durable, searchable personal workspace.</p>
      </body>
    </html>
    """


@app.get("/api/status")
def status() -> dict[str, object]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    return store.status()


@app.get("/api/entries")
def entries(category: str | None = None, tag: str | None = None, kind: str | None = None) -> list[dict[str, object]]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    return [entry.to_dict() for entry in store.list_entries(kind=kind, category=category, tag=tag)]


@app.post("/api/notes")
def create_note(payload: MemoryPayload) -> dict[str, object]:
    if payload.kind != "note":
        payload.kind = "note"
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    entry = store.add_note(payload.text, category=payload.category, tags=payload.tags)
    return entry.to_dict()


@app.post("/api/tasks")
def create_task(payload: MemoryPayload) -> dict[str, object]:
    if payload.kind != "task":
        payload.kind = "task"
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    entry = store.add_task(payload.text, category=payload.category, tags=payload.tags)
    return entry.to_dict()


def main() -> None:
    import uvicorn

    uvicorn.run("workspace_memory.web_app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
