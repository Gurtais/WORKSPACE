from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from workspace_memory.storage import (
    DEFAULT_MEMORY_DIR,
    MemoryStore,
    normalize_entry_datetime,
    normalize_entry_status,
)


app = FastAPI(title="WORKSPACE Memory", version="0.2.3")
base_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(base_dir / "templates"))
SECRET_KEY = "workspace-dev-secret"


class MemoryPayload(BaseModel):
    text: str = Field(..., min_length=1)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    kind: str = "note"
    status: str = "new"
    due_at: str | None = None
    reminder_at: str | None = None

    @property
    def normalized_status(self) -> str:
        return normalize_entry_status(self.status)

    @property
    def normalized_due_at(self) -> str | None:
        return normalize_entry_datetime(self.due_at, "due_at")

    @property
    def normalized_reminder_at(self) -> str | None:
        return normalize_entry_datetime(self.reminder_at, "reminder_at")


class UpdateEntryPayload(BaseModel):
    text: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    due_at: str | None = None
    reminder_at: str | None = None

    @property
    def normalized_status(self) -> str | None:
        if self.status is None:
            return None
        return normalize_entry_status(self.status)

    @property
    def normalized_due_at(self) -> str | None:
        return normalize_entry_datetime(self.due_at, "due_at")

    @property
    def normalized_reminder_at(self) -> str | None:
        return normalize_entry_datetime(self.reminder_at, "reminder_at")


class LoginPayload(BaseModel):
    username: str
    password: str


class RegisterPayload(BaseModel):
    username: str
    password: str
    display_name: str | None = None


class ProfilePayload(BaseModel):
    display_name: str | None = None
    role: str | None = None
    bio: str | None = None


def _signed_cookie_value(user_id: int) -> str:
    payload = f"{user_id}:{hmac.new(SECRET_KEY.encode(), str(user_id).encode(), hashlib.sha256).hexdigest()}"
    return payload


def _verify_cookie(value: str | None) -> int | None:
    if not value:
        return None
    try:
        user_id_text, sig = value.split(":", 1)
        if hmac.compare_digest(sig, hmac.new(SECRET_KEY.encode(), user_id_text.encode(), hashlib.sha256).hexdigest()):
            return int(user_id_text)
    except Exception:
        return None
    return None


def _get_current_user_id(request: Request) -> int | None:
    cookie_value = request.cookies.get("workspace_session")
    return _verify_cookie(cookie_value)


