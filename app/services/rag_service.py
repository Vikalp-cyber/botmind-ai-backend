from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.llm import get_llm_client
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.chat import Citation


class RagService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.repository = KnowledgeRepository(session)
        self.llm = get_llm_client()

    async def retrieve(self, *, tenant_id: UUID, query: str) -> tuple[list[Citation], list[str]]:
        [query_embedding] = await self.llm.embed_texts([query])
        results = await self.repository.search(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            limit=self.settings.rag_top_k,
        )
        citations = [
            Citation(
                knowledge_base_id=document.id,
                title=document.title,
                chunk_index=embedding.chunk_index,
                score=max(0.0, 1 - distance),
                excerpt=embedding.chunk_text[:280],
            )
            for embedding, document, distance in results
        ]
        context_blocks = [embedding.chunk_text for embedding, _, _ in results]
        return citations, context_blocks
