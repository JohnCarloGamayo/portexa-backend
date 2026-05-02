from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class OpenRouterError(RuntimeError):
    pass


async def ask_openrouter(prompt: str, *, model: str | None = None, messages: list[dict[str, str]] | None = None) -> dict[str, Any]:
    if not settings.openrouter_api_key:
        raise OpenRouterError("OpenRouter API key is not configured")

    request_messages = messages or [{"role": "user", "content": prompt}]
    payload = {
        "model": model or settings.openrouter_model,
        "messages": request_messages,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    if settings.openrouter_app_url:
        headers["HTTP-Referer"] = settings.openrouter_app_url
    if settings.openrouter_app_name:
        headers["X-Title"] = settings.openrouter_app_name

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code >= 400:
        detail = response.text
        raise OpenRouterError(detail)

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    return {
        "response": content,
        "model": data.get("model", payload["model"]),
        "raw": data,
    }
