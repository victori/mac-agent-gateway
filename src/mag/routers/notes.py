"""Notes API router for Mac Agent Gateway."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from mag.auth import verify_api_key
from mag.config import get_settings
from mag.models.notes import Note, NoteAccount, NoteCreate, NoteFolder
from mag.services import notesapp
from mag.services.notesapp import NotesAppError

router = APIRouter(prefix="/notes", dependencies=[Depends(verify_api_key)])


def _handle_notes_error(e: NotesAppError) -> HTTPException:
    """Convert NotesAppError to HTTPException with helpful details."""
    return HTTPException(status_code=502, detail=e.to_dict())


def _require_capability(capability: str) -> None:
    """Check if a Notes capability is enabled."""
    settings = get_settings()
    capability_map = {
        "read": settings.notes_read,
        "write": settings.notes_write,
    }
    if not capability_map.get(capability, False):
        raise HTTPException(
            status_code=403,
            detail={
                "error": f"Capability 'notes.{capability}' is disabled",
                "hint": f"Set MAG_NOTES_{capability.upper()}=true to enable",
            },
        )


def _validate_attachment_paths(files: list[str]) -> None:
    """Validate note attachment paths against configured allowed directories."""
    if not files:
        return

    settings = get_settings()
    allowed_dirs = settings.get_attachment_allowed_dirs()
    if not allowed_dirs:
        return

    for file_path in files:
        try:
            resolved = Path(file_path).expanduser().resolve()
        except (OSError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Invalid file path: {file_path}", "hint": str(e)},
            )

        is_allowed = any(
            resolved == allowed_dir or allowed_dir in resolved.parents
            for allowed_dir in allowed_dirs
        )
        if not is_allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": f"File path not in allowed directories: {file_path}",
                    "hint": "Configure MAG_ATTACHMENT_ALLOWED_DIRS to specify allowed directories",
                    "allowed_directories": [str(d) for d in sorted(allowed_dirs)],
                },
            )


@router.get("", response_model=list[Note])
async def list_notes(
    account: list[str] | None = Query(default=None, description="Filter by account name"),
    name: list[str] | None = Query(default=None, description="Filter by note name"),
    body: list[str] | None = Query(default=None, description="Filter by HTML body"),
    text: list[str] | None = Query(default=None, description="Filter by plaintext"),
    password_protected: bool | None = Query(default=None, description="Filter by password status"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum notes to return"),
    offset: int = Query(default=0, ge=0, description="Number of matching notes to skip"),
) -> list[Note]:
    """List/search Apple Notes."""
    _require_capability("read")
    try:
        return await notesapp.list_notes(
            accounts=account,
            name=name,
            body=body,
            text=text,
            password_protected=password_protected,
            limit=limit,
            offset=offset,
        )
    except NotesAppError as e:
        raise _handle_notes_error(e)


@router.get("/accounts", response_model=list[NoteAccount])
async def list_note_accounts() -> list[NoteAccount]:
    """List Notes accounts."""
    _require_capability("read")
    try:
        return await notesapp.list_accounts()
    except NotesAppError as e:
        raise _handle_notes_error(e)


@router.get("/folders", response_model=list[NoteFolder])
async def list_note_folders(
    account: str | None = Query(default=None, description="Account name"),
) -> list[NoteFolder]:
    """List top-level folders for a Notes account."""
    _require_capability("read")
    try:
        return await notesapp.list_folders(account=account)
    except NotesAppError as e:
        raise _handle_notes_error(e)


@router.get("/{note_id}", response_model=Note)
async def get_note(note_id: str) -> Note:
    """Get a single note by id."""
    _require_capability("read")
    try:
        note = await notesapp.get_note(note_id)
    except NotesAppError as e:
        raise _handle_notes_error(e)
    if note is None:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    return note


@router.post("", response_model=Note, status_code=201)
async def create_note(data: NoteCreate) -> Note:
    """Create a new note."""
    _require_capability("write")
    _validate_attachment_paths(data.attachments)
    try:
        return await notesapp.create_note(
            name=data.name,
            body=data.body,
            account=data.account,
            folder=data.folder,
            attachments=data.attachments,
        )
    except NotesAppError as e:
        raise _handle_notes_error(e)
