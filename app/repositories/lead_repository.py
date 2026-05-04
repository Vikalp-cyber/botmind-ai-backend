from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lead, LeadTag


class LeadRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_lead(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID | None,
        name: str | None,
        email: str | None,
        phone: str | None,
        tag: LeadTag,
        notes: dict | None = None,
    ) -> Lead:
        conditions = []
        if email:
            conditions.append(Lead.email == email)
        if phone:
            conditions.append(Lead.phone == phone)

        lead = None
        if conditions:
            lead = await self.session.scalar(
                select(Lead).where(Lead.tenant_id == tenant_id, or_(*conditions))
            )
        if lead is None:
            lead = Lead(
                tenant_id=tenant_id,
                session_id=session_id,
                name=name,
                email=email,
                phone=phone,
                tag=tag,
                notes=notes or {},
            )
            self.session.add(lead)
        else:
            lead.name = name or lead.name
            lead.email = email or lead.email
            lead.phone = phone or lead.phone
            lead.tag = tag
            lead.session_id = session_id or lead.session_id
            lead.notes = {**lead.notes, **(notes or {})}
        await self.session.flush()
        return lead

    async def list_leads(self, tenant_id: UUID) -> list[Lead]:
        result = await self.session.execute(select(Lead).where(Lead.tenant_id == tenant_id))
        return list(result.scalars().all())
