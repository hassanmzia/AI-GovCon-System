<p align="center">
  <h1 align="center">AI Deal Manager</h1>
  <p align="center">
    <strong>Enterprise-Grade Autonomous AI Platform for Government Contracting</strong>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-0.2-7C3AED" alt="LangGraph" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/MCP-1.0-FF6B35" alt="MCP" />
  <img src="https://img.shields.io/badge/Agents-21-E91E63" alt="21 AI Agents" />
  <img src="https://img.shields.io/badge/License-Proprietary-EF4444" alt="License" />
</p>

---

**AI Deal Manager** is an enterprise-grade, autonomous agentic deal management platform purpose-built for government contracting. It orchestrates a network of **21 specialized AI agents** across the full capture-to-close lifecycle — from opportunity discovery on SAM.gov through proposal writing, pricing analysis, legal review, teaming, compliance, and contract award.

The platform combines a robust **Django REST API** backend, a modern **Next.js 14** frontend, a **FastAPI-based AI orchestration layer** powered by LangGraph and Anthropic Claude models, real-time collaboration via **Socket.IO**, and a suite of **12 Model Context Protocol (MCP) tool servers** that give agents structured access to external data sources and internal systems.

> **Documentation Hub**: For detailed docs, see the [`docs/`](docs/) directory — including [Architecture](docs/ARCHITECTURE.md), [Data Flow](docs/DATA_FLOW.md), [User Guide](docs/USER_GUIDE.md), [Product Overview](docs/PRODUCT_OVERVIEW.md), and [API Reference](docs/API_REFERENCE.md).

---

## Table of Contents

