"""Pydantic models for Apple Notes."""

from datetime import datetime

from pydantic import BaseModel, Field


class NoteAttachment(BaseModel):
    """Response model for a note attachment."""

    id: str | None = Field(None, description="Unique attachment identifier")
    name: str | None = Field(None, description="Attachment name")
    content_identifier: str | None = Field(None, description="Attachment content identifier")
    url: str | None = Field(None, description="Attachment URL")
    creation_date: datetime | None = Field(None, description="Attachment creation date")
    modification_date: datetime | None = Field(None, description="Attachment modification date")


class Note(BaseModel):
    """Response model for an Apple Note."""

    id: str = Field(..., description="Unique note identifier")
    name: str = Field(..., description="Note title")
    account: str | None = Field(None, description="Notes account name")
    folder: str | None = Field(None, description="Folder name")
    body: str | None = Field(None, description="HTML note body")
    plaintext: str | None = Field(None, description="Plaintext note body")
    creation_date: datetime | None = Field(None, description="Note creation date")
    modification_date: datetime | None = Field(None, description="Note modification date")
    password_protected: bool = Field(False, description="Whether the note is password protected")
    attachments: list[NoteAttachment] = Field(default_factory=list, description="Attachments")


class NoteCreate(BaseModel):
    """Request model for creating a note."""

    name: str = Field(..., min_length=1, description="Note title")
    body: str = Field(..., min_length=1, description="HTML note body")
    account: str | None = Field(None, description="Notes account name")
    folder: str | None = Field(None, description="Top-level folder name")
    attachments: list[str] = Field(default_factory=list, description="Attachment file paths")


class NoteAccount(BaseModel):
    """Response model for a Notes account."""

    name: str = Field(..., description="Account name")


class NoteFolder(BaseModel):
    """Response model for a Notes folder."""

    name: str = Field(..., description="Folder name")


class NotesError(BaseModel):
    """Error response from Notes.app integration."""

    error: str = Field(..., description="Error message")
    code: int = Field(..., description="Gateway error code")
    details: str = Field(default="", description="Detailed error context")
    hint: str | None = Field(None, description="Suggested fix")
