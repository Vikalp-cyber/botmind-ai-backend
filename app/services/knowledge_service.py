from uuid import UUID

import httpx
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Embedding, SourceType
from app.integrations.llm import get_llm_client
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeDocumentResponse
from app.utils.chunking import chunk_text, estimate_token_count
from app.utils.documents import extract_text_from_html, extract_text_from_pdf
import structlog

logger = structlog.get_logger(__name__)


class KnowledgeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = KnowledgeRepository(session)
        self.llm = get_llm_client()

    async def ingest_text(self, *, tenant_id: UUID, title: str, text: str) -> KnowledgeDocumentResponse:
        return await self._ingest(
            tenant_id=tenant_id,
            title=title,
            raw_text=text,
            source_type=SourceType.TEXT,
        )

    async def ingest_url(self, *, tenant_id: UUID, title: str, url: str) -> KnowledgeDocumentResponse:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()
        raw_text = extract_text_from_html(response.text)
        return await self._ingest(
            tenant_id=tenant_id,
            title=title,
            raw_text=raw_text,
            source_type=SourceType.URL,
            source_uri=url,
        )

    async def ingest_file(self, *, tenant_id: UUID, title: str, file: UploadFile) -> KnowledgeDocumentResponse:
        content = await file.read()
        filename = (file.filename or "uploaded_file").lower()
        
        if filename.endswith(".pdf"):
            source_type = SourceType.PDF
            raw_text = extract_text_from_pdf(content)
        else:
            source_type = SourceType.TEXT
            try:
                raw_text = content.decode("utf-8").strip()
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file format: Could not decode file as UTF-8 text."
                )
            
        return await self._ingest(
            tenant_id=tenant_id,
            title=title,
            raw_text=raw_text,
            source_type=source_type,
            source_uri=file.filename,
        )

    async def list_documents(self, tenant_id: UUID) -> list[KnowledgeDocumentResponse]:
        documents = await self.repository.list_documents(tenant_id)
        return [
            KnowledgeDocumentResponse(
                id=document.id,
                title=document.title,
                source_type=document.source_type,
                status=document.status,
                chunk_count=chunk_count,
                created_at=document.created_at,
            )
            for document, chunk_count in documents
        ]

    async def _ingest(
        self,
        *,
        tenant_id: UUID,
        title: str,
        raw_text: str,
        source_type: SourceType,
        source_uri: str | None = None,
    ) -> KnowledgeDocumentResponse:
        chunks = chunk_text(raw_text)
        logger.info("text_chunked", tenant_id=str(tenant_id), title=title, chunk_count=len(chunks))
        document = await self.repository.create_document(
            tenant_id=tenant_id,
            title=title,
            source_type=source_type,
            raw_text=raw_text,
            source_uri=source_uri,
            meta={"chunk_count": len(chunks)},
        )
        vectors = await self.llm.embed_texts(chunks) if chunks else []
        logger.info("embeddings_generated", tenant_id=str(tenant_id), vector_count=len(vectors))
        rows = [
            Embedding(
                tenant_id=tenant_id,
                knowledge_base_id=document.id,
                chunk_index=index,
                chunk_text=chunk,
                token_count=estimate_token_count(chunk),
                embedding=vector,
                meta={"source_type": source_type},
            )
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False))
        ]
        if rows:
            await self.repository.add_embeddings(rows)
        await self.session.commit()
        await self.session.refresh(document)
        return KnowledgeDocumentResponse(
            id=document.id,
            title=document.title,
            source_type=document.source_type,
            status=document.status,
            chunk_count=len(rows),
            created_at=document.created_at,
        )
