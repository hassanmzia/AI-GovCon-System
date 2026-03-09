# AI Deal Manager — Product Overview

**Version:** 2.0
**Last Updated:** March 2026
**Audience:** Stakeholders, Executives, Sales, Business Development

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem](#2-the-problem)
3. [The Solution](#3-the-solution)
4. [Platform Capabilities](#4-platform-capabilities)
5. [AI Agent Network](#5-ai-agent-network)
6. [Deal Lifecycle Management](#6-deal-lifecycle-management)
7. [Key Modules](#7-key-modules)
8. [Technology Foundation](#8-technology-foundation)
9. [Security & Compliance](#9-security--compliance)
10. [Roles & Access Control](#10-roles--access-control)
11. [Integration Ecosystem](#11-integration-ecosystem)
12. [Deployment Options](#12-deployment-options)
13. [Competitive Differentiators](#13-competitive-differentiators)
14. [Product Roadmap Highlights](#14-product-roadmap-highlights)

---

## 1. Executive Summary

**AI Deal Manager** is an enterprise-grade platform that transforms government contracting through autonomous AI orchestration. It deploys **21 specialized AI agents** and **12 tool servers** across the full capture-to-close lifecycle, reducing proposal development time, improving win rates, and ensuring compliance at every stage.

### Key Metrics at a Glance

| Metric | Value |
|---|---|
| AI Agents | 21 specialized agents |
| MCP Tool Servers | 12 integrated tool servers |
| Backend Modules | 18 Django applications |
| Pipeline Stages | 12 active + 3 closed |
| RBAC Roles | 9 granular roles |
| External Integrations | SAM.gov, GSA, FPDS-NG, BLS |
| LLM Provider | Anthropic Claude (Sonnet 4.6 / Opus 4.6) |
| Search Technology | pgvector semantic search |
| Real-Time Collaboration | Socket.IO WebSocket |
| Observability | Langfuse LLM tracing |

---

## 2. The Problem

Government contracting firms face compounding challenges:

### Opportunity Overload
- Thousands of solicitations posted daily on SAM.gov
- Manual screening misses high-probability opportunities
- Inconsistent bid/no-bid decisions lead to wasted pursuit costs

### Proposal Bottlenecks
- Proposal writing consumes 40-60% of BD budget
- Teams start from scratch despite existing boilerplate and past performance
- Compliance checking is manual, error-prone, and last-minute

### Knowledge Silos
- Past performance narratives scattered across file shares
- Institutional knowledge walks out the door with employee turnover
- No way to semantically search across decades of proposal content

### Pricing Complexity
- Labor rate benchmarking requires manual research across multiple databases
- Price-to-win analysis relies on intuition rather than data
- Cost volume errors discovered too late in the review cycle

### Compliance Risk
- FAR/DFARS requirements change frequently
- CMMC/NIST 800-171 compliance tracking is spreadsheet-based
- Legal review of contract terms is a bottleneck

---

## 3. The Solution

AI Deal Manager addresses each challenge with purpose-built AI automation:

```
┌──────────────────────────────────────────────────────────────────┐
│                    AI DEAL MANAGER PLATFORM                      │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  DISCOVER      │  │  PLAN          │  │  WRITE         │    │
│  │                │  │                │  │                │    │
│  │  SAM.gov auto- │  │  AI-generated  │  │  Parallel AI   │    │
│  │  scan + AI     │  │  capture plans │  │  section       │    │
│  │  opportunity   │  │  and win       │  │  drafting with │    │
│  │  scoring       │  │  themes        │  │  knowledge     │    │
│  │                │  │                │  │  vault context │    │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘    │
│           │                   │                    │            │
│           ▼                   ▼                    ▼            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  PRICE         │  │  REVIEW        │  │  SUBMIT        │    │
│  │                │  │                │  │                │    │
│  │  Market-rate   │  │  AI compliance │  │  Automated     │    │
│  │  benchmarking  │  │  shredding +   │  │  formatting,   │    │
│  │  + price-to-   │  │  quality       │  │  page count,   │    │
│  │  win modeling  │  │  assurance     │  │  and packaging │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
│  ┌──────────────────── CROSS-CUTTING ─────────────────────┐    │
│  │  Knowledge Vault  •  Past Performance  •  Compliance     │    │
│  │  Real-Time Collab •  Analytics         •  Audit Trail    │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Platform Capabilities

### 4.1 Intelligent Opportunity Discovery

- **Automated SAM.gov monitoring** — Continuous polling of federal solicitations
- **AI-powered scoring** — Each opportunity scored 0-100 against your company profile
- **Smart recommendations** — Bid / No-Bid / Evaluate with reasoning
- **Factor analysis** — NAICS match, past performance alignment, set-aside eligibility, keyword relevance
- **Learning system** — Scoring improves with each win/loss/bid decision

### 4.2 Autonomous Proposal Factory

- **Multi-agent collaboration** — RFP Analyst, Strategy, Proposal Writer, QA, and Compliance agents work in sequence
- **Knowledge-grounded drafting** — Every section references your knowledge vault, past performance, and approved win themes
- **Compliance-first** — Auto-generated compliance matrix tracks every requirement
- **Parallel processing** — Multiple sections drafted simultaneously
- **Human-in-the-loop** — Low-confidence outputs routed to human reviewers

### 4.3 Intelligent Pricing Engine

- **GSA schedule integration** — Real-time access to published labor rates
- **FPDS-NG analysis** — Historical award data for competitive benchmarking
- **BLS wage data** — Bureau of Labor Statistics integration for market validation
- **Scenario modeling** — Side-by-side comparison of multiple pricing strategies
- **Price-to-win** — AI-recommended pricing range with probability curves

### 4.4 Legal & Contract Intelligence

- **Automated clause analysis** — AI identifies high-risk contract terms
- **FAR/DFARS lookup** — Instant clause reference and compliance checking
- **Redline generation** — Automated markup of counterparty contract changes
- **Escalation workflows** — High-risk items routed to legal counsel

### 4.5 Security & Compliance Automation

- **CMMC assessment** — Control-by-control evaluation against CMMC levels
- **NIST 800-171** — Automated gap analysis with remediation tasks
- **Evidence collection** — Structured evidence tracking per control
- **SSP generation** — System Security Plan section drafting

### 4.6 Competitive Intelligence

- **Competitor profiling** — FPDS-NG award history, win pattern analysis
- **Incumbent tracking** — Identify current contract holders for recompetes
- **Market research** — Web and database research synthesized into reports

### 4.7 Knowledge Management

- **Vector-indexed vault** — All institutional knowledge embedded and semantically searchable
- **Automatic ingestion** — Upload documents; system chunks, embeds, and indexes automatically
- **Cross-reference** — AI agents query the vault when drafting proposals, narratives, and strategies
- **Living knowledge** — Content continuously updated with new wins, lessons learned, and capabilities

### 4.8 Real-Time Collaboration

- **Live editing** — Multiple users editing proposals simultaneously
- **Agent streaming** — See AI outputs appear in real-time
- **Presence awareness** — Know who's online and viewing the same deal
- **Push notifications** — Instant alerts for stage changes, approvals, and deadlines

---

## 5. AI Agent Network

### Agent Architecture

Each agent is built on **LangGraph**, a stateful multi-agent orchestration framework. Agents have:

- **Defined I/O schemas** — Pydantic models for type-safe input/output
- **Tool access via MCP** — Model Context Protocol for structured, auditable external access
- **Configurable LLM backend** — Switch between Claude Sonnet (fast) and Opus (capable)
- **Human-in-the-loop** — Confidence thresholds for escalation to human reviewers
- **Full observability** — Every LLM call, tool invocation, and decision traced in Langfuse

### The 21 Agents

```
┌──────────────────────────────────────────────────────────────────┐
│                    AI AGENT NETWORK (21 AGENTS)                  │
│                                                                  │
│  ┌──────────────── OPPORTUNITY & STRATEGY ────────────────┐     │
│  │                                                         │     │
│  │  Opportunity Agent     → Score & route solicitations    │     │
│  │  Strategy Agent        → Capture plans & win themes     │     │
│  │  Competitive Intel     → Competitor profiles & analysis │     │
│  │  Research Agent        → Market & agency intelligence   │     │
│  │  Deal Pipeline Agent   → Health monitoring & alerts     │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────── PROPOSAL & CONTENT ────────────────────┐     │
│  │                                                         │     │
│  │  RFP Analyst Agent     → Parse RFP, build comp matrix  │     │
│  │  Proposal Writer Agent → Draft proposal sections       │     │
│  │  Past Performance Agent→ Retrieve & adapt PP narratives│     │
│  │  Solution Architect    → Technical solutions & diagrams│     │
│  │  Marketing Agent       → Capability statements & BD    │     │
│  │  Communication Agent   → Emails, RFI responses         │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────── PRICING & CONTRACTS ───────────────────┐     │
│  │                                                         │     │
│  │  Pricing Agent         → Cost models & win pricing     │     │
│  │  Legal Agent           → Contract review & risk flags  │     │
│  │  Contracts Agent       → Post-award administration     │     │
│  │  Contracts (Post-Award)→ Deliverable monitoring        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────── QUALITY & COMPLIANCE ──────────────────┐     │
│  │                                                         │     │
│  │  QA Agent              → Quality review & formatting   │     │
│  │  Compliance Agent      → Final compliance shredding    │     │
│  │  Security Agent        → CMMC/NIST assessment          │     │
│  │  Teaming Agent         → Partner identification        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────── PLATFORM INTELLIGENCE ─────────────────┐     │
│  │                                                         │     │
│  │  Learning Agent        → Win/loss analysis & tuning    │     │
│  │  Knowledge Vault Agent → Content lifecycle management  │     │
│  └─────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Deal Lifecycle Management

### 12-Stage Active Pipeline + 3 Closed States

```
DISCOVERY           QUALIFICATION         DEVELOPMENT          EXECUTION
─────────           ─────────────         ───────────          ─────────

┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ INTAKE │→ │QUALIFY │→ │BID/    │→ │CAPTURE │→ │PROPOSAL│→ │RED     │
│        │  │        │  │NO-BID  │  │PLAN    │  │DEV     │  │TEAM    │
└────────┘  └────────┘  └────┬───┘  └────────┘  └────────┘  └────────┘
                             │                                    │
                        ┌────▼───┐                                │
                        │NO BID  │                                │
                        │(closed)│                                │
                        └────────┘                                │
                                                                  │
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
│DELIVERY│← │CONTRACT│← │AWARD   │← │POST    │← │SUBMIT- │← ┌──┴─────┐
│        │  │SETUP   │  │PENDING │  │SUBMIT  │  │TED     │  │FINAL   │
└───┬────┘  └────────┘  └───┬────┘  └────────┘  └────────┘  │REVIEW  │
    │                       │                                └────────┘
    ▼                       ▼
┌────────┐           ┌────────┐
│CLOSED  │           │CLOSED  │
│WON     │           │LOST    │
└────────┘           └────────┘
```

**Every stage transition** captures:
- Who moved it
- When it was moved
- Why it was moved (mandatory reason)
- Supporting documents (optional)

This creates a complete audit trail and feeds the Learning Agent for continuous improvement.

---

## 7. Key Modules

### Module Map

```
┌──────────────────────────────────────────────────────────────────┐
│                    AI DEAL MANAGER MODULES                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    DASHBOARD                             │    │
│  │  KPIs • Pipeline Chart • Activity Feed • Deadlines      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Opportuni-│ │  Deals   │ │   RFP    │ │ Proposals│          │
│  │ties      │ │ Pipeline │ │ Analysis │ │ Factory  │          │
│  │          │ │          │ │          │ │          │          │
│  │ SAM.gov  │ │ Kanban   │ │ Parse    │ │ AI Draft │          │
│  │ Scoring  │ │ 12 Stage │ │ Complnce │ │ Review   │          │
│  │ Filters  │ │ Tracking │ │ Matrix   │ │ Export   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Pricing  │ │Contracts │ │ Strategy │ │ Analytics│          │
│  │          │ │          │ │          │ │          │          │
│  │ Rate Card│ │ Template │ │ Win Theme│ │ Win Rate │          │
│  │ Scenario │ │ Clause   │ │ Capture  │ │ Pipeline │          │
│  │ Win Price│ │ Redline  │ │ Compete  │ │ Deadline │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Knowledge │ │ Past     │ │ Teaming  │ │ Legal    │          │
│  │ Vault    │ │ Perform  │ │          │ │          │          │
│  │          │ │          │ │ Partners │ │ Risk     │          │
│  │ Semantic │ │ Semantic │ │ Agree-   │ │ Review   │          │
│  │ Search   │ │ Search   │ │ ments    │ │ Workflow │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Security │ │ Research │ │ Comms    │ │ Policies │          │
│  │          │ │          │ │          │ │          │          │
│  │ CMMC     │ │ Market   │ │ Email    │ │ Policy   │          │
│  │ NIST     │ │ Compet.  │ │ RFI      │ │ Version  │          │
│  │ FedRAMP  │ │ Intel    │ │ Follow-up│ │ Tracking │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ADMIN / SETTINGS                       │    │
│  │  User Management • RBAC • Agent Config • System Config  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Technology Foundation

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  PRESENTATION          │  BUSINESS LOGIC      │  AI / AGENTS    │
│  ─────────────         │  ──────────────      │  ──────────     │
│                        │                      │                  │
│  Next.js 14            │  Django 5.1          │  FastAPI         │
│  React 18              │  DRF 3.x             │  LangGraph 0.2   │
│  TypeScript 5.x        │  Celery 5.4          │  LangChain 0.3   │
│  Tailwind CSS 3.x      │  SimpleJWT           │  Anthropic Claude│
│  Zustand 4.x           │  18 Django Apps      │  12 MCP Servers  │
│  Socket.IO Client      │                      │  21 AI Agents    │
│                        │                      │                  │
├────────────────────────┼──────────────────────┼──────────────────┤
│  DATA                  │  INFRASTRUCTURE      │  OBSERVABILITY   │
│  ────                  │  ──────────────      │  ─────────────   │
│                        │                      │                  │
│  PostgreSQL 16         │  Docker Compose      │  Langfuse        │
│  pgvector 0.7          │  NGINX               │  Structured JSON │
│  Redis 7.x             │  Gunicorn            │  Health Checks   │
│  MinIO (S3)            │  Node.js + Socket.IO │  Prometheus      │
└────────────────────────┴──────────────────────┴──────────────────┘
```

### Technology Selection Rationale

| Choice | Why |
|---|---|
| **Django + DRF** | Battle-tested framework for complex business logic, ORM, auth, admin, and 100+ reusable packages |
| **FastAPI** | Native async/await for high-throughput AI orchestration; Pydantic for type-safe schemas |
| **Next.js 14** | Server-side rendering, App Router, and React Server Components for optimal UX |
| **LangGraph** | Stateful, graph-based multi-agent orchestration with built-in checkpointing and human-in-the-loop |
| **pgvector** | Semantic search without operational complexity of a separate vector database |
| **MCP** | Standardized, auditable tool access prevents direct LLM-to-database connections |
| **Celery** | Proven distributed task queue for long-running AI workflows with retry and monitoring |
| **Anthropic Claude** | Leading performance on complex reasoning, instruction following, and long-context tasks |

---

## 9. Security & Compliance

| Domain | Implementation |
|---|---|
| **Data Encryption** | TLS 1.3 in transit; AES-256 at rest (PostgreSQL, MinIO) |
| **Authentication** | JWT with short-lived access tokens (15 min) and refresh rotation (24h) |
| **Authorization** | 9-role RBAC enforced at API and UI level |
| **Input Validation** | DRF serializers + Pydantic schemas; parameterized queries |
| **Audit Trail** | Every deal transition, proposal edit, agent run, and admin action logged |
| **LLM Security** | MCP tool servers prevent direct LLM-to-database access; per-agent tool scoping |
| **Session Protection** | Account lockout after 5 failed attempts; JWT blacklisting on logout |
| **Secret Management** | Environment variables; never in version control; `.env` gitignored |
| **Network Isolation** | Docker internal network; only NGINX exposed externally |
| **Compliance Tracking** | Built-in CMMC, NIST 800-171, FedRAMP, and FAR/DFARS assessment tools |

---

## 10. Roles & Access Control

| Role | Description | Access Scope |
|---|---|---|
| **Admin** | Full platform control | Everything including user management |
| **Executive** | Strategic oversight | All deals (read), analytics, approval authority |
| **Capture Manager** | Deal lifecycle owner | Assigned deals, agent config, proposal approval |
| **Proposal Manager** | Proposal workflow lead | Proposal authoring, writer/reviewer assignment |
| **Pricing Manager** | Pricing authority | Rate cards, cost models, competitive analysis |
| **Writer** | Content creator | Proposal editing within assigned deals |
| **Reviewer** | Quality reviewer | Comment and review access, no editing |
| **Contracts Manager** | Post-award admin | Contract docs, clause library, deliverables |
| **Viewer** | Read-only observer | Assigned deal data only |

---

## 11. Integration Ecosystem

### External Data Sources

| Integration | Data | Protocol |
|---|---|---|
| **SAM.gov** | Federal solicitations, awards, entity data | REST API |
| **FPDS-NG** | Historical federal contract awards | REST API |
| **GSA Schedules** | Published labor category rates | REST API |
| **BLS** | Bureau of Labor Statistics wage data | REST API |

### Internal Integrations

| Integration | Protocol | Purpose |
|---|---|---|
| **Email (SMTP)** | SMTP/IMAP | Stakeholder communications, RFI responses |
| **Document Storage (MinIO)** | S3 API | File upload, versioning, presigned URLs |
| **Real-Time (Socket.IO)** | WebSocket | Live editing, notifications, presence |
| **Observability (Langfuse)** | HTTPS | LLM tracing, cost tracking, quality monitoring |

### MCP Tool Servers (12)

| Server | Tools | External Access |
|---|---|---|
| samgov_tools | Opportunity search, award data, entity lookup | SAM.gov API |
| document_tools | PDF parse, DOCX convert, document generation | Local processing |
| email_tools | Send, read, search, draft emails | SMTP/IMAP |
| pricing_tools | GSA rates, FPDS awards, labor mix calc | GSA, FPDS-NG APIs |
| legal_tools | Clause analysis, risk ID, redline generation | FAR/DFARS database |
| market_rate_tools | BLS wages, salary surveys, geo differentials | BLS API |
| qa_tracking_tools | Review items, checklists, page count checks | Internal DB |
| image_search_tools | Stock images, diagram search | Image APIs |
| security_compliance_tools | CMMC/NIST assessment, SSP generation | Compliance DB |
| knowledge_vault_tools | Semantic search, document CRUD | pgvector |
| competitive_intel_tools | Competitor awards, win patterns | FPDS-NG API |
| diagram_tools | Org charts, architecture diagrams, Gantt | Mermaid rendering |

---

## 12. Deployment Options

### Docker Compose (Standard)

- **Development**: `docker compose up --build`
- **Production**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- **Scaling**: `docker compose up -d --scale celery-worker=N`

### Production Requirements

| Component | Specification |
|---|---|
| CPU | 8+ cores (16 recommended) |
| RAM | 32 GB minimum (64 GB recommended) |
| Storage | 500 GB SSD (for DB, MinIO, and logs) |
| Network | 100 Mbps+ (for LLM API calls) |
| OS | Linux (Ubuntu 22.04 LTS or RHEL 8+) |
| Docker | 24.x with Docker Compose v2 |

---

## 13. Competitive Differentiators

| Differentiator | AI Deal Manager | Traditional GovCon Tools |
|---|---|---|
| **AI Agents** | 21 specialized, autonomous agents | None or basic AI features |
| **Agent Orchestration** | LangGraph stateful graphs | N/A |
| **Semantic Search** | pgvector with 1536-dim embeddings | Keyword search only |
| **Proposal Generation** | Multi-agent parallel drafting | Manual or template-based |
| **Compliance Automation** | Auto-generated compliance matrix | Manual spreadsheets |
| **Pricing Intelligence** | GSA/FPDS/BLS integrated analysis | Manual market research |
| **Real-Time Collaboration** | Socket.IO live editing | File sharing (sequential) |
| **Tool Protocol** | MCP standardized, auditable access | Direct API calls (unaudited) |
| **LLM Provider** | Anthropic Claude (state of the art) | GPT-3.5 or none |
| **Observability** | Langfuse per-call tracing | None |
| **Knowledge Management** | Vector-indexed vault with auto-ingestion | File server / SharePoint |
| **Human-in-the-Loop** | Configurable confidence thresholds | All-or-nothing automation |

---

## 14. Product Roadmap Highlights

### Current Release (v2.0) — March 2026

- 21 AI agents with LangGraph orchestration
- 12 MCP tool servers
- 18 backend modules
- Full proposal generation workflow
- pgvector semantic search
- Real-time collaboration
- Langfuse observability
- 9-role RBAC

### Planned Enhancements

| Feature | Description |
|---|---|
| **Multi-Org Tenancy** | Support multiple organizations on a single platform instance |
| **Custom Agent Builder** | No-code interface for creating custom AI agents |
| **Advanced Analytics** | ML-powered deal scoring and pipeline forecasting |
| **Mobile Native** | iOS and Android native apps for deal monitoring |
| **Contract Analytics** | Post-award performance analytics and predictive alerts |
| **Workflow Automation** | Custom automation rules (if-this-then-that) across modules |
| **External CRM Integration** | Salesforce, HubSpot, and GovWin connectors |
| **Document Generation** | Advanced templating with auto-populated proposal sections |
| **Voice & Chat** | Conversational AI interface for deal queries and actions |

---

*For technical architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md). For complete API reference, see [API_REFERENCE.md](API_REFERENCE.md). For end-user guidance, see [USER_GUIDE.md](USER_GUIDE.md).*

*Built for government contractors who win.*
