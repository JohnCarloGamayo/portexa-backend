from fastapi import APIRouter

from app.api.routes import ai, auth, embed, health, resumes

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ai.router)
api_router.include_router(auth.router)
api_router.include_router(embed.router)
api_router.include_router(health.router)
api_router.include_router(resumes.router)
