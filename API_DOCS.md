# Botmind AI Backend (v0.1.0)

## health API

### Healthcheck
**`GET`** `/api/v1/health`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | N/A |

---

## auth API

### Signup
**`POST`** `/api/v1/auth/signup`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `SignupRequest`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `201` | Successful Response | `TokenResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

### Login
**`POST`** `/api/v1/auth/login`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `LoginRequest`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `TokenResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

### Me
**`GET`** `/api/v1/auth/me`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `UserResponse` |

---

### Create Api Key
**`POST`** `/api/v1/auth/api-keys`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `APIKeyCreateRequest`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `201` | Successful Response | `APIKeyResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

## chat API

### Chat
**`POST`** `/api/v1/chat`


**Parameters:**

| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `Authorization` | `header` | No | `any` |  |
| `X-API-Key` | `header` | No | `any` |  |

**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `ChatRequest`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `ChatResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

## knowledge-base API

### List Documents
**`GET`** `/api/v1/knowledge-base`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `KnowledgeDocumentResponse` |

---

### Ingest Text
**`POST`** `/api/v1/knowledge-base/text`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `KnowledgeTextIngestRequest`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `201` | Successful Response | `KnowledgeDocumentResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

### Ingest Url
**`POST`** `/api/v1/knowledge-base/url`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `KnowledgeUrlIngestRequest`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `201` | Successful Response | `KnowledgeDocumentResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

### Ingest File
**`POST`** `/api/v1/knowledge-base/file`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `multipart/form-data`
- **Schema:** `Body_ingest_file_api_v1_knowledge_base_file_post`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `201` | Successful Response | `KnowledgeDocumentResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

## history API

### List Sessions
**`GET`** `/api/v1/history/sessions`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `SessionResponse` |

---

### Get Session Messages
**`GET`** `/api/v1/history/sessions/{session_id}`


**Parameters:**

| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `session_id` | `path` | Yes | `string` |  |

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `MessageResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

## leads API

### List Leads
**`GET`** `/api/v1/leads`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `LeadResponse` |

---

## usage API

### Summary
**`GET`** `/api/v1/usage/summary`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `UsageSummaryResponse` |

---

## webhooks API

### List Endpoints
**`GET`** `/api/v1/webhooks/endpoints`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | `WebhookEndpointResponse` |

---

### Create Endpoint
**`POST`** `/api/v1/webhooks/endpoints`


**Request Body:**

- **Required:** Yes
- **Content-Type:** `application/json`
- **Schema:** `WebhookEndpointCreate`

**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `201` | Successful Response | `WebhookEndpointResponse` |
| `422` | Validation Error | `HTTPValidationError` |

---

### Dispatch Test
**`POST`** `/api/v1/webhooks/dispatch-test`


**Responses:**

| Status Code | Description | Schema |
|---|---|---|
| `200` | Successful Response | N/A |

---

## Schemas & Models

### `APIKeyCreateRequest`

| Property | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes |  |


### `APIKeyResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `name` | `string` | Yes |  |
| `raw_key` | `string or null` | No |  |


### `Body_ingest_file_api_v1_knowledge_base_file_post`

| Property | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes |  |
| `file` | `string` | Yes |  |


### `ChatRequest`

| Property | Type | Required | Description |
|---|---|---|---|
| `message` | `string` | Yes |  |
| `session_id` | `string` | Yes |  |
| `tenant_id` | `string` | Yes |  |


### `ChatResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `response` | `string` | Yes |  |
| `session_id` | `string` | Yes |  |
| `tenant_id` | `string` | Yes |  |
| `cached` | `boolean` | No |  |
| `citations` | `Array[Citation]` | No |  |
| `lead_captured` | `boolean` | No |  |


### `Citation`

| Property | Type | Required | Description |
|---|---|---|---|
| `knowledge_base_id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `chunk_index` | `integer` | Yes |  |
| `score` | `number` | Yes |  |
| `excerpt` | `string` | Yes |  |


### `HTTPValidationError`

| Property | Type | Required | Description |
|---|---|---|---|
| `detail` | `Array[ValidationError]` | No |  |


### `KnowledgeDocumentResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `source_type` | `string` | Yes |  |
| `status` | `string` | Yes |  |
| `chunk_count` | `integer` | Yes |  |
| `created_at` | `string` | Yes |  |


### `KnowledgeTextIngestRequest`

| Property | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes |  |
| `text` | `string` | Yes |  |


### `KnowledgeUrlIngestRequest`

| Property | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes |  |
| `url` | `string` | Yes |  |


### `LeadResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `session_id` | `string or null` | Yes |  |
| `name` | `string or null` | Yes |  |
| `email` | `string or null` | Yes |  |
| `phone` | `string or null` | Yes |  |
| `tag` | `string` | Yes |  |
| `created_at` | `string` | Yes |  |


### `LoginRequest`

| Property | Type | Required | Description |
|---|---|---|---|
| `tenant_slug` | `string` | Yes |  |
| `email` | `string` | Yes |  |
| `password` | `string` | Yes |  |


### `MessageResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `role` | `string` | Yes |  |
| `content` | `string` | Yes |  |
| `created_at` | `string` | Yes |  |


### `SessionResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `external_id` | `string` | Yes |  |
| `channel` | `string` | Yes |  |
| `created_at` | `string` | Yes |  |
| `last_activity_at` | `string or null` | Yes |  |


### `SignupRequest`

| Property | Type | Required | Description |
|---|---|---|---|
| `tenant_name` | `string` | Yes |  |
| `tenant_slug` | `string` | Yes |  |
| `full_name` | `string` | Yes |  |
| `email` | `string` | Yes |  |
| `password` | `string` | Yes |  |


### `TokenResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `access_token` | `string` | Yes |  |
| `token_type` | `string` | No |  |
| `tenant_id` | `string` | Yes |  |
| `role` | `string` | Yes |  |


### `UsageSummaryResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `total_requests` | `integer` | Yes |  |
| `prompt_tokens` | `integer` | Yes |  |
| `completion_tokens` | `integer` | Yes |  |
| `total_cost_usd` | `number` | Yes |  |
| `cache_hits` | `integer` | Yes |  |


### `UserResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `tenant_id` | `string` | Yes |  |
| `full_name` | `string` | Yes |  |
| `email` | `string` | Yes |  |
| `role` | `string` | Yes |  |
| `is_active` | `boolean` | Yes |  |


### `ValidationError`

| Property | Type | Required | Description |
|---|---|---|---|
| `loc` | `Array[]` | Yes |  |
| `msg` | `string` | Yes |  |
| `type` | `string` | Yes |  |
| `input` | `` | No |  |
| `ctx` | `object` | No |  |


### `WebhookEndpointCreate`

| Property | Type | Required | Description |
|---|---|---|---|
| `provider` | `string` | Yes |  |
| `url` | `string` | Yes |  |
| `secret` | `string or null` | No |  |


### `WebhookEndpointResponse`

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `provider` | `string` | Yes |  |
| `url` | `string` | Yes |  |
| `is_active` | `boolean` | Yes |  |
| `created_at` | `string` | Yes |  |

