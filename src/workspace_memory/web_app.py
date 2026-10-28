from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from workspace_memory.storage import DEFAULT_MEMORY_DIR, MemoryStore


app = FastAPI(title="WORKSPACE Memory", version="0.2.1")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class MemoryPayload(BaseModel):
    text: str = Field(..., min_length=1)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    kind: str = "note"


class UpdateEntryPayload(BaseModel):
    text: str | None = None
    category: str | None = None
    tags: list[str] | None = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status")
def status() -> dict[str, object]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    return store.status()


@app.get("/api/entries")
def entries(
    category: str | None = None,
    tag: str | None = None,
    kind: str | None = None,
    query: str | None = None,
) -> list[dict[str, object]]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    result = store.list_entries(kind=kind, category=category, tag=tag, text_query=query)
    return [
        {
            "id": idx + 1,
            "kind": entry.kind,
            "text": entry.text,
            "category": entry.category,
            "tags": entry.tags,
            "created_at": entry.created_at,
        }
        for idx, entry in enumerate(result)
    ]


@app.post("/api/notes")
def create_note(payload: MemoryPayload) -> dict[str, object]:
    payload.kind = "note"
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    entry = store.add_note(payload.text, category=payload.category, tags=payload.tags)
    return {
        "id": 1,
        "kind": entry.kind,
        "text": entry.text,
        "category": entry.category,
        "tags": entry.tags,
        "created_at": entry.created_at,
    }


@app.post("/api/tasks")
def create_task(payload: MemoryPayload) -> dict[str, object]:
    payload.kind = "task"
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    entry = store.add_task(payload.text, category=payload.category, tags=payload.tags)
    return {
        "id": 1,
        "kind": entry.kind,
        "text": entry.text,
        "category": entry.category,
        "tags": entry.tags,
        "created_at": entry.created_at,
    }


@app.put("/api/entries/{entry_id}")
def update_entry(entry_id: int, payload: UpdateEntryPayload) -> dict[str, object]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    row = store.update_entry(entry_id, text=payload.text, category=payload.category, tags=payload.tags)
    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {
        "id": entry_id,
        "kind": row.kind,
        "text": row.text,
        "category": row.category,
        "tags": row.tags,
        "created_at": row.created_at,
    }


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int) -> dict[str, str]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    if not store.delete_entry(entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted", "id": str(entry_id)}


@app.post("/api/export")
def export_entries(payload: dict[str, str]) -> dict[str, str]:
    format_name = (payload.get("format") or "markdown").lower()
    target = payload.get("path") or ".memory/export"
    if format_name in {"md", "markdown"}:
        target = f"{target}.md" if not target.endswith(".md") else target
    elif format_name == "csv":
        target = f"{target}.csv" if not target.endswith(".csv") else target
    elif format_name in {"json", "jsn"}:
        target = f"{target}.json" if not target.endswith(".json") else target
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

    store = MemoryStore(DEFAULT_MEMORY_DIR)
    path = store.export_any(target, format_name)
    return {"path": str(path), "format": format_name}


@app.post("/api/import")
def import_entries(payload: dict[str, str]) -> dict[str, object]:
    import_path = payload.get("path")
    if not import_path:
        raise HTTPException(status_code=400, detail="Import path is required")
    format_name = (payload.get("format") or "markdown").lower()
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    count = store.import_any(import_path, format_name)
    return {"count": count, "path": import_path, "format": format_name}


def main() -> None:
    import uvicorn

    uvicorn.run("workspace_memory.web_app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
