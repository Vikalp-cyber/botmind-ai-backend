# Botmind AI Backend

Production-ready FastAPI backend for a multi-tenant AI chatbot SaaS platform with RAG, tenant isolation, JWT auth, Redis-backed memory/cache, lead capture, usage tracking, and CRM webhooks.

## Highlights

- Multi-tenant PostgreSQL schema with `tenant_id` on all tenant-owned tables
- PostgreSQL Row-Level Security bootstrap script using `SET LOCAL app.current_tenant`
- JWT auth with role-based access and tenant-scoped API keys for widget traffic
- RAG pipeline using `pgvector` cosine similarity and OpenAI `text-embedding-3-small`
- Knowledge base ingestion for raw text, URLs, and PDFs
- Redis session memory, response cache, and rate limiting
- Lead capture from chat transcripts with webhook delivery hooks
- Session-based chat history, usage tracking, and optional WebSocket chat

## Project Layout

```text
app/
  api/            FastAPI routes and request dependencies
  core/           settings, security, logging, rate limiting, exceptions
  db/             SQLAlchemy models and async session setup
  integrations/   OpenAI client
  repositories/   data access layer
  schemas/        request/response models
  services/       auth, chat, RAG, knowledge, leads, usage, webhooks
  utils/          chunking, text extraction, hashing, lead parsing
sql/
  00_apply_schema.sh  Applies schema (embedding dimension from EMBEDDING_DIMENSIONS)
  01_schema.tpl       Schema template (substituted into Postgres on first boot)
  02_rls.sql          Row-level security policies
tests/            focused unit tests
```

## Core Endpoints

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/api-keys`
- `POST /api/v1/chat`
- `GET /api/v1/history/sessions`
- `GET /api/v1/history/sessions/{session_id}`
- `POST /api/v1/knowledge-base/text`
- `POST /api/v1/knowledge-base/url`
- `POST /api/v1/knowledge-base/file`
- `GET /api/v1/leads`
- `GET /api/v1/usage/summary`
- `GET /api/v1/webhooks/endpoints`
- `POST /api/v1/webhooks/endpoints`
- `POST /api/v1/webhooks/dispatch-test`
- `WS /api/v1/ws/chat/{tenant_id}/{session_id}?token=<jwt>`

## Local Run

1. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` plus a real `JWT_SECRET_KEY`.
2. Start infrastructure:

```bash
docker compose up -d postgres redis
```

3. Install dependencies and run the API:

```bash
pip install -e .
uvicorn app.main:app --reload
```

4. Start the full stack with containers if preferred:

```bash
docker compose up --build
```

The `postgres` container runs `sql/00_apply_schema.sh` (which applies `01_schema.tpl` using `EMBEDDING_DIMENSIONS`, default 768 for Ollama `nomic-embed-text`) then `sql/02_rls.sql` on first boot. If you change embedding size after init, recreate the volume (`docker compose down -v`) or alter the `embeddings.embedding` column to match.

## Tenant Isolation

Every authenticated request resolves the tenant and runs:

```sql
SELECT set_config('app.current_tenant', :tenant_id, true);
```

RLS policies in [sql/02_rls.sql](/c:/New%20folder/botmind-ai/sql/02_rls.sql) then enforce tenant filtering inside PostgreSQL itself, not just in application code.

## Chat Flow

1. Validate tenant auth via JWT or widget API key.
2. Store the incoming user message.
3. Create an embedding for the message.
4. Search tenant-scoped `embeddings` with cosine similarity.
5. Pull recent Redis memory for the session.
6. Send context plus the query to the LLM.
7. Cache the answer, persist assistant output, capture leads, and track usage.

## Testing

```bash
pytest
python -m compileall app
```

## Notes

- OpenAI integration uses the current Python SDK patterns for embeddings and the Responses API.
- Cost tracking is scaffolded and persisted, but exact per-model billing math is left configurable because pricing can change.
- The code is ready for Alembic integration if you want migration files added next.
