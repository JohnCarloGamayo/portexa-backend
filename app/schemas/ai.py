from pydantic import BaseModel, Field


class AIChatMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str


class AIChatRequest(BaseModel):
    prompt: str
    model: str | None = None
    messages: list[AIChatMessage] | None = None


class AIChatResponse(BaseModel):
    response: str
    model: str


class ResumeStructureRequest(BaseModel):
    file_name: str
    raw_text: str
    source_type: str | None = None


class ResumeExperienceItem(BaseModel):
    title: str
    company: str
    period: str


class ResumeStructureResponse(BaseModel):
    file_name: str
    source_type: str
    name: str
    summary: str
    experience: list[ResumeExperienceItem]
    education: list[str]
    skills: list[str]
    raw_text: str
