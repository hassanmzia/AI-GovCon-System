# AI Deal Manager — API Reference

**Version:** 2.0
**Last Updated:** March 2026
**Audience:** Backend Developers, Integration Developers, API Consumers

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication](#2-authentication)
3. [Request & Response Conventions](#3-request--response-conventions)
4. [Accounts API](#4-accounts-api)
5. [Opportunities API](#5-opportunities-api)
6. [Deals API](#6-deals-api)
7. [RFP API](#7-rfp-api)
8. [Proposals API](#8-proposals-api)
9. [Pricing API](#9-pricing-api)
10. [Contracts API](#10-contracts-api)
11. [Knowledge Vault API](#11-knowledge-vault-api)
12. [Past Performance API](#12-past-performance-api)
13. [Analytics API](#13-analytics-api)
14. [Strategy API](#14-strategy-api)
15. [Teaming API](#15-teaming-api)
16. [Legal API](#16-legal-api)
17. [Security & Compliance API](#17-security--compliance-api)
18. [Communications API](#18-communications-api)
19. [Policies API](#19-policies-api)
20. [AI Orchestrator API](#20-ai-orchestrator-api)
21. [WebSocket Events](#21-websocket-events)
22. [Error Codes](#22-error-codes)
23. [Rate Limiting](#23-rate-limiting)
24. [Pagination](#24-pagination)

---

## 1. Overview

AI Deal Manager exposes two primary APIs:

| API | Base URL | Framework | Purpose |
|---|---|---|---|
| **Django REST API** | `http://localhost:3027/api/v1/` | Django REST Framework | Business logic, CRUD, auth |
| **AI Orchestrator API** | `http://localhost:8003/` | FastAPI | Agent execution, workflows |

### Interactive Documentation

| Docs | URL |
|---|---|
| Django Swagger UI | `http://localhost:3027/api/v1/docs/` |
| Django OpenAPI Schema | `http://localhost:3027/api/v1/schema/` |
| FastAPI Swagger UI | `http://localhost:8003/docs` |
| FastAPI ReDoc | `http://localhost:8003/redoc` |

---

## 2. Authentication

### Obtain JWT Token

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "Admin1234!"
}
```

**Response (200):**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

| Token | Lifetime | Purpose |
|---|---|---|
| `access` | 15 minutes | Bearer token for API requests |
| `refresh` | 24 hours | Used to obtain a new access token |

### Use Access Token

```http
GET /api/v1/deals/
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Refresh Token

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Verify Token

```http
POST /api/v1/auth/token/verify/
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):** `{}` (empty body = valid)
**Response (401):** `{"detail": "Token is invalid or expired"}`

---

## 3. Request & Response Conventions

### Content Type

All requests and responses use `application/json` unless otherwise specified (e.g., file uploads use `multipart/form-data`).

### Pagination

All list endpoints return paginated responses:

```json
{
  "count": 142,
  "next": "http://localhost:3027/api/v1/deals/?page=2",
  "previous": null,
  "results": [
    { "id": "uuid-1", "..." },
    { "id": "uuid-2", "..." }
  ]
}
```

Default page size: 25. Override with `?page_size=50` (max 100).

### Filtering

Most list endpoints support query parameter filtering:

```
GET /api/v1/deals/?stage=proposal_dev&agency=DoD
GET /api/v1/opportunities/?fit_score_min=70&status=open
```

### Ordering

Use `?ordering=field_name` (ascending) or `?ordering=-field_name` (descending):

```
GET /api/v1/deals/?ordering=-estimated_value
```

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "code": "error_code",
  "errors": {
    "field_name": ["Validation error message"]
  }
}
```

---

## 4. Accounts API

### Users

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| `GET` | `/api/v1/users/` | List users | admin |
| `POST` | `/api/v1/users/` | Create/invite user | admin |
| `GET` | `/api/v1/users/{id}/` | Get user details | admin, self |
| `PATCH` | `/api/v1/users/{id}/` | Update user | admin, self |
| `DELETE` | `/api/v1/users/{id}/` | Deactivate user | admin |
| `GET` | `/api/v1/users/me/` | Get current user profile | any |
| `PATCH` | `/api/v1/users/me/` | Update own profile | any |

### Example: Create User

```http
POST /api/v1/users/
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "john.doe@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "capture_manager"
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "capture_manager",
  "is_active": true,
  "date_joined": "2026-03-09T10:30:00Z"
}
```

---

## 5. Opportunities API

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| `GET` | `/api/v1/opportunities/` | List opportunities | capture_manager+  |
| `POST` | `/api/v1/opportunities/` | Create opportunity | capture_manager+ |
| `GET` | `/api/v1/opportunities/{id}/` | Get opportunity details | capture_manager+ |
| `PATCH` | `/api/v1/opportunities/{id}/` | Update opportunity | capture_manager+ |
| `POST` | `/api/v1/opportunities/{id}/score/` | Trigger AI scoring | capture_manager+ |
| `POST` | `/api/v1/opportunities/sync-samgov/` | Sync from SAM.gov | admin, capture_manager |
| `GET` | `/api/v1/opportunities/{id}/similar/` | Find similar opportunities | capture_manager+ |

### Filters

| Parameter | Type | Description |
|---|---|---|
| `agency` | string | Filter by agency name |
| `naics` | string | Filter by NAICS code |
| `status` | string | `open`, `upcoming`, `closed`, `pre_solicitation` |
| `set_aside` | string | `small_business`, `8a`, `wosb`, `hubzone`, `sdvosb` |
| `recommendation` | string | `bid`, `no_bid`, `evaluate` |
| `fit_score_min` | integer | Minimum fit score (0-100) |
| `fit_score_max` | integer | Maximum fit score (0-100) |
| `response_deadline_after` | date | Deadline after this date |
| `response_deadline_before` | date | Deadline before this date |
| `search` | string | Full-text search across title, description, agency |

### Example: List High-Fit Opportunities

```http
GET /api/v1/opportunities/?fit_score_min=80&status=open&ordering=-fit_score
Authorization: Bearer <token>
```

### Example: Trigger SAM.gov Sync

```http
POST /api/v1/opportunities/sync-samgov/
Authorization: Bearer <token>
Content-Type: application/json

{
  "naics_codes": ["541512", "541519"],
  "keywords": ["cloud migration", "cybersecurity"],
  "posted_after": "2026-01-01"
}
```

**Response (202):**

```json
{
  "task_id": "abc123-def456",
  "status": "processing",
  "message": "SAM.gov sync initiated"
}
```

---

## 6. Deals API

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| `GET` | `/api/v1/deals/` | List deals | varies by role |
| `POST` | `/api/v1/deals/` | Create deal | capture_manager+ |
| `GET` | `/api/v1/deals/{id}/` | Get deal details | assigned team+ |
| `PATCH` | `/api/v1/deals/{id}/` | Update deal | capture_manager+ |
| `POST` | `/api/v1/deals/{id}/advance-stage/` | Advance stage | capture_manager+ |
| `GET` | `/api/v1/deals/{id}/activity/` | Get activity log | assigned team+ |
| `GET` | `/api/v1/deals/{id}/team/` | List team members | assigned team+ |
| `POST` | `/api/v1/deals/{id}/team/` | Add team member | capture_manager+ |
| `GET` | `/api/v1/deals/pipeline-summary/` | Pipeline stage counts | capture_manager+ |

### Example: Create Deal

```http
POST /api/v1/deals/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "DoD Cloud Migration FY26",
  "opportunity_id": "550e8400-e29b-41d4-a716-446655440000",
  "agency": "Department of Defense",
  "naics_code": "541512",
  "estimated_value": 15000000,
  "proposal_due_date": "2026-06-15",
  "set_aside_type": null,
  "capture_manager_id": "user-uuid-here"
}
```

### Example: Advance Stage

```http
POST /api/v1/deals/{id}/advance-stage/
Authorization: Bearer <token>
Content-Type: application/json

{
  "target_stage": "qualify",
  "reason": "Qualified based on incumbent analysis and scope alignment with NAICS 541512.",
  "attachments": []
}
```

**Response (200):**

```json
{
  "id": "deal-uuid",
  "stage": "qualify",
  "previous_stage": "intake",
  "transitioned_at": "2026-03-09T14:30:00Z",
  "transitioned_by": "user-uuid"
}
```

---

## 7. RFP API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/rfp/` | List RFP documents |
| `POST` | `/api/v1/rfp/` | Upload RFP document |
| `GET` | `/api/v1/rfp/{id}/` | Get RFP details |
| `POST` | `/api/v1/rfp/{id}/analyze/` | Trigger AI analysis |
| `GET` | `/api/v1/rfp/{id}/compliance-matrix/` | Get compliance matrix |
| `PATCH` | `/api/v1/rfp/{id}/compliance-matrix/{item_id}/` | Update matrix item |
| `GET` | `/api/v1/rfp/{id}/questions/` | List Q&A items |
| `POST` | `/api/v1/rfp/{id}/questions/` | Add question |

### Example: Upload RFP

```http
POST /api/v1/rfp/
Authorization: Bearer <token>
Content-Type: multipart/form-data

deal_id: <deal-uuid>
file: <RFP.pdf>
auto_analyze: true
```

---

## 8. Proposals API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/proposals/` | List proposals |
| `POST` | `/api/v1/proposals/` | Create proposal |
| `GET` | `/api/v1/proposals/{id}/` | Get proposal details |
| `PATCH` | `/api/v1/proposals/{id}/` | Update proposal metadata |
| `GET` | `/api/v1/proposals/{id}/sections/` | List sections |
| `POST` | `/api/v1/proposals/{id}/sections/` | Create section |
| `PATCH` | `/api/v1/proposals/{id}/sections/{sid}/` | Update section content |
| `POST` | `/api/v1/proposals/{id}/generate/` | Trigger AI generation |
| `POST` | `/api/v1/proposals/{id}/export/` | Export to DOCX/PDF |
| `GET` | `/api/v1/proposals/{id}/sections/{sid}/comments/` | List section comments |
| `POST` | `/api/v1/proposals/{id}/sections/{sid}/comments/` | Add comment |

### Example: Trigger AI Generation

```http
POST /api/v1/proposals/{id}/generate/
Authorization: Bearer <token>
Content-Type: application/json

{
  "sections": ["technical_approach", "management_approach", "past_performance"],
  "model": "claude-opus-4-6",
  "use_knowledge_vault": true,
  "use_past_performance": true
}
```

**Response (202):**

```json
{
  "task_id": "task-uuid",
  "status": "processing",
  "estimated_duration_seconds": 600
}
```

---

## 9. Pricing API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/pricing/rate-cards/` | List rate cards |
| `POST` | `/api/v1/pricing/rate-cards/` | Create rate card |
| `GET` | `/api/v1/pricing/rate-cards/{id}/` | Get rate card |
| `GET` | `/api/v1/pricing/scenarios/` | List cost scenarios |
| `POST` | `/api/v1/pricing/scenarios/` | Create scenario |
| `GET` | `/api/v1/pricing/scenarios/{id}/` | Get scenario details |
| `POST` | `/api/v1/pricing/scenarios/{id}/line-items/` | Add line item |
| `POST` | `/api/v1/pricing/scenarios/compare/` | Compare scenarios |
| `POST` | `/api/v1/pricing/win-price-analysis/` | Trigger win price analysis |

---

## 10. Contracts API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/contracts/` | List contracts |
| `POST` | `/api/v1/contracts/` | Create contract |
| `GET` | `/api/v1/contracts/{id}/` | Get contract details |
| `GET` | `/api/v1/contracts/templates/` | List templates |
| `POST` | `/api/v1/contracts/templates/` | Create template |
| `GET` | `/api/v1/contracts/clause-library/` | Search clause library |
| `POST` | `/api/v1/contracts/clause-library/` | Add clause |
| `POST` | `/api/v1/contracts/{id}/redline/` | Upload counterparty version |
| `GET` | `/api/v1/contracts/{id}/redline/` | Get redline comparison |

---

## 11. Knowledge Vault API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/knowledge-vault/documents/` | List documents |
| `POST` | `/api/v1/knowledge-vault/documents/` | Upload document |
| `GET` | `/api/v1/knowledge-vault/documents/{id}/` | Get document |
| `DELETE` | `/api/v1/knowledge-vault/documents/{id}/` | Delete document |
| `GET` | `/api/v1/knowledge-vault/search/` | Semantic search |
| `GET` | `/api/v1/knowledge-vault/articles/` | List articles |
| `POST` | `/api/v1/knowledge-vault/articles/` | Create article |

### Example: Semantic Search

```http
GET /api/v1/knowledge-vault/search/?q=cloud+migration+federal+health&limit=10
Authorization: Bearer <token>
```

**Response (200):**

```json
{
  "query": "cloud migration federal health",
  "results": [
    {
      "id": "chunk-uuid",
      "document_id": "doc-uuid",
      "document_title": "VA Cloud Migration Past Performance",
      "content": "Migrated 200+ applications to AWS GovCloud...",
      "relevance_score": 0.94,
      "metadata": {
        "category": "past_performance",
        "agency": "VA",
        "naics": "541512"
      }
    }
  ]
}
```

---

## 12. Past Performance API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/past-performance/` | List records |
| `POST` | `/api/v1/past-performance/` | Create record |
| `GET` | `/api/v1/past-performance/{id}/` | Get record |
| `PATCH` | `/api/v1/past-performance/{id}/` | Update record |
| `GET` | `/api/v1/past-performance/search/` | Semantic search |
| `POST` | `/api/v1/past-performance/generate-narrative/` | Generate PP narrative |

---

## 13. Analytics API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/analytics/pipeline/` | Pipeline metrics |
| `GET` | `/api/v1/analytics/win-loss/` | Win/loss statistics |
| `GET` | `/api/v1/analytics/agent-performance/` | Agent performance data |
| `GET` | `/api/v1/analytics/deadlines/` | Upcoming deadlines |
| `GET` | `/api/v1/analytics/kpis/` | Dashboard KPI data |

### Example: Pipeline Metrics

```http
GET /api/v1/analytics/pipeline/
Authorization: Bearer <token>
```

**Response (200):**

```json
{
  "total_pipeline_value": 125000000,
  "active_deals": 42,
  "stages": {
    "intake": {"count": 8, "value": 15000000},
    "qualify": {"count": 6, "value": 12000000},
    "bid_no_bid": {"count": 4, "value": 8000000},
    "capture_plan": {"count": 5, "value": 18000000},
    "proposal_dev": {"count": 7, "value": 28000000},
    "red_team": {"count": 3, "value": 12000000},
    "final_review": {"count": 2, "value": 8000000},
    "submit": {"count": 3, "value": 10000000},
    "post_submit": {"count": 2, "value": 6000000},
    "award_pending": {"count": 1, "value": 4000000},
    "contract_setup": {"count": 1, "value": 4000000}
  },
  "win_rate_ytd": 0.52,
  "avg_cycle_days": 87
}
```

---

## 14. Strategy API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/strategy/` | List strategy documents |
| `POST` | `/api/v1/strategy/` | Create strategy |
| `GET` | `/api/v1/strategy/{id}/` | Get strategy details |
| `GET` | `/api/v1/strategy/{id}/win-themes/` | List win themes |
| `POST` | `/api/v1/strategy/{id}/win-themes/` | Add win theme |

---

## 15. Teaming API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/teaming/partners/` | List partners |
| `POST` | `/api/v1/teaming/partners/` | Add partner |
| `GET` | `/api/v1/teaming/agreements/` | List agreements |
| `POST` | `/api/v1/teaming/agreements/` | Create agreement |
| `PATCH` | `/api/v1/teaming/agreements/{id}/` | Update agreement status |

---

## 16. Legal API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/legal/reviews/` | List review requests |
| `POST` | `/api/v1/legal/reviews/` | Submit for review |
| `GET` | `/api/v1/legal/reviews/{id}/` | Get review details |
| `PATCH` | `/api/v1/legal/reviews/{id}/` | Update review status |
| `GET` | `/api/v1/legal/risk-flags/` | List risk flags |

---

## 17. Security & Compliance API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/compliance/assessments/` | List assessments |
| `POST` | `/api/v1/compliance/assessments/` | Create assessment |
| `GET` | `/api/v1/compliance/controls/` | List controls |
| `GET` | `/api/v1/compliance/evidence/` | List evidence |
| `POST` | `/api/v1/compliance/evidence/` | Upload evidence |

---

## 18. Communications API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/communications/` | List communications |
| `POST` | `/api/v1/communications/` | Create communication |
| `GET` | `/api/v1/communications/{id}/` | Get details |
| `POST` | `/api/v1/communications/{id}/send/` | Send communication |

---

## 19. Policies API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/policies/` | List policies |
| `POST` | `/api/v1/policies/` | Create policy |
| `GET` | `/api/v1/policies/{id}/` | Get policy |
| `GET` | `/api/v1/policies/{id}/acknowledgments/` | List acknowledgments |
| `POST` | `/api/v1/policies/{id}/acknowledge/` | Acknowledge policy |

---

## 20. AI Orchestrator API

**Base URL:** `http://localhost:8003/`

### Agents

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/agents/` | List all available agents |
| `POST` | `/agents/{agent_name}/run` | Run agent synchronously |
| `POST` | `/agents/{agent_name}/run-async` | Run agent asynchronously |
| `GET` | `/agents/{agent_name}/status/{task_id}` | Get async task status |

### Example: Run Agent Synchronously

```http
POST /agents/opportunity/run
Content-Type: application/json

{
  "opportunity_id": "opp-uuid",
  "actions": ["score", "recommend"],
  "model_override": "claude-opus-4-6"
}
```

**Response (200):**

```json
{
  "agent": "opportunity",
  "status": "completed",
  "result": {
    "fit_score": 87,
    "recommendation": "bid",
    "reasoning": "Strong NAICS alignment, relevant past performance...",
    "confidence": 0.91
  },
  "execution_time_ms": 4500,
  "tokens_used": 12500,
  "cost_usd": 0.038
}
```

### Workflows

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/workflows/proposal-generation` | Full proposal generation |
| `POST` | `/workflows/opportunity-analysis` | Complete opportunity analysis |
| `GET` | `/workflows/{workflow_id}/status` | Workflow progress |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `GET` | `/metrics` | Prometheus metrics |

---

## 21. WebSocket Events

Connect to the Socket.IO server at `ws://localhost:3027/ws/`.

### Client-to-Server Events

| Event | Payload | Description |
|---|---|---|
| `join_deal` | `{deal_id}` | Join a deal room |
| `leave_deal` | `{deal_id}` | Leave a deal room |
| `proposal_edit` | `{section_id, content, cursor_pos}` | Send edit to collaborators |

### Server-to-Client Events

| Event | Payload | Description |
|---|---|---|
| `deal:update` | `{deal_id, field, value}` | Deal data changed |
| `deal:stage_changed` | `{deal_id, from_stage, to_stage}` | Stage transition |
| `proposal:edit` | `{section_id, content, user_id}` | Collaborator edit |
| `proposal:saved` | `{proposal_id, timestamp}` | Proposal saved |
| `notification` | `{type, message, link}` | Push notification |
| `presence:join` | `{user_id, deal_id}` | User joined deal room |
| `presence:leave` | `{user_id, deal_id}` | User left deal room |
| `agent:progress` | `{task_id, percentage, message}` | Agent progress update |
| `agent:complete` | `{task_id, result}` | Agent finished |

---

## 22. Error Codes

| HTTP Code | Meaning | Common Causes |
|---|---|---|
| `400` | Bad Request | Invalid JSON, missing required fields, validation error |
| `401` | Unauthorized | Missing/expired JWT token |
| `403` | Forbidden | Insufficient role permissions |
| `404` | Not Found | Resource does not exist or not accessible |
| `409` | Conflict | Duplicate resource (e.g., duplicate email) |
| `413` | Payload Too Large | File upload exceeds 50 MB limit |
| `422` | Unprocessable Entity | Valid JSON but semantically invalid |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `502` | Bad Gateway | Upstream service unavailable |
| `503` | Service Unavailable | Service is starting up or overloaded |

---

## 23. Rate Limiting

| Endpoint Category | Limit | Window |
|---|---|---|
| Authentication | 10 requests | per minute |
| SAM.gov Sync | 1 request | per 5 minutes |
| AI Agent Run | 20 requests | per minute |
| Standard API | 100 requests | per minute |
| File Upload | 10 requests | per minute |
| Semantic Search | 30 requests | per minute |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 94
X-RateLimit-Reset: 1709978400
```

---

## 24. Pagination

All list endpoints support cursor-based or offset pagination:

### Offset Pagination (Default)

```
GET /api/v1/deals/?page=2&page_size=25
```

Response includes `count`, `next`, `previous`, and `results`.

### Cursor Pagination (Optional)

For large datasets, use cursor pagination:

```
GET /api/v1/opportunities/?cursor=cD0yMDI2LTAzLTA5
```

Response includes `next` cursor URL and `results`.

---

*For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md). For data flow diagrams, see [DATA_FLOW.md](DATA_FLOW.md).*

*This document is maintained by the platform engineering team. Last reviewed: March 2026.*
