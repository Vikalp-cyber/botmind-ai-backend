# Knowledge Base API Documentation

This document describes how to interact with the Botmind AI Knowledge Base API.

## Base URL
`http://localhost:8000/api/v1/knowledge-base`

## Authentication
All requests (except health check) require a Bearer Token in the `Authorization` header.

**Header Example:**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 1. List Documents
Retrieve all documents uploaded to your knowledge base.

**Endpoint:** `GET /`

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/knowledge-base" \
     -H "Authorization: Bearer $TOKEN"
```

---

## 2. Ingest Raw Text
Submit a block of text to be indexed and used for chat context.

**Endpoint:** `POST /text`

**Body (JSON):**
```json
{
  "title": "Company Policy",
  "text": "Our office hours are 9 AM to 5 PM..."
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-base/text" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "Company Policy",
           "text": "Our office hours are 9 AM to 5 PM..."
         }'
```

---

## 3. Ingest from URL (Web Scraping)
Provide a URL, and the system will scrape the text content.

**Endpoint:** `POST /url`

**Body (JSON):**
```json
{
  "title": "Documentation Page",
  "url": "https://example.com/docs"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-base/url" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "Documentation Page",
           "url": "https://example.com/docs"
         }'
```

---

## 4. Ingest from File (PDF/TXT)
Upload a document file. Supported formats: `.pdf`, `.txt`.

**Endpoint:** `POST /file`
**Content-Type:** `multipart/form-data`

**Form Fields:**
- `title`: (string) The name of the document.
- `file`: (binary) The actual file content.

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-base/file" \
     -H "Authorization: Bearer $TOKEN" \
     -F "title=Employee Handbook" \
     -F "file=@/path/to/your/document.pdf"
```

---

## Response Format
Success responses (201 Created) return the following structure:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Employee Handbook",
  "source_type": "pdf",
  "status": "active",
  "chunk_count": 42,
  "created_at": "2024-05-04T10:00:00Z"
}
```

## Error Handling
- **401 Unauthorized**: Missing or invalid token.
- **400 Bad Request**: Invalid file format (e.g., missing PDF header) or malformed JSON.
- **403 Forbidden**: User does not have 'admin' role (required for ingestion).
- **404 Not Found**: Tenant context could not be resolved from token.
