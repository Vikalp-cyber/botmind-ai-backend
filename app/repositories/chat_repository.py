from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, Message, MessageRole


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_session(self, tenant_id: UUID, external_id: str) -> ChatSession:
        statement = select(ChatSession).where(
            ChatSession.tenant_id == tenant_id,
            ChatSession.external_id == external_id,
        )
        session = await self.session.scalar(statement)
        if session is not None:
            session.last_activity_at = datetime.now(UTC)
            await self.session.flush()
            return session

        session = ChatSession(
            tenant_id=tenant_id,
            external_id=external_id,
            last_activity_at=datetime.now(UTC),
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def add_message(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        role: MessageRole,
        content: str,
        cached_response: bool = False,
        meta: dict | None = None,
    ) -> Message:
        message = Message(
            tenant_id=tenant_id,
            session_id=session_id,
            role=role,
            content=content,
            cached_response=cached_response,
            meta=meta or {},
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, tenant_id: UUID, session_id: UUID) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.tenant_id == tenant_id, Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_messages_by_external_id(self, tenant_id: UUID, external_id: str) -> list[Message]:
        statement = (
            select(Message)
            .join(ChatSession, ChatSession.id == Message.session_id)
            .where(Message.tenant_id == tenant_id, ChatSession.external_id == external_id)
            .order_by(Message.created_at.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_sessions(self, tenant_id: UUID) -> list[ChatSession]:
        statement = (
            select(ChatSession)
            .where(ChatSession.tenant_id == tenant_id)
            .order_by(desc(ChatSession.created_at))
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())
