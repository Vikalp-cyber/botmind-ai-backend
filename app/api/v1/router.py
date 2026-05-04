from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, health, history, knowledge_base, leads, usage, webhooks

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["knowledge-base"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
