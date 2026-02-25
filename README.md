# AI Deal Manager

<!-- Badges -->
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.1-green?logo=django)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![License](https://img.shields.io/badge/License-Proprietary-red)

**AI Deal Manager** is an enterprise-grade, autonomous agentic deal management platform purpose-built for government contracting. It orchestrates a network of 21 specialized AI agents across the full capture-to-close lifecycle — from opportunity discovery on SAM.gov through proposal writing, pricing analysis, legal review, teaming, compliance, and contract award.

The platform combines a robust Django REST API backend, a modern Next.js 14 frontend, a FastAPI-based AI orchestration layer powered by LangGraph and Anthropic Claude models, real-time collaboration via Socket.IO, and a suite of 12 Model Context Protocol (MCP) tool servers that give agents structured access to external data sources and internal systems.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Architecture Overview](#3-architecture-overview)
4. [Tech Stack](#4-tech-stack)
5. [Prerequisites](#5-prerequisites)
6. [Quick Start](#6-quick-start)
7. [Environment Setup](#7-environment-setup)
8. [Services & Ports](#8-services--ports)
9. [Backend Apps](#9-backend-apps)
10. [AI Agents](#10-ai-agents)
11. [MCP Tool Servers](#11-mcp-tool-servers)
12. [RBAC Roles](#12-rbac-roles)
13. [API Documentation](#13-api-documentation)
14. [Development Setup (Local)](#14-development-setup-local)
15. [Running Tests](#15-running-tests)
16. [Deployment](#16-deployment)
17. [Project Structure](#17-project-structure)
18. [Contributing](#18-contributing)
19. [License](#19-license)

---

## 1. Project Overview

Government contracting is one of the most process-intensive, document-heavy, and compliance-critical business domains in existence. Capture teams juggle dozens of opportunities simultaneously, each requiring market research, competitor analysis, teaming partner identification, proposal writing, pricing strategy, legal review, and rigorous compliance checking — all under tight deadlines.

**AI Deal Manager** eliminates manual bottlenecks by deploying a coordinated fleet of AI agents that work autonomously and collaboratively across every phase of the deal lifecycle:

- **Opportunity Discovery**: Continuously monitors SAM.gov and other sources for relevant solicitations, scores them against your past performance and capabilities, and surfaces the highest-probability wins.
- **Capture Planning**: Automatically generates capture plans, win themes, and competitive assessments using your knowledge vault and market intelligence.
- **Proposal Automation**: Drafts, reviews, and iterates on proposal sections in parallel, grounded in your approved content library and compliance requirements.
- **Pricing Intelligence**: Analyzes market rates, historical contract data, and labor category benchmarks to recommend compliant and competitive pricing strategies.
- **Legal & Compliance**: Reviews teaming agreements, NDAs, and contract terms; flags risks; and ensures Section 508, FAR/DFARS, and customer-specific compliance requirements are met.
- **Real-Time Collaboration**: Entire teams work together in live sessions with full audit trails, role-based access, and AI-assisted content generation surfaced directly in the editing workflow.

---

## 2. Features

### Core Platform Features

1. **Autonomous Multi-Agent Orchestration** — LangGraph-powered agent graphs coordinate 21 specialized agents that hand off tasks, share context, and escalate to human reviewers when confidence thresholds are not met.

2. **SAM.gov Opportunity Ingestion** — Automated polling and parsing of SAM.gov solicitations via the official API, with AI-driven scoring, classification, and routing to the appropriate capture team.

3. **End-to-End Proposal Factory** — Full proposal authoring environment with section-level AI drafting, compliance matrix generation, executive summary writing, and automated page-count and format checks.

4. **Intelligent Pricing Engine** — Labor category mapping, market rate benchmarking (GSA schedules, FPDS-NG data), and scenario-based price-to-win modeling with cost narrative generation.

5. **Knowledge Vault** — Centralized, vector-indexed repository of past performance narratives, resumes, boilerplate content, approved graphics, and lessons learned — semantically searchable by all agents and users.

6. **Teaming & Partner Management** — Identifies potential teaming partners based on capability gaps, small business set-aside requirements, and historical performance; tracks NDAs and teaming agreements through signature.

7. **Legal & Risk Review** — Automated contract term analysis, risk scoring, redline generation, and escalation workflows for high-risk clauses, powered by specialized legal AI agents.

8. **Security & Compliance Automation** — Continuous CMMC, NIST 800-171, Section 508, and FAR/DFARS compliance tracking with gap analysis, evidence collection, and remediation task generation.

9. **Competitive Intelligence** — Web research, FPDS-NG analysis, and incumbent identification to build competitor profiles and inform differentiation strategy.

10. **Real-Time Collaboration** — Socket.IO-powered live editing, agent status streaming, notification delivery, and presence awareness across all active users.

11. **Full Observability** — All LLM calls, agent decisions, tool invocations, and latency metrics are captured in Langfuse for tracing, cost analysis, and continuous improvement.

12. **Role-Based Access Control** — Nine granular RBAC roles govern access to every API endpoint and UI surface, from read-only viewer through full administrative control.

13. **Async Task Processing** — Celery task queues with Redis broker handle long-running AI workflows, document processing, OCR, scheduled opportunity polling, and report generation without blocking the request/response cycle.

14. **Document Management** — MinIO S3-compatible object storage for all uploaded and generated documents, with versioning, access control, and direct presigned URL generation for the frontend.

15. **Past Performance Repository** — Structured capture and retrieval of past contract performance data, CPARs, and project narratives for reuse in new proposals and agency relationship mapping.

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          NGINX (Reverse Proxy)                       │
│                     Port 80 (prod) / 3027 (dev)                      │
└──────────┬──────────────────────────┬───────────────────────────────┘
           │                          │                          │
           ▼                          ▼                          ▼
┌──────────────────┐    ┌─────────────────────┐    ┌────────────────────┐
│   Next.js 14     │    │   Django REST API    │    │  Node.js Realtime  │
│   Frontend       │    │   (django-api)       │    │  (Socket.IO)       │
│   Port: 3000     │    │   Port: 8001         │    │  Port: 8002        │
└──────────────────┘    └──────────┬──────────┘    └────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
           ┌──────────────┐ ┌──────────┐ ┌──────────────┐
           │  PostgreSQL  │ │  Redis   │ │    MinIO     │
           │  + pgvector  │ │  Cache / │ │  Object      │
           │  Port: 5432  │ │  Broker  │ │  Storage     │
           └──────────────┘ │  6379    │ │  9000/9001   │
                            └──────────┘ └──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
           ┌──────────────┐ ┌──────────┐ ┌──────────────┐
           │ Celery       │ │ Celery   │ │  AI          │
           │ Worker       │ │ Beat     │ │  Orchestrator│
           │ (async jobs) │ │(scheduler│ │  FastAPI /   │
           └──────────────┘ └──────────┘ │  LangGraph   │
                                         │  Port: 8003  │
                                         └──────┬───────┘
                                                │
                              ┌─────────────────┼─────────────────┐
                              ▼                 ▼                 ▼
                    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
                    │  21 AI       │  │  12 MCP      │  │  Langfuse    │
                    │  Agents      │  │  Tool        │  │  Observ.     │
                    │  (LangGraph) │  │  Servers     │  │  Port: 8004  │
                    └──────────────┘  └──────────────┘  └──────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  Anthropic   │ │  OpenAI      │ │  SAM.gov     │
     │  Claude      │ │  (optional)  │ │  API         │
     │  (primary)   │ │              │ │              │
     └──────────────┘ └──────────────┘ └──────────────┘
```

### Key Architectural Decisions

- **Polyglot services**: Django handles business logic and data persistence; FastAPI handles high-throughput AI orchestration with async/await natively; Node.js handles persistent WebSocket connections at scale.
- **Agent isolation**: Each AI agent runs in its own LangGraph graph node with a defined input/output schema, enabling independent testing, replacement, and observability.
- **MCP for tool access**: Model Context Protocol servers provide agents with a standardized, auditable interface to external systems and internal APIs, preventing direct LLM-to-database access.
- **pgvector for semantic search**: All knowledge vault documents, past performance records, and proposal content are chunked, embedded, and stored in PostgreSQL with pgvector, enabling fast similarity search without a separate vector database.
- **Celery for durability**: Long-running AI workflows (full proposal generation can take 10-30 minutes) are managed as Celery tasks with retry logic, progress tracking, and result persistence.

---

## 4. Tech Stack

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
| **Primary LLM** | Anthropic Claude | claude-sonnet-4-6 / claude-opus-4-6 | Core reasoning and generation |
| **Tool Protocol** | MCP | 1.0 | Standardized agent tool access |
| **Realtime Server** | Node.js + Express + Socket.IO | 4.7 | WebSocket server |
| **Reverse Proxy** | NGINX | latest | Load balancing, SSL termination, routing |
| **Observability** | Langfuse | latest | LLM tracing, cost tracking |
| **Containerization** | Docker Compose | v2 | Local and production orchestration |

---

## 5. Prerequisites

Ensure the following are installed on your system before proceeding:

| Requirement | Minimum Version | Notes |
|---|---|---|
| Docker | 24.x | Required for all containerized services |
| Docker Compose | v2.20+ | Included with Docker Desktop; use `docker compose` (v2) |
| Git | 2.x | Version control |
| Node.js | 20.x LTS | Required only for local (non-Docker) frontend development |
| Python | 3.12 | Required only for local (non-Docker) backend development |
| Make | any | Optional; used for convenience targets in Makefile |

### External API Keys Required

| Service | Environment Variable | Where to Obtain |
|---|---|---|
| Anthropic Claude | `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| SAM.gov | `SAMGOV_API_KEY` | https://sam.gov/profile/details (free registration) |
| OpenAI (optional) | `OPENAI_API_KEY` | https://platform.openai.com (fallback LLM provider) |
| Langfuse (optional) | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | https://cloud.langfuse.com or self-hosted (included in compose) |

---

## 6. Quick Start

The fastest path to a running local environment using Docker Compose.

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/ai-deal-manager.git
cd ai-deal-manager
```

### Step 2: Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and at minimum set your `ANTHROPIC_API_KEY` and `SAMGOV_API_KEY`. All other defaults are pre-configured for local development.

### Step 3: Start All Services

```bash
docker compose up --build
```

On first run, Docker will build all images and initialize the database. This may take 5-10 minutes depending on your internet connection and hardware.

### Step 4: Initialize the Database

In a separate terminal (while services are running):

```bash
docker compose exec django-api python manage.py migrate
docker compose exec django-api python manage.py createsuperuser \
    --username admin \
    --email admin@example.com \
    --no-input
# Then set password:
docker compose exec django-api python manage.py shell -c \
    "from django.contrib.auth import get_user_model; \
     User = get_user_model(); \
     u = User.objects.get(username='admin'); \
     u.set_password('Admin1234!'); \
     u.save()"
```

Or use the pre-configured fixture:

```bash
docker compose exec django-api python manage.py loaddata fixtures/dev_seed.json
```

### Step 5: Access the Application

| Service | URL | Credentials |
|---|---|---|
| Frontend | http://localhost:3027 | admin / Admin1234! |
| Django Admin | http://localhost:3027/admin | admin / Admin1234! |
| Django API | http://localhost:3027/api/v1/ | — |
| AI Orchestrator | http://localhost:8003/docs | — |
| Langfuse | http://localhost:8004 | See Langfuse setup |
| MinIO Console | http://localhost:9001 | minioadmin / changeme |

### Stopping Services

```bash
docker compose down          # Stop and remove containers
docker compose down -v       # Also remove volumes (wipes database)
```

---

## 7. Environment Setup

Copy `.env.example` to `.env` and configure the following variables:

```bash
cp .env.example .env
```

### Core Django Settings

```env
# Django
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=postgresql://dealmanager:changeme@postgres:5432/dealmanager

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
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
# Primary LLM Provider
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6

# Optional: OpenAI fallback
OPENAI_API_KEY=sk-your-openai-key-here

# SAM.gov Integration
SAMGOV_API_KEY=your-samgov-api-key-here
```

### Observability (Langfuse)

```env
# Self-hosted Langfuse (included in docker compose)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://langfuse:3000
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | — | Django cryptographic signing key |
| `DEBUG` | No | `False` | Enable Django debug mode |
| `ALLOWED_HOSTS` | Yes | — | Comma-separated list of allowed hostnames |
| `DATABASE_URL` | Yes | — | PostgreSQL connection URL |
| `REDIS_URL` | Yes | — | Redis connection URL |
| `MINIO_ROOT_USER` | Yes | — | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | Yes | — | MinIO admin password |
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic Claude API key |
| `OPENAI_API_KEY` | No | — | OpenAI API key (fallback provider) |
| `LLM_PROVIDER` | No | `anthropic` | Active LLM provider (`anthropic` or `openai`) |
| `LLM_MODEL` | No | `claude-sonnet-4-6` | Model identifier for the active provider |
| `SAMGOV_API_KEY` | Yes | — | SAM.gov public API key |
| `LANGFUSE_PUBLIC_KEY` | No | — | Langfuse project public key |
| `LANGFUSE_SECRET_KEY` | No | — | Langfuse project secret key |
| `LANGFUSE_HOST` | No | `http://langfuse:3000` | Langfuse server URL |
| `JWT_SECRET_KEY` | Yes | — | JWT token signing secret |

---

## 8. Services & Ports

### Docker Compose Services

| Service | Image / Build | Port (Internal) | Port (Host) | Description |
|---|---|---|---|---|
| `nginx` | nginx:alpine | 80 | 80, 3027 | Reverse proxy and static file serving |
| `postgres` | postgres:16 + pgvector | 5432 | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | 6379 | Cache and Celery message broker |
| `minio` | minio/minio | 9000, 9001 | 9000, 9001 | Object storage (API + console) |
| `django-api` | ./backend | 8001 | 8001 | Django REST API server (Gunicorn) |
| `celery-worker` | ./backend | — | — | Celery async task workers |
| `celery-beat` | ./backend | — | — | Celery periodic task scheduler |
| `frontend` | ./frontend | 3000 | — | Next.js development/production server |
| `node-realtime` | ./realtime | 8002 | 8002 | Node.js Socket.IO real-time server |
| `ai-orchestrator` | ./ai-orchestrator | 8003 | 8003 | FastAPI LangGraph agent orchestrator |
| `langfuse` | langfuse/langfuse | 3000 | 8004 | LLM observability and tracing |

### Network Routing (via NGINX)

| Path Prefix | Upstream Service | Notes |
|---|---|---|
| `/` | `frontend:3000` | Next.js application |
| `/api/` | `django-api:8001` | REST API endpoints |
| `/admin/` | `django-api:8001` | Django admin interface |
| `/ws/` | `node-realtime:8002` | WebSocket upgrade |
| `/agents/` | `ai-orchestrator:8003` | AI agent API |
| `/static/` | `django-api:8001` | Django static files |
| `/media/` | `minio:9000` | Media file proxy |

---

## 9. Backend Apps

The Django backend is organized into 18 modular applications, each owning a distinct domain of the platform:

| App | Description |
|---|---|
| `accounts` | Custom user model, authentication (JWT + session), user profiles, organization management, and RBAC role assignments. |
| `core` | Shared base models, mixins, utilities, middleware, exception handling, and platform-wide configuration. |
| `opportunities` | SAM.gov opportunity ingestion, scoring, classification, pipeline stage tracking, and Go/No-Go decision workflows. |
| `deals` | Deal workspace management, deal metadata, stage transitions, team assignments, and deal-level activity feeds. |
| `rfp` | RFP/solicitation document parsing, requirements extraction, compliance matrix generation, and question-and-answer tracking. |
| `proposals` | Proposal section management, outline generation, content authoring, version control, review cycles, and submission packaging. |
| `pricing` | Labor category management, rate card storage, pricing model configuration, cost volume generation, and price-to-win analysis. |
| `contracts` | Contract document management, clause library, modification tracking, deliverable schedules, and obligation monitoring. |
| `strategy` | Capture strategy documents, win theme management, discriminator tracking, and competitive positioning records. |
| `marketing` | Marketing collateral management, capability statements, past performance summaries, and brand asset library. |
| `research` | Market research findings, competitor profiles, industry analysis reports, and source tagging with evidence links. |
| `legal` | Legal document repository, review request workflow, risk flagging, redline management, and approval tracking. |
| `teaming` | Partner identification, teaming agreement lifecycle, subcontractor management, and small business tracking. |
| `security_compliance` | CMMC/NIST control tracking, evidence collection, gap analysis, audit log management, and compliance assessment records. |
| `knowledge_vault` | Vector-indexed content library, document chunking and embedding pipeline, semantic search API, and content approval workflows. |
| `communications` | Email integration, notification management, internal messaging, task assignments, and stakeholder communication logs. |
| `policies` | Company policy document management, version control, acknowledgment tracking, and policy-to-requirement mapping. |
| `analytics` | Dashboard metrics, pipeline KPIs, win/loss reporting, agent performance statistics, and custom report generation. |
| `past_performance` | Past contract registry, CPARS record management, narrative library, reference contact management, and relevancy scoring. |

---

## 10. AI Agents

The AI orchestration layer deploys 21 specialized agents, each implemented as a LangGraph graph with defined state schemas, tool access via MCP, and configurable LLM backends.

| # | Agent Name | Primary Responsibilities |
|---|---|---|
| 1 | **Strategy Agent** | Generates and maintains capture plans, win themes, competitive discriminators, and Go/No-Go recommendations based on opportunity analysis and historical win data. |
| 2 | **Opportunity Agent** | Monitors SAM.gov and other sources for new solicitations, scores opportunities against company capabilities and strategic priorities, and routes high-value bids to capture managers. |
| 3 | **RFP Analyst Agent** | Parses solicitation documents, extracts requirements, builds compliance matrices, identifies evaluation criteria, and flags ambiguities requiring customer clarification. |
| 4 | **Proposal Writer Agent** | Drafts proposal sections (technical approach, management, past performance) grounded in the knowledge vault, RFP requirements, and approved win themes. |
| 5 | **Pricing Agent** | Maps labor categories to solicitation requirements, benchmarks against market rates, builds cost models, generates price narratives, and supports price-to-win analysis. |
| 6 | **Legal Agent** | Reviews teaming agreements, NDAs, and contract terms; identifies high-risk clauses; generates redlines; and escalates issues requiring attorney review. |
| 7 | **Contracts Agent** | Manages post-award contract administration tasks including deliverable tracking, modification identification, obligation monitoring, and closeout preparation. |
| 8 | **Research Agent** | Conducts deep web and database research on agencies, incumbents, competitors, and market conditions; synthesizes findings into structured intelligence reports. |
| 9 | **Marketing & Sales Agent** | Drafts capability statements, tailors past performance summaries for specific agencies, generates targeted marketing content, and supports BD outreach campaigns. |
| 10 | **Security & Compliance Agent** | Assesses CMMC, NIST 800-171, FedRAMP, and FAR/DFARS compliance requirements; identifies gaps; generates remediation plans; and tracks evidence collection. |
| 11 | **Teaming Agent** | Identifies potential teaming partners based on capability gaps and set-aside requirements, researches partner past performance and financial health, and drafts teaming agreement outlines. |
| 12 | **Past Performance Agent** | Retrieves and ranks relevant past performance narratives from the knowledge vault, adapts them to the current solicitation's requirements, and ensures relevancy claim accuracy. |
| 13 | **Communication Agent** | Manages stakeholder communications, drafts customer emails and RFI responses, tracks follow-ups, and maintains communication logs linked to deal records. |
| 14 | **Learning Agent** | Analyzes win/loss patterns, agent performance data, and proposal feedback to continuously improve agent configurations, prompt templates, and knowledge vault content. |
| 15 | **QA Agent** | Reviews proposal drafts for compliance with RFP requirements, page limits, formatting rules, and internal quality standards; generates structured review feedback. |
| 16 | **Deal Pipeline Agent** | Monitors deal health across the pipeline, identifies at-risk opportunities, generates stage-progression recommendations, and alerts capture managers to action items. |
| 17 | **Solution Architect Agent** | Develops technical solution concepts, architecture diagrams, staffing plans, and technology stack recommendations aligned to the customer's technical requirements. |
| 18 | **Compliance Agent** | Performs final end-to-end compliance shredding of completed proposals against the solicitation's requirements checklist before submission. |
| 19 | **Competitive Intelligence Agent** | Builds and maintains competitor profiles using FPDS-NG data, news monitoring, and web research; identifies incumbent relationships and competitive pricing intelligence. |
| 20 | **Knowledge Vault Agent** | Manages the knowledge vault lifecycle: ingesting new documents, triggering re-embedding on updates, resolving content conflicts, and recommending content for archival. |
| 21 | **Contracts (Post-Award) Agent** | Monitors active contracts for deliverable deadlines, modification triggers, and performance reporting requirements; drafts status reports and correspondence. |

### Agent Configuration

Agents are configured via the AI orchestrator's `agents/config.yaml` file. Each agent supports:

- **LLM Model Override**: Swap between `claude-sonnet-4-6` (faster, lower cost) and `claude-opus-4-6` (highest capability) per agent.
- **Temperature and Max Tokens**: Fine-tuned per agent role (e.g., creative writing vs. compliance checking).
- **Tool Access**: Declarative list of MCP tool servers the agent is permitted to invoke.
- **Human-in-the-Loop Thresholds**: Confidence score below which the agent pauses and requests human review.
- **Memory Configuration**: Short-term (in-graph state), long-term (knowledge vault retrieval), and episodic (per-deal context window) memory settings.

---

## 11. MCP Tool Servers

12 Model Context Protocol (MCP) tool servers provide agents with structured, auditable access to external APIs, databases, and internal services.

| # | Tool Server | Key Tools Exposed | Description |
|---|---|---|---|
| 1 | **samgov_tools** | `search_opportunities`, `get_opportunity_detail`, `get_award_data`, `search_entities` | Direct integration with the SAM.gov REST API for opportunity search, award history retrieval, and entity (vendor) lookups. |
| 2 | **document_tools** | `parse_pdf`, `extract_text`, `convert_docx`, `chunk_document`, `generate_pdf`, `merge_documents` | Document ingestion, parsing, conversion, and generation utilities supporting PDF, DOCX, and HTML formats. |
| 3 | **email_tools** | `send_email`, `read_inbox`, `search_emails`, `create_draft`, `schedule_email` | Email integration for reading agency communications, sending correspondence, and managing BD outreach campaigns. |
| 4 | **pricing_tools** | `get_gsa_rates`, `search_fpds_awards`, `calculate_labor_mix`, `generate_cost_volume`, `benchmark_rates` | Access to GSA schedule labor rates, FPDS-NG historical award data, and pricing model calculation utilities. |
| 5 | **legal_tools** | `analyze_contract_clause`, `identify_risk_clauses`, `generate_redline`, `compare_documents`, `lookup_far_clause` | Contract analysis, FAR/DFARS clause library lookup, risk identification, and automated redline generation. |
| 6 | **market_rate_tools** | `get_bls_wage_data`, `search_salary_surveys`, `get_geographic_differentials`, `analyze_labor_market` | Bureau of Labor Statistics data, commercial salary survey integration, and geographic compensation differential analysis. |
| 7 | **qa_tracking_tools** | `create_review_item`, `get_review_checklist`, `update_review_status`, `generate_qa_report`, `check_page_count` | Proposal quality assurance tracking, compliance checklist management, and review cycle coordination. |
| 8 | **image_search_tools** | `search_stock_images`, `find_diagrams`, `search_knowledge_vault_images`, `generate_image_prompt` | Stock image search, internal graphic library search, and image prompt generation for diagram creation requests. |
| 9 | **security_compliance_tools** | `assess_cmmc_control`, `check_nist_control`, `get_far_requirement`, `search_compliance_db`, `generate_ssp_section` | CMMC/NIST control assessment, FAR compliance requirement lookup, and System Security Plan section generation. |
| 10 | **knowledge_vault_tools** | `semantic_search`, `get_document`, `add_document`, `update_embedding`, `find_similar_content`, `get_past_performance` | Semantic search over the embedded knowledge vault, document CRUD, and past performance narrative retrieval. |
| 11 | **competitive_intel_tools** | `search_competitor_awards`, `get_company_profile`, `analyze_win_patterns`, `research_incumbent`, `track_recompete` | Competitor award history from FPDS-NG, company profile research, win pattern analysis, and recompete opportunity tracking. |
| 12 | **diagram_tools** | `generate_org_chart`, `create_architecture_diagram`, `build_process_flow`, `create_gantt_chart`, `render_mermaid` | Automated diagram generation for organization charts, technical architecture, process flows, and project schedules. |

---

## 12. RBAC Roles

Access to all API endpoints and UI surfaces is governed by role-based access control. Users are assigned one or more roles within an organization context.

| Role | Description | Typical Users |
|---|---|---|
| `admin` | Full platform administration access. Can manage users, roles, system configuration, and all data. | IT administrators, platform owners |
| `executive` | Read access to all deals and analytics dashboards. Can approve Go/No-Go decisions and strategy documents. | VP, C-suite, Business Development leadership |
| `capture_manager` | Full lifecycle management of assigned deals. Can configure agents, approve proposals, and manage teaming. | Capture managers, BD directors |
| `proposal_manager` | Manages proposal development workflows. Can assign writers, reviewers, and kick off proposal-specific agents. | Proposal managers, color review coordinators |
| `pricing_manager` | Full access to pricing models, rate cards, cost volumes, and competitive pricing analysis. | Pricing directors, cost analysts |
| `writer` | Can author and edit proposal content within assigned deals. Read access to knowledge vault and past performance. | Proposal writers, technical authors |
| `reviewer` | Can review and comment on proposal sections. Read-only access to deal data. No editing rights. | Color reviewers, subject matter experts |
| `contracts_manager` | Manages post-award contract administration, modifications, and deliverable tracking. | Contracts administrators, program managers |
| `viewer` | Read-only access to assigned deal data. Cannot edit content or trigger agent workflows. | Subcontractors, consultants, auditors |

### Permission Matrix (Summary)

| Action | admin | executive | capture_manager | proposal_manager | pricing_manager | writer | reviewer | contracts_manager | viewer |
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

## 13. API Documentation

### Django REST API

The Django API follows REST conventions and uses JWT for authentication.

- **Base URL**: `http://localhost:3027/api/v1/`
- **Interactive Docs (Swagger UI)**: `http://localhost:3027/api/v1/docs/`
- **OpenAPI Schema**: `http://localhost:3027/api/v1/schema/`

#### Authentication

```bash
# Obtain JWT token pair
curl -X POST http://localhost:3027/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin1234!"}'

# Response:
# {
#   "access": "eyJ...",
#   "refresh": "eyJ..."
# }

# Use access token in subsequent requests
curl http://localhost:3027/api/v1/opportunities/ \
  -H "Authorization: Bearer eyJ..."
```

#### Key API Endpoints

```
Authentication:
  POST   /api/v1/auth/token/                    Obtain JWT token pair
  POST   /api/v1/auth/token/refresh/            Refresh access token
  POST   /api/v1/auth/token/verify/             Verify token validity

Opportunities:
  GET    /api/v1/opportunities/                 List opportunities (paginated)
  POST   /api/v1/opportunities/                 Create opportunity
  GET    /api/v1/opportunities/{id}/            Retrieve opportunity
  PATCH  /api/v1/opportunities/{id}/            Update opportunity
  POST   /api/v1/opportunities/{id}/score/      Trigger AI scoring
  POST   /api/v1/opportunities/sync-samgov/     Sync from SAM.gov

Deals:
  GET    /api/v1/deals/                         List deals
  POST   /api/v1/deals/                         Create deal
  GET    /api/v1/deals/{id}/                    Retrieve deal
  PATCH  /api/v1/deals/{id}/                    Update deal
  POST   /api/v1/deals/{id}/advance-stage/      Advance pipeline stage

Proposals:
  GET    /api/v1/proposals/                     List proposals
  POST   /api/v1/proposals/                     Create proposal
  GET    /api/v1/proposals/{id}/sections/       List proposal sections
  POST   /api/v1/proposals/{id}/generate/       Trigger AI generation
  POST   /api/v1/proposals/{id}/export/         Export to DOCX/PDF

Knowledge Vault:
  GET    /api/v1/knowledge-vault/search/        Semantic search
  POST   /api/v1/knowledge-vault/documents/     Upload document
  GET    /api/v1/knowledge-vault/documents/     List documents

Analytics:
  GET    /api/v1/analytics/pipeline/            Pipeline metrics
  GET    /api/v1/analytics/win-loss/            Win/loss statistics
  GET    /api/v1/analytics/agent-performance/   Agent performance data
```

### AI Orchestrator API

- **Base URL**: `http://localhost:8003/`
- **Interactive Docs**: `http://localhost:8003/docs`

```
Agents:
  POST   /agents/{agent_name}/run               Run agent synchronously
  POST   /agents/{agent_name}/run-async         Run agent as background task
  GET    /agents/{agent_name}/status/{task_id}  Get async task status
  GET    /agents/                               List all available agents

Workflows:
  POST   /workflows/proposal-generation         Full proposal generation workflow
  POST   /workflows/opportunity-analysis        Complete opportunity analysis
  GET    /workflows/{workflow_id}/status        Get workflow status and progress

Health:
  GET    /health                                Service health check
  GET    /metrics                               Prometheus metrics
```

---

## 14. Development Setup (Local)

For development without Docker, you can run each service locally. This requires PostgreSQL 16, Redis, and MinIO to be available (either locally or via `docker compose up postgres redis minio`).

### Backend (Django)

```bash
cd backend

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements/dev.txt

# Configure environment (use localhost ports)
cp ../.env.example .env
# Edit .env: set DATABASE_URL to use localhost:5432 instead of postgres:5432

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:8001
```

In a separate terminal, start Celery:

```bash
cd backend
source .venv/bin/activate

# Start worker
celery -A config worker --loglevel=info

# Start beat scheduler (separate terminal)
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### AI Orchestrator (FastAPI)

```bash
cd ai-orchestrator

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn main:app --reload --host 0.0.0.0 --port 8003
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local to point API URLs to localhost

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Real-Time Server (Node.js)

```bash
cd realtime

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## 15. Running Tests

### Backend Tests (Django + pytest)

```bash
# Run all tests
docker compose exec django-api pytest

# Run with coverage report
docker compose exec django-api pytest --cov=. --cov-report=html

# Run specific app tests
docker compose exec django-api pytest apps/opportunities/tests/

# Run specific test file
docker compose exec django-api pytest apps/proposals/tests/test_generation.py

# Run with verbose output
docker compose exec django-api pytest -v

# Run only fast tests (skip integration tests)
docker compose exec django-api pytest -m "not integration"
```

### AI Orchestrator Tests

```bash
# Run all agent tests
docker compose exec ai-orchestrator pytest

# Run with coverage
docker compose exec ai-orchestrator pytest --cov=. --cov-report=term-missing

# Run specific agent tests
docker compose exec ai-orchestrator pytest tests/agents/test_proposal_writer.py
```

### Frontend Tests

```bash
# Run unit tests (Vitest)
docker compose exec frontend npm run test

# Run tests in watch mode
docker compose exec frontend npm run test:watch

# Run end-to-end tests (Playwright)
docker compose exec frontend npm run test:e2e

# Generate coverage report
docker compose exec frontend npm run test:coverage
```

### Local Testing (without Docker)

```bash
# Backend
cd backend && source .venv/bin/activate
pytest --cov=. --cov-report=term-missing

# Orchestrator
cd ai-orchestrator && source .venv/bin/activate
pytest

# Frontend
cd frontend
npm run test
```

---

## 16. Deployment

### Production Docker Compose

For production deployments, use the production compose override:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Key differences in production mode:
- Django runs under Gunicorn with multiple workers
- Next.js runs the optimized production build
- NGINX enforces HTTPS and applies rate limiting
- Debug mode is disabled
- Environment variables sourced from a secrets manager or `.env.prod`

### Environment Checklist Before Production Deployment

- [ ] `DEBUG=False` in environment
- [ ] Strong, unique `DJANGO_SECRET_KEY` (50+ random characters)
- [ ] Strong, unique `JWT_SECRET_KEY`
- [ ] `ALLOWED_HOSTS` set to your actual domain(s)
- [ ] PostgreSQL running with strong credentials and TLS
- [ ] Redis password set (`REDIS_URL=redis://:password@redis:6379/0`)
- [ ] MinIO credentials changed from defaults
- [ ] SSL/TLS certificates configured in NGINX
- [ ] ANTHROPIC_API_KEY rate limits and spend limits configured
- [ ] Langfuse configured for production data retention policies
- [ ] Celery workers scaled to match expected task volume
- [ ] Database backups configured and tested
- [ ] Log aggregation configured (e.g., Datadog, CloudWatch, Loki)

### Scaling Celery Workers

```bash
# Scale to 4 Celery worker containers
docker compose up -d --scale celery-worker=4

# Or set concurrency within a single worker container
# Edit docker-compose.yml celery-worker command:
# celery -A config worker --concurrency=8 --loglevel=info
```

### Database Migrations in Production

Always run migrations before restarting the Django API in production:

```bash
docker compose exec django-api python manage.py migrate --no-input
docker compose exec django-api python manage.py collectstatic --no-input
```

---

## 17. Project Structure

```
ai-deal-manager/
├── backend/                        # Django REST API
│   ├── apps/
│   │   ├── accounts/               # Users, auth, RBAC
│   │   ├── core/                   # Shared base models and utilities
│   │   ├── opportunities/          # SAM.gov opportunity management
│   │   ├── deals/                  # Deal workspace management
│   │   ├── rfp/                    # RFP parsing and analysis
│   │   ├── proposals/              # Proposal authoring and management
│   │   ├── pricing/                # Pricing models and rate cards
│   │   ├── contracts/              # Contract management
│   │   ├── strategy/               # Capture strategy
│   │   ├── marketing/              # Marketing collateral
│   │   ├── research/               # Market research
│   │   ├── legal/                  # Legal review workflows
│   │   ├── teaming/                # Partner management
│   │   ├── security_compliance/    # CMMC/NIST compliance
│   │   ├── knowledge_vault/        # Vector-indexed content library
│   │   ├── communications/         # Email and notifications
│   │   ├── policies/               # Company policies
│   │   ├── analytics/              # Dashboards and reporting
│   │   └── past_performance/       # Past contract performance
│   ├── config/                     # Django settings, URLs, Celery
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── fixtures/                   # Dev seed data
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── dev.txt
│   │   └── prod.txt
│   ├── Dockerfile
│   └── manage.py
│
├── frontend/                       # Next.js 14 application
│   ├── src/
│   │   ├── app/                    # Next.js App Router pages
│   │   │   ├── (auth)/             # Login, register
│   │   │   ├── dashboard/          # Analytics dashboard
│   │   │   ├── opportunities/      # Opportunity management
│   │   │   ├── deals/              # Deal workspaces
│   │   │   ├── proposals/          # Proposal editor
│   │   │   ├── pricing/            # Pricing tools
│   │   │   ├── contracts/          # Contract management
│   │   │   ├── knowledge-vault/    # Content library
│   │   │   └── settings/           # Platform settings
│   │   ├── components/             # Reusable UI components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── lib/                    # API clients, utilities
│   │   ├── store/                  # Zustand global state
│   │   └── types/                  # TypeScript type definitions
│   ├── public/                     # Static assets
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── ai-orchestrator/                # FastAPI + LangGraph
│   ├── agents/                     # Individual agent implementations
│   │   ├── strategy_agent.py
│   │   ├── opportunity_agent.py
│   │   ├── rfp_analyst_agent.py
│   │   ├── proposal_writer_agent.py
│   │   ├── pricing_agent.py
│   │   ├── legal_agent.py
│   │   ├── contracts_agent.py
│   │   ├── research_agent.py
│   │   ├── marketing_agent.py
│   │   ├── security_compliance_agent.py
│   │   ├── teaming_agent.py
│   │   ├── past_performance_agent.py
│   │   ├── communication_agent.py
│   │   ├── learning_agent.py
│   │   ├── qa_agent.py
│   │   ├── deal_pipeline_agent.py
│   │   ├── solution_architect_agent.py
│   │   ├── compliance_agent.py
│   │   ├── competitive_intel_agent.py
│   │   ├── knowledge_vault_agent.py
│   │   └── contracts_post_award_agent.py
│   ├── mcp_servers/                # MCP tool server implementations
│   │   ├── samgov_tools/
│   │   ├── document_tools/
│   │   ├── email_tools/
│   │   ├── pricing_tools/
│   │   ├── legal_tools/
│   │   ├── market_rate_tools/
│   │   ├── qa_tracking_tools/
│   │   ├── image_search_tools/
│   │   ├── security_compliance_tools/
│   │   ├── knowledge_vault_tools/
│   │   ├── competitive_intel_tools/
│   │   └── diagram_tools/
│   ├── workflows/                  # Multi-agent workflow graphs
│   ├── config/                     # Agent and model configuration
│   ├── routers/                    # FastAPI route handlers
│   ├── schemas/                    # Pydantic request/response models
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── realtime/                       # Node.js Socket.IO server
│   ├── src/
│   │   ├── handlers/               # Socket event handlers
│   │   ├── middleware/             # Auth, rate limiting
│   │   └── rooms/                  # Room management (per-deal)
│   ├── Dockerfile
│   └── package.json
│
├── nginx/                          # NGINX configuration
│   ├── nginx.conf
│   ├── conf.d/
│   │   ├── default.conf            # Production config
│   │   └── dev.conf                # Development config
│   └── ssl/                        # SSL certificates (gitignored)
│
├── docker-compose.yml              # Base compose configuration
├── docker-compose.override.yml     # Development overrides
├── docker-compose.prod.yml         # Production overrides
├── .env.example                    # Environment variable template
├── Makefile                        # Convenience targets
└── README.md                       # This file
```

---

## 18. Contributing

We welcome contributions from the team and approved collaborators. Please follow these guidelines:

### Branch Strategy

```
main          Production-ready code. Protected branch.
develop       Integration branch. All features merge here first.
feature/*     New features (e.g., feature/pricing-scenario-modeling)
fix/*         Bug fixes (e.g., fix/samgov-pagination-error)
agent/*       AI agent development (e.g., agent/qa-agent-v2)
```

### Development Workflow

1. Create a branch from `develop`:
   ```bash
   git checkout develop && git pull
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards below.

3. Write or update tests for all changed functionality.

4. Ensure all tests pass:
   ```bash
   docker compose exec django-api pytest
   docker compose exec frontend npm run test
   ```

5. Ensure code quality checks pass:
   ```bash
   # Backend
   docker compose exec django-api ruff check .
   docker compose exec django-api mypy .

   # Frontend
   docker compose exec frontend npm run lint
   docker compose exec frontend npm run type-check
   ```

6. Submit a pull request to `develop` with a clear description of changes.

### Coding Standards

**Python / Django:**
- Follow PEP 8; enforced by `ruff`
- Type hints required on all function signatures
- Docstrings required on all public classes and methods (Google style)
- Tests required for all new business logic (minimum 80% coverage on new code)
- Use Django ORM; raw SQL only when strictly necessary and must include a comment explaining why

**TypeScript / React:**
- Strict TypeScript mode; no `any` types without justification
- Functional components with hooks; no class components
- Components scoped to single responsibility
- Props interfaces defined with JSDoc comments
- Tests required for all non-trivial components and hooks

**AI Agents / LangGraph:**
- Each agent must have a clearly defined input and output Pydantic schema
- Tool calls must be logged with the MCP audit layer
- Agents must implement human-in-the-loop checkpoints for high-stakes decisions
- Prompt templates stored in `prompts/` directory (never hardcoded inline)
- New agents require a corresponding integration test with mock tool servers

### Commit Message Format

```
type(scope): short description

Longer description if needed.

Refs: #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `agent`

Examples:
```
feat(proposals): add parallel section generation workflow
fix(pricing): correct fringe rate calculation for SCA contracts
agent(qa): implement compliance shredding with RFP matrix validation
docs(readme): update environment variable reference table
```

---

## 19. License

This software is proprietary and confidential. All rights reserved.

Unauthorized copying, distribution, modification, or use of this software, in whole or in part, without the express written permission of the copyright holder is strictly prohibited.

For licensing inquiries, contact: legal@your-organization.com

---

*AI Deal Manager — Built for government contractors who win.*
