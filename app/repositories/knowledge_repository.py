from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Embedding, KnowledgeBase


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(
        self,
        *,
        tenant_id: UUID,
        title: str,
        source_type: str,
        raw_text: str,
        source_uri: str | None = None,
        meta: dict | None = None,
    ) -> KnowledgeBase:
        document = KnowledgeBase(
            tenant_id=tenant_id,
            title=title,
            source_type=source_type,
            raw_text=raw_text,
            source_uri=source_uri,
            meta=meta or {},
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def add_embeddings(self, rows: list[Embedding]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def list_documents(self, tenant_id: UUID) -> list[tuple[KnowledgeBase, int]]:
        statement: Select = (
            select(KnowledgeBase, func.count(Embedding.id))
            .outerjoin(Embedding, Embedding.knowledge_base_id == KnowledgeBase.id)
            .where(KnowledgeBase.tenant_id == tenant_id)
            .group_by(KnowledgeBase.id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.all())

    async def search(
        self,
        *,
        tenant_id: UUID,
        query_embedding: list[float],
        limit: int,
    ) -> list[tuple[Embedding, KnowledgeBase, float]]:
        distance = Embedding.embedding.cosine_distance(query_embedding).label("distance")
        statement = (
            select(Embedding, KnowledgeBase, distance)
            .join(KnowledgeBase, KnowledgeBase.id == Embedding.knowledge_base_id)
            .where(Embedding.tenant_id == tenant_id)
            .order_by(distance.asc())
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return [(row[0], row[1], float(row[2])) for row in result.all()]