1. [Why AI Deal Manager](#why-ai-deal-manager)
2. [Key Capabilities](#key-capabilities)
3. [System Architecture](#system-architecture)
4. [Tech Stack](#tech-stack)
5. [Prerequisites](#prerequisites)
6. [Quick Start](#quick-start)
7. [Environment Configuration](#environment-configuration)
8. [Services & Ports](#services--ports)
9. [Backend Apps (18 Modules)](#backend-apps-18-modules)
10. [AI Agents (21 Agents)](#ai-agents-21-agents)
11. [MCP Tool Servers (12 Servers)](#mcp-tool-servers-12-servers)
12. [RBAC & Security](#rbac--security)
13. [API Documentation](#api-documentation)
14. [Development Guide](#development-guide)
15. [Testing](#testing)
16. [Deployment](#deployment)
17. [Project Structure](#project-structure)
18. [Documentation Index](#documentation-index)
19. [Contributing](#contributing)
20. [License](#license)

---

## Why AI Deal Manager

Government contracting is one of the most process-intensive, document-heavy, and compliance-critical business domains in existence. Capture teams juggle dozens of opportunities simultaneously, each requiring market research, competitor analysis, teaming partner identification, proposal writing, pricing strategy, legal review, and rigorous compliance checking — all under tight deadlines.

**AI Deal Manager** eliminates manual bottlenecks by deploying a coordinated fleet of AI agents that work autonomously and collaboratively across every phase of the deal lifecycle:

| Challenge | How AI Deal Manager Solves It |
|---|---|
| **Opportunity overload** | AI continuously monitors SAM.gov, scores opportunities against your capabilities, and surfaces the highest-probability wins |
| **Slow capture planning** | Agents auto-generate capture plans, win themes, and competitive assessments from your knowledge vault |
| **Proposal bottlenecks** | Parallel AI drafting of proposal sections, grounded in your approved content library and compliance requirements |
| **Pricing complexity** | Market rate analysis, historical award benchmarking, and scenario-based price-to-win modeling |
| **Compliance risk** | Automated FAR/DFARS, CMMC, NIST 800-171, and Section 508 compliance tracking with gap analysis |
| **Teaming coordination** | AI-driven partner identification based on capability gaps and set-aside requirements |
| **Knowledge silos** | Centralized, vector-indexed knowledge vault with semantic search across all institutional knowledge |

---

## Key Capabilities

### Core Platform Features

| # | Feature | Description |
|---|---|---|
| 1 | **Autonomous Multi-Agent Orchestration** | LangGraph-powered agent graphs coordinate 21 specialized agents that hand off tasks, share context, and escalate to human reviewers when confidence thresholds are not met |
| 2 | **SAM.gov Opportunity Ingestion** | Automated polling and parsing of SAM.gov solicitations via the official API, with AI-driven scoring, classification, and routing |
| 3 | **End-to-End Proposal Factory** | Full proposal authoring environment with section-level AI drafting, compliance matrix generation, executive summary writing, and automated format checks |
| 4 | **Intelligent Pricing Engine** | Labor category mapping, market rate benchmarking (GSA schedules, FPDS-NG), and scenario-based price-to-win modeling with cost narrative generation |
| 5 | **Knowledge Vault** | Centralized, vector-indexed repository of past performance, resumes, boilerplate content, and lessons learned — semantically searchable by all agents and users |
| 6 | **Teaming & Partner Management** | Identifies teaming partners based on capability gaps and set-aside requirements; tracks NDAs and teaming agreements through signature |
| 7 | **Legal & Risk Review** | Automated contract term analysis, risk scoring, redline generation, and escalation workflows for high-risk clauses |
| 8 | **Security & Compliance Automation** | CMMC, NIST 800-171, Section 508, and FAR/DFARS compliance tracking with gap analysis, evidence collection, and remediation tasks |
| 9 | **Competitive Intelligence** | FPDS-NG analysis, incumbent identification, and competitor profiling to inform differentiation strategy |
| 10 | **Real-Time Collaboration** | Socket.IO-powered live editing, agent status streaming, notifications, and presence awareness |
| 11 | **Full Observability** | All LLM calls, agent decisions, tool invocations, and latency metrics captured in Langfuse |
| 12 | **RBAC (9 Roles)** | Nine granular roles govern access to every API endpoint and UI surface |
| 13 | **Async Task Processing** | Celery task queues with Redis broker for long-running AI workflows and document processing |
| 14 | **Document Management** | MinIO S3-compatible object storage with versioning, access control, and presigned URLs |
| 15 | **Past Performance Repository** | Structured capture and retrieval of past contract performance, CPARs, and project narratives |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            NGINX REVERSE PROXY                              │
│                        Port 80 (prod) / 3027 (dev)                          │
│                  TLS Termination • Load Balancing • Routing                  │
└────────────┬──────────────────────┬───────────────────────┬──────────────────┘
             │ /                    │ /api/ /admin/          │ /ws/
             ▼                     ▼                        ▼
┌────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐
│   NEXT.JS 14       │  │   DJANGO REST API   │  │   NODE.JS REALTIME   │
│   Frontend         │  │   (Gunicorn)        │  │   (Socket.IO)        │
│   React 18 + TS    │  │   DRF + JWT Auth    │  │   WebSocket Server   │
│   Tailwind CSS     │  │   18 Django Apps    │  │   Presence + Events  │
│   Zustand State    │  │   Port: 8001        │  │   Port: 8002         │
│   Port: 3000       │  │                     │  │                      │
└────────────────────┘  └──────────┬──────────┘  └──────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
           ┌──────────────┐ ┌──────────┐  ┌──────────────┐
           │ PostgreSQL 16│ │  Redis 7 │  │    MinIO      │
           │ + pgvector   │ │  Cache / │  │  S3-compat   │
           │ Vector Store │ │  Broker  │  │  Object Store│
           │ Port: 5432   │ │  Port:   │  │  Port:       │
           │              │ │  6379    │  │  9000/9001   │
           └──────────────┘ └──────────┘  └──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
           ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
           │ Celery       │ │ Celery   │  │  AI ORCHESTRATOR │
           │ Worker(s)    │ │ Beat     │  │  FastAPI +       │
           │ Async Tasks  │ │ Scheduler│  │  LangGraph       │
           │              │ │          │  │  Port: 8003      │
           └──────────────┘ └──────────┘  └────────┬─────────┘
                                                   │
                              ┌─────────────────────┼─────────────────────┐
                              ▼                     ▼                     ▼
                    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
                    │  21 AI AGENTS    │  │  12 MCP TOOL     │  │  Langfuse    │
                    │  ─────────────   │  │  SERVERS         │  │  LLM Tracing │
                    │  Strategy        │  │  ─────────────   │  │  Cost Track  │
                    │  Opportunity     │  │  SAM.gov         │  │  Port: 8004  │
                    │  RFP Analyst     │  │  Documents       │  └──────────────┘
                    │  Proposal Writer │  │  Email           │
                    │  Pricing         │  │  Pricing         │
                    │  Legal           │  │  Legal           │
                    │  Contracts       │  │  Market Rates    │
                    │  Research        │  │  QA Tracking     │
                    │  Marketing       │  │  Image Search    │
                    │  Security/Compl  │  │  Security/Compl  │
                    │  Teaming         │  │  Knowledge Vault │
                    │  Past Perf       │  │  Competitive     │
                    │  Communication   │  │  Diagrams        │
                    │  Learning        │  └──────────────────┘
                    │  QA              │
                    │  Deal Pipeline   │          ┌──────────────────────┐
                    │  Solution Arch   │          │  EXTERNAL SERVICES   │
                    │  Compliance      │          │  ─────────────────   │
                    │  Competitive     │  ◄──────►│  Anthropic Claude    │
                    │  Knowledge Vault │          │  SAM.gov API         │
                    │  Contracts (PA)  │          │  OpenAI (fallback)   │
                    └──────────────────┘          │  BLS / GSA / FPDS    │
                                                  └──────────────────────┘
```

### Key Architectural Decisions

| Decision | Rationale |
|---|---|
| **Polyglot services** | Django handles business logic and data persistence; FastAPI handles high-throughput AI orchestration with async/await; Node.js handles persistent WebSocket connections |
| **Agent isolation** | Each AI agent runs in its own LangGraph graph node with defined I/O schemas, enabling independent testing, replacement, and observability |
| **MCP for tool access** | Model Context Protocol servers provide agents with a standardized, auditable interface to external systems — no direct LLM-to-database access |
| **pgvector for semantic search** | All knowledge vault documents and past performance records are embedded and stored in PostgreSQL with pgvector — no separate vector database needed |
| **Celery for durability** | Long-running AI workflows (full proposal generation: 10-30 min) run as Celery tasks with retry logic, progress tracking, and result persistence |

> For detailed architecture documentation, see **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend Framework** | Next.js | 14 | SSR/SSG React application framework |
| **UI Library** | React | 18 | Component-based UI |
| **Language (FE)** | TypeScript | 5.x | Type-safe frontend development |
| **Styling** | Tailwind CSS | 3.x | Utility-first CSS framework |
| **State Management** | Zustand | 4.x | Lightweight global state |
| **Realtime (client)** | Socket.IO Client | 4.7 | WebSocket communication |
| **Backend Framework** | Django | 5.1 | Primary API and business logic |
| **REST API** | Django REST Framework | 3.x | API serialization and routing |
| **Language (BE)** | Python | 3.12 | Backend language |
| **Database** | PostgreSQL | 16 | Primary relational data store |
| **Vector Extension** | pgvector | 0.7 | Semantic similarity search |
| **Task Queue** | Celery | 5.4 | Async/distributed task processing |
| **Message Broker / Cache** | Redis | 7.x | Celery broker, Django cache |
| **Object Storage** | MinIO | latest | S3-compatible document storage |
| **AI Orchestration** | FastAPI | latest | High-performance async API for agents |
| **Agent Framework** | LangGraph | 0.2 | Stateful multi-agent graph orchestration |
| **LLM Framework** | LangChain | 0.3 | LLM abstractions and tooling |
| **Primary LLM** | Anthropic Claude | Sonnet 4.6 / Opus 4.6 | Core reasoning and generation |
| **Tool Protocol** | MCP | 1.0 | Standardized agent tool access |
| **Realtime Server** | Node.js + Socket.IO | 4.7 | WebSocket server |
| **Reverse Proxy** | NGINX | latest | Load balancing, SSL, routing |
| **Observability** | Langfuse | latest | LLM tracing, cost tracking |
| **Containerization** | Docker Compose | v2 | Local and production orchestration |

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Docker | 24.x | Required for all containerized services |
| Docker Compose | v2.20+ | Included with Docker Desktop; use `docker compose` (v2) |
| Git | 2.x | Version control |
| Node.js | 20.x LTS | Required only for local (non-Docker) frontend development |
| Python | 3.12 | Required only for local (non-Docker) backend development |
| Make | any | Optional; convenience targets in Makefile |

### External API Keys

| Service | Environment Variable | Where to Obtain |
|---|---|---|
| Anthropic Claude | `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| SAM.gov | `SAMGOV_API_KEY` | https://sam.gov/profile/details (free registration) |
| OpenAI (optional) | `OPENAI_API_KEY` | https://platform.openai.com (fallback LLM provider) |
| Langfuse (optional) | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | https://cloud.langfuse.com or self-hosted (included in compose) |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-deal-manager.git
cd ai-deal-manager
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY and SAMGOV_API_KEY
```

### 3. Start All Services

```bash
docker compose up --build
```

> First run builds all images and initializes the database (5-10 minutes).

### 4. Initialize the Database

```bash
# Run migrations
docker compose exec django-api python manage.py migrate

# Create superuser
docker compose exec django-api python manage.py createsuperuser \
    --username admin --email admin@example.com --no-input

# Set password
docker compose exec django-api python manage.py shell -c \
    "from django.contrib.auth import get_user_model; \
     User = get_user_model(); \
     u = User.objects.get(username='admin'); \
     u.set_password('Admin1234!'); \
     u.save()"

# Or load dev seed data:
docker compose exec django-api python manage.py loaddata fixtures/dev_seed.json
```

### 5. Access the Application

| Service | URL | Credentials |
|---|---|---|
| **Frontend** | http://localhost:3027 | admin / Admin1234! |
| **Django Admin** | http://localhost:3027/admin | admin / Admin1234! |
| **REST API** | http://localhost:3027/api/v1/ | JWT token |
| **AI Orchestrator** | http://localhost:8003/docs | — |
| **Langfuse** | http://localhost:8004 | See Langfuse setup |
| **MinIO Console** | http://localhost:9001 | minioadmin / changeme |

### Stopping Services

```bash
docker compose down          # Stop and remove containers
docker compose down -v       # Also remove volumes (wipes database)
```

---

## Environment Configuration

```bash
cp .env.example .env
```

<details>
<summary><strong>Full Environment Variable Reference</strong> (click to expand)</summary>

### Core Django Settings

```env
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_URL=postgresql://dealmanager:changeme@postgres:5432/dealmanager
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### Object Storage (MinIO)

```env
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET_NAME=deal-manager
MINIO_USE_SSL=False
```

### AI / LLM Configuration

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
OPENAI_API_KEY=sk-your-openai-key-here          # optional fallback
SAMGOV_API_KEY=your-samgov-api-key-here
```

### Observability (Langfuse)

```env
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://langfuse:3000
```

### Variable Reference Table

| Variable | Required | Default | Description |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | — | Django cryptographic signing key |
| `DEBUG` | No | `False` | Enable Django debug mode |
| `ALLOWED_HOSTS` | Yes | — | Comma-separated allowed hostnames |
| `DATABASE_URL` | Yes | — | PostgreSQL connection URL |
| `REDIS_URL` | Yes | — | Redis connection URL |
| `MINIO_ROOT_USER` | Yes | — | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | Yes | — | MinIO admin password |
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic Claude API key |
| `OPENAI_API_KEY` | No | — | OpenAI API key (fallback provider) |
| `LLM_PROVIDER` | No | `anthropic` | Active LLM provider |
| `LLM_MODEL` | No | `claude-sonnet-4-6` | Model identifier |
| `SAMGOV_API_KEY` | Yes | — | SAM.gov public API key |
| `LANGFUSE_PUBLIC_KEY` | No | — | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | No | — | Langfuse project secret key |
| `LANGFUSE_HOST` | No | `http://langfuse:3000` | Langfuse server URL |
| `JWT_SECRET_KEY` | Yes | — | JWT token signing secret |

</details>

---

## Services & Ports

### Docker Compose Services

| Service | Port (Host) | Description |
|---|---|---|
| `nginx` | 80, 3027 | Reverse proxy, TLS termination, static files |
| `postgres` | 5432 | PostgreSQL 16 + pgvector |
| `redis` | 6379 | Cache and Celery message broker |
| `minio` | 9000, 9001 | Object storage (API + console) |
| `django-api` | 8001 | Django REST API (Gunicorn) |
| `celery-worker` | — | Celery async task workers |
| `celery-beat` | — | Celery periodic task scheduler |
| `frontend` | — | Next.js dev/production server |
| `node-realtime` | 8002 | Node.js Socket.IO real-time server |
| `ai-orchestrator` | 8003 | FastAPI LangGraph agent orchestrator |
| `langfuse` | 8004 | LLM observability and tracing |

### NGINX Routing

| Path | Upstream | Notes |
|---|---|---|
| `/` | `frontend:3000` | Next.js application |
| `/api/` | `django-api:8001` | REST API endpoints |
| `/admin/` | `django-api:8001` | Django admin interface |
| `/ws/` | `node-realtime:8002` | WebSocket upgrade |
| `/agents/` | `ai-orchestrator:8003` | AI agent API |
| `/static/` | `django-api:8001` | Django static files |
| `/media/` | `minio:9000` | Media file proxy |

---

## Backend Apps (18 Modules)

The Django backend is organized into 18 modular applications:

| App | Description |
|---|---|
| `accounts` | Custom user model, JWT + session auth, profiles, organization management, RBAC |
| `core` | Shared base models, mixins, utilities, middleware, exception handling |
| `opportunities` | SAM.gov ingestion, scoring, classification, pipeline tracking, Go/No-Go workflows |
| `deals` | Deal workspace management, metadata, stage transitions, team assignments, activity feeds |
| `rfp` | RFP document parsing, requirements extraction, compliance matrix, Q&A tracking |
| `proposals` | Section management, outline generation, content authoring, version control, review cycles |
| `pricing` | Labor categories, rate cards, pricing models, cost volumes, price-to-win analysis |
| `contracts` | Contract documents, clause library, modification tracking, deliverable schedules |
| `strategy` | Capture strategy, win themes, discriminator tracking, competitive positioning |
| `marketing` | Marketing collateral, capability statements, past performance summaries |
| `research` | Market research, competitor profiles, industry analysis, source tagging |
| `legal` | Legal document repository, review workflows, risk flagging, redline management |
| `teaming` | Partner identification, teaming agreements, subcontractor management |
| `security_compliance` | CMMC/NIST tracking, evidence collection, gap analysis, audit logs |
| `knowledge_vault` | Vector-indexed content library, chunking/embedding pipeline, semantic search API |
| `communications` | Email integration, notifications, internal messaging, task assignments |
| `policies` | Policy document management, version control, acknowledgment tracking |
| `analytics` | Dashboard metrics, pipeline KPIs, win/loss reporting, agent performance stats |
| `past_performance` | Past contract registry, CPARs, narrative library, relevancy scoring |

---

## AI Agents (21 Agents)

The AI orchestration layer deploys 21 specialized agents, each implemented as a LangGraph graph with defined state schemas, tool access via MCP, and configurable LLM backends.

| # | Agent | Primary Responsibilities |
|---|---|---|
| 1 | **Strategy** | Capture plans, win themes, competitive discriminators, Go/No-Go recommendations |
| 2 | **Opportunity** | SAM.gov monitoring, opportunity scoring, capability matching, routing |
| 3 | **RFP Analyst** | Solicitation parsing, requirements extraction, compliance matrix, ambiguity flagging |
| 4 | **Proposal Writer** | Section drafting (technical, management, past performance) grounded in knowledge vault |
| 5 | **Pricing** | Labor mapping, market benchmarking, cost models, price narratives, price-to-win |
| 6 | **Legal** | Teaming/NDA review, risk clause identification, redline generation, escalation |
| 7 | **Contracts** | Post-award administration, deliverable tracking, modification identification |
| 8 | **Research** | Web/database research on agencies, incumbents, competitors; intelligence reports |
| 9 | **Marketing & Sales** | Capability statements, tailored past performance summaries, BD outreach |
| 10 | **Security & Compliance** | CMMC/NIST/FedRAMP/FAR assessment, gap analysis, remediation plans |
| 11 | **Teaming** | Partner identification, past performance research, teaming agreement drafts |
| 12 | **Past Performance** | Narrative retrieval, adaptation to solicitation requirements, relevancy validation |
| 13 | **Communication** | Stakeholder communications, email/RFI drafts, follow-ups, communication logs |
| 14 | **Learning** | Win/loss pattern analysis, agent tuning, prompt improvement, knowledge curation |
| 15 | **QA** | Compliance review, page/format checks, quality standards, structured feedback |
| 16 | **Deal Pipeline** | Deal health monitoring, risk identification, stage recommendations, alerts |
| 17 | **Solution Architect** | Technical concepts, architecture diagrams, staffing plans, tech stack alignment |
| 18 | **Compliance** | Final end-to-end compliance shredding before submission |
| 19 | **Competitive Intelligence** | FPDS-NG competitor profiles, incumbent analysis, pricing intelligence |
| 20 | **Knowledge Vault** | Document lifecycle, re-embedding, conflict resolution, archival recommendations |
| 21 | **Contracts (Post-Award)** | Deliverable monitoring, modification triggers, performance reporting |

### Agent Configuration

Agents are configured via `ai-orchestrator/agents/config.yaml`:

- **LLM Model Override** — Swap between `claude-sonnet-4-6` (faster) and `claude-opus-4-6` (highest capability) per agent
- **Temperature & Max Tokens** — Fine-tuned per agent role
- **Tool Access** — Declarative list of MCP tool servers each agent can invoke
- **Human-in-the-Loop** — Confidence thresholds below which agents pause for human review
- **Memory** — Short-term (in-graph), long-term (knowledge vault), and episodic (per-deal) memory

---

## MCP Tool Servers (12 Servers)

Model Context Protocol servers provide agents with structured, auditable access to external APIs and internal services.

| # | Server | Key Tools | Description |
|---|---|---|---|
| 1 | **samgov_tools** | `search_opportunities`, `get_opportunity_detail`, `get_award_data` | SAM.gov REST API integration |
| 2 | **document_tools** | `parse_pdf`, `extract_text`, `convert_docx`, `generate_pdf` | Document ingestion/conversion/generation |
| 3 | **email_tools** | `send_email`, `read_inbox`, `search_emails`, `create_draft` | Email integration and outreach |
| 4 | **pricing_tools** | `get_gsa_rates`, `search_fpds_awards`, `calculate_labor_mix` | GSA rates, FPDS-NG data, pricing models |
| 5 | **legal_tools** | `analyze_contract_clause`, `identify_risk_clauses`, `generate_redline` | Contract analysis and FAR/DFARS lookup |
| 6 | **market_rate_tools** | `get_bls_wage_data`, `search_salary_surveys` | BLS data, salary surveys, geographic diffs |
| 7 | **qa_tracking_tools** | `create_review_item`, `get_review_checklist`, `check_page_count` | QA tracking and compliance checklists |
| 8 | **image_search_tools** | `search_stock_images`, `find_diagrams` | Stock images, internal graphics, diagram prompts |
| 9 | **security_compliance_tools** | `assess_cmmc_control`, `check_nist_control` | CMMC/NIST assessment, SSP generation |
| 10 | **knowledge_vault_tools** | `semantic_search`, `get_document`, `add_document` | Semantic search, document CRUD |
| 11 | **competitive_intel_tools** | `search_competitor_awards`, `analyze_win_patterns` | Competitor tracking, recompete analysis |
| 12 | **diagram_tools** | `generate_org_chart`, `create_architecture_diagram` | Automated diagram generation |

---

## RBAC & Security

### Roles (9 Roles)

| Role | Description | Typical Users |
|---|---|---|
| `admin` | Full platform administration | IT administrators, platform owners |
| `executive` | Read all deals + analytics; approve Go/No-Go and strategy | VP, C-suite, BD leadership |
| `capture_manager` | Full deal lifecycle management; configure agents | Capture managers, BD directors |
| `proposal_manager` | Proposal workflow management; assign writers/reviewers | Proposal managers, color review leads |
| `pricing_manager` | Pricing models, rate cards, cost volumes, competitive analysis | Pricing directors, cost analysts |
| `writer` | Author/edit proposal content within assigned deals | Proposal writers, technical authors |
| `reviewer` | Review and comment on proposals; read-only deal access | Color reviewers, SMEs |
| `contracts_manager` | Post-award contract admin, modifications, deliverables | Contract admins, program managers |
| `viewer` | Read-only access to assigned deals | Subcontractors, consultants, auditors |

### Permission Matrix

| Action | admin | exec | capture | proposal | pricing | writer | reviewer | contracts | viewer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Manage users | X | | | | | | | | |
| View all deals | X | X | | | | | | | |
| Manage assigned deals | X | | X | | | | | | |
| Edit proposals | X | | X | X | | X | | | |
| Review proposals | X | X | X | X | | X | X | | |
| Manage pricing | X | | X | | X | | | | |
| Trigger AI agents | X | | X | X | X | | | | |
| Manage contracts | X | | | | | | | X | |
| View dashboards | X | X | X | X | X | | | X | X |

---

## API Documentation

### Django REST API

- **Base URL**: `http://localhost:3027/api/v1/`
- **Swagger UI**: `http://localhost:3027/api/v1/docs/`
- **OpenAPI Schema**: `http://localhost:3027/api/v1/schema/`

```bash
# Obtain JWT token
curl -X POST http://localhost:3027/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin1234!"}'
```

### AI Orchestrator API

- **Base URL**: `http://localhost:8003/`
- **Swagger UI**: `http://localhost:8003/docs`

> For complete API reference with all endpoints, request/response schemas, and examples, see **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)**.

---

## Development Guide

### Backend (Django)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp ../.env.example .env   # edit DATABASE_URL to localhost:5432
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8001

# Celery (separate terminals):
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### AI Orchestrator (FastAPI)

```bash
cd ai-orchestrator
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8003
```

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env.local   # edit API URLs to localhost
npm run dev                   # http://localhost:3000
```

### Real-Time Server (Node.js)

```bash
cd realtime
npm install
npm run dev
```

---

## Testing

```bash
# Backend (Django + pytest)
docker compose exec django-api pytest                              # all tests
docker compose exec django-api pytest --cov=. --cov-report=html    # with coverage
docker compose exec django-api pytest apps/proposals/tests/        # specific app
docker compose exec django-api pytest -m "not integration"         # skip slow tests

# AI Orchestrator
docker compose exec ai-orchestrator pytest
docker compose exec ai-orchestrator pytest --cov=. --cov-report=term-missing

# Frontend (Vitest + Playwright)
docker compose exec frontend npm run test           # unit tests
docker compose exec frontend npm run test:e2e       # e2e tests
docker compose exec frontend npm run test:coverage  # coverage report
```

---

## Deployment

### Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Pre-Deployment Checklist

- [ ] `DEBUG=False`
- [ ] Strong, unique `DJANGO_SECRET_KEY` (50+ characters)
- [ ] Strong, unique `JWT_SECRET_KEY`
- [ ] `ALLOWED_HOSTS` set to actual domain(s)
- [ ] PostgreSQL TLS and strong credentials
- [ ] Redis password set
- [ ] MinIO credentials changed from defaults
- [ ] SSL/TLS certificates in NGINX
- [ ] Anthropic API rate/spend limits configured
- [ ] Database backups configured and tested
- [ ] Log aggregation configured (Datadog, CloudWatch, Loki)
- [ ] Celery workers scaled to expected volume

### Scaling

```bash
docker compose up -d --scale celery-worker=4
```

### Production Migrations

```bash
docker compose exec django-api python manage.py migrate --no-input
docker compose exec django-api python manage.py collectstatic --no-input
```

---

## Project Structure

```
ai-deal-manager/
├── backend/                          # Django REST API
│   ├── apps/                         # 18 Django applications
│   │   ├── accounts/                 #   Users, auth, RBAC
│   │   ├── core/                     #   Shared base models and utilities
│   │   ├── opportunities/            #   SAM.gov opportunity management
│   │   ├── deals/                    #   Deal workspace management
│   │   ├── rfp/                      #   RFP parsing and analysis
│   │   ├── proposals/                #   Proposal authoring
│   │   ├── pricing/                  #   Pricing models and rate cards
│   │   ├── contracts/                #   Contract management
│   │   ├── strategy/                 #   Capture strategy
│   │   ├── marketing/                #   Marketing collateral
│   │   ├── research/                 #   Market research
│   │   ├── legal/                    #   Legal review workflows
│   │   ├── teaming/                  #   Partner management
│   │   ├── security_compliance/      #   CMMC/NIST compliance
│   │   ├── knowledge_vault/          #   Vector-indexed content library
│   │   ├── communications/           #   Email and notifications
│   │   ├── policies/                 #   Company policies
│   │   ├── analytics/                #   Dashboards and reporting
│   │   └── past_performance/         #   Past contract performance
│   ├── config/                       # Django settings, URLs, Celery
│   ├── fixtures/                     # Dev seed data
│   ├── requirements/                 # base.txt, dev.txt, prod.txt
│   ├── Dockerfile
│   └── manage.py
│
├── frontend/                         # Next.js 14 Application
│   ├── src/
│   │   ├── app/                      # App Router pages
│   │   ├── components/               # Reusable UI components
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── lib/                      # API clients, utilities
│   │   ├── store/                    # Zustand global state
│   │   └── types/                    # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
│
├── ai-orchestrator/                  # FastAPI + LangGraph
│   ├── agents/                       # 21 agent implementations
│   ├── mcp_servers/                  # 12 MCP tool servers
│   ├── workflows/                    # Multi-agent workflow graphs
│   ├── config/                       # Agent and model configuration
│   ├── routers/                      # FastAPI route handlers
│   ├── schemas/                      # Pydantic models
│   ├── Dockerfile
│   └── main.py
│
├── realtime/                         # Node.js Socket.IO Server
│   ├── src/
│   │   ├── handlers/                 # Socket event handlers
│   │   ├── middleware/               # Auth, rate limiting
│   │   └── rooms/                    # Room management
│   ├── Dockerfile
│   └── package.json
│
├── nginx/                            # NGINX Configuration
│   ├── nginx.conf
│   ├── conf.d/                       # default.conf, dev.conf
│   └── ssl/                          # Certificates (gitignored)
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md               # System architecture deep-dive
│   ├── DATA_FLOW.md                  # Data flow diagrams
│   ├── USER_GUIDE.md                 # End-user guide
│   ├── PRODUCT_OVERVIEW.md           # Product overview document
│   ├── API_REFERENCE.md              # Complete API reference
│   ├── architecture.drawio           # Editable architecture diagram
│   └── data_flow.drawio              # Editable data flow diagram
│
├── docker-compose.yml                # Base compose config
├── docker-compose.override.yml       # Dev overrides
├── docker-compose.prod.yml           # Prod overrides
├── .env.example                      # Environment template
├── Makefile                          # Convenience targets
└── README.md                         # This file
```

---

## Documentation Index

| Document | Description | Audience |
|---|---|---|
| [README.md](README.md) | Project overview, quick start, tech reference | Developers, DevOps |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Detailed system architecture, component interactions, design decisions | Architects, Senior Engineers |
| [docs/DATA_FLOW.md](docs/DATA_FLOW.md) | Data flow diagrams for all major workflows | Engineers, Architects |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Complete end-user guide for all platform modules | All platform users |
| [docs/PRODUCT_OVERVIEW.md](docs/PRODUCT_OVERVIEW.md) | Product capabilities, value proposition, competitive positioning | Stakeholders, Sales, Executives |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API endpoint reference with examples | Backend/Integration Developers |
| [ADMIN_SETUP.md](ADMIN_SETUP.md) | Admin setup and configuration guide | System Administrators |
| [MIGRATIONS_DOCUMENTATION.md](MIGRATIONS_DOCUMENTATION.md) | Database migration log and procedures | Backend Developers |

---

## Contributing

### Branch Strategy

```
main          Production-ready code (protected)
develop       Integration branch — features merge here first
feature/*     New features (e.g., feature/pricing-scenario-modeling)
fix/*         Bug fixes (e.g., fix/samgov-pagination-error)
agent/*       AI agent development (e.g., agent/qa-agent-v2)
```

### Workflow

1. Branch from `develop`
2. Follow coding standards (see below)
3. Write/update tests (80%+ coverage on new code)
4. Ensure all tests pass
5. Submit PR to `develop`

### Coding Standards

**Python / Django:** PEP 8 (enforced by `ruff`), type hints on all functions, Google-style docstrings, Django ORM preferred over raw SQL.

**TypeScript / React:** Strict mode, no `any` without justification, functional components with hooks, props interfaces with JSDoc.

**AI Agents / LangGraph:** Pydantic I/O schemas, MCP audit logging, human-in-the-loop checkpoints, prompt templates in `prompts/` directory.

### Commit Format

```
type(scope): short description

Types: feat, fix, docs, style, refactor, test, chore, agent
```

---

## License

This software is proprietary and confidential. All rights reserved.

Unauthorized copying, distribution, modification, or use of this software, in whole or in part, without the express written permission of the copyright holder is strictly prohibited.

For licensing inquiries, contact: legal@your-organization.com

---

<p align="center">
  <strong>AI Deal Manager</strong> — Built for government contractors who win.
</p>
