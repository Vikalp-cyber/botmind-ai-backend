from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.integrations.llm import get_llm_client
from app.repositories.lead_repository import LeadRepository
from app.utils.leads import classify_lead_tag, extract_contact_details


class LeadService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = LeadRepository(session)
        self.settings = get_settings()
        self.llm = get_llm_client()

    async def capture_from_transcript(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID | None,
        transcript: str,
    ):
        details = extract_contact_details(transcript)
        if self.settings.openai_api_key and not any(details.values()):
            details = await self.llm.extract_lead(transcript)
        if not any(details.values()):
            return None
        lead = await self.repository.upsert_lead(
            tenant_id=tenant_id,
            session_id=session_id,
            name=details.get("name"),
            email=details.get("email"),
            phone=details.get("phone"),
            tag=classify_lead_tag(transcript, details),
            notes={"source": "chat"},
        )
        return lead

    async def list_leads(self, tenant_id: UUID):
        return await self.repository.list_leads(tenant_id)
