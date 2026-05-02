from datetime import datetime

from pydantic import BaseModel


class ResumeLibraryItem(BaseModel):
    id: str
    file_name: str
    source_type: str
    indexed_at: datetime
    name: str
    summary: str
    experience: list[dict[str, str]]
    education: list[str]
    skills: list[str]
    raw_text: str
    size_bytes: int
    is_active: bool = False


class ResumeLibraryResponse(BaseModel):
    active_id: str | None = None
    items: list[ResumeLibraryItem]
