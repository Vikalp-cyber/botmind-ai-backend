from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_roles, resolve_tenant_context
from app.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeTextIngestRequest,
    KnowledgeUrlIngestRequest,
)
from app.services.knowledge_service import KnowledgeService
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get(
    "",
    response_model=list[KnowledgeDocumentResponse],
    summary="List knowledge documents",
    description="All ingested documents for the tenant with chunk counts.",
)
async def list_documents(
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin", "member")),
    session: AsyncSession = Depends(get_db_session),
):
    logger.info("listing_documents", tenant_id=tenant.tenant_id, user_id=str(user.id))
    return await KnowledgeService(session).list_documents(UUID(tenant.tenant_id))


@router.post(
    "/text",
    response_model=KnowledgeDocumentResponse,
    status_code=201,
    summary="Ingest raw text",
    description="Chunks, embeds, and stores text for RAG. **Admin only.**",
)
async def ingest_text(
    payload: KnowledgeTextIngestRequest,
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_db_session),
):
    logger.info(
        "ingesting_text",
        tenant_id=tenant.tenant_id,
        title=payload.title,
        text_length=len(payload.text),
    )
    result = await KnowledgeService(session).ingest_text(
        tenant_id=UUID(tenant.tenant_id),
        title=payload.title,
        text=payload.text,
    )
    logger.info("ingest_text_success", document_id=str(result.id))
    return result


@router.post(
    "/url",
    response_model=KnowledgeDocumentResponse,
    status_code=201,
    summary="Ingest URL",
    description="Fetches URL, extracts HTML text, then ingests. **Admin only.**",
)
async def ingest_url(
    payload: KnowledgeUrlIngestRequest,
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_db_session),
):
    logger.info(
        "ingesting_url",
        tenant_id=tenant.tenant_id,
        title=payload.title,
        url=str(payload.url),
    )
    result = await KnowledgeService(session).ingest_url(
        tenant_id=UUID(tenant.tenant_id),
        title=payload.title,
        url=str(payload.url),
    )
    logger.info("ingest_url_success", document_id=str(result.id))
    return result


@router.post(
    "/file",
    response_model=KnowledgeDocumentResponse,
    status_code=201,
    summary="Upload file",
    description=(
        "Multipart form: `title` + `file`. Supports **PDF**, **DOCX**, and UTF-8 **text**. **Admin only.**"
    ),
)
async def ingest_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    tenant=Depends(resolve_tenant_context),
    user=Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_db_session),
):
    logger.info(
        "ingesting_file",
        tenant_id=tenant.tenant_id,
        title=title,
        filename=file.filename,
        content_type=file.content_type,
    )
    result = await KnowledgeService(session).ingest_file(
        tenant_id=UUID(tenant.tenant_id),
        title=title,
        file=file,
    )
    logger.info("ingest_file_success", document_id=str(result.id))
    return result
