from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from workspace_memory.storage import DEFAULT_MEMORY_DIR, MemoryStore


app = FastAPI(title="WORKSPACE Memory", version="0.2.0")


class MemoryPayload(BaseModel):
    text: str = Field(..., min_length=1)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    kind: str = "note"


HTML_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>WORKSPACE Memory Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; background: #f4f7fb; color: #122033; margin: 0; }
      .container { max-width: 1100px; margin: 0 auto; padding: 32px 20px 80px; }
      .hero { background: linear-gradient(135deg, #1f3a5f, #4e7dc3); color: white; border-radius: 18px; padding: 32px; box-shadow: 0 12px 26px rgba(31,58,95,0.2); }
      .hero h1 { margin: 0 0 12px; font-size: 2.5rem; }
      .hero p { margin: 0; opacity: 0.9; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px; margin-top: 28px; }
      .card { background: white; border-radius: 14px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08); padding: 20px; }
      .stat { font-size: 2rem; font-weight: bold; margin-bottom: 6px; }
      .muted { color: #5b6b7f; }
      table { width: 100%; border-collapse: collapse; margin-top: 18px; }
      th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #e7edf4; }
      .pill { display: inline-block; background: #eaf1ff; color: #2a4d7d; border-radius: 999px; padding: 4px 10px; font-size: 0.8rem; margin: 2px; }
      .toolbar { display: flex; gap: 12px; flex-wrap: wrap; margin: 22px 0; }
      input, select, button { padding: 10px 12px; border-radius: 10px; border: 1px solid #d9e2ef; font-size: 1rem; }
      button { background: #4e7dc3; color: white; border: none; cursor: pointer; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="hero">
        <h1>WORKSPACE Memory</h1>
        <p>Durable notes, tasks, and context for your workflow.</p>
      </div>
      <div class="grid">
        <div class="card"><div class="stat" id="note-count">0</div><div class="muted">Notes</div></div>
        <div class="card"><div class="stat" id="task-count">0</div><div class="muted">Tasks</div></div>
        <div class="card"><div class="stat" id="category-count">0</div><div class="muted">Categories</div></div>
      </div>

      <div class="toolbar">
        <input id="search" type="text" placeholder="Search entries..." />
        <select id="category-filter">
          <option value="">All categories</option>
        </select>
        <select id="kind-filter">
          <option value="">All types</option>
          <option value="note">Notes</option>
          <option value="task">Tasks</option>
        </select>
        <button id="refresh">Refresh</button>
      </div>

      <div class="card">
        <table>
          <thead>
            <tr><th>Type</th><th>Category</th><th>Tags</th><th>Summary</th></tr>
          </thead>
          <tbody id="entry-table"></tbody>
        </table>
      </div>
    </div>

    <script>
      async function fetchJson(url) {
        const res = await fetch(url);
        return res.json();
      }

      async function loadDashboard() {
        const status = await fetchJson('/api/status');
        const entries = await fetchJson('/api/entries');
        document.getElementById('note-count').textContent = status.notes ?? 0;
        document.getElementById('task-count').textContent = status.tasks ?? 0;
        document.getElementById('category-count').textContent = (status.categories || []).length;

        const categorySelect = document.getElementById('category-filter');
        categorySelect.innerHTML = '<option value="">All categories</option>' + (status.categories || []).map(cat => `<option value="${cat}">${cat}</option>`).join('');

        const query = document.getElementById('search').value.trim().toLowerCase();
        const category = categorySelect.value;
        const kind = document.getElementById('kind-filter').value;

        const filtered = entries.filter(entry => {
          const matchesQuery = !query || entry.text.toLowerCase().includes(query) || (entry.tags || []).some(tag => tag.toLowerCase().includes(query));
          const matchesCategory = !category || entry.category === category;
          const matchesKind = !kind || entry.kind === kind;
          return matchesQuery && matchesCategory && matchesKind;
        });

        const rows = filtered.map(entry => {
          const tags = (entry.tags || []).map(tag => `<span class="pill">${tag}</span>`).join('');
          return `<tr><td>${entry.kind}</td><td>${entry.category}</td><td>${tags || '<span class="muted">—</span>'}</td><td>${entry.text}</td></tr>`;
        }).join('');

        document.getElementById('entry-table').innerHTML = rows || '<tr><td colspan="4">No entries found.</td></tr>';
      }

      document.getElementById('refresh').addEventListener('click', loadDashboard);
      document.getElementById('search').addEventListener('input', loadDashboard);
      document.getElementById('category-filter').addEventListener('change', loadDashboard);
      document.getElementById('kind-filter').addEventListener('change', loadDashboard);
      loadDashboard();
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HTML_PAGE


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
    return [entry.to_dict() for entry in store.list_entries(kind=kind, category=category, tag=tag, text_query=query)]


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


@app.post("/api/export")
def export_entries() -> dict[str, str]:
    store = MemoryStore(DEFAULT_MEMORY_DIR)
    path = store.export_markdown(".memory/export.md")
    return {"path": str(path)}


@app.post("/api/import")
def import_entries(payload: dict[str, str]) -> dict[str, object]:
    import_path = payload.get("path")
    if not import_path:
        raise HTTPException(status_code=400, detail="Import path is required")

    store = MemoryStore(DEFAULT_MEMORY_DIR)
    count = store.import_markdown(import_path)
    return {"count": count, "path": import_path}


def main() -> None:
    import uvicorn

    uvicorn.run("workspace_memory.web_app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
