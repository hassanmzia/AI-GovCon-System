# AI Deal Manager — System Architecture

**Version:** 2.0
**Last Updated:** March 2026
**Audience:** System Architects, Senior Engineers, DevOps Engineers

---

## Table of Contents

1. [Architecture Philosophy](#1-architecture-philosophy)
2. [High-Level System Architecture](#2-high-level-system-architecture)
3. [Service Topology](#3-service-topology)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Backend Architecture](#5-backend-architecture)
6. [AI Orchestration Layer](#6-ai-orchestration-layer)
7. [Agent Architecture](#7-agent-architecture)
8. [MCP Tool Server Architecture](#8-mcp-tool-server-architecture)
9. [Real-Time Communication](#9-real-time-communication)
10. [Data Layer](#10-data-layer)
11. [Authentication & Authorization](#11-authentication--authorization)
12. [Async Task Processing](#12-async-task-processing)
13. [Observability & Monitoring](#13-observability--monitoring)
14. [Security Architecture](#14-security-architecture)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Scalability Considerations](#16-scalability-considerations)

---

## 1. Architecture Philosophy

AI Deal Manager follows a **service-oriented, polyglot architecture** designed around these principles:

| Principle | Implementation |
|---|---|
| **Separation of concerns** | Each service owns a single domain: Django for business logic, FastAPI for AI orchestration, Node.js for real-time communication |
| **Agent isolation** | Each of 21 AI agents runs as an independent LangGraph graph node with defined I/O contracts |
| **Standardized tool access** | Model Context Protocol (MCP) provides a uniform, auditable interface between agents and external systems |
| **Human-in-the-loop by default** | Every agent has configurable confidence thresholds — below threshold, work is routed to human reviewers |
| **Async-first for AI workloads** | Long-running AI tasks are managed as durable Celery tasks with retry, progress tracking, and result persistence |
| **Vector-native search** | pgvector extension in PostgreSQL eliminates the need for a separate vector database |
| **Infrastructure as code** | Docker Compose for consistent dev/staging/prod environments |

---

## 2. High-Level System Architecture

```
                                 ┌─────────────────┐
                                 │   End Users      │
                                 │   (Browser)      │
                                 └────────┬─────────┘
                                          │ HTTPS
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              NGINX REVERSE PROXY                               │
│                                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  /       │    │ /api/*   │    │ /admin/* │    │ /ws/*    │    │ /agents/*│  │
│  │  ────►   │    │  ────►   │    │  ────►   │    │  ────►   │    │  ────►   │  │
│  │ Frontend │    │ Django   │    │ Django   │    │ Node.js  │    │ FastAPI  │  │
│  │  :3000   │    │  :8001   │    │  :8001   │    │  :8002   │    │  :8003   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                                 │
│  TLS Termination  •  Rate Limiting  •  CORS  •  Static File Serving            │
└─────────────────────────────────────────────────────────────────────────────────┘
             │                │                │                │
             ▼                ▼                ▼                ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
    │  Next.js 14 │  │  Django 5.1  │  │  Node.js     │  │  FastAPI         │
    │  FRONTEND   │  │  BACKEND     │  │  REALTIME    │  │  AI ORCHESTRATOR │
    │             │  │              │  │              │  │                  │
    │  React 18   │  │  DRF 3.x     │  │  Socket.IO  │  │  LangGraph 0.2   │
    │  TypeScript │  │  18 Apps      │  │  Express    │  │  LangChain 0.3   │
    │  Tailwind   │  │  Celery 5.4  │  │  JWT Auth   │  │  21 Agents       │
    │  Zustand    │  │  JWT Auth    │  │              │  │  12 MCP Servers  │
    └─────────────┘  └──────┬───────┘  └──────────────┘  └────────┬─────────┘
                            │                                      │
               ┌────────────┼────────────┐              ┌─────────┼──────────┐
               ▼            ▼            ▼              ▼         ▼          ▼
        ┌───────────┐ ┌──────────┐ ┌──────────┐  ┌──────────┐ ┌────────┐ ┌────────┐
        │PostgreSQL │ │  Redis   │ │  MinIO   │  │ Anthropic│ │SAM.gov │ │Langfuse│
        │16+pgvect  │ │  7.x     │ │  S3      │  │ Claude   │ │ API    │ │Tracing │
        └───────────┘ └──────────┘ └──────────┘  └──────────┘ └────────┘ └────────┘
```

---

## 3. Service Topology

### Service Dependency Graph

```
                    nginx
                   / | \ \
                  /  |  \ \
                 ▼   ▼   ▼ ▼
          frontend  django  node-realtime  ai-orchestrator
                      |                        |
               ┌──────┼──────┐          ┌──────┼──────┐
               ▼      ▼      ▼          ▼      ▼      ▼
           postgres  redis  minio   anthropic sam.gov langfuse
               ▲      ▲
               │      │
          ┌────┴──────┴────┐
          │                │
    celery-worker    celery-beat
```

### Service Communication Matrix

| From | To | Protocol | Purpose |
|---|---|---|---|
| nginx | frontend | HTTP | Proxy SSR pages |
| nginx | django-api | HTTP | Proxy REST API |
| nginx | node-realtime | WebSocket | Proxy WS connections |
| nginx | ai-orchestrator | HTTP | Proxy agent API |
| frontend | django-api | REST/HTTP | Data CRUD operations |
| frontend | node-realtime | WebSocket | Real-time updates |
| django-api | postgres | TCP/SQL | Data persistence |
| django-api | redis | TCP | Cache, sessions, Celery broker |
| django-api | minio | HTTP/S3 | Document storage |
| django-api | ai-orchestrator | REST/HTTP | Trigger agent workflows |
| celery-worker | postgres | TCP/SQL | Task state, data access |
| celery-worker | redis | TCP | Task broker, result backend |
| celery-worker | ai-orchestrator | REST/HTTP | Async agent invocation |
| ai-orchestrator | anthropic | HTTPS | LLM inference |
| ai-orchestrator | sam.gov | HTTPS | Opportunity data |
| ai-orchestrator | langfuse | HTTPS | Tracing and cost |
| ai-orchestrator | postgres | TCP/SQL | Knowledge vault vectors |
| node-realtime | redis | TCP | Pub/sub for cross-instance messaging |

---

## 4. Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       NEXT.JS 14 APPLICATION                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     APP ROUTER                            │   │
│  │                                                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │(auth)/   │ │dashboard/│ │deals/    │ │proposals/│    │   │
│  │  │ login    │ │          │ │ [id]/    │ │ [id]/    │    │   │
│  │  │ register │ │          │ │ edit     │ │ sections │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │opportun- │ │pricing/  │ │contracts/│ │knowledge-│    │   │
│  │  │ities/   │ │          │ │          │ │vault/    │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │analytics/│ │settings/ │ │admin/    │ │...more   │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐     │
│  │ COMPONENTS  │  │   HOOKS      │  │   STATE (Zustand)   │     │
│  │             │  │              │  │                     │     │
│  │ Layout      │  │ useAuth      │  │ authStore           │     │
│  │ Sidebar     │  │ useDeals     │  │ dealStore           │     │
│  │ TopBar      │  │ useSocket    │  │ opportunityStore    │     │
│  │ KanbanBoard │  │ useOpps      │  │ proposalStore       │     │
│  │ DataTable   │  │ useProposals │  │ pricingStore        │     │
│  │ Charts      │  │ usePricing   │  │ uiStore (theme)     │     │
│  │ Forms       │  │ useAnalytics │  │ notificationStore   │     │
│  │ Modals      │  │ useKnowledge │  │ socketStore         │     │
│  └─────────────┘  └─────────────┘  └─────────────────────┘     │
│                                                                 │
│  ┌─────────────────────┐  ┌───────────────────────────────┐     │
│  │    LIB / SERVICES   │  │      TYPES (TypeScript)       │     │
│  │                     │  │                               │     │
│  │ apiClient (axios)   │  │ Deal, Opportunity, Proposal   │     │
│  │ authService         │  │ User, Role, Permission        │     │
│  │ socketService       │  │ PricingScenario, RateCard     │     │
│  │ formatters          │  │ ComplianceMatrix, Section     │     │
│  └─────────────────────┘  └───────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Design Patterns

- **Server-Side Rendering (SSR)** for SEO-irrelevant but latency-sensitive pages
- **Client-Side State** via Zustand stores for cross-component reactivity
- **API Layer Abstraction** — all REST calls go through `lib/apiClient.ts` with interceptors for JWT refresh
- **Socket.IO Integration** — persistent connection managed via `hooks/useSocket.ts` with automatic reconnection
- **Theme System** — Light/Dark mode toggle persisted in localStorage, applied via Tailwind CSS `dark:` variants
- **Responsive Design** — Mobile-first with collapsible sidebar (hamburger menu < 768px)

---

## 5. Backend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO 5.1 BACKEND                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    config/ (Project Root)                  │   │
│  │  settings/base.py  •  settings/dev.py  •  settings/prod.py│   │
│  │  urls.py  •  celery.py  •  wsgi.py                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────── DJANGO APPS ────────────────────────┐   │
│  │                                                          │   │
│  │  CORE DOMAIN            │  INTELLIGENCE DOMAIN           │   │
│  │  ─────────────          │  ─────────────────────         │   │
│  │  accounts               │  opportunities                 │   │
│  │  core                   │  analytics                     │   │
│  │  deals                  │  knowledge_vault               │   │
│  │  contracts              │  past_performance              │   │
│  │  communications         │  research                      │   │
│  │                         │                                │   │
│  │  PROPOSAL DOMAIN        │  COMPLIANCE DOMAIN             │   │
│  │  ───────────────        │  ─────────────────             │   │
│  │  rfp                    │  security_compliance           │   │
│  │  proposals              │  legal                         │   │
│  │  pricing                │  policies                      │   │
│  │  strategy               │                                │   │
│  │  marketing              │  COLLABORATION DOMAIN          │   │
│  │  teaming                │  ─────────────────────         │   │
│  │                         │  communications                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────── CROSS-CUTTING ────────────────────────┐   │
│  │                                                          │   │
│  │  Middleware          │  Authentication      │  Caching    │   │
│  │  ──────────          │  ──────────────      │  ───────    │   │
│  │  CORS               │  JWT (SimpleJWT)     │  Redis      │   │
│  │  Auth Enforcement    │  Session Fallback    │  Per-view   │   │
│  │  Request Logging     │  Permission Classes  │  Template   │   │
│  │  Rate Limiting       │  RBAC Decorators     │  Fragment   │   │
│  │  Exception Handler   │                      │             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────── INTEGRATIONS ─────────────────────────┐   │
│  │  PostgreSQL (ORM)  •  Redis (cache/broker)               │   │
│  │  MinIO (S3 storage) •  Celery (async tasks)              │   │
│  │  AI Orchestrator (HTTP client)                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Django App Architecture Pattern

Each Django app follows a consistent internal structure:

```
apps/<app_name>/
├── models.py          # Domain models (inherit from core.BaseModel)
├── serializers.py     # DRF serializers for API I/O
├── views.py           # DRF viewsets and API views
├── urls.py            # URL routing
├── services.py        # Business logic layer
├── permissions.py     # RBAC permission classes
├── filters.py         # DRF filter backends
├── signals.py         # Django signals for side effects
├── tasks.py           # Celery task definitions
├── admin.py           # Django admin configuration
├── tests/             # pytest test modules
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
└── migrations/        # Database migrations
```

---

## 6. AI Orchestration Layer

```
┌──────────────────────────────────────────────────────────────────┐
│                    FASTAPI AI ORCHESTRATOR                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application                     │    │
│  │  main.py  •  Pydantic schemas  •  Dependency injection    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────── ROUTERS ─────────────────────────────────────┐    │
│  │  /agents/{name}/run       Synchronous agent execution     │    │
│  │  /agents/{name}/run-async Async (Celery) agent execution  │    │
│  │  /agents/{name}/status    Task status polling             │    │
│  │  /workflows/{name}        Multi-agent workflow execution  │    │
│  │  /health                  Service health check            │    │
│  │  /metrics                 Prometheus metrics              │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────── LANGGRAPH ENGINE ────────────────────────────┐    │
│  │                                                           │    │
│  │  ┌───────────────────────────────────────────────────┐   │    │
│  │  │              WORKFLOW GRAPHS                       │   │    │
│  │  │                                                    │   │    │
│  │  │   Proposal Generation    Opportunity Analysis      │   │    │
│  │  │        Graph                  Graph                │   │    │
│  │  │   ┌────┐ ┌────┐         ┌────┐ ┌────┐            │   │    │
│  │  │   │RFP │►│Prop│         │Opp │►│Str │            │   │    │
│  │  │   │Anal│ │Writ│         │Agt │ │Agt │            │   │    │
│  │  │   └────┘ └──┬─┘         └────┘ └──┬─┘            │   │    │
│  │  │             ▼                      ▼               │   │    │
│  │  │          ┌────┐              ┌────┐               │   │    │
│  │  │          │QA  │              │Comp│               │   │    │
│  │  │          │Agt │              │Int │               │   │    │
│  │  │          └──┬─┘              └────┘               │   │    │
│  │  │             ▼                                      │   │    │
│  │  │          ┌────┐                                    │   │    │
│  │  │          │Comp│                                    │   │    │
│  │  │          │Agt │                                    │   │    │
│  │  │          └────┘                                    │   │    │
│  │  └───────────────────────────────────────────────────┘   │    │
│  │                                                           │    │
│  │  ┌───────────────────────────────────────────────────┐   │    │
│  │  │              INDIVIDUAL AGENTS (21)                │   │    │
│  │  │                                                    │   │    │
│  │  │  Each agent is a LangGraph StateGraph with:        │   │    │
│  │  │  • Input/Output Pydantic schemas                   │   │    │
│  │  │  • Tool bindings (via MCP)                         │   │    │
│  │  │  • LLM configuration (model, temp, tokens)        │   │    │
│  │  │  • Human-in-the-loop breakpoints                   │   │    │
│  │  │  • Memory configuration                            │   │    │
│  │  │  • Langfuse tracing hooks                          │   │    │
│  │  └───────────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────── MCP TOOL SERVERS (12) ───────────────────────┐    │
│  │  samgov  •  document  •  email  •  pricing  •  legal      │    │
│  │  market_rate  •  qa_tracking  •  image_search             │    │
│  │  security_compliance  •  knowledge_vault                  │    │
│  │  competitive_intel  •  diagram                            │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Agent Architecture

### Single Agent Internal Structure

```
┌──────────────────────────────────────────────────────────────┐
│                    LANGGRAPH AGENT                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   STATE SCHEMA                         │  │
│  │  (Pydantic BaseModel)                                  │  │
│  │                                                        │  │
│  │  messages: List[BaseMessage]    # Conversation history │  │
│  │  context: Dict[str, Any]       # Deal/opportunity ctx │  │
│  │  tools_output: Dict            # Results from tools   │  │
│  │  confidence: float             # Agent confidence      │  │
│  │  requires_human_review: bool   # HITL flag            │  │
│  │  output: Any                   # Final agent output   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────── GRAPH NODES ────────────────────────┐  │
│  │                                                        │  │
│  │  [START] ──► [retrieve_context] ──► [reason]           │  │
│  │                                        │               │  │
│  │                              ┌─────────┴─────────┐     │  │
│  │                              ▼                   ▼     │  │
│  │                        [use_tools]        [human_review]│  │
│  │                              │                   │     │  │
│  │                              ▼                   ▼     │  │
│  │                        [synthesize] ◄────────────┘     │  │
│  │                              │                         │  │
│  │                              ▼                         │  │
│  │                           [END]                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────── CONFIGURATION ──────────────────────┐  │
│  │  llm_model: claude-sonnet-4-6 | claude-opus-4-6       │  │
│  │  temperature: 0.0 - 1.0                               │  │
│  │  max_tokens: 1024 - 8192                              │  │
│  │  confidence_threshold: 0.7                            │  │
│  │  allowed_tools: [mcp_server_1, mcp_server_2, ...]     │  │
│  │  max_iterations: 5                                    │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Agent Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AGENT MEMORY                            │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  SHORT-TERM      │  │  LONG-TERM   │  │  EPISODIC      │ │
│  │  (In-Graph)      │  │  (K. Vault)  │  │  (Per-Deal)    │ │
│  │                  │  │              │  │                │ │
│  │  Current         │  │  Semantic    │  │  Deal-specific │ │
│  │  conversation    │  │  search of   │  │  context from  │ │
│  │  context and     │  │  knowledge   │  │  prior agent   │ │
│  │  tool results    │  │  vault via   │  │  runs on this  │ │
│  │  within this     │  │  pgvector    │  │  deal stored   │ │
│  │  single run      │  │  embeddings  │  │  in deal       │ │
│  │                  │  │              │  │  metadata      │ │
│  │  Scope: request  │  │  Scope: org  │  │  Scope: deal   │ │
│  └─────────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. MCP Tool Server Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                   MCP TOOL SERVER PATTERN                      │
│                                                               │
│  ┌─────────────┐         ┌──────────────┐       ┌──────────┐│
│  │  AI Agent    │  MCP    │  Tool Server │ HTTP  │ External ││
│  │  (LangGraph) │ ──────►│              │──────►│ Service  ││
│  │             │ Request │  Validates    │       │          ││
│  │             │         │  Executes     │       │ SAM.gov  ││
│  │             │◄────────│  Returns      │◄──────│ BLS.gov  ││
│  │             │ Response│  Logs audit   │       │ GSA      ││
│  └─────────────┘         └──────┬───────┘       └──────────┘│
│                                 │                            │
│                                 ▼                            │
│                          ┌──────────────┐                    │
│                          │   Langfuse   │                    │
│                          │  Audit Trail │                    │
│                          │  (every call │                    │
│                          │   logged)    │                    │
│                          └──────────────┘                    │
└───────────────────────────────────────────────────────────────┘
```

### Tool Server Interaction Flow

```
Agent                 MCP Server              External API
  │                       │                        │
  │  tool_call(params)    │                        │
  │──────────────────────►│                        │
  │                       │  validate(params)      │
  │                       │──────┐                 │
  │                       │      │                 │
  │                       │◄─────┘                 │
  │                       │                        │
  │                       │  api_request(...)       │
  │                       │───────────────────────►│
  │                       │                        │
  │                       │  api_response(...)      │
  │                       │◄───────────────────────│
  │                       │                        │
  │                       │  transform(response)   │
  │                       │──────┐                 │
  │                       │      │                 │
  │                       │◄─────┘                 │
  │                       │                        │
  │                       │  log_to_langfuse(...)   │
  │                       │──────┐                 │
  │                       │      │                 │
  │                       │◄─────┘                 │
  │                       │                        │
  │  tool_result(data)    │                        │
  │◄──────────────────────│                        │
  │                       │                        │
```

---

## 9. Real-Time Communication

```
┌──────────────────────────────────────────────────────────────────┐
│                    REAL-TIME ARCHITECTURE                         │
│                                                                  │
│  ┌──────────────┐           ┌──────────────────┐                │
│  │  Browser A    │           │  Browser B        │                │
│  │  (User 1)     │           │  (User 2)         │                │
│  │               │           │                   │                │
│  │  Socket.IO    │           │  Socket.IO        │                │
│  │  Client       │           │  Client           │                │
│  └──────┬───────┘           └──────┬────────────┘                │
│         │ WSS                      │ WSS                         │
│         └──────────┬───────────────┘                             │
│                    ▼                                             │
│  ┌──────────────────────────────────────────┐                   │
│  │          NODE.JS SOCKET.IO SERVER         │                   │
│  │                                           │                   │
│  │  ┌─────────────────────────────────────┐ │                   │
│  │  │         EVENT HANDLERS               │ │                   │
│  │  │                                      │ │                   │
│  │  │  deal:update     Agent status change │ │                   │
│  │  │  proposal:edit   Live editing events │ │                   │
│  │  │  notification    Push notifications  │ │                   │
│  │  │  presence        User online status  │ │                   │
│  │  │  agent:stream    AI output streaming │ │                   │
│  │  └─────────────────────────────────────┘ │                   │
│  │                                           │                   │
│  │  ┌─────────────────────────────────────┐ │                   │
│  │  │          ROOM MANAGEMENT             │ │                   │
│  │  │                                      │ │                   │
│  │  │  deal:{deal_id}      Per-deal rooms  │ │                   │
│  │  │  proposal:{prop_id}  Per-proposal    │ │                   │
│  │  │  user:{user_id}      Per-user notif  │ │                   │
│  │  │  org:{org_id}        Org-wide events │ │                   │
│  │  └─────────────────────────────────────┘ │                   │
│  │                    │                      │                   │
│  │                    ▼                      │                   │
│  │           ┌──────────────┐               │                   │
│  │           │  Redis Pub/Sub│               │                   │
│  │           │  (cross-node) │               │                   │
│  │           └──────────────┘               │                   │
│  └──────────────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. Data Layer

### Database Schema Organization

```
┌──────────────────────────────────────────────────────────────────┐
│                     POSTGRESQL 16 + PGVECTOR                     │
│                                                                  │
│  ┌─────────────────────── SCHEMAS ──────────────────────────┐   │
│  │                                                           │   │
│  │  ACCOUNTS                    DEALS & PIPELINE             │   │
│  │  ────────                    ──────────────               │   │
│  │  users                       deals                        │   │
│  │  organizations               deal_team_members            │   │
│  │  user_profiles               deal_stage_history           │   │
│  │  roles                       deal_activities              │   │
│  │                                                           │   │
│  │  OPPORTUNITIES               PROPOSALS                    │   │
│  │  ─────────────               ─────────                    │   │
│  │  opportunities               proposals                    │   │
│  │  opportunity_scores          proposal_sections            │   │
│  │  samgov_sync_logs            section_versions             │   │
│  │                              review_comments              │   │
│  │  RFP                                                      │   │
│  │  ───                         PRICING                      │   │
│  │  rfp_documents               ───────                      │   │
│  │  compliance_matrix_items     rate_cards                    │   │
│  │  rfp_questions               labor_categories             │   │
│  │                              cost_scenarios               │   │
│  │  CONTRACTS                   cost_line_items              │   │
│  │  ─────────                                                │   │
│  │  contracts                   KNOWLEDGE VAULT              │   │
│  │  contract_clauses            ───────────────              │   │
│  │  contract_modifications      documents                    │   │
│  │  clause_library              document_chunks              │   │
│  │                              embeddings (pgvector)        │   │
│  │  COMPLIANCE                                               │   │
│  │  ──────────                  PAST PERFORMANCE             │   │
│  │  compliance_controls         ────────────────             │   │
│  │  compliance_evidence         performance_records          │   │
│  │  compliance_assessments      cpars_ratings                │   │
│  │                              reference_contacts           │   │
│  │  ANALYTICS                                                │   │
│  │  ─────────                   POLICIES                     │   │
│  │  pipeline_snapshots          ────────                     │   │
│  │  win_loss_records            policy_documents             │   │
│  │  agent_performance_logs      policy_acknowledgments       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────── VECTOR STORAGE ───────────────────────┐   │
│  │  pgvector extension (v0.7)                                │   │
│  │  • 1536-dimensional embeddings (OpenAI ada-002 compatible)│   │
│  │  • HNSW index for ANN search                             │   │
│  │  • Cosine similarity distance metric                      │   │
│  │  • Used by: knowledge_vault, past_performance, proposals  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Object Storage (MinIO)

```
MinIO S3-Compatible Storage
├── deal-manager/                    # Primary bucket
│   ├── rfp-documents/               # Uploaded RFP files
│   ├── proposals/                   # Generated proposal documents
│   ├── contracts/                   # Contract documents
│   ├── knowledge-vault/             # Knowledge vault uploads
│   ├── past-performance/            # PP evidence documents
│   ├── exports/                     # Generated exports (PDF, DOCX)
│   └── temp/                        # Temporary processing files
```

---

## 11. Authentication & Authorization

```
┌──────────────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW                              │
│                                                                  │
│  Client                    Django                   Database     │
│    │                         │                         │         │
│    │  POST /auth/token/      │                         │         │
│    │  {username, password}   │                         │         │
│    │────────────────────────►│                         │         │
│    │                         │  validate credentials   │         │
│    │                         │────────────────────────►│         │
│    │                         │                         │         │
│    │                         │  user record + roles    │         │
│    │                         │◄────────────────────────│         │
│    │                         │                         │         │
│    │  {access, refresh}      │  sign JWT (access 15m,  │         │
│    │◄────────────────────────│  refresh 24h)           │         │
│    │                         │                         │         │
│    │  GET /api/v1/deals/     │                         │         │
│    │  Authorization: Bearer  │                         │         │
│    │────────────────────────►│                         │         │
│    │                         │  verify JWT signature   │         │
│    │                         │  extract user + roles   │         │
│    │                         │  check RBAC permissions │         │
│    │                         │  return filtered data   │         │
│    │  {deals: [...]}         │                         │         │
│    │◄────────────────────────│                         │         │
│    │                         │                         │         │
│    │  POST /auth/token/      │                         │         │
│    │  refresh/               │                         │         │
│    │  {refresh: "eyJ..."}    │                         │         │
│    │────────────────────────►│                         │         │
│    │                         │  validate refresh token │         │
│    │  {access: "new eyJ..."} │  issue new access token │         │
│    │◄────────────────────────│                         │         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. Async Task Processing

```
┌──────────────────────────────────────────────────────────────────┐
│                    CELERY TASK ARCHITECTURE                       │
│                                                                  │
│  ┌──────────────┐     ┌────────────┐     ┌──────────────────┐   │
│  │  Django API   │     │   Redis    │     │  Celery Workers  │   │
│  │  (Producer)   │────►│   Broker   │────►│  (Consumers)     │   │
│  │               │     │            │     │                  │   │
│  │  Enqueue task │     │  FIFO      │     │  Execute task    │   │
│  │  Return ID    │     │  Queues    │     │  Store result    │   │
│  └──────────────┘     └────────────┘     └──────────────────┘   │
│                                                                  │
│  ┌───────────────── TASK CATEGORIES ────────────────────────┐   │
│  │                                                           │   │
│  │  AI Workflows (High Priority)                             │   │
│  │  ────────────────────────────                             │   │
│  │  • Full proposal generation (10-30 min)                   │   │
│  │  • Opportunity scoring and classification                 │   │
│  │  • Compliance matrix generation                           │   │
│  │  • Price-to-win analysis                                  │   │
│  │                                                           │   │
│  │  Document Processing (Medium Priority)                    │   │
│  │  ─────────────────────────────────                        │   │
│  │  • RFP PDF parsing and text extraction                    │   │
│  │  • Document chunking and embedding                        │   │
│  │  • Proposal export (DOCX/PDF generation)                  │   │
│  │  • OCR for scanned documents                              │   │
│  │                                                           │   │
│  │  Scheduled Tasks (Celery Beat)                            │   │
│  │  ─────────────────────────────                            │   │
│  │  • SAM.gov opportunity sync (every 6 hours)               │   │
│  │  • Pipeline health snapshot (daily)                        │   │
│  │  • Deadline notification check (hourly)                    │   │
│  │  • Knowledge vault re-indexing (weekly)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 13. Observability & Monitoring

```
┌──────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                     LANGFUSE                               │  │
│  │                                                            │  │
│  │  Traces every LLM call with:                               │  │
│  │  • Input prompt and system message                         │  │
│  │  • Output completion                                       │  │
│  │  • Model used, tokens consumed, latency                    │  │
│  │  • Cost calculation (per-token pricing)                     │  │
│  │  • Tool calls and results                                  │  │
│  │  • Agent decision tree                                     │  │
│  │  • User feedback (thumbs up/down)                          │  │
│  │                                                            │  │
│  │  Dashboards:                                               │  │
│  │  • Cost per agent, per workflow, per user                  │  │
│  │  • Latency percentiles (p50, p95, p99)                     │  │
│  │  • Token usage trends                                      │  │
│  │  • Error rate by agent                                     │  │
│  │  • Quality scores over time                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   APPLICATION LOGGING                      │  │
│  │                                                            │  │
│  │  Django:  structured JSON logs → stdout → log aggregator   │  │
│  │  FastAPI: structured JSON logs → stdout → log aggregator   │  │
│  │  Node.js: structured JSON logs → stdout → log aggregator   │  │
│  │  Celery:  task lifecycle events → Redis → log aggregator   │  │
│  │  NGINX:   access + error logs → stdout → log aggregator    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   HEALTH CHECKS                            │  │
│  │                                                            │  │
│  │  /health endpoints on all services:                        │  │
│  │  • Django: DB, Redis, MinIO, Celery connectivity           │  │
│  │  • FastAPI: LLM provider, MCP servers, memory              │  │
│  │  • Node.js: Redis pub/sub, active connections              │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 14. Security Architecture

| Layer | Controls |
|---|---|
| **Network** | NGINX TLS termination, CORS whitelisting, rate limiting per IP |
| **Authentication** | JWT with short-lived access tokens (15 min), refresh rotation (24h), bcrypt password hashing |
| **Authorization** | 9-role RBAC enforced at API view level via DRF permission classes |
| **Data at Rest** | PostgreSQL with TLS; MinIO with server-side encryption |
| **Data in Transit** | TLS 1.3 for all external connections; internal Docker network isolation |
| **Secrets** | Environment variables; never committed to version control; `.env` in `.gitignore` |
| **Input Validation** | DRF serializer validation; Pydantic schemas on AI orchestrator; parameterized SQL queries |
| **Audit Trail** | All deal stage transitions, proposal edits, agent runs, and admin actions logged with timestamp and user |
| **LLM Security** | MCP tool servers prevent direct LLM-to-database access; tool permissions scoped per agent |
| **Session Security** | Account lockout after 5 failed attempts (15 min), JWT blacklisting on logout |

---

## 15. Deployment Architecture

### Production Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRODUCTION DEPLOYMENT                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    DOCKER COMPOSE                          │  │
│  │                                                            │  │
│  │  nginx (1)  ──►  frontend (1)                              │  │
│  │             ──►  django-api (1, Gunicorn N workers)        │  │
│  │             ──►  node-realtime (1)                         │  │
│  │             ──►  ai-orchestrator (1)                       │  │
│  │                                                            │  │
│  │  celery-worker (1-N, scalable)                             │  │
│  │  celery-beat (1, singleton)                                │  │
│  │                                                            │  │
│  │  postgres (1, with WAL + point-in-time recovery)           │  │
│  │  redis (1, with AOF persistence)                           │  │
│  │  minio (1, with bucket versioning)                         │  │
│  │  langfuse (1)                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Production Hardening:                                           │
│  • DEBUG=False, strong secrets, TLS everywhere                   │
│  • Gunicorn workers = (2 * CPU cores) + 1                        │
│  • Celery workers scaled by task volume                          │
│  • PostgreSQL: connection pooling, automated backups             │
│  • Redis: password, maxmemory policy, persistence               │
│  • NGINX: rate limiting, request size limits, security headers   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 16. Scalability Considerations

| Component | Scaling Strategy |
|---|---|
| **Django API** | Horizontal: Gunicorn worker count; Vertical: CPU/RAM per container |
| **Celery Workers** | Horizontal: `docker compose up --scale celery-worker=N` |
| **AI Orchestrator** | Vertical: CPU/RAM for concurrent LLM calls; consider async request pooling |
| **PostgreSQL** | Vertical: CPU/RAM/IOPS; Read replicas for analytics queries |
| **Redis** | Vertical: RAM; Redis Cluster for high-availability |
| **MinIO** | Horizontal: distributed mode for multi-node; bucket versioning for durability |
| **Node.js Realtime** | Horizontal: multiple instances with Redis adapter for cross-node pub/sub |
| **NGINX** | Load balancer in front of multiple NGINX instances (cloud LB or HAProxy) |

---

*For data flow details, see [DATA_FLOW.md](DATA_FLOW.md). For API specifics, see [API_REFERENCE.md](API_REFERENCE.md).*

*This document is maintained by the platform engineering team. Last reviewed: March 2026.*
