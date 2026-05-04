"""OpenAPI / Swagger metadata for the HTTP API (FastAPI serves /docs and /openapi.json)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

API_DESCRIPTION = """
Multi-tenant SaaS chatbot backend: **JWT auth**, **tenant-scoped RAG** (knowledge base + embeddings),
**chat** (HTTP and WebSocket), **session history**, **leads**, **usage**, and **CRM webhooks**.

### Authentication

| Mode | Use on |
|------|--------|
| **Bearer JWT** | Most routes: `Authorization: Bearer &lt;access_token&gt;` from `POST /auth/login` or `POST /auth/signup`. |
| **X-API-Key** | `POST /chat` for embedded widgets: header `X-API-Key` with a key created via `POST /auth/api-keys` (admin). |

Tenant scope is taken from the JWT (or from the API key for chat). Row-level security applies per tenant.

### Roles

- **admin**: full access (knowledge ingest, API keys, webhooks, etc.).
- **member**: read-oriented access (list knowledge, history, leads, usage) where noted.

### WebSocket

Streaming chat: **`/api/v1/ws/chat/{tenant_id}/{session_id}?token=&lt;jwt&gt;`** (WebSocket; JWT query param; limited OpenAPI tooling support).
""".strip()

OPENAPI_TAGS: list[dict[str, Any]] = [
    {
        "name": "health",
        "description": "Process and load-balancer health checks.",
    },
    {
        "name": "auth",
        "description": "Register, authenticate, current user, and API keys for widget traffic.",
    },
    {
        "name": "chat",
        "description": "Synchronous chat and WebSocket streaming (RAG + session memory).",
    },
    {
        "name": "knowledge-base",
        "description": "List and ingest tenant documents (text, URL, PDF, DOCX) for RAG.",
    },
    {
        "name": "history",
        "description": "List chat sessions and messages for the tenant.",
    },
    {
        "name": "leads",
        "description": "Captured leads from conversations.",
    },
    {
        "name": "usage",
        "description": "Aggregated usage metrics for billing and dashboards.",
    },
    {
        "name": "webhooks",
        "description": "Outbound CRM webhook endpoints and connectivity test.",
    },
]


def custom_openapi(app: FastAPI) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        summary="Botmind AI — multi-tenant chatbot API",
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )

    components = openapi_schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    # JWT bearer is registered automatically as HTTPBearer from dependencies; add widget API key only.
    schemes["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Widget API key from `POST /auth/api-keys` (tenant admin).",
    }
    http_bearer = schemes.get("HTTPBearer")
    if isinstance(http_bearer, dict):
        http_bearer.setdefault(
            "description",
            "Access token from `POST /auth/login` or `POST /auth/signup`.",
        )

    # POST /chat accepts either Bearer or API key (OR). OpenAPI 3: multiple objects in `security` = OR.
    for path_key, path_item in openapi_schema.get("paths", {}).items():
        if not path_key.endswith("/chat"):
            continue
        post = path_item.get("post")
        if post:
            post["security"] = [{"HTTPBearer": []}, {"ApiKeyAuth": []}]
            break

    app.openapi_schema = openapi_schema
    return app.openapi_schema
