from fastapi import APIRouter, HTTPException, status

from app.core.openrouter import OpenRouterError, ask_openrouter
from app.schemas.ai import (
    AIChatRequest,
    AIChatResponse,
    ResumeStructureRequest,
    ResumeStructureResponse,
    ResumeExperienceItem,
)

import json
import re

router = APIRouter(prefix="/ai", tags=["ai"])


def _extract_json_block(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    return text.strip()


def _summary_from_raw_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return "Resume indexed successfully."

    if len(lines) == 1:
        return lines[0][:280]

    return f"{lines[0]} • {lines[1]}"[:280]


def _normalize_experience(items: list[dict[str, str]]) -> list[ResumeExperienceItem]:
    normalized: list[ResumeExperienceItem] = []

    for item in items:
        title = (item.get("title") or "").strip()
        company = (item.get("company") or "").strip()
        period = (item.get("period") or "").strip()

        if not title:
            title = company or "Professional Role"
        if not company:
            company = "Organization"
        if not period:
            period = "Parsed from resume"

        normalized.append(
            ResumeExperienceItem(
                title=title,
                company=company,
                period=period,
            )
        )

    if not normalized:
        normalized.append(
            ResumeExperienceItem(
                title="Indexed Resume",
                company="Ready for AI retrieval",
                period="Parsed automatically",
            )
        )

    return normalized


@router.post("/chat", response_model=AIChatResponse)
async def chat(request: AIChatRequest):
    messages = [message.model_dump() for message in request.messages] if request.messages else None

    try:
        result = await ask_openrouter(
            request.prompt,
            model=request.model,
            messages=messages,
        )
    except OpenRouterError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return AIChatResponse(response=result["response"], model=result["model"])


@router.post("/structure-resume", response_model=ResumeStructureResponse)
async def structure_resume(request: ResumeStructureRequest):
    system_prompt = (
        "You are a resume structuring engine. Convert the user's raw resume text into strict JSON only. "
        "Do not add markdown, commentary, or code fences. Use this exact schema: "
        "{file_name, source_type, name, summary, experience:[{title, company, period}], education:[string], skills:[string], raw_text}. "
        "Keep experience entries concise and normalize noisy formatting. If a field is missing, infer conservatively or use an empty list/string."
    )

    user_prompt = (
        f"File name: {request.file_name}\n"
        f"Source type: {request.source_type or 'unknown'}\n\n"
        f"Raw resume text:\n{request.raw_text}"
    )

    try:
        result = await ask_openrouter(
            user_prompt,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        payload = json.loads(_extract_json_block(result["response"]))
        payload["file_name"] = payload.get("file_name") or request.file_name
        payload["source_type"] = payload.get("source_type") or (request.source_type or "unknown")
        payload["raw_text"] = payload.get("raw_text") or request.raw_text
        payload["name"] = (payload.get("name") or "").strip() or request.file_name.replace(".pdf", "").replace(".docx", "").replace(".txt", "").strip() or "Untitled Candidate"
        payload["summary"] = (payload.get("summary") or "").strip() or _summary_from_raw_text(request.raw_text)
        payload["experience"] = [item.model_dump() for item in _normalize_experience(payload.get("experience", []))]
        payload["education"] = [str(item).strip() for item in payload.get("education", []) if str(item).strip()]
        payload["skills"] = [str(item).strip() for item in payload.get("skills", []) if str(item).strip()]
        return ResumeStructureResponse(**payload)
    except OpenRouterError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Unable to structure resume: {error}") from error