def _require_auth(request: Request) -> int:
    user_id = _get_current_user_id(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def _user_store() -> MemoryStore:
    return MemoryStore(DEFAULT_MEMORY_DIR)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/api/auth/register")
def register(payload: RegisterPayload, response: Response) -> dict[str, object]:
    store = _user_store()
    try:
        user = store.create_user(payload.username.strip(), payload.password, display_name=payload.display_name or payload.username.strip(), role="user")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response.set_cookie("workspace_session", _signed_cookie_value(int(user["id"])), httponly=True, samesite="lax")
    return {"status": "ok", "user": user}


@app.post("/api/auth/login")
def login(payload: LoginPayload, response: Response) -> dict[str, object]:
    store = _user_store()
    user = store.verify_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    response.set_cookie("workspace_session", _signed_cookie_value(int(user["id"])), httponly=True, samesite="lax")
    return {"status": "ok", "user": user}


@app.get("/api/auth/me")
def me(request: Request) -> dict[str, object]:
    user_id = _get_current_user_id(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    store = _user_store()
    profile = store.get_user_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=401, detail="User profile not found")
    return profile


@app.get("/api/auth/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("workspace_session")
    return response


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request) -> HTMLResponse:
    user_id = _get_current_user_id(request)
    if user_id is None:
        return RedirectResponse(url="/login", status_code=302)
    store = _user_store()
    profile = store.get_user_profile(user_id)
    return templates.TemplateResponse("profile.html", {"request": request, "profile": profile})


@app.post("/api/profile")
def update_profile(request: Request, payload: ProfilePayload) -> dict[str, object]:
    user_id = _require_auth(request)
    store = _user_store()
    profile = store.update_profile(user_id, display_name=payload.display_name, role=payload.role, bio=payload.bio)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    user_id = _get_current_user_id(request)
    if user_id is None:
        return RedirectResponse(url="/login", status_code=302)
    store = _user_store()
    profile = store.get_user_profile(user_id)
    return templates.TemplateResponse("index.html", {"request": request, "profile": profile})


@app.get("/api/status")
def status(request: Request) -> dict[str, object]:
    user_id = _require_auth(request)
    store = _user_store()
    return store.status(user_id=user_id)


@app.get("/api/entries")
def entries(
    request: Request,
    category: str | None = None,
    tag: str | None = None,
    kind: str | None = None,
    query: str | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> list[dict[str, object]]:
    user_id = _require_auth(request)
    store = _user_store()
    try:
        normalized_status = normalize_entry_status(status) if status else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = store.list_entries(kind=kind, category=category, tag=tag, text_query=query, status=normalized_status, user_id=user_id, sort_by=sort_by, order=order)
    return [
        {
            "id": entry_id + 1,
            "kind": entry.kind,
            "text": entry.text,
            "category": entry.category,
            "tags": entry.tags,
            "status": getattr(entry, "status", "new"),
            "due_at": getattr(entry, "due_at", None),
            "reminder_at": getattr(entry, "reminder_at", None),
            "created_at": entry.created_at,
        }
        for entry_id, entry in enumerate(result)
    ]


@app.post("/api/notes")
def create_note(request: Request, payload: MemoryPayload) -> dict[str, object]:
    user_id = _require_auth(request)
    store = _user_store()
    try:
        entry = store.add_note(
            payload.text,
            category=payload.category,
            tags=payload.tags,
            status=payload.normalized_status,
            user_id=user_id,
            due_at=payload.normalized_due_at,
            reminder_at=payload.normalized_reminder_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": 1,
        "kind": entry.kind,
        "text": entry.text,
        "category": entry.category,
        "tags": entry.tags,
        "status": getattr(entry, "status", "new"),
        "due_at": getattr(entry, "due_at", None),
        "reminder_at": getattr(entry, "reminder_at", None),
        "created_at": entry.created_at,
    }


@app.post("/api/tasks")
def create_task(request: Request, payload: MemoryPayload) -> dict[str, object]:
    user_id = _require_auth(request)
    store = _user_store()
    try:
        entry = store.add_task(
            payload.text,
            category=payload.category,
            tags=payload.tags,
            status=payload.normalized_status,
            user_id=user_id,
            due_at=payload.normalized_due_at,
            reminder_at=payload.normalized_reminder_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": 1,
        "kind": entry.kind,
        "text": entry.text,
        "category": entry.category,
        "tags": entry.tags,
        "status": getattr(entry, "status", "new"),
        "due_at": getattr(entry, "due_at", None),
        "reminder_at": getattr(entry, "reminder_at", None),
        "created_at": entry.created_at,
    }


@app.put("/api/entries/{entry_id}")
def update_entry(request: Request, entry_id: int, payload: UpdateEntryPayload) -> dict[str, object]:
    user_id = _require_auth(request)
    store = _user_store()
    try:
        row = store.update_entry(
            entry_id,
            user_id=user_id,
            text=payload.text,
            category=payload.category,
            tags=payload.tags,
            status=payload.normalized_status,
            due_at=payload.normalized_due_at,
            reminder_at=payload.normalized_reminder_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {
        "id": entry_id,
        "kind": row.kind,
        "text": row.text,
        "category": row.category,
        "tags": row.tags,
        "status": getattr(row, "status", "new"),
        "due_at": getattr(row, "due_at", None),
        "reminder_at": getattr(row, "reminder_at", None),
        "created_at": row.created_at,
    }


@app.delete("/api/entries/{entry_id}")
def delete_entry(request: Request, entry_id: int) -> dict[str, str]:
    user_id = _require_auth(request)
    store = _user_store()
    if not store.delete_entry(entry_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted", "id": str(entry_id)}


@app.post("/api/export")
def export_entries(request: Request, payload: dict[str, str]) -> dict[str, str]:
    user_id = _require_auth(request)
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

    store = _user_store()
    path = store.export_any(target, format_name, user_id=user_id)
    return {"path": str(path), "format": format_name}


@app.post("/api/import")
def import_entries(request: Request, payload: dict[str, str]) -> dict[str, object]:
    user_id = _require_auth(request)
    import_path = payload.get("path")
    if not import_path:
        raise HTTPException(status_code=400, detail="Import path is required")
    format_name = (payload.get("format") or "markdown").lower()
    store = _user_store()
    count = store.import_any(import_path, format_name, user_id=user_id)
    return {"count": count, "path": import_path, "format": format_name}


@app.post("/api/sync")
def sync_entries(request: Request, payload: dict[str, str]) -> dict[str, object]:
    user_id = _require_auth(request)
    direction = (payload.get("direction") or "export").lower()
    path = payload.get("path")
    file_format = (payload.get("format") or "markdown").lower()
    if not path:
        raise HTTPException(status_code=400, detail="Sync path is required")
    store = _user_store()
    if direction == "export":
        target = store.export_any(path, file_format, user_id=user_id)
        return {"direction": direction, "path": str(target), "format": file_format}
    if direction == "import":
        count = store.import_any(path, file_format, user_id=user_id)
        return {"direction": direction, "count": count, "path": path, "format": file_format}
    raise HTTPException(status_code=400, detail="Direction must be export or import")


def main() -> None:
    import uvicorn

    uvicorn.run("workspace_memory.web_app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
