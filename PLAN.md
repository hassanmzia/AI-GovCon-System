# AI Deal Manager — Implementation Plan

## Enterprise Autonomous Agentic Deal Management Platform

**For:** AI Consulting Company
**Stack:** Django + PostgreSQL | Node.js + React/TypeScript | LangGraph/LangChain | MCP + A2A | RAG + RL
**Infrastructure:** Docker Compose (multi-host, no port conflicts)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Docker Compose & Infrastructure](#2-docker-compose--infrastructure)
3. [Phase 1 — Foundation & Auth](#3-phase-1--foundation--auth)
4. [Phase 2 — Opportunity Intelligence](#4-phase-2--opportunity-intelligence)
5. [Phase 3 — Deal Pipeline & Workflow](#5-phase-3--deal-pipeline--workflow)
6. [Phase 4 — RFP Workspace & Compliance](#6-phase-4--rfp-workspace--compliance)
6A. [Phase 4A — Company AI Strategy Agent](#6a-phase-4a--company-ai-strategy-agent)
6B. [Phase 4B — Marketing & Sales Expert Agent](#6b-phase-4b--marketing--sales-expert-agent) **(NEW)**
6C. [Phase 4C — Deep Research Agent](#6c-phase-4c--deep-research-agent) **(NEW)**
6D. [Phase 4D — Business Legal Agent](#6d-phase-4d--business-legal-agent) **(NEW)**
6E. [Phase 4E — Teaming & Subcontractor Selection Agent](#6e-phase-4e--teaming--subcontractor-selection-agent) **(NEW)**
6F. [Phase 4F — Security & Compliance Mapping Agent](#6f-phase-4f--security--compliance-mapping-agent) **(NEW)**
7. [Phase 5 — Past Performance Vault](#7-phase-5--past-performance-vault)
8. [Phase 6 — Proposal Authoring Studio](#8-phase-6--proposal-authoring-studio) (includes **Fully Autonomous AI Solutions Architect** + **Multimodal Knowledge Vault**)
9. [Phase 7 — Intelligent Pricing & Staffing Engine](#9-phase-7--intelligent-pricing--staffing-engine) **(MAJOR UPGRADE)**
10. [Phase 8 — Contract Management](#10-phase-8--contract-management)
11. [Phase 9 — AI Agent Orchestration](#11-phase-9--ai-agent-orchestration)
12. [Phase 10 — Learning & Optimization](#12-phase-10--learning--optimization)
13. [Data Model](#13-data-model)
14. [File/Folder Structure](#14-filefolder-structure)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        NGINX Reverse Proxy (:80/:443)               │
├──────────────┬───────────────┬────────────────┬──────────────────────┤
│  React/TS    │  Django API   │  Node.js       │  AI Orchestrator     │
│  Frontend    │  (Core BizAPI)│  (Realtime/WS) │  (LangGraph)         │
│  :3000       │  :8001        │  :8002         │  :8003               │
├──────────────┴───────────────┴────────────────┴──────────────────────┤
│                        Internal Docker Network                       │
├──────────┬──────────┬───────────┬──────────┬─────────┬──────────────┤
│ Postgres │  Redis   │  MinIO    │ pgvector │ Celery  │  Langfuse    │
│  :5432   │  :6379   │  :9000   │ (in PG)  │ Workers │  :8004       │
└──────────┴──────────┴───────────┴──────────┴─────────┴──────────────┘
```

### Key Design Decisions

- **Django** = system of record (auth, RBAC, workflow state machine, audit, all CRUD)
- **Node.js** = real-time collaboration (WebSocket for live proposal editing, notifications)
- **React/TypeScript** = SPA frontend with AI Workbench on every entity
- **LangGraph** = multi-agent orchestration with HITL gates
- **MCP** = tool servers (each integration is a separate MCP server)
- **A2A** = agent-to-agent protocol for inter-agent communication
- **RAG** = pgvector in PostgreSQL for vector search (past performance, proposals, knowledge)
- **Celery + Redis** = async task queue (opportunity scanning, document processing, AI jobs)
- **MinIO** = S3-compatible object storage for attachments & generated documents
- **Langfuse** = LLM observability (prompt traces, cost, evals)

---

## 2. Docker Compose & Infrastructure

### 2.1 Services

| Service | Internal Port | External (via Nginx) | Image/Build |
|---------|--------------|---------------------|-------------|
| `nginx` | 80, 443 | 80, 443 | nginx:alpine |
| `frontend` | 3000 | /app/* → 3000 | Node 20 (build) |
| `django-api` | 8001 | /api/* → 8001 | Python 3.12 |
| `node-realtime` | 8002 | /ws/* → 8002 | Node 20 |
| `ai-orchestrator` | 8003 | /ai/* → 8003 | Python 3.12 |
| `postgres` | 5432 | internal only | postgres:16 + pgvector |
| `redis` | 6379 | internal only | redis:7-alpine |
| `minio` | 9000/9001 | internal only | minio/minio |
| `celery-worker` | — | — | Same as django |
| `celery-beat` | — | — | Same as django |
| `langfuse` | 8004 | /langfuse/* → 8004 | langfuse/langfuse |

### 2.2 Files to Create

```
docker-compose.yml          # All services
docker-compose.override.yml # Dev overrides (volumes, debug)
.env.example                # All env vars template
nginx/nginx.conf            # Reverse proxy config
nginx/ssl/                  # SSL certs (gitignored)
```

### 2.3 Network Strategy

- Single Docker bridge network: `dealmanager-net`
- All inter-service communication via service names (e.g., `postgres:5432`)
- Only nginx exposes ports 80/443 to host
- Dev mode: optionally expose frontend:3000 for HMR

---

## 3. Phase 1 — Foundation & Auth

### 3.1 Django Backend Setup

```
backend/
├── manage.py
├── requirements.txt
├── Dockerfile
├── config/
│   ├── settings/
│   │   ├── base.py          # Common settings
│   │   ├── development.py   # Dev overrides
│   │   └── production.py    # Prod overrides
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/            # Auth, RBAC, MFA, profiles
│   ├── core/                # Shared models, utils, audit
│   ├── opportunities/       # Opportunity intelligence
│   ├── deals/               # Deal pipeline & workflow
│   ├── rfp/                 # RFP workspace & compliance
│   ├── past_performance/    # Past performance vault
│   ├── proposals/           # Proposal authoring
│   ├── pricing/             # Pricing & staffing
│   ├── contracts/           # Contract management
│   ├── communications/      # Email & narrative drafting
│   ├── policies/            # AI policy & goal settings
│   └── analytics/           # Dashboards & reporting
```

### 3.2 Authentication & Authorization

- **Django Auth** activated with session-based auth + JWT tokens for API
- **django-rest-framework** with token auth + session auth
- **django-allauth** for optional SSO (SAML/OIDC) readiness
- **django-otp** + **django-two-factor-auth** for optional TOTP MFA

### 3.3 RBAC Roles

| Role | Description | Key Permissions |
|------|-------------|----------------|
| `admin` | Platform administrator | Full access, user management, system config |
| `executive` | C-suite / leadership | View all, approve major decisions, dashboards |
| `capture_manager` | Opportunity & deal owner | Manage opportunities, deals, bid/no-bid |
| `proposal_manager` | Proposal lifecycle owner | Manage proposals, reviews, submissions |
| `pricing_manager` | Pricing authority | Rate cards, scenarios, pricing approval |
| `writer` | Proposal/content author | Edit proposal sections, past perf narratives |
| `reviewer` | Pink/Red team reviewer | Review & comment, approve/reject sections |
| `contracts_manager` | Contract lifecycle owner | Contract templates, clause library, redlines |
| `viewer` | Read-only stakeholder | View dashboards, pipeline, reports |

### 3.4 User Profile Features

- Profile picture upload (to MinIO)
- Change password (with strength validation)
- Edit profile information (name, title, department, skills)
- MFA enable/disable (per user)
- Activity log (recent actions)
- Notification preferences

### 3.5 Audit System

- **Immutable audit log** table: `who`, `what`, `when`, `entity_type`, `entity_id`, `old_value`, `new_value`, `ip_address`
- **AI audit log**: `agent_name`, `prompt`, `tool_calls`, `retrieved_sources`, `output`, `approval_status`, `cost`, `latency`
- Django signals for automatic change tracking

### 3.6 React Frontend Setup

```
frontend/
├── package.json
├── tsconfig.json
├── Dockerfile
├── src/
│   ├── app/                 # Next.js app router (or CRA routes)
│   ├── components/
│   │   ├── ui/              # Reusable UI (shadcn/ui or MUI)
│   │   ├── layout/          # Shell, sidebar, topbar
│   │   ├── auth/            # Login, MFA, profile
│   │   ├── dashboard/       # Executive dashboards
│   │   ├── opportunities/   # Opportunity cards, scoring
│   │   ├── deals/           # Pipeline board (Kanban)
│   │   ├── rfp/             # RFP workspace
│   │   ├── proposals/       # Proposal editor
│   │   ├── pricing/         # Pricing scenarios
│   │   ├── contracts/       # Contract workspace
│   │   ├── ai-workbench/    # AI chat + actions panel
│   │   └── settings/        # Policy, goals, admin
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client (axios/fetch)
│   ├── store/               # State management (Zustand or Redux)
│   ├── types/               # TypeScript interfaces
│   └── utils/               # Helpers
```

### 3.7 Node.js Realtime Service

```
realtime/
├── package.json
├── tsconfig.json
├── Dockerfile
├── src/
│   ├── server.ts            # Express + Socket.IO
│   ├── handlers/
│   │   ├── notifications.ts # Push notifications
│   │   ├── collaboration.ts # Live proposal editing
│   │   └── ai-stream.ts    # Stream AI responses
│   └── middleware/
│       └── auth.ts          # JWT verification
```

---

## 4. Phase 2 — Opportunity Intelligence

### 4.1 Data Sources & Connectors

| Source | Method | Frequency |
|--------|--------|-----------|
| **SAM.gov** | Official API (api.sam.gov) | Every 4 hours |
| **instantmarkets.com** | API or ToS-compliant scraping | Daily |
| **Oak Ridge National Lab** | Procurement page monitor | Daily |
| **Brookhaven National Lab** | Procurement page monitor | Daily |
| **Kansas City Security Complex** | Procurement page monitor | Daily |
| **Sandia National Lab** | Procurement page monitor | Daily |
| **Oregon National Lab (PNNL?)** | Procurement page monitor | Daily |
| **USASpending/FPDS** | API (historical context) | Weekly |

### 4.2 SAM.gov Integration (Primary)

```python
# apps/opportunities/services/samgov_client.py
class SAMGovClient:
    """
    Official SAM.gov API integration
    - Search opportunities by NAICS, PSC, set-aside, keyword
    - Fetch full opportunity details + attachments
    - Track amendments and updates
    - Extract Q&A / clarification responses
    """
    BASE_URL = "https://api.sam.gov/opportunities/v2"

    def search_opportunities(self, filters: dict) -> list[Opportunity]
    def get_opportunity_detail(self, notice_id: str) -> OpportunityDetail
    def get_attachments(self, resource_links: list) -> list[Attachment]
    def check_amendments(self, notice_id: str) -> list[Amendment]
```

### 4.3 Opportunity Normalization Pipeline

```
Raw Source Data → Normalize → Deduplicate → Enrich → Score → Rank → Publish Top 10
```

Each step is a Celery task:

1. **Ingest**: Pull from each source, store raw JSON
2. **Normalize**: Map to unified `Opportunity` schema (title, agency, NAICS, PSC, set-aside, deadline, description, attachments, value_estimate)
3. **Deduplicate**: Match by notice_id + source; merge updates
4. **Enrich**: Add agency history, incumbent info, NAICS mapping, keyword extraction
5. **Score**: ML-based fit scoring (see §4.4)
6. **Rank**: Sort by composite score, select Top 10
7. **Publish**: Create daily digest, push notifications, update dashboard

### 4.4 ML Fit Scoring Engine

**Phase 1 (Rule-based + Embedding Similarity):**
```
Score = w1*NAICS_match + w2*PSC_match + w3*keyword_overlap
      + w4*capability_similarity + w5*past_performance_relevance
      + w6*value_fit + w7*deadline_feasibility + w8*set_aside_match
      - w9*competition_intensity - w10*risk_factors
```

**Phase 2 (ML model, once labeled data exists):**
- Features: all above + agency history, win/loss record, team availability
- Model: LightGBM or XGBoost (binary classifier: bid/no-bid → probability)
- Labels: historical bid/no-bid decisions + outcomes (win/loss)
- Explainability: SHAP values → "why this score"

**Phase 3 (RL refinement):**
- Contextual bandit: each day select Top 10 from Top 30 candidates
- Reward: +1 if bid, +5 if won, -1 if bid and lost, 0 if no-bid
- Policy: Thompson Sampling or LinUCB for exploration/exploitation

### 4.5 Company Profile & Capability Statement

```python
# apps/opportunities/models.py
class CompanyProfile(models.Model):
    name = models.CharField(max_length=255)
    uei_number = models.CharField(max_length=12)       # SAM.gov UEI
    cage_code = models.CharField(max_length=5)          # CAGE code
    naics_codes = models.JSONField(default=list)        # Primary NAICS
    psc_codes = models.JSONField(default=list)          # Product/Service codes
    set_aside_categories = models.JSONField(default=list)  # 8a, SDVOSB, etc.
    capability_statement = models.TextField()            # Full text
    capability_embedding = VectorField(dimensions=1536)  # For similarity
    core_competencies = models.JSONField(default=list)
    past_performance_summary = models.TextField()
    key_personnel = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    clearance_levels = models.JSONField(default=list)
    contract_vehicles = models.JSONField(default=list)   # GSA, SEWP, etc.
```

---

## 5. Phase 3 — Deal Pipeline & Workflow

### 5.1 Pipeline Stages (Standard Federal Capture)

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐
│ INTAKE  │→  │ QUALIFY  │→  │ BID/NO   │→  │ CAPTURE    │→  │ PROPOSAL │
│         │   │          │   │ BID (H)  │   │ PLAN       │   │ DEV      │
└─────────┘   └──────────┘   └──────────┘   └─────────────┘   └──────────┘
                                                                     │
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐         │
│ POST    │←  │ SUBMIT   │←  │ FINAL    │←  │ RED TEAM   │←  ───────┘
│ SUBMIT  │   │ (H)      │   │ REVIEW(H)│   │ REVIEW (H) │
└─────────┘   └──────────┘   └──────────┘   └─────────────┘
     │
┌─────────┐   ┌──────────┐   ┌──────────┐
│ AWARD   │→  │ CONTRACT │→  │ DELIVERY │
│ PENDING │   │ SETUP(H) │   │          │
└─────────┘   └──────────┘   └──────────┘

(H) = Human-in-the-Loop approval gate
```

### 5.2 Deal Model

```python
class Deal(models.Model):
    STAGES = [
        ('intake', 'Intake'),
        ('qualify', 'Qualify'),
        ('bid_no_bid', 'Bid/No-Bid Decision'),
        ('capture_plan', 'Capture Planning'),
        ('proposal_dev', 'Proposal Development'),
        ('red_team', 'Red Team Review'),
        ('final_review', 'Final Review'),
        ('submit', 'Submission'),
        ('post_submit', 'Post-Submission'),
        ('award_pending', 'Award Pending'),
        ('contract_setup', 'Contract Setup'),
        ('delivery', 'Delivery/Execution'),
        ('closed_won', 'Closed - Won'),
        ('closed_lost', 'Closed - Lost'),
        ('no_bid', 'No-Bid'),
    ]

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    stage = models.CharField(max_length=30, choices=STAGES, default='intake')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    team = models.ManyToManyField(User, related_name='deal_team')
    priority = models.IntegerField(choices=[(1,'Critical'),(2,'High'),(3,'Medium'),(4,'Low')])
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    win_probability = models.FloatField(default=0.0)
    fit_score = models.FloatField(default=0.0)
    ai_recommendation = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True)

    # Stage transition tracking
    stage_entered_at = models.DateTimeField(auto_now=True)
    stage_history = models.JSONField(default=list)
```

### 5.3 Workflow Engine

```python
class WorkflowEngine:
    """
    State machine for deal stage transitions.
    Enforces HITL approval gates and prerequisite checks.
    """
    HITL_GATES = {'bid_no_bid', 'final_review', 'submit', 'contract_setup'}

    PREREQUISITES = {
        'bid_no_bid': ['fit_score_computed', 'qualification_checklist_complete'],
        'proposal_dev': ['bid_approved', 'capture_plan_exists'],
        'red_team': ['proposal_draft_complete'],
        'final_review': ['red_team_complete', 'pricing_approved'],
        'submit': ['final_review_approved', 'submission_checklist_complete'],
        'contract_setup': ['award_received'],
    }

    def transition(self, deal, target_stage, user, approval=None):
        """Validate prerequisites, enforce HITL, log transition"""
```

### 5.4 Task & Checklist System

- Auto-generated tasks per stage (templated checklists)
- Assignable to team members
- SLA timers with escalation
- AI can auto-complete certain tasks (document generation, analysis)

### 5.5 Approval System

```python
class Approval(models.Model):
    TYPES = [
        ('bid_no_bid', 'Bid/No-Bid Decision'),
        ('pricing', 'Pricing Approval'),
        ('proposal_final', 'Final Proposal Approval'),
        ('submission', 'Submission Authorization'),
        ('contract_terms', 'Contract Terms Approval'),
    ]

    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    approval_type = models.CharField(max_length=30, choices=TYPES)
    requested_by = models.ForeignKey(User, related_name='approvals_requested')
    requested_from = models.ForeignKey(User, related_name='approvals_pending')
    status = models.CharField(choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')])
    ai_recommendation = models.TextField(blank=True)
    ai_confidence = models.FloatField(null=True)
    decision_rationale = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True)
```

---

## 6. Phase 4 — RFP Workspace & Compliance

### 6.1 RFP Document Ingestion

- Upload RFP documents (PDF, DOCX, Excel)
- AI-powered extraction:
  - Requirements (shall/must statements)
  - Evaluation criteria & weights
  - Deliverables & CDRLs
  - Page limits & formatting rules
  - Submission instructions
  - Key dates (Q&A deadline, proposal due, etc.)
  - Required forms & certifications

### 6.2 Compliance Matrix Generator

```python
class ComplianceMatrixItem(models.Model):
    rfp_document = models.ForeignKey(RFPDocument, on_delete=models.CASCADE)
    requirement_id = models.CharField(max_length=50)    # e.g., "L.3.2.1"
    requirement_text = models.TextField()
    section_reference = models.CharField(max_length=100)  # Section L/M ref
    requirement_type = models.CharField(choices=[
        ('mandatory', 'Mandatory'),
        ('desirable', 'Desirable'),
        ('informational', 'Informational'),
    ])
    evaluation_weight = models.FloatField(null=True)

    # Response tracking
    proposal_section = models.CharField(max_length=100, blank=True)
    response_owner = models.ForeignKey(User, null=True)
    response_status = models.CharField(choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('drafted', 'Drafted'),
        ('reviewed', 'Reviewed'),
        ('final', 'Final'),
    ])
    ai_draft_response = models.TextField(blank=True)
    human_final_response = models.TextField(blank=True)
    compliance_status = models.CharField(choices=[
        ('compliant', 'Compliant'),
        ('partial', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('not_assessed', 'Not Assessed'),
    ])
    evidence_references = models.JSONField(default=list)
```

### 6.3 Amendment & Change Tracker

- Detect new amendments/modifications from SAM.gov
- Diff against previous version
- Highlight changed requirements
- Auto-update compliance matrix
- Trigger re-review if material changes found (HITL gate)

---

## 6A. Phase 4A — Company AI Strategy Agent

> **Purpose:** A strategic intelligence layer that sits ABOVE the deal pipeline. It maintains your company's evolving strategy, influences every bid/no-bid decision, balances the portfolio, and ensures the entire platform optimizes toward your business goals — not just individual deal fit.

### 6A.1 Strategic Knowledge Base

```python
class CompanyStrategy(models.Model):
    """Living strategic plan maintained by strategy agent + leadership"""
    version = models.IntegerField()
    effective_date = models.DateField()

    # Strategic positioning
    mission_statement = models.TextField()
    vision_3_year = models.TextField()
    target_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    target_win_rate = models.FloatField()
    target_margin = models.FloatField()

    # Market focus
    target_agencies = models.JSONField(default=list)        # ["DoD", "DHS", "DOE", "HHS"]
    target_domains = models.JSONField(default=list)         # ["AI/ML", "Cloud", "Cyber", "Data"]
    target_naics_codes = models.JSONField(default=list)
    growth_markets = models.JSONField(default=list)         # Markets to BREAK INTO
    mature_markets = models.JSONField(default=list)         # Markets to DEFEND
    exit_markets = models.JSONField(default=list)           # Markets to phase out

    # Competitive strategy
    differentiators = models.JSONField(default=list)        # Key competitive advantages
    win_themes = models.JSONField(default=list)             # Reusable win themes
    pricing_philosophy = models.TextField()                 # Aggressive, value-based, etc.
    teaming_strategy = models.TextField()                   # Prime vs sub, preferred partners

    # Capacity constraints
    max_concurrent_proposals = models.IntegerField(default=5)
    available_key_personnel = models.JSONField(default=list)
    clearance_capacity = models.JSONField(default=dict)     # TS/SCI slots, Secret, etc.

    # Embedding for semantic matching
    strategy_embedding = VectorField(dimensions=1536)

class StrategicGoal(models.Model):
    """Quantified strategic objectives that drive agent behavior"""
    strategy = models.ForeignKey(CompanyStrategy, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.CharField(choices=[
        ('revenue', 'Revenue Growth'),
        ('market_entry', 'New Market Entry'),
        ('market_share', 'Market Share Defense'),
        ('capability', 'Capability Building'),
        ('relationship', 'Client Relationship'),
        ('portfolio', 'Portfolio Balance'),
        ('profitability', 'Profitability'),
    ])
    metric = models.CharField(max_length=100)
    current_value = models.FloatField()
    target_value = models.FloatField()
    deadline = models.DateField()
    weight = models.FloatField(default=1.0)    # Priority among goals
    status = models.CharField(choices=[('on_track','On Track'),('at_risk','At Risk'),('behind','Behind')])

class PortfolioSnapshot(models.Model):
    """Periodic snapshot of pipeline portfolio health"""
    snapshot_date = models.DateField()
    active_deals = models.IntegerField()
    total_pipeline_value = models.DecimalField(max_digits=15, decimal_places=2)
    weighted_pipeline = models.DecimalField(max_digits=15, decimal_places=2)
    deals_by_agency = models.JSONField()
    deals_by_domain = models.JSONField()
    deals_by_stage = models.JSONField()
    deals_by_size = models.JSONField()
    capacity_utilization = models.FloatField()     # % of available team engaged
    concentration_risk = models.JSONField()         # Over-reliance on single client/domain
    strategic_alignment_score = models.FloatField() # Overall portfolio-strategy fit
    ai_recommendations = models.JSONField()         # Strategy agent's recommended actions
```

### 6A.2 Strategy Agent Capabilities

```python
class StrategyAgent:
    """
    Company AI Strategy Agent — the strategic brain of the platform.
    Influences EVERY bid decision and shapes the entire pipeline.
    """

    # ── Strategic Scoring (runs on every opportunity) ──────────────
    def compute_strategic_score(self, opportunity, strategy) -> StrategicScore:
        """
        Score an opportunity against the company strategy.
        This score ADDS to the technical fit score to create
        a composite 'pursue score'.

        Factors:
        - Agency alignment (is this a target agency?)
        - Domain alignment (does this grow a target capability?)
        - Growth market bonus (extra weight for break-in markets)
        - Portfolio balance (do we need more deals in this area?)
        - Revenue target contribution (deal size vs remaining target)
        - Capacity fit (do we have people for this?)
        - Strategic relationship value (gateway deal for bigger wins?)
        - Competitive positioning (can we differentiate here?)
        """

    # ── Bid/No-Bid Influence ───────────────────────────────────────
    def generate_bid_recommendation(self, deal, strategy) -> BidRecommendation:
        """
        Generates a strategic bid/no-bid recommendation
        that's presented alongside the fit score at the HITL gate.

        Returns:
        - recommendation: BID / NO-BID / CONDITIONAL_BID
        - strategic_rationale: "This deal opens DoD AI market..."
        - opportunity_cost: "Bidding this blocks 2 other pursuits..."
        - portfolio_impact: "Improves agency diversification by 15%..."
        - resource_impact: "Requires 3 key personnel for 4 months..."
        - risk_assessment: strategic risks of bidding / not bidding
        """

    # ── Portfolio Optimization ─────────────────────────────────────
    def analyze_portfolio(self, all_active_deals, strategy) -> PortfolioAnalysis:
        """
        Weekly analysis of the entire pipeline against strategy.

        Outputs:
        - Portfolio balance scorecard (by agency, domain, size, stage)
        - Concentration risk warnings
        - Gap analysis (target areas with no active pursuits)
        - Capacity forecast (team utilization by month)
        - Revenue projection vs target
        - Recommended actions (pursue more in X, deprioritize Y)
        """

    # ── Win Theme Generation ───────────────────────────────────────
    def generate_win_themes(self, deal, strategy) -> list[WinTheme]:
        """
        Generate deal-specific win themes aligned with company strategy.
        These flow into proposal writing and pricing positioning.
        """

    # ── Competitive Intelligence ───────────────────────────────────
    def assess_competitive_landscape(self, opportunity) -> CompetitiveAssessment:
        """
        Analyze likely competitors, incumbent advantages,
        and recommend positioning strategy.
        Uses historical data from won/lost deals + public info.
        """

    # ── Strategy Evolution ─────────────────────────────────────────
    def recommend_strategy_updates(self, outcomes, portfolio) -> list[StrategyUpdate]:
        """
        Based on win/loss patterns, market trends, and portfolio
        performance, recommend updates to the company strategy.
        Presented to executives at HITL gate (quarterly review).
        """
```

### 6A.3 Strategy Agent Integration Points

```
Every Bid/No-Bid Gate:
  ┌─────────────────────┐
  │ Technical Fit Score  │ ← Opportunity Scout
  │ Strategic Score      │ ← Strategy Agent
  │ Composite Score      │ ← Weighted combination
  │ Bid Recommendation   │ ← Strategy Agent
  │ Portfolio Impact     │ ← Strategy Agent
  │ Resource Availability│ ← Strategy Agent
  └──────────┬──────────┘
             │
        [HITL GATE]
        Human decides
             │
  ┌──────────┴──────────┐
  │ Decision + rationale │
  │ → feeds back to      │
  │   strategy learning  │
  └─────────────────────┘

Weekly Portfolio Review (automated):
  Strategy Agent → Portfolio Analysis → Dashboard
  → Alerts if portfolio drifts from strategy
  → Recommends opportunity hunting priorities

Quarterly Strategy Review (HITL):
  Strategy Agent → Strategy Update Recommendations
  → Executive review + approval
  → Updated strategy → influences all future scoring
```

### 6A.4 LangGraph Strategy Graph

```python
class StrategyGraphState(TypedDict):
    opportunity: dict
    company_strategy: dict
    active_portfolio: list
    team_capacity: dict
    historical_outcomes: list
    strategic_score: float
    bid_recommendation: dict
    win_themes: list
    competitive_assessment: dict

strategy_graph = StateGraph(StrategyGraphState)
strategy_graph.add_node("load_strategy", load_current_strategy)
strategy_graph.add_node("assess_alignment", assess_strategic_alignment)
strategy_graph.add_node("analyze_portfolio_impact", analyze_portfolio_impact)
strategy_graph.add_node("check_capacity", check_resource_capacity)
strategy_graph.add_node("assess_competition", assess_competitive_landscape)
strategy_graph.add_node("generate_recommendation", generate_bid_recommendation)
strategy_graph.add_node("generate_win_themes", generate_win_themes)

strategy_graph.add_edge("load_strategy", "assess_alignment")
strategy_graph.add_edge("assess_alignment", "analyze_portfolio_impact")
strategy_graph.add_edge("analyze_portfolio_impact", "check_capacity")
strategy_graph.add_edge("check_capacity", "assess_competition")
strategy_graph.add_edge("assess_competition", "generate_recommendation")
strategy_graph.add_edge("generate_recommendation", "generate_win_themes")
strategy_graph.add_edge("generate_win_themes", END)
```

---

## 6B. Phase 4B — Marketing & Sales Expert Agent

> **Purpose:** A fully autonomous marketing strategist and sales intelligence engine that crafts winning positioning, develops pursuit-specific marketing strategies, generates capture narratives, and coaches the team on how to sell — not just what to bid on. Works hand-in-hand with the Strategy Agent (strategic direction) and Solution Architect (technical substance) to create irresistible proposals.

### 6B.1 Marketing Intelligence Models

```python
class MarketIntelligence(models.Model):
    """Market intelligence gathered and maintained by the marketing agent"""
    agency = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True)

    # Agency profile
    mission = models.TextField()
    strategic_priorities = models.JSONField(default=list)    # Current fiscal year priorities
    budget_trends = models.JSONField(default=dict)           # Historical + projected budgets
    technology_initiatives = models.JSONField(default=list)  # Digital transformation, AI, cloud, etc.
    key_decision_makers = models.JSONField(default=list)     # CIO, CTO, PM, CO (redacted/public)
    procurement_preferences = models.JSONField(default=dict) # LPTA vs best-value, set-aside patterns

    # Competitive landscape for this agency
    incumbent_contracts = models.JSONField(default=list)     # Known incumbents + contract values
    recompete_timeline = models.JSONField(default=list)      # Upcoming recompetes
    win_loss_history = models.JSONField(default=list)        # Our history with this agency

    # Relationship strength
    relationship_score = models.FloatField(default=0.0)      # 0-100 based on past interactions
    last_interaction = models.DateField(null=True)
    engagement_history = models.JSONField(default=list)

    # Vector embedding for semantic search
    embedding = VectorField(dimensions=1536)

class CompetitorProfile(models.Model):
    """Detailed competitor profiles for competitive positioning"""
    name = models.CharField(max_length=255)
    cage_code = models.CharField(max_length=5, blank=True)
    uei_number = models.CharField(max_length=12, blank=True)

    # Capabilities
    core_competencies = models.JSONField(default=list)
    naics_codes = models.JSONField(default=list)
    certifications = models.JSONField(default=list)       # 8a, SDVOSB, HUBZone, etc.
    contract_vehicles = models.JSONField(default=list)    # GSA, SEWP, CIO-SP3, etc.
    key_personnel = models.JSONField(default=list)        # Known experts/leaders (public info)

    # Performance
    known_contract_wins = models.JSONField(default=list)  # From FPDS/USASpending
    estimated_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    growth_trend = models.CharField(max_length=20, blank=True)  # Growing, Stable, Declining
    employee_count_estimate = models.IntegerField(null=True)

    # Strengths/Weaknesses
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    pricing_tendency = models.CharField(max_length=50, blank=True)  # Aggressive, Moderate, Premium
    known_teaming_partners = models.JSONField(default=list)

    # Win/loss against us
    head_to_head_record = models.JSONField(default=dict)   # {wins: X, losses: Y, deals: [...]}

    embedding = VectorField(dimensions=1536)

class CaptureStrategy(models.Model):
    """Per-deal capture and marketing strategy"""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE)

    # Positioning
    value_proposition = models.TextField()                  # Why us for THIS deal
    win_themes = models.JSONField(default=list)             # 3-5 deal-specific win themes
    discriminators = models.JSONField(default=list)         # What makes us uniquely qualified
    ghost_strategies = models.JSONField(default=list)       # How to ghost competitors' strengths
    counter_strategies = models.JSONField(default=list)     # How to counter our weaknesses

    # Customer insight
    customer_hot_buttons = models.JSONField(default=list)   # What the evaluator cares about most
    evaluation_bias_analysis = models.TextField(blank=True) # Predicted evaluator preferences
    incumbency_analysis = models.TextField(blank=True)      # Incumbent strengths/weaknesses

    # Teaming strategy
    recommended_team = models.JSONField(default=list)       # Prime/sub structure
    teaming_rationale = models.TextField(blank=True)
    key_personnel_assignments = models.JSONField(default=list)

    # Messaging
    elevator_pitch = models.TextField(blank=True)           # 30-second pitch for this deal
    executive_summary_themes = models.JSONField(default=list)
    section_messaging_guide = models.JSONField(default=dict)  # Per-section key messages

    # Metrics
    pwin_estimate = models.FloatField(null=True)            # Marketing-assessed P(win)
    competitive_advantage_score = models.FloatField(null=True)
```

### 6B.2 Marketing & Sales Agent Capabilities

```python
class MarketingSalesAgent:
    """
    Fully Autonomous Marketing & Sales Expert Agent.

    This agent is a virtual capture manager, BD strategist, and marketing
    expert rolled into one. It doesn't just analyze — it CRAFTS winning
    strategies and COACHES the team on how to position every proposal.
    """

    # ── Market Intelligence ────────────────────────────────
    def build_agency_profile(self, agency_name: str) -> MarketIntelligence:
        """
        Deep research on a target agency:
        - Budget analysis (USASpending, agency budget docs)
        - Strategic priorities (agency strategic plan, CIO reports)
        - Technology initiatives (IT modernization, AI strategy)
        - Procurement patterns (contract types, set-aside preferences)
        - Decision-maker mapping (public org charts, SAM.gov)
        Uses Deep Research Agent for comprehensive web intelligence.
        """

    def profile_competitor(self, competitor_name: str) -> CompetitorProfile:
        """
        Build detailed competitor profile:
        - FPDS/USASpending contract history
        - Public capability statements
        - Known wins/losses in target agencies
        - Key personnel (LinkedIn public, SAM.gov)
        - Pricing patterns from historical awards
        - Teaming partner network
        """

    # ── Competitive Positioning ────────────────────────────
    def generate_competitive_analysis(self, deal, competitors: list) -> CompetitiveAnalysis:
        """
        For a specific deal, produce:
        1. Competitor probability matrix (who's likely to bid)
        2. Competitor strength/weakness analysis per evaluation criterion
        3. Incumbent advantage assessment
        4. Our competitive advantages vs each competitor
        5. Ghost strategies (highlight areas where WE excel, competitors don't)
        6. Counter strategies (address our known weaknesses proactively)
        7. Price positioning recommendation
        """

    # ── Win Theme & Discriminator Engine ───────────────────
    def generate_win_strategy(self, deal, rfp, solution, company_strategy) -> CaptureStrategy:
        """
        The core capture strategy engine. Produces:

        1. VALUE PROPOSITION — Why this agency should choose us
           - Maps our capabilities to their specific pain points
           - Quantifies the value we bring (cost savings, efficiency, innovation)

        2. WIN THEMES (3-5 per deal) — Recurring messages throughout the proposal
           - Each theme ties to an evaluation criterion
           - Each theme is supported by evidence (past performance, solution design)
           - Each theme has a customer benefit statement

        3. DISCRIMINATORS — What makes us uniquely qualified
           - Technical differentiators (from SA agent's solution)
           - Team differentiators (key personnel, clearances)
           - Past performance differentiators
           - Innovation differentiators
           - Price/value differentiators

        4. GHOST STRATEGIES — Subtle competitive positioning
           - "Our solution uses [approach] which provides [benefit]"
           - Implies competitors lack this without naming them
           - Tied to known competitor weaknesses

        5. MESSAGING GUIDE — Per-section key messages
           - What to emphasize in each proposal section
           - How to weave win themes into technical writing
           - Executive summary tone and themes
        """

    # ── Proposal Messaging ─────────────────────────────────
    def craft_executive_summary(self, deal, capture_strategy, solution) -> str:
        """
        Generate a compelling executive summary that:
        - Opens with customer's problem (their words, their priorities)
        - Presents our understanding (shows deep insight)
        - Introduces our approach (high-level, benefit-focused)
        - Weaves in all win themes
        - Closes with differentiators and call to action
        - Follows the Shipley method or similar capture methodology
        """

    def generate_section_themes(self, deal, section_name, capture_strategy) -> SectionThemes:
        """
        For each proposal section, provide:
        - Opening theme statement
        - Key messages to include
        - Evidence to reference (past perf, metrics)
        - Customer benefit to highlight
        - Action captions for any diagrams/figures
        """

    # ── Customer Engagement Strategy ───────────────────────
    def recommend_engagement_plan(self, deal) -> EngagementPlan:
        """
        Pre-RFP and during-RFP engagement recommendations:
        - Capability briefing talking points
        - Questions to ask in industry days
        - Clarification questions strategy (what to ask, what not to)
        - White paper or RFI response strategy
        - Relationship-building touchpoints
        """

    # ── B&P (Bid & Proposal) ROI Analysis ──────────────────
    def estimate_capture_roi(self, deal, estimated_bp_cost) -> CaptureROI:
        """
        Business case for pursuing this deal:
        - Estimated B&P cost (labor, materials, travel)
        - Expected revenue if won
        - Expected margin if won
        - P(win) assessment (combining all agent scores)
        - Expected value = P(win) × margin - B&P cost
        - Comparison to other pipeline opportunities
        - GO / NO-GO recommendation with confidence level
        """

    # ── Sales Coaching ─────────────────────────────────────
    def generate_review_coaching(self, review_type, proposal_section) -> ReviewCoaching:
        """
        AI-powered review coaching for Pink/Red/Gold teams:
        - Evaluator perspective analysis ("If I were the evaluator...")
        - Strength/weakness assessment per section
        - Score prediction per evaluation criterion
        - Specific improvement recommendations
        - "Missing elements" check against evaluation criteria
        """
```

### 6B.3 Marketing Frameworks Library

```python
MARKETING_FRAMEWORKS = {
    "shipley_capture": {
        "name": "Shipley Capture Management",
        "phases": [
            "Long-Range Positioning (pre-RFP)",
            "Opportunity Assessment",
            "Capture Planning",
            "Proposal Planning",
            "Proposal Development",
            "Post-Submittal",
        ],
        "key_tools": ["Competitive Analysis", "Win Strategy",
                       "Price-to-Win", "Customer Profiling"],
    },
    "lohfeld_win_strategy": {
        "name": "Lohfeld Consulting Win Strategy",
        "elements": [
            "Customer Intimacy (understand their world)",
            "Solution Superiority (best technical approach)",
            "Competitive Advantage (why us, not them)",
            "Win Themes (recurring proof points)",
            "Price Competitiveness (value, not just lowest)",
        ],
    },
    "blue_ocean_strategy": {
        "name": "Blue Ocean Strategy for Proposals",
        "tools": [
            "Strategy Canvas (value curve vs competitors)",
            "Four Actions Framework (Eliminate/Reduce/Raise/Create)",
            "Buyer Utility Map",
            "Non-Customer Analysis",
        ],
    },
    "miller_heiman": {
        "name": "Miller Heiman Strategic Selling",
        "concepts": [
            "Economic Buyer (who controls budget)",
            "User Buyer (who uses the solution)",
            "Technical Buyer (who evaluates compliance)",
            "Coach (internal champion)",
            "Win-Results (what each buyer wins personally)",
        ],
    },
    "spin_selling": {
        "name": "SPIN Selling for Proposals",
        "framework": [
            "Situation (demonstrate understanding of current state)",
            "Problem (articulate their pain better than they can)",
            "Implication (show cost of inaction)",
            "Need-Payoff (present our solution as the answer)",
        ],
    },
}
```

### 6B.4 LangGraph Marketing Graph

```python
class MarketingGraphState(TypedDict):
    deal: dict
    rfp_requirements: list
    company_strategy: dict
    technical_solution: dict          # From SA agent
    competitor_profiles: list
    agency_intelligence: dict
    capture_strategy: dict
    win_themes: list
    executive_summary: str
    section_messaging: dict
    engagement_plan: dict
    pwin_assessment: float

marketing_graph = StateGraph(MarketingGraphState)
marketing_graph.add_node("gather_agency_intel", build_agency_intelligence)
marketing_graph.add_node("profile_competitors", profile_likely_competitors)
marketing_graph.add_node("analyze_competition", generate_competitive_analysis)
marketing_graph.add_node("craft_win_strategy", generate_capture_strategy)
marketing_graph.add_node("generate_messaging", generate_section_messaging)
marketing_graph.add_node("craft_exec_summary", craft_executive_summary)
marketing_graph.add_node("assess_pwin", assess_probability_of_win)
marketing_graph.add_node("human_review", interrupt_for_capture_review)  # HITL

marketing_graph.add_edge("gather_agency_intel", "profile_competitors")
marketing_graph.add_edge("profile_competitors", "analyze_competition")
marketing_graph.add_edge("analyze_competition", "craft_win_strategy")
marketing_graph.add_edge("craft_win_strategy", "generate_messaging")
marketing_graph.add_edge("generate_messaging", "craft_exec_summary")
marketing_graph.add_edge("craft_exec_summary", "assess_pwin")
marketing_graph.add_edge("assess_pwin", "human_review")
marketing_graph.add_edge("human_review", END)
```

---

## 6C. Phase 4C — Deep Research Agent

> **Purpose:** An autonomous deep research agent (inspired by [ConsultRalph](https://github.com/hassanmzia/AI-Consultant-Deep-Research)) that performs comprehensive, multi-source intelligence gathering on ANY topic relevant to the deal pipeline. It produces consulting-quality research reports with cited sources, data tables, and executive summaries — and feeds its findings into every other agent.

### 6C.1 Research Capabilities

```python
class DeepResearchAgent:
    """
    Autonomous Deep Research Agent.

    Inspired by ConsultRalph's approach of using deep research APIs
    to search across thousands of sources, this agent is the "intelligence
    gathering engine" for the entire platform.

    Every other agent can REQUEST research, and this agent delivers
    structured, cited, consulting-quality intelligence.
    """

    # ── Research Types ─────────────────────────────────────
    RESEARCH_TYPES = {
        "agency_due_diligence": {
            "description": "Deep dive on a federal agency",
            "sections": [
                "Agency Mission & Strategic Plan",
                "Budget Analysis (current + trends)",
                "Technology Modernization Initiatives",
                "Key Personnel & Decision Makers (public)",
                "Procurement Patterns & Preferences",
                "Recent Contract Awards in Our Domain",
                "Industry Day & RFI Summary",
                "Pain Points & Challenges",
            ],
        },
        "competitor_intelligence": {
            "description": "Competitive intelligence on a specific company",
            "sections": [
                "Company Overview & Size",
                "Core Capabilities & Differentiators",
                "Contract History (FPDS/USASpending)",
                "Key Wins & Losses",
                "Key Personnel & Leadership",
                "Technology Focus Areas",
                "Teaming Partners & Alliances",
                "Pricing Patterns (from public awards)",
                "Strengths & Vulnerabilities",
            ],
        },
        "market_analysis": {
            "description": "Market sizing and analysis for a technology/domain",
            "sections": [
                "Market Overview (TAM/SAM/SOM)",
                "Growth Drivers & Trends",
                "Key Players & Market Share",
                "Government Spending in This Area",
                "Technology Maturity Assessment",
                "Regulatory Landscape",
                "Emerging Opportunities",
                "Risk Factors",
            ],
        },
        "technology_assessment": {
            "description": "Deep research on a specific technology for proposals",
            "sections": [
                "Technology Overview & Maturity",
                "Current State of the Art",
                "Key Vendors & Implementations",
                "Government Adoption Status",
                "Security & Compliance Considerations",
                "Cost/Benefit Analysis",
                "Integration Challenges",
                "Case Studies & Success Stories",
                "Future Roadmap & Trends",
            ],
        },
        "incumbent_analysis": {
            "description": "Deep analysis of an incumbent on a recompete",
            "sections": [
                "Current Contract Details (value, period, scope)",
                "Incumbent Performance (CPARS if available)",
                "Known Issues or Protests",
                "Incumbent's Strengths on This Contract",
                "Incumbent's Weaknesses / Gaps",
                "Likelihood of Incumbent Retention",
                "Strategy to Unseat Incumbent",
            ],
        },
        "price_benchmarking": {
            "description": "Research market rates and pricing benchmarks",
            "sections": [
                "GSA Schedule Rate Analysis",
                "FPDS Award Price Analysis (similar contracts)",
                "Industry Rate Surveys (Deltek, etc.)",
                "Geographic Rate Variations",
                "Contract Vehicle Pricing Norms",
                "Competitor Pricing Patterns",
                "Government Budget Constraints",
                "Price-to-Win Range Estimate",
            ],
        },
        "custom": {
            "description": "Any custom research query",
            "sections": [],  # Agent determines structure
        },
    }

    # ── Core Research Pipeline ─────────────────────────────
    def execute_research(self, research_request: ResearchRequest) -> ResearchReport:
        """
        Full research pipeline:

        1. QUERY PLANNING
           - Decompose the research question into sub-queries
           - Identify required data sources (web, APIs, databases)
           - Plan research strategy (breadth-first, then depth on key findings)

        2. MULTI-SOURCE SEARCH
           - Web search (multiple search engines, academic, news)
           - Government databases (SAM.gov, FPDS, USASpending, agency sites)
           - Industry databases (GovWin, Deltek, Bloomberg Gov)
           - Knowledge Vault (internal documents, past research)
           - File/URL analysis (uploaded documents, specified URLs)

        3. INFORMATION EXTRACTION
           - Extract key facts, statistics, quotes
           - Identify patterns and trends
           - Cross-reference across sources for accuracy
           - Flag conflicting information

        4. SYNTHESIS & ANALYSIS
           - Organize findings by research section
           - Generate analysis and insights
           - Create data tables and comparisons
           - Develop strategic implications

        5. REPORT GENERATION
           - Executive summary (1-page)
           - Full research report (structured markdown)
           - Data tables (structured JSON → CSV/Excel)
           - Source citations (all findings backed by URLs)
           - Confidence scoring (high/medium/low per finding)

        6. DELIVERABLES
           - Markdown report (stored in DB + rendered in UI)
           - PDF export (professional formatting)
           - CSV/Excel (structured data tables)
           - DOCX executive summary
           - JSON (structured findings for other agents to consume)
        """

    # ── Follow-Up Research ─────────────────────────────────
    def follow_up(self, previous_report_id: str, follow_up_query: str) -> ResearchReport:
        """
        Continue research using previous report as context.
        Like ConsultRalph's follow-up feature — uses previous findings
        to go deeper on specific aspects.
        """

    # ── Parallel Research Swarm ────────────────────────────
    def swarm_research(self, research_requests: list[ResearchRequest]) -> list[ResearchReport]:
        """
        Launch multiple research tasks simultaneously.
        Like ConsultRalph's parallel research capability —
        complete in minutes what would take days manually.

        Use cases:
        - Research all 5 likely competitors in parallel
        - Research agency + technology + market simultaneously
        - Research multiple incumbents on a recompete
        """

    # ── Integration with Other Agents ──────────────────────
    def research_for_agent(self, requesting_agent: str, context: dict) -> ResearchReport:
        """
        Other agents can request research:

        - Strategy Agent → "Research this agency's AI priorities for FY2026"
        - Marketing Agent → "Research competitor X's recent wins at DoD"
        - Solution Architect → "Research current state of graph RAG implementations"
        - Pricing Agent → "Research GSA rates for AI engineers in DC area"
        - Proposal Writer → "Research case studies of similar solutions at this agency"
        """
```

### 6C.2 Research Data Models

```python
class ResearchRequest(models.Model):
    """Research task request from any agent or human"""
    requested_by_agent = models.CharField(max_length=100, blank=True)
    requested_by_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    deal = models.ForeignKey('deals.Deal', null=True, on_delete=models.SET_NULL)

    research_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=500)
    focus_areas = models.TextField(blank=True)
    specific_questions = models.JSONField(default=list)
    context = models.TextField(blank=True)                  # Why this research is needed

    # Attached files/URLs for context
    attached_files = models.JSONField(default=list)         # MinIO file references
    attached_urls = models.JSONField(default=list)          # URLs to analyze

    # Status
    status = models.CharField(choices=[
        ('queued', 'Queued'),
        ('researching', 'Researching'),
        ('synthesizing', 'Synthesizing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='queued')
    progress_steps = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    # Follow-up chain
    parent_research = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

class ResearchReport(models.Model):
    """Completed research report with all deliverables"""
    request = models.OneToOneField(ResearchRequest, on_delete=models.CASCADE)

    # Content
    executive_summary = models.TextField()
    full_report_markdown = models.TextField()
    structured_findings = models.JSONField(default=dict)    # Machine-readable findings
    data_tables = models.JSONField(default=list)            # Structured tables

    # Sources
    sources = models.JSONField(default=list)                # [{title, url, snippet, confidence}]
    source_count = models.IntegerField(default=0)

    # Deliverables (files in MinIO)
    pdf_file = models.FileField(null=True)
    csv_file = models.FileField(null=True)
    docx_file = models.FileField(null=True)

    # Quality
    confidence_score = models.FloatField(default=0.0)       # Overall confidence in findings
    ai_quality_assessment = models.TextField(blank=True)

    # Usage tracking
    consumed_by_agents = models.JSONField(default=list)     # Which agents used this research
    cited_in_proposals = models.JSONField(default=list)     # Which proposals referenced this

    # Embedding for future retrieval
    embedding = VectorField(dimensions=1536)

class ResearchActivity(models.Model):
    """Real-time activity feed during research (like ConsultRalph's activity feed)"""
    request = models.ForeignKey(ResearchRequest, on_delete=models.CASCADE, related_name='activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    activity_type = models.CharField(choices=[
        ('search', 'Searching'),
        ('extract', 'Extracting'),
        ('analyze', 'Analyzing'),
        ('synthesize', 'Synthesizing'),
        ('generate', 'Generating'),
    ])
    message = models.TextField()                            # "Searching SAM.gov for DoD AI contracts..."
    sources_found = models.IntegerField(default=0)
```

### 6C.3 LangGraph Research Graph

```python
class ResearchGraphState(TypedDict):
    research_request: dict
    sub_queries: list                   # Decomposed research questions
    search_results: dict                # Results from all sources
    extracted_facts: list               # Structured facts with citations
    analysis: dict                      # Synthesized analysis
    report: dict                        # Final report
    deliverables: dict                  # Generated files
    activity_log: list                  # Real-time progress messages

research_graph = StateGraph(ResearchGraphState)
research_graph.add_node("plan_research", decompose_and_plan)
research_graph.add_node("search_web", search_web_sources)
research_graph.add_node("search_gov_databases", search_government_databases)
research_graph.add_node("search_knowledge_vault", search_internal_knowledge)
research_graph.add_node("analyze_attached_files", analyze_uploaded_files_urls)
research_graph.add_node("extract_facts", extract_and_structure_facts)
research_graph.add_node("cross_reference", cross_reference_and_validate)
research_graph.add_node("synthesize", synthesize_analysis)
research_graph.add_node("generate_report", generate_full_report)
research_graph.add_node("generate_deliverables", generate_pdf_csv_docx)
research_graph.add_node("quality_check", assess_quality_and_confidence)

# Parallel search branches
research_graph.add_edge("plan_research", "search_web")
research_graph.add_edge("plan_research", "search_gov_databases")
research_graph.add_edge("plan_research", "search_knowledge_vault")
research_graph.add_edge("plan_research", "analyze_attached_files")

# Merge results
research_graph.add_edge("search_web", "extract_facts")
research_graph.add_edge("search_gov_databases", "extract_facts")
research_graph.add_edge("search_knowledge_vault", "extract_facts")
research_graph.add_edge("analyze_attached_files", "extract_facts")

# Analysis pipeline
research_graph.add_edge("extract_facts", "cross_reference")
research_graph.add_edge("cross_reference", "synthesize")
research_graph.add_edge("synthesize", "generate_report")
research_graph.add_edge("generate_report", "generate_deliverables")
research_graph.add_edge("generate_deliverables", "quality_check")
research_graph.add_edge("quality_check", END)
```

---

## 6D. Phase 4D — Business Legal Agent

> **Purpose:** A fully autonomous business legal expert agent, inspired by [AI-Legal-Assistant](https://github.com/hassanmzia/AI-Legal-Assistant), customized for federal government contracting. It guides the entire bidding process from a legal perspective, reviews and drafts contracts, ensures FAR/DFARS compliance, identifies legal risks in proposals and teaming arrangements, and protects the company from legal exposure at every stage of the deal pipeline.

### 6D.1 Legal Knowledge Base (RAG-Powered)

```python
class LegalKnowledgeBase(models.Model):
    """
    Legal knowledge base for the Business Legal Agent.
    Seeded with federal acquisition law, contract law, and business law
    — then continuously updated with case outcomes and new regulations.
    """
    title = models.CharField(max_length=500)
    category = models.CharField(choices=[
        # Federal Acquisition
        ('far', 'Federal Acquisition Regulation (FAR)'),
        ('dfars', 'Defense FAR Supplement (DFARS)'),
        ('gsam', 'GSA Acquisition Manual (GSAM)'),
        ('agar', 'Agency-Specific Acquisition Regulation'),
        ('executive_order', 'Executive Order'),

        # Contract Law
        ('contract_precedent', 'Contract Law Precedent'),
        ('gao_decision', 'GAO Bid Protest Decision'),
        ('cofc_decision', 'Court of Federal Claims Decision'),
        ('bca_decision', 'Board of Contract Appeals Decision'),

        # Compliance & Regulatory
        ('far_clause', 'FAR Clause Library'),
        ('dfars_clause', 'DFARS Clause Library'),
        ('compliance_guide', 'Compliance Guide'),
        ('ethics_regulation', 'Ethics & OCI Regulation'),

        # Business Law
        ('teaming_agreement', 'Teaming Agreement Template/Precedent'),
        ('nda_template', 'NDA Template/Precedent'),
        ('subcontract_template', 'Subcontract Template/Precedent'),
        ('ip_agreement', 'IP/Data Rights Agreement'),
        ('employment_law', 'Employment Law (for staffing)'),

        # Risk & Insurance
        ('insurance_requirement', 'Insurance Requirement'),
        ('bonding_requirement', 'Bonding Requirement'),
        ('liability_precedent', 'Liability Precedent'),

        # Other
        ('internal_policy', 'Company Legal Policy'),
        ('other', 'Other Legal Document'),
    ])

    content = models.TextField()
    source = models.CharField(max_length=500, blank=True)   # "FAR 52.232-1", "GAO B-420123"
    effective_date = models.DateField(null=True)
    jurisdiction = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list)

    # Vector embedding for RAG
    embedding = VectorField(dimensions=1536)

class LegalClauseLibrary(models.Model):
    """
    Comprehensive clause library for contract drafting and review.
    Each clause has standard text, risk analysis, and negotiation guidance.
    """
    clause_number = models.CharField(max_length=50)          # "FAR 52.212-4"
    title = models.CharField(max_length=255)
    regulation_source = models.CharField(max_length=50)      # FAR, DFARS, GSAM
    full_text = models.TextField()

    # Legal analysis
    risk_level = models.CharField(choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical — Requires Legal Review'),
    ])
    risk_explanation = models.TextField(blank=True)
    common_issues = models.JSONField(default=list)           # Known problems with this clause
    negotiation_guidance = models.TextField(blank=True)      # How to negotiate this clause
    standard_response = models.TextField(blank=True)         # Pre-approved response language
    requires_legal_review = models.BooleanField(default=False)

    # Applicability
    contract_types = models.JSONField(default=list)          # FFP, T&M, CPFF, IDIQ, etc.
    applicable_thresholds = models.JSONField(default=dict)   # SAT, commercial item, etc.
    mandatory = models.BooleanField(default=False)
    flowdown_required = models.BooleanField(default=False)   # Must flow to subs

    embedding = VectorField(dimensions=1536)
```

### 6D.2 Business Legal Agent Capabilities

```python
class BusinessLegalAgent:
    """
    Fully Autonomous Business Legal Agent.

    Inspired by AI-Legal-Assistant's multi-tool ReAct architecture
    (RAG search, loophole detection, risk assessment, contract review,
    compliance checking, evaluation framework) — customized for
    federal government contracting and deal pipeline.
    """

    # ── Bidding Process Legal Guidance ─────────────────────

    def review_rfp_legal_terms(self, rfp_document) -> RFPLegalReview:
        """
        Legal review of the RFP:
        1. Identify all FAR/DFARS clauses cited
        2. Flag high-risk clauses (unlimited data rights, etc.)
        3. Identify unusual or onerous terms
        4. Check for OCI concerns
        5. Assess protest-worthy issues
        6. Review set-aside requirements
        7. Identify mandatory certifications
        8. Flag insurance/bonding requirements
        9. Review IP/data rights provisions
        10. Assess penalty clauses
        """

    def assess_bid_legal_risks(self, deal, rfp, proposal) -> BidLegalRiskAssessment:
        """
        Legal risk assessment for the entire bid:
        - False Claims Act exposure
        - OCI risk
        - Key personnel commitment liability
        - Pricing certification risk (CAS)
        - Small business subcontracting plan compliance
        - Buy American Act / Trade Agreements Act
        - Section 889 (banned telecom)
        - CMMC compliance
        - Representation and certification accuracy
        """

    def guide_bid_no_bid_legal(self, deal) -> BidNoBidLegalGuidance:
        """
        Legal perspective on bid/no-bid:
        - Eligibility check (set-aside, size standard, OCI)
        - Certification requirements met?
        - Unacceptable liability exposure?
        - Protest grounds if we lose?
        - Teaming arrangement exposure?
        """

    # ── Contract Review & Drafting ─────────────────────────

    def review_contract(self, contract_text, contract_type) -> ContractReview:
        """
        Comprehensive contract review (clause-by-clause):
        1. Map every clause to FAR/DFARS source
        2. Risk-score each clause
        3. Identify missing mandatory clauses
        4. Liability analysis (indemnification, limitation, liquidated damages)
        5. IP & data rights review
        6. Termination provisions (T4C, T4D, cure/show cause)
        7. Payment & pricing terms
        8. Compliance requirements (CAS, TINA, SCA, BAA)
        9. Dispute resolution (CDA, ADR)
        """

    def draft_contract(self, deal, contract_type, terms) -> ContractDraft:
        """
        Draft contracts with clause-by-clause justification:
        - Prime contract terms response
        - Teaming Agreements (with flow-down)
        - Subcontract Agreements
        - NDAs (mutual, one-way, gov-specific)
        - Consultant Agreements
        - Task Order responses
        Includes negotiation positions (ideal, acceptable, walk-away).
        """

    def generate_redline(self, original, proposed) -> RedlineAnalysis:
        """
        Intelligent redline with legal impact assessment per change.
        """

    # ── Teaming & Subcontracting ───────────────────────────

    def review_teaming_arrangement(self, agreement, partner) -> TeamingReview:
        """
        Legal review of teaming/subcontracting:
        - Work share allocation (set-aside rules)
        - Limitation on subcontracting (SBA)
        - IP protection between team members
        - Non-compete / non-solicitation
        - Flow-down clause compliance
        - Joint venture vs prime/sub analysis
        """

    def assess_oci_risk(self, deal, team_members) -> OCIAssessment:
        """
        OCI analysis: biased ground rules, unequal access,
        impaired objectivity — with mitigation plan.
        """

    # ── FAR/DFARS Compliance ───────────────────────────────

    def check_far_compliance(self, document, document_type) -> FARComplianceReport:
        """
        Full FAR/DFARS compliance audit:
        Representations, CAS, TINA, Buy American, Section 889,
        CMMC, SCA/DBA, EEO, affirmative action.
        """

    def check_ethics_compliance(self, deal, team) -> EthicsReport:
        """
        Procurement ethics: Procurement Integrity Act,
        revolving door, gifts, lobbying, personal COI,
        mandatory disclosure.
        """

    def monitor_regulatory_changes(self) -> list[RegulatoryAlert]:
        """
        Monitor FAR/DFARS changes via Deep Research Agent.
        """

    # ── Bid Protest & Disputes ─────────────────────────────

    def assess_protest_viability(self, deal, award_decision) -> ProtestAssessment:
        """
        Protest viability: grounds, GAO vs COFC, timeline,
        cost/benefit, precedent search (RAG), corrective action probability.
        """

    def draft_protest(self, deal, protest_grounds) -> ProtestDraft:
        """
        Draft protest with facts, legal grounds, precedent citations.
        """

    def prepare_claims(self, contract, issue_type) -> ClaimPreparation:
        """
        CDA claims: REA drafting, certification, documentation, interest calc.
        """

    # ── Proposal Legal Review ──────────────────────────────

    def review_proposal_legal(self, proposal, rfp) -> ProposalLegalReview:
        """
        Final legal review before submission:
        Representations accuracy, False Claims Act check,
        key personnel language, pricing certifications,
        subcontracting plan, OCI disclosure, data rights assertions.
        """

    # ── Evaluation Framework (from AI-Legal-Assistant) ─────

    def evaluate_legal_analysis(self, output, analysis_type) -> LegalEvaluation:
        """
        Quality evaluation (DeepEval-inspired):
        - Tool Correctness (were right legal tools used?)
        - Task Completion (all legal aspects covered?)
        - Answer Relevancy (analysis relevant to question?)
        - Content Coverage (thoroughness by category)
        - Grading: A-F scale
        """
```

### 6D.3 Legal Analysis Types

```python
LEGAL_ANALYSIS_TYPES = {
    "rfp_legal_review": {
        "tools": ["legal_rag_search", "clause_library_search",
                  "compliance_check", "risk_assessment"],
        "required_aspects": ["FAR/DFARS clauses", "liability", "IP/data rights",
                            "set-aside compliance", "OCI", "insurance/bonding"],
    },
    "contract_review": {
        "tools": ["legal_rag_search", "clause_library_search", "contract_review",
                  "compliance_check", "risk_assessment", "loophole_detection"],
        "required_aspects": ["clause analysis", "liability", "IP rights",
                            "termination", "payment", "compliance", "disputes"],
    },
    "teaming_review": {
        "tools": ["legal_rag_search", "contract_review",
                  "compliance_check", "oci_assessment"],
        "required_aspects": ["work share", "IP protection", "exclusivity",
                            "flow-down", "small business compliance"],
    },
    "bid_protest_assessment": {
        "tools": ["legal_rag_search", "web_legal_search",
                  "protest_precedent_search", "risk_assessment"],
        "required_aspects": ["protest grounds", "standing", "timeliness",
                            "precedent", "likelihood of success"],
    },
    "compliance_audit": {
        "tools": ["clause_library_search", "compliance_check", "web_legal_search"],
        "required_aspects": ["representations", "CAS", "TINA", "Buy American",
                            "Section 889", "CMMC", "SCA/DBA", "EEO"],
    },
    "ethics_review": {
        "tools": ["legal_rag_search", "compliance_check", "risk_assessment"],
        "required_aspects": ["Procurement Integrity", "revolving door",
                            "gifts", "lobbying", "personal COI"],
    },
}
```

### 6D.4 LangGraph Legal Agent (ReAct Pattern)

```python
class LegalAgentState(TypedDict):
    messages: list                       # Conversation history (ReAct)
    deal: dict
    document_text: str                   # Contract/RFP/agreement text
    analysis_type: str
    knowledge_results: list              # RAG results from legal KB
    clause_analysis: list                # Per-clause risk analysis
    compliance_report: dict
    risk_assessment: dict
    recommendations: list
    evaluation_scores: dict              # Quality evaluation (A-F)
    tools_used: list
    iteration_count: int                 # ReAct loop (max 10)
    final_analysis: str

legal_graph = StateGraph(LegalAgentState)

# ReAct pattern (from AI-Legal-Assistant)
legal_graph.add_node("agent", legal_agent_node)          # LLM reasoning
legal_graph.add_node("tools", legal_tool_node)           # Tool execution
legal_graph.add_node("evaluate", evaluate_legal_output)  # Quality evaluation

legal_graph.set_entry_point("agent")
legal_graph.add_conditional_edges("agent", should_continue_legal,
    {"tools": "tools", "evaluate": "evaluate", "end": END})
legal_graph.add_edge("tools", "agent")
legal_graph.add_edge("evaluate", END)
```

### 6D.5 MCP Tools for Legal Agent

```python
@legal_server.tool("legal_rag_search")
async def legal_rag_search(query: str, categories: list[str] = None):
    """Search legal KB for FAR/DFARS, precedents, GAO decisions"""

@legal_server.tool("clause_library_search")
async def clause_search(clause_number: str = None, keywords: str = None,
                        risk_level: str = None):
    """Search FAR/DFARS clause library with risk analysis"""

@legal_server.tool("contract_review")
async def review_contract(contract_text: str, contract_type: str):
    """Review contract clause-by-clause with risk scoring"""

@legal_server.tool("compliance_check")
async def check_compliance(document_text: str, regulations: list[str]):
    """Check FAR/DFARS compliance"""

@legal_server.tool("loophole_detection")
async def detect_loopholes(document_text: str, document_type: str):
    """Identify legal loopholes and vulnerabilities"""

@legal_server.tool("risk_assessment")
async def assess_legal_risk(situation: str, context: str):
    """Assess legal risk with probability estimates"""

@legal_server.tool("oci_assessment")
async def assess_oci(company_profile: str, deal_details: str, team: list[str]):
    """Assess Organizational Conflict of Interest risk"""

@legal_server.tool("protest_precedent_search")
async def search_protest_precedents(grounds: str, agency: str):
    """Search GAO/COFC decisions for protest precedents"""

@legal_server.tool("web_legal_search")
async def search_legal_web(query: str):
    """Search web for recent legal developments and rule changes"""
```

### 6D.6 Legal Agent Integration Points

```
Every Stage of the Deal Pipeline:

INTAKE → RFP legal review, flag high-risk terms
BID/NO-BID (HITL) → eligibility check, legal risk score, OCI assessment
CAPTURE PLANNING → teaming agreement drafting, NDA drafting, OCI mitigation
PROPOSAL DEV → False Claims Act check, certification review, data rights
PRICING → CAS/TINA compliance, cost allowability, subcontracting plan
RED TEAM (HITL) → final legal review of entire proposal
SUBMISSION → certification sign-off, format compliance
POST-AWARD → contract review, redline, protest assessment
CONTRACT EXECUTION → compliance monitoring, modifications, claims (REA/CDA)
```

---

## 6E. Phase 4E — Teaming & Subcontractor Selection Agent

> **The strategic teaming engine.** In federal contracting, teaming decisions are make-or-break capture decisions. This agent actively identifies, evaluates, recommends, and manages teaming partners and subcontractors — optimizing for capabilities, clearances, small business goals, past performance, and competitive advantage. It goes beyond the Legal Agent (which reviews teaming agreements) and the Pricing Agent (which handles sub costs) to be the intelligent matchmaker that assembles winning teams.

### 6E.1 Teaming Data Models

```python
# backend/apps/teaming/models.py

class TeamingPartner(BaseModel):
    """Database of potential teaming partners and subcontractors."""
    company_name = models.CharField(max_length=500)
    cage_code = models.CharField(max_length=10, blank=True)
    uei = models.CharField(max_length=20, blank=True)  # SAM.gov UEI
    duns = models.CharField(max_length=15, blank=True)

    # Capabilities
    naics_codes = models.JSONField(default=list)  # NAICS codes they perform
    capabilities = models.JSONField(default=list)  # Technical capabilities
    service_areas = models.JSONField(default=list)  # Domains (cloud, AI, cyber, etc.)
    technology_stack = models.JSONField(default=list)  # Specific technologies

    # Clearances & Certifications
    facility_clearance = models.CharField(max_length=50, blank=True)  # Secret, TS, TS/SCI
    personnel_clearances = models.JSONField(default=dict)  # {TS: 15, Secret: 30, ...}
    certifications = models.JSONField(default=list)  # ISO, CMMI, FedRAMP, etc.

    # Small Business Status
    small_business_type = models.CharField(max_length=50, blank=True)  # 8(a), HUBZone, SDVOSB, WOSB, SDB, None
    is_small_business = models.BooleanField(default=False)
    sb_certifications = models.JSONField(default=list)  # Active SBA certifications
    sb_graduation_date = models.DateField(null=True, blank=True)

    # Past Performance with Us
    past_teaming_count = models.IntegerField(default=0)
    past_teaming_wins = models.IntegerField(default=0)
    reliability_score = models.FloatField(default=0.0)  # 0-100 based on delivery history
    last_teamed_date = models.DateField(null=True, blank=True)

    # Contract Vehicles
    contract_vehicles = models.JSONField(default=list)  # GSA MAS, STARS III, OASIS+, etc.

    # Financial
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    employee_count = models.IntegerField(null=True)
    typical_rate_range = models.JSONField(default=dict)  # {role: [min, max]}

    # Relationship
    relationship_status = models.CharField(max_length=50)  # preferred, approved, new, blacklisted
    nda_on_file = models.BooleanField(default=False)
    nda_expiry = models.DateField(null=True, blank=True)
    primary_contact = models.JSONField(default=dict)  # {name, title, email, phone}
    notes = models.TextField(blank=True)

    # Embeddings for RAG matching
    capability_embedding = VectorField(dimensions=1536, null=True)


class TeamingRecommendation(BaseModel):
    """AI-generated teaming recommendation for a specific deal."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=50)  # prime, sub, jv, mentor_protege

    # Recommended Partners
    recommended_partners = models.JSONField(default=list)  # Ranked list with scores
    # Each entry: {partner_id, role, work_share_pct, rationale, capability_match,
    #              clearance_match, sb_value, risk_score, rate_competitiveness}

    # Team Composition
    proposed_team_structure = models.JSONField(default=dict)
    # {prime: {company, work_share, capabilities},
    #  subs: [{company, work_share, capabilities, sb_type}],
    #  key_personnel_from: {partner_id: [roles]}}

    # Small Business Analysis
    sb_goal_analysis = models.JSONField(default=dict)
    # {required_sb_pct, achieved_sb_pct, by_category: {8a: pct, HUBZone: pct, ...},
    #  compliant: bool, gap_areas: [...], recommended_additions: [...]}

    # Competitive Assessment
    team_strength_score = models.FloatField()  # 0-100
    competitive_advantage = models.TextField()
    team_weaknesses = models.TextField()
    mitigation_strategies = models.JSONField(default=list)

    # Work Share Optimization
    work_share_matrix = models.JSONField(default=dict)
    # {wbs_element: {partner: pct, rationale}}
    limitation_on_subcontracting_check = models.JSONField(default=dict)
    # {rule, threshold_pct, current_pct, compliant, corrective_action}

    status = models.CharField(max_length=20, default='draft')  # draft, reviewed, approved


class TeamingAgreement(BaseModel):
    """Tracks teaming agreements, NDAs, and LOIs between parties."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE, null=True)
    partner = models.ForeignKey(TeamingPartner, on_delete=models.CASCADE)
    agreement_type = models.CharField(max_length=50)  # nda, loi, teaming_agreement, subcontract, jv_agreement
    status = models.CharField(max_length=30)  # draft, sent, negotiating, executed, expired
    effective_date = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    document = models.FileField(upload_to='teaming_agreements/')

    # Key Terms
    work_share = models.JSONField(default=dict)  # Agreed work allocation
    exclusivity = models.BooleanField(default=False)
    ip_provisions = models.TextField(blank=True)
    non_compete_scope = models.TextField(blank=True)
    flow_down_clauses = models.JSONField(default=list)

    # Legal Review Status (from Legal Agent)
    legal_review_status = models.CharField(max_length=20, default='pending')
    legal_review_notes = models.TextField(blank=True)
    legal_risk_score = models.FloatField(null=True)
```

### 6E.2 Teaming Agent Capabilities

```python
# ai_orchestrator/src/agents/teaming_agent.py

class TeamingAgent:
    """
    Autonomous Teaming & Subcontractor Selection Agent.

    Identifies, evaluates, and recommends optimal teaming arrangements for
    each deal — considering capabilities, clearances, small business goals,
    past teaming performance, contract vehicle access, and competitive positioning.
    """

    async def identify_teaming_needs(self, deal_id: str) -> TeamingNeedsAnalysis:
        """
        Analyze RFP requirements and solution architecture to identify
        what capabilities, clearances, and certifications we need from partners.

        Inputs:
        - RFP requirements (from Compliance Agent)
        - Solution architecture (from SA Agent)
        - Company capability profile
        - Small business subcontracting requirements (from Legal Agent)

        Outputs:
        - Capability gaps requiring partner support
        - Clearance requirements we cannot fill internally
        - Certification requirements (FedRAMP, CMMI, etc.)
        - Small business participation targets (by category)
        - Contract vehicle requirements
        - Key personnel gaps
        """
        ...

    async def search_and_rank_partners(self, needs: TeamingNeedsAnalysis) -> list[RankedPartner]:
        """
        Search partner database + external sources to find best matches.

        Search Strategy:
        1. Internal database (TeamingPartner records) — vector similarity on capabilities
        2. SAM.gov entity search — find registered entities with matching NAICS/capabilities
        3. FPDS historical data — who has won similar contracts
        4. Deep Research Agent — market intelligence on potential partners
        5. Past teaming history — prefer reliable partners

        Ranking Algorithm (weighted scoring):
        - Capability match (30%): How well partner capabilities fill our gaps
        - Past performance (20%): Their relevant contract wins + CPARS ratings
        - Clearance match (15%): Facility + personnel clearances available
        - Reliability (10%): Our past teaming experience with them (delivery, quality)
        - Rate competitiveness (10%): Their rates vs. budget constraints
        - Small business value (10%): SB status value toward goal compliance
        - Relationship maturity (5%): Existing NDA, past collaboration, contact quality
        """
        ...

    async def optimize_team_composition(self, deal_id: str, ranked_partners: list) -> TeamComposition:
        """
        Optimize the overall team for competitive advantage.

        Optimization Goals:
        1. Maximize capability coverage (every RFP requirement addressed)
        2. Maximize past performance relevance (combined team experience)
        3. Meet small business subcontracting goals (mandatory for large businesses)
        4. Minimize team risk (reliable partners, no conflicts)
        5. Optimize cost (competitive rates while maintaining quality)
        6. Ensure contract vehicle coverage (if vehicle-specific procurement)

        Constraints:
        - FAR limitation on subcontracting rules (51%/50% for various contract types)
        - No OCI conflicts between team members (Legal Agent validates)
        - Key personnel availability
        - Clearance availability timelines
        - Budget constraints from Pricing Agent

        Output:
        - Recommended team structure (prime + subs + roles)
        - Work share allocation (WBS element → partner mapping)
        - Key personnel assignments (partner → roles)
        - Small business participation percentage by category
        - Team capability matrix (requirement → partner mapping)
        - Risk register (per partner)
        """
        ...

    async def analyze_small_business_compliance(self, deal_id: str, team: TeamComposition) -> SBAnalysis:
        """
        Ensure team meets small business subcontracting plan requirements.

        For large business primes, federal contracts require:
        - Overall SB goal (typically 23%)
        - SDB goal (typically 5%)
        - WOSB goal (typically 5%)
        - HUBZone goal (typically 3%)
        - SDVOSB goal (typically 3%)

        Analysis:
        1. Parse RFP for specific SB goals (may differ from standard)
        2. Calculate current team SB participation by category
        3. Identify shortfalls by category
        4. Recommend additional SB partners to fill gaps
        5. Generate Individual Subcontracting Plan (ISP) data
        6. Flag mentor-protégé opportunities
        """
        ...

    async def generate_teaming_documents(self, deal_id: str, partner_id: str, doc_type: str) -> Document:
        """
        Generate teaming documents for Legal Agent review.

        Document Types:
        - NDA (Non-Disclosure Agreement): Standard mutual NDA
        - LOI (Letter of Intent): Pre-proposal commitment to team
        - Teaming Agreement: Full teaming terms (work share, IP, exclusivity, flow-downs)
        - Subcontract Template: Draft subcontract (when we're prime)
        - JV Operating Agreement: Joint venture terms (when applicable)
        - Mentor-Protégé Agreement: For SBA mentor-protégé relationships

        All documents:
        1. Generated with deal-specific terms
        2. Sent to Legal Agent for review before distribution
        3. Tracked through negotiation lifecycle
        4. Version-controlled with redline history
        """
        ...

    async def assess_teaming_risk(self, deal_id: str, team: TeamComposition) -> TeamingRiskAssessment:
        """
        Comprehensive risk assessment of the proposed team.

        Risk Categories:
        - Performance risk: Can each partner deliver their work share?
        - Financial risk: Is any partner at risk of financial instability?
        - Clearance risk: Will clearance timelines cause delays?
        - OCI risk: Any organizational conflicts? (validated by Legal Agent)
        - Dependency risk: Over-reliance on any single partner?
        - Key personnel risk: Are critical people actually available?
        - Exclusivity risk: Is any partner on a competing team?
        - Past performance risk: Any CPARs issues or protests on record?
        - Small business risk: Any SB certifications expiring during performance?

        Output: Risk matrix with likelihood × impact, mitigation for each
        """
        ...

    async def recommend_engagement_strategy(self, partner_id: str, deal_id: str) -> EngagementPlan:
        """
        Recommend how to approach and engage a potential partner.

        Engagement Plan:
        - Initial outreach approach (warm intro vs cold contact)
        - Capability briefing talking points
        - Proposed work share overview
        - NDA initiation (if no NDA on file)
        - Key personnel discussion points
        - Rate negotiation strategy (from Pricing Agent insights)
        - Timeline and milestones for teaming agreement execution
        """
        ...

    async def monitor_teaming_agreements(self) -> list[TeamingAlert]:
        """
        Ongoing monitoring of all active teaming relationships.

        Monitors:
        - NDA expiration dates (alert 60/30/7 days before)
        - Teaming agreement compliance (work share actuals vs agreed)
        - Partner SB certification changes
        - Partner capability changes (new wins, new certs)
        - Partner risk indicators (layoffs, lawsuits, financial issues)
        - Exclusivity violations (partner appearing on competing teams)
        """
        ...
```

### 6E.3 Teaming Agent Integration Points

```
OPPORTUNITY SCORING → teaming feasibility score (can we build a competitive team?)
BID/NO-BID → teaming readiness assessment (do we have partners for this?)
CAPTURE PLANNING → recommended team composition + engagement plan
SOLUTION ARCHITECTURE → partner capabilities feed into technical approach
PRICING → partner rates + work share → cost model
LEGAL → all teaming documents reviewed by Legal Agent before distribution
PROPOSAL → team qualifications section, org charts, past performance blending
SUBMISSION → ensure all teaming agreements executed before submission
POST-AWARD → transition partner work share to subcontracts
```

### 6E.4 LangGraph Teaming Graph

```python
# ai_orchestrator/src/graphs/teaming_graph.py

from langgraph.graph import StateGraph, END

class TeamingState(TypedDict):
    deal_id: str
    rfp_requirements: dict
    solution_architecture: dict
    company_capabilities: dict
    sb_requirements: dict
    teaming_needs: dict
    ranked_partners: list
    team_composition: dict
    sb_analysis: dict
    risk_assessment: dict
    documents: list
    engagement_plans: list

def build_teaming_graph():
    graph = StateGraph(TeamingState)

    graph.add_node("analyze_teaming_needs", analyze_teaming_needs)
    graph.add_node("search_rank_partners", search_rank_partners)
    graph.add_node("optimize_team", optimize_team_composition)
    graph.add_node("check_sb_compliance", analyze_sb_compliance)
    graph.add_node("assess_team_risk", assess_teaming_risk)
    graph.add_node("check_oci", request_oci_check)          # → Legal Agent
    graph.add_node("generate_documents", generate_teaming_docs)
    graph.add_node("legal_review", request_legal_review)     # → Legal Agent
    graph.add_node("plan_engagement", plan_partner_engagement)
    graph.add_node("human_review", present_team_for_approval) # HITL gate

    graph.set_entry_point("analyze_teaming_needs")
    graph.add_edge("analyze_teaming_needs", "search_rank_partners")
    graph.add_edge("search_rank_partners", "optimize_team")
    graph.add_edge("optimize_team", "check_sb_compliance")
    graph.add_edge("check_sb_compliance", "assess_team_risk")
    graph.add_edge("assess_team_risk", "check_oci")
    graph.add_conditional_edges("check_oci", oci_decision,
        {"clear": "generate_documents", "conflict": "optimize_team"})  # re-optimize if OCI
    graph.add_edge("generate_documents", "legal_review")
    graph.add_edge("legal_review", "plan_engagement")
    graph.add_edge("plan_engagement", "human_review")
    graph.add_edge("human_review", END)

    return graph.compile()
```

---

## 6F. Phase 4F — Security & Compliance Mapping Agent

> **The security controls authority.** Federal IT proposals almost always require detailed security narratives mapping specific control frameworks (NIST 800-53, 800-171, CMMC, FedRAMP, HIPAA/HITRUST) to RFP requirements. This agent goes deeper than the Solution Architect's high-level security architecture to provide control-by-control mapping, SSP narrative drafting, ATO approach narratives, and compliance evidence management. It ensures every security requirement is traceable to a specific control implementation.

### 6F.1 Security Compliance Data Models

```python
# backend/apps/security_compliance/models.py

class SecurityControlFramework(BaseModel):
    """Master repository of security control frameworks."""
    name = models.CharField(max_length=200)  # NIST 800-53, NIST 800-171, CMMC, FedRAMP, HIPAA, HITRUST
    version = models.CharField(max_length=50)  # Rev 5, v2.0, etc.
    description = models.TextField()
    source_url = models.URLField(blank=True)

    # Control hierarchy
    control_families = models.JSONField(default=list)
    # [{family_id: "AC", name: "Access Control", control_count: 25}, ...]

    total_controls = models.IntegerField()
    is_active = models.BooleanField(default=True)


class SecurityControl(BaseModel):
    """Individual security control within a framework."""
    framework = models.ForeignKey(SecurityControlFramework, on_delete=models.CASCADE)
    control_id = models.CharField(max_length=50)  # AC-1, AC-2, SC-7, etc.
    family = models.CharField(max_length=100)  # Access Control, System & Comms Protection
    title = models.CharField(max_length=500)
    description = models.TextField()
    supplemental_guidance = models.TextField(blank=True)

    # Control metadata
    priority = models.CharField(max_length=10)  # P1, P2, P3 (NIST priority)
    baseline_impact = models.JSONField(default=list)  # [Low, Moderate, High]
    control_type = models.CharField(max_length=50)  # technical, operational, management
    is_required = models.BooleanField(default=True)

    # Implementation guidance
    implementation_guidance = models.TextField(blank=True)
    assessment_objectives = models.JSONField(default=list)
    related_controls = models.JSONField(default=list)  # Cross-references

    # Embedding for RAG matching
    control_embedding = VectorField(dimensions=1536, null=True)


class SecurityControlMapping(BaseModel):
    """Maps RFP security requirements to specific controls and implementation narratives."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE)
    rfp_requirement = models.ForeignKey('rfp.RFPRequirement', on_delete=models.CASCADE)
    control = models.ForeignKey(SecurityControl, on_delete=models.CASCADE)

    # Mapping metadata
    mapping_confidence = models.FloatField()  # 0.0-1.0 confidence of mapping accuracy
    mapping_rationale = models.TextField()  # Why this control maps to this requirement

    # Implementation
    implementation_status = models.CharField(max_length=30)
    # planned, partially_implemented, implemented, inherited, not_applicable
    implementation_narrative = models.TextField(blank=True)  # SSP-style control narrative
    responsible_party = models.CharField(max_length=200, blank=True)  # Who implements
    implementation_evidence = models.JSONField(default=list)  # Evidence references

    # Assessment
    assessment_method = models.CharField(max_length=50, blank=True)  # examine, interview, test
    assessment_frequency = models.CharField(max_length=50, blank=True)  # continuous, annual, etc.


class SecurityComplianceReport(BaseModel):
    """Generated security compliance report for a deal."""
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE)
    report_type = models.CharField(max_length=50)
    # ssp_section, ato_narrative, control_matrix, fedramp_package,
    # cmmc_readiness, hipaa_mapping, security_volume_section

    framework = models.ForeignKey(SecurityControlFramework, on_delete=models.CASCADE)
    content = models.TextField()  # Generated narrative content

    # Coverage metrics
    total_applicable_controls = models.IntegerField()
    controls_mapped = models.IntegerField()
    controls_with_narratives = models.IntegerField()
    coverage_percentage = models.FloatField()

    # Gap analysis
    unmapped_requirements = models.JSONField(default=list)
    control_gaps = models.JSONField(default=list)  # Controls needed but not addressed
    risk_items = models.JSONField(default=list)  # High-risk areas requiring attention


class ComplianceEvidenceLibrary(BaseModel):
    """Reusable evidence artifacts that demonstrate control implementation."""
    control = models.ForeignKey(SecurityControl, on_delete=models.CASCADE)
    evidence_type = models.CharField(max_length=50)  # policy, procedure, screenshot, config, test_result, audit_report
    title = models.CharField(max_length=500)
    description = models.TextField()
    document = models.FileField(upload_to='compliance_evidence/', blank=True)
    is_reusable = models.BooleanField(default=True)  # Can be used across proposals
    last_validated = models.DateField(null=True)
```

### 6F.2 Security Compliance Agent Capabilities

```python
# ai_orchestrator/src/agents/security_compliance_agent.py

class SecurityComplianceAgent:
    """
    Autonomous Security & Compliance Mapping Agent.

    Performs deep control-by-control mapping of security frameworks
    to RFP requirements, drafts SSP narratives, generates ATO approach
    documentation, and ensures complete security compliance traceability
    in proposals.
    """

    async def identify_security_requirements(self, deal_id: str) -> SecurityRequirementsAnalysis:
        """
        Deep analysis of RFP to extract ALL security-related requirements.

        Scans for:
        - Explicit security requirements (Section L/M instructions)
        - Referenced frameworks (NIST, FedRAMP, CMMC, HIPAA, HITRUST)
        - Impact level (Low/Moderate/High for FISMA)
        - CMMC maturity level required
        - FedRAMP authorization requirements
        - Data handling requirements (PII, PHI, CUI, classified)
        - Facility/personnel clearance requirements
        - Specific clauses: DFARS 252.204-7012 (CUI), FAR 52.239-1 (privacy)
        - Cloud security requirements (FedRAMP, IL levels for DoD)
        - Continuous monitoring requirements
        - Supply chain risk management (SCRM)
        - Incident response requirements
        - Privacy requirements (SORN, PIA, Privacy Act)

        Output: Categorized security requirements with framework mappings
        """
        ...

    async def determine_applicable_frameworks(self, security_reqs: SecurityRequirementsAnalysis) -> list[ApplicableFramework]:
        """
        Determine which security frameworks apply and at what level.

        Logic:
        - Federal civilian → NIST 800-53 (Low/Moderate/High) + FedRAMP
        - DoD → NIST 800-171 + CMMC Level 2/3 + DFARS 7012
        - Healthcare → HIPAA Security Rule + HITRUST CSF
        - Financial → SOC 2 Type II + PCI DSS (if payment)
        - Intelligence → ICD 503 + CNSSI 1253
        - Cloud hosting → FedRAMP (Low/Moderate/High) or DoD IL2/4/5/6
        - Any CUI → NIST 800-171 minimum

        Output: Ordered list of frameworks with applicability rationale
        """
        ...

    async def map_requirements_to_controls(self, deal_id: str) -> ControlMappingResult:
        """
        Core mapping engine: RFP requirement → security control(s).

        Process:
        1. For each security requirement, identify matching controls via:
           - Semantic similarity (RAG search on control descriptions)
           - Keyword matching (control IDs referenced in RFP)
           - Framework baseline lookup (all controls at the required impact level)
        2. Score mapping confidence (0.0-1.0)
        3. Identify many-to-many relationships (one requirement → multiple controls)
        4. Flag unmapped requirements (gaps)
        5. Identify overlapping controls across frameworks (cross-walk)

        Output: Complete requirement-to-control mapping matrix with confidence scores
        """
        ...

    async def draft_control_narratives(self, deal_id: str, control_id: str) -> ControlNarrative:
        """
        Draft SSP-style implementation narrative for a specific control.

        Narrative Structure (per NIST SP 800-18):
        - Control description (what the control requires)
        - Implementation status (implemented/partially/planned/inherited/N/A)
        - Implementation description (HOW we implement this control)
           - Uses SA Agent's solution architecture for technical specifics
           - References specific technologies, configurations, processes
        - Responsible role/organization
        - How inherited controls are provided (if cloud/shared services)
        - Evidence references (policies, procedures, configurations)
        - Assessment method and frequency

        For proposal use:
        - Adapts language for evaluator audience (not auditor)
        - Weaves in win themes and discriminators
        - References past performance on similar security implementations
        - Highlights innovation (zero trust, AI-powered monitoring, etc.)
        """
        ...

    async def generate_ssp_sections(self, deal_id: str) -> SSPDocument:
        """
        Generate System Security Plan sections for the proposal.

        SSP Sections:
        1. System Identification and Overview
        2. System Environment and Boundary
        3. System Interconnections
        4. Security Control Implementation Details (all applicable controls)
        5. Continuous Monitoring Strategy
        6. POA&M (Plan of Action & Milestones) approach
        7. Incident Response Plan summary
        8. Configuration Management approach
        9. Contingency Plan summary
        10. Access Control narrative

        Pulls from:
        - SA Agent's system architecture (boundary diagrams, data flows)
        - Solution architecture details (technologies, configurations)
        - Company's existing compliance evidence library
        - Past SSPs from winning proposals (Knowledge Vault)
        """
        ...

    async def generate_ato_approach(self, deal_id: str) -> ATOApproachDocument:
        """
        Draft the Authority to Operate (ATO) approach narrative.

        Includes:
        - ATO strategy (full ATO vs ongoing authorization vs reciprocity)
        - FedRAMP authorization path (if applicable)
        - ISSO/ISSM staffing plan
        - Security assessment timeline and milestones
        - POA&M management approach
        - Continuous monitoring plan (ConMon)
        - Tools and automation (vulnerability scanning, SIEM, SOAR)
        - Security documentation deliverables schedule
        - Relationship with agency AO and ISSO
        """
        ...

    async def generate_cmmc_readiness(self, deal_id: str, level: int) -> CMMCReadinessReport:
        """
        Assess and document CMMC readiness.

        CMMC Level 2 (110 practices from NIST 800-171):
        - Map all 110 practices to implementation status
        - Identify gaps requiring remediation
        - Draft SSP for CUI handling
        - POA&M for any gaps
        - Timeline to achieve certification

        CMMC Level 3 (additional 24 enhanced security requirements):
        - Additional controls assessment
        - DIBCAC assessment preparation
        """
        ...

    async def cross_walk_frameworks(self, frameworks: list[str]) -> CrossWalkMatrix:
        """
        Generate cross-walk matrix between multiple frameworks.

        When an RFP requires compliance with multiple frameworks (e.g.,
        NIST 800-53 + FedRAMP + HIPAA), many controls overlap.

        Cross-walk shows:
        - NIST 800-53 AC-2 ↔ FedRAMP AC-2 ↔ HIPAA §164.312(a)(1)
        - One implementation narrative satisfying multiple frameworks
        - Gaps unique to each framework
        - Efficiency: "implementing X controls satisfies Y across all frameworks"
        """
        ...

    async def assess_compliance_gaps(self, deal_id: str) -> ComplianceGapAnalysis:
        """
        Identify security compliance gaps in our proposed solution.

        Analysis:
        - Controls required but not addressed in solution architecture
        - Controls we claim to implement but lack evidence for
        - Inherited controls requiring provider documentation (AWS, Azure)
        - POA&M candidates (controls we'll implement post-award)
        - Risk ratings for each gap (Low/Moderate/High)
        - Recommended remediation for each gap
        - Cost/timeline estimates for remediation

        Feeds back to SA Agent for solution refinement.
        """
        ...

    async def generate_security_volume_section(self, deal_id: str) -> ProposalSection:
        """
        Generate the complete security section for the proposal.

        Sections:
        1. Security Approach Overview (executive summary)
        2. Security Architecture (references SA diagrams)
        3. Compliance Framework Mapping (matrix + narratives)
        4. Access Control & Identity Management
        5. Data Protection & Encryption
        6. Network Security & Boundary Protection
        7. Continuous Monitoring & Incident Response
        8. Supply Chain Risk Management
        9. Security Staffing (ISSO, Security Engineers)
        10. ATO Approach & Timeline
        11. Security Innovation (zero trust, AI-powered security, etc.)

        Each section:
        - Maps to specific evaluation criteria
        - References specific controls being implemented
        - Includes win themes from Marketing Agent
        - References relevant past performance
        """
        ...

    async def validate_security_claims(self, deal_id: str) -> ValidationReport:
        """
        Self-validate all security claims in the proposal.

        Checks:
        - Every security requirement has a mapped control ✓/✗
        - Every control has an implementation narrative ✓/✗
        - Implementation narratives are consistent with SA architecture ✓/✗
        - No contradictions between security sections ✓/✗
        - Evidence library covers claimed implementations ✓/✗
        - Clearance levels match what's proposed ✓/✗
        - Cloud security posture matches FedRAMP/IL requirements ✓/✗
        - All compliance matrices are complete ✓/✗
        """
        ...
```

### 6F.3 Security Knowledge Base (RAG-Indexed)

```
Pre-loaded and continuously updated:

FRAMEWORKS (Full Text, Chunked + Embedded):
├── NIST SP 800-53 Rev 5 (1,189 controls across 20 families)
├── NIST SP 800-171 Rev 2/3 (110 CUI security requirements)
├── FedRAMP Security Assessment Framework (baselines: Low/Moderate/High)
├── CMMC v2.0 Model (Levels 1-3, practices + assessment objectives)
├── HIPAA Security Rule (§164.302-318, administrative/physical/technical safeguards)
├── HITRUST CSF (14 control categories)
├── SOC 2 Trust Service Criteria
├── PCI DSS v4.0
├── ICD 503 / CNSSI 1253 (IC systems)
└── NIST Cybersecurity Framework (CSF) v2.0

CROSS-WALKS:
├── NIST 800-53 ↔ FedRAMP ↔ 800-171 ↔ CMMC
├── NIST 800-53 ↔ HIPAA ↔ HITRUST
├── NIST CSF ↔ 800-53 ↔ ISO 27001
└── FedRAMP ↔ DoD IL2/4/5/6

TEMPLATES:
├── SSP templates (by impact level)
├── POA&M templates
├── ATO package templates
├── Control narrative templates (per control family)
├── Continuous monitoring plan templates
├── Incident response plan templates
└── Configuration management plan templates

EVIDENCE LIBRARY:
├── Company security policies (reusable across proposals)
├── Past security implementation evidence
├── Tool configurations (SIEM, scanning, endpoint)
└── Past winning security narratives
```

### 6F.4 LangGraph Security Compliance Graph

```python
# ai_orchestrator/src/graphs/security_compliance_graph.py

from langgraph.graph import StateGraph, END

class SecurityComplianceState(TypedDict):
    deal_id: str
    rfp_requirements: list
    solution_architecture: dict
    security_requirements: dict
    applicable_frameworks: list
    control_mappings: list
    control_narratives: list
    ssp_sections: dict
    ato_approach: dict
    gap_analysis: dict
    security_volume: dict
    validation_report: dict

def build_security_compliance_graph():
    graph = StateGraph(SecurityComplianceState)

    graph.add_node("identify_security_reqs", identify_security_requirements)
    graph.add_node("determine_frameworks", determine_applicable_frameworks)
    graph.add_node("map_controls", map_requirements_to_controls)
    graph.add_node("draft_narratives", draft_control_narratives)
    graph.add_node("cross_walk", cross_walk_frameworks)
    graph.add_node("assess_gaps", assess_compliance_gaps)
    graph.add_node("generate_ssp", generate_ssp_sections)
    graph.add_node("generate_ato", generate_ato_approach)
    graph.add_node("generate_security_volume", generate_security_volume_section)
    graph.add_node("validate_claims", validate_security_claims)
    graph.add_node("refine_solution", feedback_to_sa_agent)  # → SA Agent for gap fixes

    graph.set_entry_point("identify_security_reqs")
    graph.add_edge("identify_security_reqs", "determine_frameworks")
    graph.add_edge("determine_frameworks", "map_controls")
    graph.add_edge("map_controls", "draft_narratives")
    graph.add_edge("draft_narratives", "cross_walk")
    graph.add_edge("cross_walk", "assess_gaps")
    graph.add_conditional_edges("assess_gaps", has_critical_gaps,
        {"critical_gaps": "refine_solution", "acceptable": "generate_ssp"})
    graph.add_edge("refine_solution", "map_controls")  # Re-map after SA updates
    graph.add_edge("generate_ssp", "generate_ato")
    graph.add_edge("generate_ato", "generate_security_volume")
    graph.add_edge("generate_security_volume", "validate_claims")
    graph.add_conditional_edges("validate_claims", validation_decision,
        {"pass": END, "issues": "draft_narratives"})  # Refine narratives if issues

    return graph.compile()
```

### 6F.5 Security Compliance Agent Integration Points

```
RFP PARSING → security requirements extracted and classified
SOLUTION ARCHITECT → provides system architecture; receives gap feedback for refinement
LEGAL AGENT → FAR/DFARS security clauses (DFARS 7012, FAR 52.239-1) fed into control mapping
TEAMING AGENT → partner clearance levels + shared responsibility model
PRICING AGENT → security staffing (ISSO, engineers) and tools factored into cost model
PROPOSAL WRITER → security volume section ready for inclusion
COMPLIANCE AGENT → security compliance items merged into master compliance matrix
PAST PERFORMANCE → security-relevant past performance for narrative support
KNOWLEDGE VAULT → past SSPs, security narratives, evidence artifacts
```

---

## 7. Phase 5 — Past Performance Vault

### 7.1 Past Performance Data Model

```python
class PastPerformance(models.Model):
    project_name = models.CharField(max_length=255)
    contract_number = models.CharField(max_length=100)
    client_agency = models.CharField(max_length=255)
    client_poc = models.JSONField(default=dict)  # name, title, phone, email
    period_of_performance = models.JSONField()     # start, end
    contract_value = models.DecimalField(max_digits=15, decimal_places=2)
    contract_type = models.CharField(max_length=50)  # FFP, T&M, CPFF, etc.

    # Categorization for matching
    naics_codes = models.JSONField(default=list)
    psc_codes = models.JSONField(default=list)
    technology_areas = models.JSONField(default=list)  # AI/ML, Cloud, Cyber, etc.
    domains = models.JSONField(default=list)            # Healthcare, Defense, etc.

    # Performance metrics
    schedule_rating = models.CharField(max_length=20)   # Exceptional, Very Good, etc.
    cost_rating = models.CharField(max_length=20)
    quality_rating = models.CharField(max_length=20)
    management_rating = models.CharField(max_length=20)

    # Narrative (for proposal reuse)
    description = models.TextField()
    relevance_narrative = models.TextField()
    key_accomplishments = models.JSONField(default=list)
    lessons_learned = models.JSONField(default=list)

    # Vector embedding for RAG retrieval
    embedding = VectorField(dimensions=1536)
```

### 7.2 RAG-Powered Past Performance Matching

- When an opportunity is qualified, the AI:
  1. Embeds the RFP requirements
  2. Searches past performance vault by vector similarity
  3. Ranks by relevance + recency + rating quality
  4. Generates justification narratives
  5. Auto-populates past performance volume draft

---

## 8. Phase 6 — Proposal Authoring Studio

### 8.1 Professional Proposal Templates

| Volume | Sections |
|--------|----------|
| **Volume I: Technical** | Executive Summary, Understanding of Requirements, Technical Approach, AI/ML Solution Architecture, Innovation, Risk Mitigation |
| **Volume II: Management** | Management Approach, Organizational Chart, Key Personnel, Staffing Plan, Quality Assurance, Transition Plan |
| **Volume III: Past Performance** | Relevant Experience (3-5 projects), Performance Metrics, Client References |
| **Volume IV: Pricing** | Price Summary, Basis of Estimate, Rate Schedule, Cost Narrative |
| **Volume V: Administrative** | Compliance Matrix, Certifications, Required Forms, Representations |

### 8.2 AI Section Generation

For each section, the AI:
1. Reads RFP requirements (from compliance matrix)
2. Retrieves relevant past performance & knowledge (RAG)
3. Applies company capability statement context
4. Generates section draft with proper formatting
5. Includes win themes & discriminators
6. Flags areas needing human input
7. Generates architectural diagrams descriptions (for solution sections)

### 8.3 Fully Autonomous AI Solutions Architect

> **This is the crown jewel of the platform.** A multimodal, RAG-powered, fully autonomous Solutions Architect agent that can produce complete, professional, real-world technical solutions for any proposal or RFP. It uses YOUR knowledge base — your reference architectures, best practices, technical documents, images, diagrams, and design patterns — combined with generative AI to produce proposal-ready technical volumes.

#### 8.3.1 Multimodal Knowledge Vault

The SA agent is powered by a comprehensive knowledge vault that you populate with everything your solutions team knows:

```python
class KnowledgeVault(models.Model):
    """
    Central multimodal knowledge repository.
    Upload EVERYTHING: reference architectures, whitepapers, technical docs,
    architecture diagrams (images), design patterns, best practices,
    framework comparisons, security standards, compliance guides, etc.
    """
    title = models.CharField(max_length=500)
    category = models.CharField(choices=[
        ('reference_architecture', 'Reference Architecture'),
        ('design_pattern', 'Design Pattern'),
        ('best_practice', 'Best Practice / Standard'),
        ('technical_whitepaper', 'Technical Whitepaper'),
        ('framework_guide', 'Framework / Library Guide'),
        ('architecture_diagram', 'Architecture Diagram (Image)'),
        ('solution_template', 'Solution Template'),
        ('security_standard', 'Security Standard / Framework'),
        ('compliance_guide', 'Compliance / Regulatory Guide'),
        ('case_study', 'Case Study / Lessons Learned'),
        ('technology_comparison', 'Technology Comparison'),
        ('infrastructure_pattern', 'Infrastructure / Cloud Pattern'),
        ('ai_ml_pattern', 'AI/ML Architecture Pattern'),
        ('agentic_pattern', 'Agentic AI Design Pattern'),
        ('integration_pattern', 'Integration / API Pattern'),
        ('data_architecture', 'Data Architecture Pattern'),
        ('devops_pattern', 'DevOps / CI-CD Pattern'),
        ('pricing_reference', 'Pricing / Estimation Reference'),
        ('proposal_example', 'Past Winning Proposal Section'),
        ('other', 'Other Knowledge Document'),
    ])

    # Content — supports multimodal
    content_type = models.CharField(choices=[
        ('document', 'Document (PDF/DOCX/MD)'),
        ('image', 'Image (PNG/JPG/SVG/Visio)'),
        ('diagram', 'Architecture Diagram'),
        ('spreadsheet', 'Spreadsheet (Excel/CSV)'),
        ('presentation', 'Presentation (PPTX)'),
        ('code', 'Code Sample / Repository'),
        ('url', 'External URL / Reference'),
    ])
    file = models.FileField(upload_to='knowledge_vault/', null=True)
    raw_text = models.TextField(blank=True)                 # Extracted text
    image_description = models.TextField(blank=True)        # AI-generated description of images/diagrams

    # Metadata
    technology_tags = models.JSONField(default=list)        # ["LangGraph", "Kubernetes", "RAG"]
    domain_tags = models.JSONField(default=list)            # ["Healthcare", "Defense", "Finance"]
    applicable_naics = models.JSONField(default=list)
    author = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=500, blank=True)
    date_created = models.DateField(null=True)
    quality_score = models.FloatField(default=0.0)          # Usage-weighted quality
    usage_count = models.IntegerField(default=0)            # How often retrieved

    # Vector embeddings (multiple per document for chunked retrieval)
    # Stored in KnowledgeChunk model below

class KnowledgeChunk(models.Model):
    """
    Chunked + embedded pieces of knowledge vault items.
    Supports text AND image embeddings for multimodal RAG.
    """
    vault_item = models.ForeignKey(KnowledgeVault, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    chunk_type = models.CharField(choices=[
        ('text', 'Text Chunk'),
        ('image', 'Image / Diagram'),
        ('table', 'Table / Structured Data'),
        ('code', 'Code Block'),
    ])
    content = models.TextField()                            # Text content or image description
    image_file = models.FileField(null=True, blank=True)    # Original image if chunk_type=image
    embedding = VectorField(dimensions=1536)                # Text embedding (OpenAI/Anthropic)
    image_embedding = VectorField(dimensions=512, null=True) # CLIP embedding for images
    metadata = models.JSONField(default=dict)               # Section headers, page numbers, etc.
```

#### 8.3.2 Solutioning Frameworks Library

The SA agent uses established architecture frameworks and solutioning methodologies:

```python
SOLUTIONING_FRAMEWORKS = {
    # ── Enterprise Architecture Frameworks ─────────────────
    "togaf": {
        "name": "TOGAF Architecture Development Method",
        "phases": ["Architecture Vision", "Business Architecture",
                   "Information Systems Architecture", "Technology Architecture",
                   "Opportunities & Solutions", "Migration Planning"],
        "artifacts": ["Architecture Building Blocks", "Solution Building Blocks",
                      "Architecture Roadmap", "Transition Architectures"],
    },
    "zachman": {
        "name": "Zachman Framework",
        "dimensions": ["What (Data)", "How (Function)", "Where (Network)",
                       "Who (People)", "When (Time)", "Why (Motivation)"],
        "perspectives": ["Executive", "Business Mgmt", "Architect",
                         "Engineer", "Technician", "Enterprise"],
    },

    # ── Solution Architecture Patterns ─────────────────────
    "c4_model": {
        "name": "C4 Model (Context, Container, Component, Code)",
        "levels": [
            "L1: System Context — shows system boundaries + external actors",
            "L2: Container — shows major deployable units (APIs, DBs, UIs)",
            "L3: Component — shows internal structure of each container",
            "L4: Code — class/module level (only for critical sections)",
        ],
    },
    "arc42": {
        "name": "arc42 Architecture Documentation",
        "sections": ["Introduction & Goals", "Constraints", "Context & Scope",
                     "Solution Strategy", "Building Block View", "Runtime View",
                     "Deployment View", "Crosscutting Concepts", "Architecture Decisions",
                     "Quality Requirements", "Risks & Technical Debt"],
    },

    # ── Cloud Well-Architected Frameworks ──────────────────
    "aws_well_architected": {
        "pillars": ["Operational Excellence", "Security", "Reliability",
                    "Performance Efficiency", "Cost Optimization", "Sustainability"],
    },
    "azure_well_architected": {
        "pillars": ["Reliability", "Security", "Cost Optimization",
                    "Operational Excellence", "Performance Efficiency"],
    },

    # ── AI/ML Specific Patterns ────────────────────────────
    "ml_ops": {
        "name": "MLOps Maturity Model",
        "levels": ["L0: No MLOps", "L1: DevOps only", "L2: ML Training Pipeline",
                   "L3: ML Deployment Pipeline", "L4: Full MLOps Automation"],
        "components": ["Data Pipeline", "Feature Store", "Model Training",
                       "Model Registry", "Model Serving", "Monitoring", "Retraining"],
    },
    "agentic_ai_patterns": {
        "name": "Agentic AI Architecture Patterns",
        "patterns": [
            "Single Agent + Tools (ReAct)",
            "Multi-Agent Orchestration (LangGraph)",
            "Hierarchical Agent Teams (Supervisor + Workers)",
            "Agent-to-Agent Protocol (A2A)",
            "Human-in-the-Loop Interrupts",
            "Reflection / Self-Critique Loops",
            "Planning Agent (Plan-and-Execute)",
            "RAG Agent (Retrieve-Augment-Generate)",
            "Code Generation Agent",
            "Multi-Modal Agent (Vision + Text + Code)",
            "Tool-Use Agent (MCP Servers)",
            "Memory-Augmented Agent (Short + Long Term)",
        ],
    },
    "rag_patterns": {
        "name": "RAG Architecture Patterns",
        "patterns": [
            "Naive RAG (embed → retrieve → generate)",
            "Advanced RAG (query rewriting, HyDE, reranking)",
            "Modular RAG (plug-and-play components)",
            "Graph RAG (knowledge graph + vector search)",
            "Agentic RAG (agent decides when/what to retrieve)",
            "Multi-Modal RAG (text + image + table retrieval)",
            "Corrective RAG (CRAG — self-correcting retrieval)",
            "Self-RAG (retrieval-augmented with self-reflection)",
        ],
    },

    # ── Integration Patterns ───────────────────────────────
    "integration_patterns": {
        "patterns": ["API Gateway", "Event-Driven (Pub/Sub)", "CQRS",
                     "Saga Pattern", "Circuit Breaker", "Sidecar",
                     "Service Mesh", "BFF (Backend for Frontend)"],
    },

    # ── Security Frameworks ────────────────────────────────
    "security_frameworks": {
        "patterns": ["Zero Trust Architecture", "NIST 800-53",
                     "FedRAMP", "FISMA", "CMMC", "SOC 2",
                     "Defense in Depth", "Least Privilege"],
    },
}
```

#### 8.3.3 Solution Architect Agent — Full Design

```python
class SolutionArchitectAgent:
    """
    FULLY AUTONOMOUS AI Solutions Architect.

    Given an RFP/opportunity, this agent produces a COMPLETE technical solution
    including architecture, diagrams, technology recommendations, integration
    design, security approach, staffing, and risk mitigation — all drawn from
    YOUR multimodal knowledge vault + generative AI.

    This is NOT a summarizer. It is a real solution architect that:
    1. Analyzes requirements deeply (functional, non-functional, constraints)
    2. Retrieves relevant knowledge (reference architectures, patterns, past solutions)
    3. Synthesizes a novel solution tailored to the specific RFP
    4. Generates actual architecture diagrams (using Mermaid/D2/PlantUML + images)
    5. Produces full technical volume sections ready for proposal insertion
    """

    # ── Phase 1: Requirement Deep Dive ─────────────────────
    def analyze_requirements(self, rfp_requirements, compliance_matrix) -> RequirementAnalysis:
        """
        Deep analysis of ALL RFP requirements:
        - Functional requirements (what the system must do)
        - Non-functional requirements (performance, scalability, availability, security)
        - Technical constraints (language, platform, certifications, clearances)
        - Integration requirements (existing systems, APIs, data sources)
        - Data requirements (volumes, sensitivity, retention)
        - AI/ML specific requirements (model accuracy, explainability, bias)
        - Compliance requirements (FedRAMP, FISMA, 508, NIST, CMMC)
        - Delivery constraints (timeline, phasing, milestones)

        Outputs a structured RequirementAnalysis with:
        - Categorized requirements
        - Complexity assessment per area
        - Risk flags (conflicting requirements, impossible constraints)
        - Key design decisions that need to be made
        """

    # ── Phase 2: Knowledge Retrieval (Multimodal RAG) ──────
    def retrieve_relevant_knowledge(self, requirement_analysis) -> KnowledgeBundle:
        """
        Multimodal RAG retrieval from your Knowledge Vault:

        1. Text retrieval:
           - Query: each requirement cluster → vector search → top-k chunks
           - Reranking: cross-encoder reranking for precision
           - Sources: reference architectures, best practices, past solutions

        2. Image/Diagram retrieval:
           - Query: requirement descriptions → CLIP embeddings → similar diagrams
           - Returns: relevant architecture diagrams, infrastructure patterns
           - AI describes each image for context injection

        3. Code/Template retrieval:
           - Query: technology stack requirements → matching code samples
           - Returns: implementation patterns, config templates

        4. Past Solution retrieval:
           - Query: similar past winning proposals' technical sections
           - Returns: proven solution approaches from your vault

        Returns KnowledgeBundle with all retrieved artifacts organized by topic.
        """

    # ── Phase 3: Solution Synthesis ────────────────────────
    def synthesize_solution(self, requirements, knowledge, strategy_context) -> TechnicalSolution:
        """
        The core solutioning engine. Uses retrieved knowledge + generative AI
        to produce a NOVEL, TAILORED solution.

        Uses selected solutioning frameworks (C4, TOGAF, arc42, etc.) based
        on the RFP's expectations and evaluation criteria.

        Generates:
        1. Solution Overview & Vision
        2. Architecture Approach (which framework, which patterns)
        3. System Context (C4 L1 — external actors, system boundaries)
        4. Container Architecture (C4 L2 — services, databases, APIs)
        5. Component Design (C4 L3 — internal structure of key containers)
        6. Technology Stack Selection (with justification per choice)
        7. Data Architecture (data flow, storage, ETL, analytics)
        8. AI/ML Architecture (if applicable — models, training, serving)
        9. Agentic Architecture (if applicable — agents, tools, orchestration)
        10. Integration Architecture (APIs, events, external systems)
        11. Security Architecture (Zero Trust, encryption, IAM, compliance)
        12. Infrastructure & Deployment (cloud, containers, CI/CD)
        13. Scalability & Performance Design
        14. Disaster Recovery & Business Continuity
        15. Migration & Transition Plan (if replacing existing system)
        16. Innovation Elements (differentiators, novel approaches)
        17. Risk Register with Mitigations
        """

    # ── Phase 4: Diagram Generation ────────────────────────
    def generate_diagrams(self, solution) -> list[ArchitectureDiagram]:
        """
        Generates ACTUAL architecture diagrams — not just descriptions.

        Methods (in priority order):
        1. Mermaid.js diagrams (rendered to SVG/PNG)
           - System context, container, sequence, flowcharts
        2. D2 diagrams (for more complex architectural views)
           - Infrastructure, network, deployment views
        3. PlantUML (for UML-specific needs)
           - Component, class, activity, state diagrams
        4. AI Image Generation (for custom visuals)
           - Generates prompt → renders via image model
           - For high-level conceptual diagrams
        5. Template-based (from Knowledge Vault)
           - Retrieves similar diagrams from vault
           - Modifies/annotates for current solution

        Standard diagram set per proposal:
        ┌─────────────────────────────────────────────────────────┐
        │ 1.  Solution Overview Diagram (conceptual)             │
        │ 2.  System Context Diagram (C4 L1)                     │
        │ 3.  Container Architecture Diagram (C4 L2)             │
        │ 4.  Component Diagrams (C4 L3, for 2-3 key services)   │
        │ 5.  Data Flow Diagram                                  │
        │ 6.  AI/ML Pipeline Architecture (if applicable)        │
        │ 7.  Agentic System Architecture (if applicable)        │
        │ 8.  Security Architecture Diagram                      │
        │ 9.  Infrastructure / Deployment Diagram                │
        │ 10. Integration / API Architecture Diagram             │
        │ 11. Network Topology Diagram                           │
        │ 12. CI/CD Pipeline Diagram                             │
        │ 13. Disaster Recovery Architecture                     │
        │ 14. Migration/Transition Roadmap                       │
        └─────────────────────────────────────────────────────────┘
        """

    # ── Phase 5: Technical Volume Generation ───────────────
    def generate_technical_volume(self, solution, diagrams, rfp_format) -> TechnicalVolume:
        """
        Produces the COMPLETE Technical Volume (Volume I) for the proposal.

        Adapts to RFP-specified format (Section L/M instructions) while
        ensuring every requirement is addressed.

        Each section includes:
        - Professional narrative (proposal-ready language)
        - Relevant diagrams (embedded in correct locations)
        - Requirement traceability (maps to compliance matrix)
        - Win themes woven throughout
        - Discriminators highlighted
        - Past performance references where relevant

        Sections generated:
        1.  Executive Technical Summary
        2.  Understanding of Requirements (paraphrased, shows deep understanding)
        3.  Technical Approach & Methodology
        4.  System Architecture & Design
        5.  AI/ML Solution (models, training, inference, monitoring)
        6.  Agentic AI Design (agents, orchestration, HITL, safety)
        7.  Data Management & Analytics
        8.  Integration Strategy
        9.  Security & Compliance Approach
        10. Infrastructure & Cloud Strategy
        11. DevOps & Continuous Delivery
        12. Scalability & Performance Engineering
        13. Innovation & Emerging Technology
        14. Risk Identification & Mitigation
        15. Technology Roadmap & Future Enhancements
        """

    # ── Phase 6: Solution Validation ───────────────────────
    def validate_solution(self, solution, requirements) -> ValidationReport:
        """
        Self-critique loop: validates the generated solution against:
        1. Every RFP requirement (are they all addressed?)
        2. Evaluation criteria (are high-weight items emphasized?)
        3. Technical feasibility (are the claims realistic?)
        4. Consistency (do diagrams match narrative?)
        5. Compliance (does it meet all regulatory requirements?)
        6. Competitiveness (does it include strong differentiators?)
        7. Cost alignment (can this be built within budget?)

        Returns ValidationReport with issues + auto-fixes.
        """
```

#### 8.3.4 Solution Architect LangGraph

```python
class SolutionArchitectState(TypedDict):
    rfp_requirements: list
    compliance_matrix: list
    company_strategy: dict
    knowledge_bundle: dict          # Retrieved from multimodal RAG
    requirement_analysis: dict
    selected_frameworks: list       # Which solutioning frameworks to use
    technical_solution: dict
    diagrams: list                  # Generated architecture diagrams
    technical_volume: dict          # Full proposal-ready volume
    validation_report: dict
    iteration_count: int            # For self-critique loops

sa_graph = StateGraph(SolutionArchitectState)

# Main flow
sa_graph.add_node("analyze_requirements", deep_requirement_analysis)
sa_graph.add_node("select_frameworks", select_solutioning_frameworks)
sa_graph.add_node("retrieve_knowledge", multimodal_rag_retrieval)
sa_graph.add_node("synthesize_solution", synthesize_technical_solution)
sa_graph.add_node("generate_diagrams", generate_architecture_diagrams)
sa_graph.add_node("generate_volume", generate_technical_volume)
sa_graph.add_node("validate", validate_and_critique)
sa_graph.add_node("refine", refine_solution)          # If validation finds issues
sa_graph.add_node("human_review", interrupt_for_review)  # HITL gate

# Edges
sa_graph.add_edge("analyze_requirements", "select_frameworks")
sa_graph.add_edge("select_frameworks", "retrieve_knowledge")
sa_graph.add_edge("retrieve_knowledge", "synthesize_solution")
sa_graph.add_edge("synthesize_solution", "generate_diagrams")
sa_graph.add_edge("generate_diagrams", "generate_volume")
sa_graph.add_edge("generate_volume", "validate")

# Conditional: if validation passes → human review; if fails → refine → re-validate
sa_graph.add_conditional_edges("validate", route_validation)
sa_graph.add_edge("refine", "generate_diagrams")  # Re-generate after refinement
sa_graph.add_edge("human_review", END)
```

#### 8.3.5 MCP Tool Servers for Solution Architect

```python
# New MCP servers specifically for the SA agent

# ── Knowledge Vault Search ─────────────────────────────────
@knowledge_server.tool("search_reference_architectures")
async def search_architectures(query: str, technology_tags: list[str],
                               domain: str, top_k: int = 10):
    """Search knowledge vault for relevant reference architectures"""

@knowledge_server.tool("search_diagrams")
async def search_diagrams(query: str, diagram_type: str, top_k: int = 5):
    """Search knowledge vault for relevant architecture diagrams (multimodal)"""

@knowledge_server.tool("search_best_practices")
async def search_practices(technology: str, context: str, top_k: int = 10):
    """Search for best practices and design patterns"""

@knowledge_server.tool("search_past_solutions")
async def search_past_solutions(requirement_summary: str, domain: str, top_k: int = 5):
    """Search past winning proposal technical sections"""

# ── Diagram Generation ─────────────────────────────────────
@diagram_server.tool("generate_mermaid_diagram")
async def gen_mermaid(diagram_type: str, components: dict, title: str) -> str:
    """Generate Mermaid.js diagram code and render to SVG/PNG"""

@diagram_server.tool("generate_d2_diagram")
async def gen_d2(diagram_spec: dict, title: str) -> str:
    """Generate D2 diagram code and render to SVG/PNG"""

@diagram_server.tool("generate_plantuml_diagram")
async def gen_plantuml(uml_type: str, spec: dict) -> str:
    """Generate PlantUML diagram and render"""

@diagram_server.tool("annotate_existing_diagram")
async def annotate(source_image_path: str, annotations: list[dict]) -> str:
    """Take an existing diagram from vault and add annotations/modifications"""

# ── Technical Writing ──────────────────────────────────────
@writing_server.tool("generate_section_with_traceability")
async def gen_section(section_name: str, content_outline: dict,
                      mapped_requirements: list[str], win_themes: list[str]):
    """Generate a proposal section with requirement traceability matrix"""

@writing_server.tool("embed_diagrams_in_docx")
async def embed_diagrams(docx_template: str, diagram_placements: list[dict]):
    """Insert generated diagrams into DOCX template at specified locations"""
```

#### 8.3.6 What YOU Upload to the Knowledge Vault

To make the SA agent truly autonomous and expert-level, you populate the Knowledge Vault with:

```
YOUR KNOWLEDGE BASE (upload all of this):
├── Reference Architectures/
│   ├── AI/ML platform architecture (your standard design)
│   ├── Agentic AI system architecture
│   ├── RAG system architecture
│   ├── Data lake/mesh architecture
│   ├── Cloud-native microservices architecture
│   ├── Zero Trust security architecture
│   ├── MLOps pipeline architecture
│   └── ... any architecture you've designed or follow
│
├── Design Patterns/
│   ├── Agentic AI patterns (LangGraph, CrewAI, AutoGen patterns)
│   ├── RAG patterns (naive, advanced, modular, graph, agentic)
│   ├── MCP tool server patterns
│   ├── A2A agent communication patterns
│   ├── HITL interrupt patterns
│   ├── Microservices patterns
│   ├── Event-driven patterns
│   └── ... all patterns you use
│
├── Best Practices/
│   ├── Your company's engineering standards
│   ├── Code review guidelines
│   ├── Security best practices
│   ├── Performance optimization guides
│   ├── Testing strategies
│   └── ... your internal standards
│
├── Architecture Diagrams (IMAGES)/
│   ├── Past solution architecture diagrams (.png, .jpg, .svg, .vsdx)
│   ├── Network topology diagrams
│   ├── Data flow diagrams
│   ├── Infrastructure diagrams
│   └── ... ALL your visual architecture assets
│
├── Technical Documents/
│   ├── Whitepapers you've written
│   ├── Technical reports
│   ├── Framework evaluations
│   ├── Technology comparison matrices
│   └── ... all technical writing
│
├── Past Winning Proposals/
│   ├── Technical volumes from won proposals (redacted if needed)
│   ├── Management approach sections
│   ├── Staffing plans
│   └── ... proven proposal content
│
├── Compliance & Standards/
│   ├── NIST 800-53 control mappings
│   ├── FedRAMP requirements
│   ├── CMMC compliance guides
│   ├── Section 508 accessibility
│   └── ... regulatory knowledge
│
└── Innovation & Research/
    ├── Emerging technology assessments
    ├── AI safety and ethics frameworks
    ├── Industry trend analyses
    └── ... forward-looking material
```

### 8.4 Fully Autonomous Management Volume Engine

> **Volume II done right.** While the Solutions Architect Agent produces best-in-class Volume I (Technical), the Management Volume (Volume II) is equally critical for evaluation scoring. This enhanced capability gives the Proposal Writer Agent the same depth for management approach — org charts, staffing plans, transition strategy, PM methodology, quality assurance, and risk management — all generated from deal context, team composition, and company methodology.

#### 8.4.1 Management Volume Capabilities

```python
# Integrated into: ai_orchestrator/src/agents/proposal_writer.py (enhanced)

class ManagementVolumeEngine:
    """
    Deep management volume generation engine integrated into the Proposal Writer Agent.
    Produces proposal-ready Volume II content with the same rigor as the SA's Volume I.
    """

    async def generate_management_approach(self, deal_id: str) -> ManagementApproach:
        """
        Generate comprehensive management approach narrative.

        Inputs:
        - RFP management requirements (from Compliance Agent)
        - Solution architecture (from SA Agent — informs management structure)
        - Team composition (from Teaming Agent — who does what)
        - Company PM methodology (from Knowledge Vault)
        - Win themes (from Marketing Agent)

        Output — Management Approach Sections:
        1. Management Philosophy & Framework
           - PM methodology (Agile, SAFe, Hybrid, PMI-aligned)
           - Governance framework (PMO structure, steering committee)
           - Communication management plan
           - Decision escalation procedures
        2. Organizational Structure & Key Personnel
           - Org chart generation (hierarchical, matrix, or hybrid)
           - Key personnel narratives (PM, Technical Lead, SMEs)
           - Roles & responsibilities matrix (RACI)
           - Succession planning
        3. Staffing Plan
           - Staffing timeline by month (ramp-up, steady state, ramp-down)
           - Labor category mix by WBS element
           - Staff augmentation approach (if applicable)
           - Recruitment & retention strategy for cleared personnel
           - On-site vs remote vs offshore distribution
        4. Transition-In Plan
           - Knowledge transfer approach (from incumbent or from scratch)
           - 30/60/90-day transition milestones
           - Risk mitigation during transition
           - Parallel operations period (if required)
           - Deliverables during transition
        5. Transition-Out Plan
           - Knowledge transfer to successor
           - Documentation and artifact handover
           - Data migration and cleanup
           - Personnel transition support
        """
        ...

    async def generate_quality_assurance_plan(self, deal_id: str) -> QAPlan:
        """
        Generate Quality Assurance & Quality Control plan.

        Includes:
        - QA philosophy and standards (ISO 9001, CMMI, etc.)
        - Quality management organization (QA lead, inspectors)
        - Quality gates and review checkpoints
        - Defect tracking and resolution process
        - Metrics and KPIs (defect density, SLA compliance, MTTR)
        - Continuous process improvement (Kaizen, Six Sigma, retrospectives)
        - Deliverable quality review process
        - Customer satisfaction measurement approach
        """
        ...

    async def generate_risk_management_plan(self, deal_id: str) -> RiskPlan:
        """
        Generate Risk Management approach for the proposal.

        Includes:
        - Risk management methodology (PMI-aligned)
        - Risk identification approach (SWOT, brainstorming, Delphi)
        - Risk assessment matrix (5x5 probability × impact)
        - Top 10 risks with mitigations (populated from deal context)
        - Risk monitoring and reporting frequency
        - Risk owner assignments
        - Risk reserve/contingency approach
        - Risk register template
        """
        ...

    async def generate_org_chart(self, deal_id: str) -> OrgChartDiagram:
        """
        Generate organizational chart diagram.

        Uses:
        - Teaming Agent team composition (prime + sub structure)
        - Key personnel assignments
        - RFP organizational requirements
        - Company standard PMO structure

        Outputs:
        - Mermaid.js org chart (rendered to SVG/PNG)
        - Interactive D2 org chart with role details
        - Color-coded by: prime/sub, clearance level, on-site/remote
        - Lines of authority and reporting relationships
        - Government interfaces (COR, CO, ISSO)
        """
        ...

    async def generate_staffing_timeline(self, deal_id: str) -> StaffingVisualization:
        """
        Generate month-by-month staffing plan visualization.

        Outputs:
        - Staffing ramp chart (FTEs by month, by role)
        - WBS-to-staffing mapping table
        - Labor category mix chart (senior/mid/junior ratio over time)
        - Prime vs sub staffing breakdown
        - Clearance pipeline timeline (if personnel need new clearances)
        - Gantt-style work schedule with staffing overlay
        """
        ...

    async def generate_wbs_chart(self, deal_id: str) -> WBSDiagram:
        """
        Generate Work Breakdown Structure diagram.

        Uses SA Agent's solution components + management tasks to produce:
        - Hierarchical WBS diagram (Mermaid/D2)
        - WBS dictionary (description of each element)
        - WBS-to-staffing mapping
        - WBS-to-deliverable mapping
        - WBS-to-schedule mapping
        """
        ...

    async def generate_schedule(self, deal_id: str) -> ScheduleDiagram:
        """
        Generate Integrated Master Schedule (IMS) / project timeline.

        Outputs:
        - Gantt chart (Mermaid.js rendered)
        - Critical path identification
        - Milestone chart
        - Phase gates and deliverable dates
        - Dependencies between WBS elements
        - Government review/approval periods
        """
        ...
```

#### 8.4.2 Management Graphics Generation

The Management Volume Engine generates the following graphics (same quality as SA's 14+ technical diagrams):

| Graphic | Tool | Description |
|---------|------|-------------|
| **Org Chart** | Mermaid/D2 | Hierarchical reporting structure with prime, subs, govt interfaces |
| **Staffing Plan** | Mermaid/D2 | Month-by-month FTE chart with ramp-up and steady state |
| **WBS Chart** | Mermaid/D2 | Work breakdown structure with 3-4 levels of decomposition |
| **IMS / Gantt** | Mermaid | Integrated master schedule with critical path and milestones |
| **RACI Matrix** | Table | Responsibility assignment matrix for key activities |
| **Risk Matrix** | D2 | 5x5 probability × impact matrix with top risks plotted |
| **Transition Timeline** | Mermaid | 30/60/90-day transition roadmap with parallel operations |
| **Communication Flow** | D2 | Governance and communication structure diagram |
| **Quality Process Flow** | Mermaid | QA/QC process with review gates and feedback loops |
| **Escalation Path** | D2 | Issue escalation and decision authority hierarchy |

### 8.5 Review Workflow

```
Writer → Pink Team → Update → Red Team → Update → Gold Team → Final → Submit
```

| Review | Purpose | Participants |
|--------|---------|-------------|
| **Pink Team** | Completeness & compliance check | Internal team |
| **Red Team** | Evaluate as if you're the government evaluator | Senior reviewers |
| **Gold Team** | Executive final review + pricing approval | Leadership |

Each review produces:
- Scored evaluation (mimics government scoring)
- Comments per section
- Must-fix items
- AI auto-incorporates feedback (with human approval)

---

## 9. Phase 7 — Intelligent Pricing & Staffing Engine (MAJOR UPGRADE)

> **Purpose:** A fully autonomous pricing agent that doesn't just calculate costs — it STRATEGIZES pricing to maximize profit while keeping prices unbeatable. It ingests the Solution Architect's output to derive accurate LOE, uses market intelligence from the Deep Research Agent for benchmarking, and applies game-theoretic optimization to find the sweet spot between maximum margin and maximum P(win).

### 9.1 Rate Card Management

```python
class RateCard(models.Model):
    labor_category = models.CharField(max_length=255)   # e.g., "Senior AI Engineer"
    gsa_equivalent = models.CharField(max_length=255, blank=True)
    dol_sca_equivalent = models.CharField(max_length=255, blank=True)  # Dept of Labor SCA mapping

    # Base rate build-up
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    base_hourly = models.DecimalField(max_digits=10, decimal_places=2)
    fringe_rate = models.FloatField()         # Fringe %
    overhead_rate = models.FloatField()       # OH %
    gna_rate = models.FloatField()            # G&A %
    profit_rate = models.FloatField()         # Fee %
    fully_loaded_rate = models.DecimalField(max_digits=10, decimal_places=2)

    # Market comparison
    market_low = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    market_median = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    market_high = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    gsa_schedule_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # Metadata
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True)
    contract_vehicle = models.CharField(max_length=100, blank=True)
    geographic_location = models.CharField(max_length=100, blank=True)  # DC, remote, etc.
    escalation_rate = models.FloatField(default=0.03)  # Annual escalation %

class ConsultantProfile(models.Model):
    """Individual consultant cost and availability for precise LOE estimation"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    labor_category = models.ForeignKey(RateCard, on_delete=models.SET_NULL, null=True)
    actual_salary = models.DecimalField(max_digits=10, decimal_places=2)
    actual_cost_rate = models.DecimalField(max_digits=10, decimal_places=2)
    bill_rate = models.DecimalField(max_digits=10, decimal_places=2)
    utilization_target = models.FloatField(default=0.85)   # Target billable %
    current_utilization = models.FloatField(default=0.0)    # Actual billable %

    # Skills & qualifications
    skills = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    clearance_level = models.CharField(max_length=50, blank=True)
    years_experience = models.IntegerField(default=0)
    resume_embedding = VectorField(dimensions=1536, null=True)

    # Availability
    available_from = models.DateField(null=True)
    committed_projects = models.JSONField(default=list)     # [{deal_id, hours_per_week, end_date}]
    max_hours_per_week = models.IntegerField(default=40)
```

### 9.2 LOE Estimation Engine (Solution-Driven)

```python
class LOEEstimationEngine:
    """
    Derives Level of Effort directly from the Solution Architect's output.
    This is what makes the pricing SMART — it doesn't guess hours,
    it CALCULATES them from the actual technical solution.
    """

    def estimate_loe_from_solution(self, technical_solution, rfp_requirements) -> LOEEstimate:
        """
        Analyzes the SA agent's solution and calculates:

        1. WORK BREAKDOWN STRUCTURE (WBS)
           - Decomposes solution into deliverable work packages
           - Each work package → tasks → subtasks
           - Maps to labor categories needed

        2. PER-TASK LOE ESTIMATION
           For each task, estimates hours using:
           - Analogous estimation (similar past projects from past perf vault)
           - Parametric estimation (complexity metrics × productivity rates)
           - Three-point estimation (optimistic, most likely, pessimistic)
           - AI assessment (LLM evaluates complexity with solutioning context)

        3. STAFFING MODEL
           - Maps tasks to specific labor categories
           - Calculates FTE requirements by month/quarter
           - Identifies key personnel requirements
           - Accounts for ramp-up/ramp-down periods
           - Includes management overhead (PM, QA, meetings)

        4. LOE CONFIDENCE SCORING
           - High confidence: similar to past projects we've done
           - Medium confidence: similar technology, different scale
           - Low confidence: novel work, padded estimates
           - Each estimate includes confidence range (±X%)

        Returns LOEEstimate with:
        - WBS with hours per task per labor category
        - Staffing plan by month
        - Total hours by labor category
        - Confidence intervals
        """

    def match_consultants_to_staffing(self, loe_estimate, available_consultants) -> StaffingPlan:
        """
        Match actual available consultants to the staffing model:
        - Skill matching (consultant skills vs task requirements)
        - Availability matching (consultant calendar vs project timeline)
        - Cost optimization (use lower-cost consultant if qualified)
        - Key personnel identification (strongest match for named positions)
        - Gap analysis (roles we need to hire or sub-contract for)
        """
```

### 9.3 Intelligent Pricing Scenario Engine

```python
class PricingScenario(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    strategy_type = models.CharField(choices=[
        ('max_profit', 'Maximum Profit (highest margin we can win at)'),
        ('competitive', 'Competitive (balance margin and win probability)'),
        ('aggressive', 'Aggressive (thin margin, maximize P(win))'),
        ('value_based', 'Value-Based (premium price justified by superior solution)'),
        ('incumbent_match', 'Incumbent Match (match estimated incumbent price)'),
        ('budget_fit', 'Budget Fit (fit within estimated government budget)'),
        ('floor', 'Floor Price (minimum viable — covers costs + minimum margin)'),
    ])

    # LOE-driven cost build-up
    wbs = models.JSONField()                                # Full work breakdown structure
    labor_mix = models.JSONField()                          # [{category, hours, rate, total, consultant_id}]
    staffing_plan_by_month = models.JSONField()             # Month-by-month FTE plan

    # Detailed cost elements
    direct_labor = models.DecimalField(max_digits=15, decimal_places=2)
    fringe = models.DecimalField(max_digits=15, decimal_places=2)
    overhead = models.DecimalField(max_digits=15, decimal_places=2)
    other_direct_costs = models.JSONField()                 # Itemized ODCs
    subcontractor_costs = models.JSONField()                # Per-sub breakdown
    travel = models.JSONField()                             # Itemized travel
    materials = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gna = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    profit_amount = models.DecimalField(max_digits=15, decimal_places=2)
    profit_rate = models.FloatField()                       # Effective fee %
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    # Price-per-unit metrics
    price_per_fte_year = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    blended_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cost_per_deliverable = models.JSONField(default=dict)

    # AI intelligence
    win_probability = models.FloatField()                   # P(win) at this price
    expected_value = models.DecimalField(max_digits=15, decimal_places=2)  # P(win) × profit
    margin_percent = models.FloatField()
    market_position = models.CharField(max_length=50)       # "Below market", "At market", "Above market"
    price_vs_competitors = models.JSONField()               # Estimated position vs each competitor
    sensitivity_analysis = models.JSONField()               # How P(win) changes with price changes
    risk_assessment = models.TextField()
    ai_recommendation = models.TextField()
    recommendation_confidence = models.FloatField()

    is_recommended = models.BooleanField(default=False)     # AI's recommended scenario
    is_selected = models.BooleanField(default=False)        # Human's selected scenario
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True)
```

### 9.4 Fully Autonomous Pricing Agent

```python
class PricingAgent:
    """
    Fully Autonomous Intelligent Pricing Agent.

    GOAL: Maximize profit while keeping prices unbeatable.
    This isn't a calculator — it's a strategic pricing brain that
    understands market dynamics, competitor behavior, and the
    government's evaluation approach.
    """

    # ── Phase 1: Market Intelligence Gathering ─────────────
    def gather_pricing_intelligence(self, deal) -> PricingIntelligence:
        """
        Uses Deep Research Agent to gather:
        1. GSA Schedule rates for relevant labor categories
        2. FPDS historical awards for similar contracts (price, winner, size)
        3. Competitor pricing patterns (from public award data)
        4. Government budget estimates (if available from agency docs)
        5. IGCE (Independent Government Cost Estimate) signals
        6. Market rate surveys (salary.com, glassdoor, Deltek)
        7. Geographic rate differentials
        8. Contract vehicle ceiling rates
        """

    # ── Phase 2: Solution-Driven LOE ───────────────────────
    def compute_solution_based_loe(self, deal, technical_solution) -> LOEEstimate:
        """
        Derives LOE from Solution Architect's output:
        - Analyzes each solution component → work packages
        - Maps work packages to labor categories + hours
        - Calculates staffing profile by month
        - Identifies key personnel requirements
        - Accounts for management overhead, meetings, QA
        - Produces three-point estimates (optimistic/likely/pessimistic)
        """

    # ── Phase 3: Cost Build-Up ─────────────────────────────
    def build_cost_model(self, loe, rate_cards, consultants) -> CostModel:
        """
        Complete cost build-up:
        - Direct labor (each person × hours × rate)
        - Fringe benefits (per-person)
        - Overhead (applied to direct labor base)
        - ODCs (software licenses, cloud costs, equipment)
        - Subcontractor costs (if teaming)
        - Travel (trips × people × per-diem)
        - Materials
        - G&A (applied to total cost input base)
        - TOTAL COST (our actual cost to perform)
        """

    # ── Phase 4: Profit Optimization (The Magic) ──────────
    def optimize_profit(self, cost_model, pricing_intelligence, competitive_analysis) -> list[PricingScenario]:
        """
        THE CORE ALGORITHM: Generates 5-7 pricing scenarios that
        find the optimal balance between profit and competitiveness.

        INPUTS:
        - Our actual cost (floor — can't go below this)
        - Market rate benchmarks (what's "normal")
        - Competitor estimated prices (from research + historical patterns)
        - Government budget signals (ceiling)
        - Evaluation method (LPTA vs Best Value vs Trade-off)
        - Technical score advantage (if our solution is stronger)

        OPTIMIZATION STRATEGIES:

        1. GAME-THEORETIC PRICING
           - Model competitors as rational agents
           - Estimate their likely price range
           - Find Nash equilibrium price point
           - Factor in our technical advantage

        2. EVALUATION-METHOD ADAPTATION
           IF LPTA (Lowest Price Technically Acceptable):
             → Price at competitive floor
             → Maximize volume and contract value
             → Minimum acceptable margin

           IF BEST VALUE (Trade-off):
             → Price higher, invest in technical superiority
             → "Slightly below competitor, much better solution"
             → Sweet spot: 5-10% below market with 20% better tech

           IF BEST VALUE (Highest Rated):
             → Price moderately, maximize technical score
             → Focus B&P investment on proposal quality
             → Government will pay more for best solution

        3. SENSITIVITY ANALYSIS
           For each scenario, compute:
           - P(win) if we're 5% cheaper → how much margin do we gain/lose?
           - P(win) if we're 5% more expensive → is the margin worth it?
           - Break-even analysis: minimum price where P(win) × margin > B&P cost
           - Monte Carlo simulation: 1000 price scenarios → P(win) distribution

        4. SCENARIO GENERATION
           Produces 5-7 named scenarios:
           ┌─────────────────────────────────────────────────────────┐
           │ Scenario          │ Margin │ P(win) │ Expected Value   │
           ├─────────────────────────────────────────────────────────┤
           │ Max Profit         │ 15%    │ 35%    │ $525K           │
           │ Value-Based        │ 12%    │ 50%    │ $600K ← OPTIMAL │
           │ Competitive        │ 10%    │ 60%    │ $540K           │
           │ Aggressive         │ 7%     │ 75%    │ $472K           │
           │ Incumbent Match    │ 8%     │ 55%    │ $396K           │
           │ Budget Fit         │ 9%     │ 65%    │ $527K           │
           │ Floor              │ 3%     │ 85%    │ $229K           │
           └─────────────────────────────────────────────────────────┘
           Recommends the scenario with highest EXPECTED VALUE
           (P(win) × profit), not just highest margin or lowest price.

        5. PROFIT MAXIMIZATION LEVERS
           The agent also suggests ways to INCREASE margin WITHOUT
           increasing price:
           - Substitute lower-cost labor where requirements allow
           - Optimize staffing ramp (don't over-staff early months)
           - Use subcontractors strategically (their OH may be lower)
           - Reduce ODCs (open-source alternatives, reuse existing tools)
           - Offshore/remote portions where allowed
           - Reuse past artifacts (reduce writing/development hours)
        """

    # ── Phase 5: Competitive Price Positioning ─────────────
    def position_against_competitors(self, scenarios, competitor_profiles) -> CompetitivePricing:
        """
        For each scenario, estimate position vs each competitor:
        - "At this price, we're likely 8% below Competitor A and 3% above Competitor B"
        - Factor in competitors' known pricing patterns
        - Factor in incumbent advantage/disadvantage
        - Flag if any scenario puts us at risk of being LPTA-excluded
        """

    # ── Phase 6: Cost Volume Generation ────────────────────
    def generate_cost_volume(self, selected_scenario) -> CostVolume:
        """
        Generate the complete Volume IV (Pricing/Cost) for the proposal:
        - Price summary table
        - Basis of Estimate (BOE) narratives per WBS element
        - Rate schedule with justification
        - Staffing plan with labor mix rationale
        - Subcontractor price summary
        - Travel estimates with justification
        - ODC breakdown and justification
        - Cost narrative explaining our pricing approach
        - Compliance with RFP pricing instructions (Section L)
        """

    # ── Phase 7: Price Defense Preparation ─────────────────
    def prepare_price_defense(self, selected_scenario) -> PriceDefense:
        """
        Prepare for potential price negotiations / audit:
        - Rate substantiation (how we derived each rate)
        - BOE backup (detailed hours justification)
        - Market rate comparisons
        - FAR compliance documentation
        - Cost realism defense (if government questions our price)
        - "Should-cost" analysis (proof our price is reasonable)
        """
```

### 9.5 LangGraph Pricing Graph

```python
class PricingGraphState(TypedDict):
    deal: dict
    technical_solution: dict            # From SA agent
    capture_strategy: dict              # From Marketing agent
    pricing_intelligence: dict          # Market rates, competitor prices
    loe_estimate: dict                  # Solution-driven LOE
    cost_model: dict                    # Full cost build-up
    scenarios: list                     # 5-7 pricing scenarios
    competitive_positioning: dict       # Price vs competitors
    sensitivity_analysis: dict          # Monte Carlo / sensitivity results
    recommended_scenario: dict          # AI's recommendation
    cost_volume: dict                   # Generated Volume IV
    price_defense: dict                 # Negotiation preparation

pricing_graph = StateGraph(PricingGraphState)
pricing_graph.add_node("gather_intelligence", gather_pricing_intelligence)
pricing_graph.add_node("compute_loe", compute_solution_based_loe)
pricing_graph.add_node("build_costs", build_cost_model)
pricing_graph.add_node("optimize_profit", optimize_profit_scenarios)
pricing_graph.add_node("position_competitively", position_against_competitors)
pricing_graph.add_node("run_sensitivity", run_monte_carlo_sensitivity)
pricing_graph.add_node("recommend", select_optimal_scenario)
pricing_graph.add_node("human_review", interrupt_for_pricing_approval)  # HITL
pricing_graph.add_node("generate_volume", generate_cost_volume)
pricing_graph.add_node("prepare_defense", prepare_price_defense)

pricing_graph.add_edge("gather_intelligence", "compute_loe")
pricing_graph.add_edge("compute_loe", "build_costs")
pricing_graph.add_edge("build_costs", "optimize_profit")
pricing_graph.add_edge("optimize_profit", "position_competitively")
pricing_graph.add_edge("position_competitively", "run_sensitivity")
pricing_graph.add_edge("run_sensitivity", "recommend")
pricing_graph.add_edge("recommend", "human_review")
pricing_graph.add_edge("human_review", "generate_volume")
pricing_graph.add_edge("generate_volume", "prepare_defense")
pricing_graph.add_edge("prepare_defense", END)
```

---

## 10. Phase 8 — Contract Management

### 10.1 Contract Templates

- Master Service Agreement (MSA)
- Statement of Work (SOW)
- Task Order
- Modification
- Non-Disclosure Agreement (NDA)
- Teaming Agreement
- Subcontractor Agreement

### 10.2 Clause Library

```python
class ContractClause(models.Model):
    title = models.CharField(max_length=255)
    clause_number = models.CharField(max_length=50)   # FAR/DFARS reference
    category = models.CharField(max_length=50)         # IP, liability, termination, etc.
    text = models.TextField()
    risk_level = models.CharField(choices=[('low','Low'),('medium','Medium'),('high','High')])
    ai_risk_notes = models.TextField(blank=True)
    requires_review = models.BooleanField(default=False)
    standard_response = models.TextField(blank=True)   # Pre-approved language
```

### 10.3 Contract Workspace

- AI drafts contract from template + deal specifics
- Clause risk scanner highlights dangerous terms
- Redline tracking with version history
- **HITL required** for all contract approvals
- Integration with e-signature (future: DocuSign API)

---

## 11. Phase 9 — AI Agent Orchestration (LangGraph + MCP + A2A)

### 11.1 Agent Architecture

```
ai_orchestrator/
├── Dockerfile
├── requirements.txt
├── src/
│   ├── main.py                    # FastAPI app for AI endpoints
│   │   ├── agents/
│   │   │   ├── orchestrator.py          # Master agent (LangGraph graph)
│   │   │   ├── strategy_agent.py        # Company AI Strategy Agent
│   │   │   ├── marketing_sales_agent.py # Marketing & Sales Expert Agent
│   │   │   ├── deep_research_agent.py   # Deep Research Agent
│   │   │   ├── legal_agent.py           # Business Legal Agent (NEW)
│   │   │   ├── teaming_agent.py        # Teaming & Subcontractor Selection Agent (NEW)
│   │   │   ├── security_compliance_agent.py # Security & Compliance Mapping Agent (NEW)
│   │   │   ├── opportunity_scout.py     # Scans & scores opportunities
│   │   │   ├── rfp_parser.py            # Extracts RFP requirements
│   │   │   ├── compliance_agent.py      # Builds compliance matrix
│   │   │   ├── past_perf_agent.py       # RAG retrieval of past performance
│   │   │   ├── solution_architect.py    # FULL Autonomous SA Agent
│   │   │   ├── proposal_writer.py       # Section-by-section authoring
│   │   │   ├── pricing_agent.py         # Intelligent Pricing Agent
│   │   │   ├── qa_agent.py              # Quality & consistency checker
│   │   │   ├── submission_agent.py      # Package & checklist builder
│   │   │   ├── contract_agent.py        # Contract drafting (uses Legal Agent)
│   │   │   ├── communication_agent.py   # Emails, Q&A tracking, clarifications, narratives (UPGRADED)
│   │   │   └── learning_agent.py        # Policy updates from outcomes
│   │   ├── mcp_servers/
│   │   │   ├── samgov_tools.py          # SAM.gov API tools
│   │   │   ├── document_tools.py        # PDF/DOCX parse, chunk, embed
│   │   │   ├── vector_search.py         # pgvector RAG search (text)
│   │   │   ├── knowledge_vault_tools.py # Multimodal knowledge vault search
│   │   │   ├── diagram_tools.py         # Mermaid/D2/PlantUML generation
│   │   │   ├── image_search_tools.py    # CLIP-based image/diagram search
│   │   │   ├── web_research_tools.py    # Web search + gov DB tools (NEW)
│   │   │   ├── competitive_intel_tools.py # FPDS/USASpending/competitor tools (NEW)
│   │   │   ├── market_rate_tools.py     # GSA rates, salary data, benchmarks
│   │   │   ├── legal_tools.py          # Legal RAG, clause library, compliance, OCI (NEW)
│   │   │   ├── teaming_tools.py       # Partner search, matching, SB analysis (NEW)
│   │   │   ├── security_compliance_tools.py # Control mapping, SSP generation, framework RAG (NEW)
│   │   │   ├── template_render.py       # DOCX/PDF/PPTX/CSV generation
│   │   │   ├── email_tools.py           # Email drafting & sending
│   │   │   ├── qa_tracking_tools.py     # Q&A log, clarification tracking, impact mapping (NEW)
│   │   │   ├── workflow_tools.py        # Stage transitions & tasks
│   │   │   └── pricing_tools.py         # Rate card, LOE calc, cost model
│   │   ├── graphs/
│   │   │   ├── daily_scan_graph.py      # Daily opportunity pipeline
│   │   │   ├── strategy_graph.py        # Strategic scoring & portfolio analysis
│   │   │   ├── marketing_graph.py       # Capture strategy & competitive positioning (NEW)
│   │   │   ├── research_graph.py        # Deep research pipeline (NEW)
│   │   │   ├── solution_arch_graph.py   # Full SA agent pipeline
│   │   │   ├── proposal_graph.py        # Full proposal generation flow
│   │   │   ├── pricing_graph.py         # Intelligent pricing optimization
│   │   │   ├── legal_graph.py          # Legal ReAct agent pipeline (NEW)
│   │   │   ├── teaming_graph.py       # Teaming selection & optimization pipeline (NEW)
│   │   │   ├── security_compliance_graph.py # Security control mapping pipeline (NEW)
│   │   │   └── contract_graph.py        # Contract generation flow (uses Legal Agent)
│   ├── rag/
│   │   ├── embeddings.py          # Embedding generation
│   │   ├── retriever.py           # Vector search + reranking
│   │   └── chunker.py             # Document chunking strategies
│   └── learning/
│       ├── reward_tracker.py      # Outcome tracking
│       ├── policy_updater.py      # Weight/threshold adjustment
│       └── bandit.py              # Contextual bandit for ranking
```

### 11.2 LangGraph Orchestration Pattern

```python
# Example: Daily Opportunity Scan Graph
from langgraph.graph import StateGraph, END

class OpportunityScanState(TypedDict):
    raw_opportunities: list
    normalized: list
    scored: list
    top_10: list
    notifications_sent: bool

graph = StateGraph(OpportunityScanState)
graph.add_node("fetch_samgov", fetch_samgov_opportunities)
graph.add_node("fetch_labs", fetch_lab_opportunities)
graph.add_node("normalize", normalize_opportunities)
graph.add_node("score", score_and_rank)
graph.add_node("publish", publish_top_10)

graph.add_edge("fetch_samgov", "normalize")
graph.add_edge("fetch_labs", "normalize")
graph.add_edge("normalize", "score")
graph.add_edge("score", "publish")
graph.add_edge("publish", END)
```

### 11.3 HITL Integration in LangGraph

```python
# Human-in-the-loop gates using LangGraph interrupts
from langgraph.checkpoint.postgres import PostgresSaver

graph.add_node("generate_proposal", generate_proposal_draft)
graph.add_node("human_review", interrupt_for_review)  # Pauses here
graph.add_node("incorporate_feedback", incorporate_feedback)
graph.add_node("finalize", finalize_proposal)

# After generate_proposal, always go to human_review
graph.add_edge("generate_proposal", "human_review")
# After human approval, proceed; after rejection, loop back
graph.add_conditional_edges("human_review", route_approval)
```

### 11.4 A2A (Agent-to-Agent) Events

```python
# Structured events for inter-agent communication
EVENTS = {
    # ── Opportunity & Strategy Events ──────────────────────
    "OpportunityIngested":       {"source": "opportunity_scout", "data": "raw opportunity"},
    "OpportunityScored":         {"source": "opportunity_scout", "data": "scored opportunity"},
    "StrategicScoreComputed":    {"source": "strategy_agent", "data": "strategic alignment score + rationale"},
    "BidRecommendationReady":    {"source": "strategy_agent", "data": "bid/no-bid recommendation"},
    "PortfolioAnalysisReady":    {"source": "strategy_agent", "data": "portfolio health report"},

    # ── Deep Research Events ───────────────────────────────
    "ResearchRequested":         {"source": "any agent", "data": "research request"},
    "ResearchInProgress":        {"source": "deep_research_agent", "data": "progress update + activity"},
    "ResearchCompleted":         {"source": "deep_research_agent", "data": "full report + deliverables"},
    "FollowUpResearchCompleted": {"source": "deep_research_agent", "data": "follow-up report"},

    # ── Marketing & Sales Events ───────────────────────────
    "AgencyIntelReady":          {"source": "marketing_sales_agent", "data": "agency profile + intel"},
    "CompetitorProfiled":        {"source": "marketing_sales_agent", "data": "competitor profile"},
    "CaptureStrategyReady":      {"source": "marketing_sales_agent", "data": "win themes + discriminators"},
    "ExecSummaryCrafted":        {"source": "marketing_sales_agent", "data": "executive summary draft"},
    "SectionMessagingReady":     {"source": "marketing_sales_agent", "data": "per-section messaging guide"},
    "PWinAssessed":              {"source": "marketing_sales_agent", "data": "probability of win"},

    # ── RFP & Compliance Events ────────────────────────────
    "RFPParsed":                 {"source": "rfp_parser", "data": "extracted requirements"},
    "ComplianceMatrixReady":     {"source": "compliance_agent", "data": "matrix items"},
    "PastPerfMatched":           {"source": "past_perf_agent", "data": "matched projects"},

    # ── Solution Architect Events ──────────────────────────
    "RequirementsAnalyzed":      {"source": "solution_architect", "data": "deep requirement analysis"},
    "KnowledgeRetrieved":        {"source": "solution_architect", "data": "multimodal knowledge bundle"},
    "SolutionSynthesized":       {"source": "solution_architect", "data": "complete technical solution"},
    "DiagramsGenerated":         {"source": "solution_architect", "data": "architecture diagrams (14+)"},
    "TechnicalVolumeReady":      {"source": "solution_architect", "data": "full Volume I draft"},
    "SolutionValidated":         {"source": "solution_architect", "data": "validation report"},

    # ── Intelligent Pricing Events ─────────────────────────
    "PricingIntelGathered":      {"source": "pricing_agent", "data": "market rates + competitor prices"},
    "LOEComputed":               {"source": "pricing_agent", "data": "solution-driven LOE estimate"},
    "CostModelBuilt":            {"source": "pricing_agent", "data": "full cost build-up"},
    "PricingScenariosReady":     {"source": "pricing_agent", "data": "5-7 optimized scenarios"},
    "PricingRecommended":        {"source": "pricing_agent", "data": "AI recommended scenario"},
    "CostVolumeGenerated":       {"source": "pricing_agent", "data": "Volume IV draft"},

    # ── Legal Agent Events (NEW) ──────────────────────────
    "RFPLegalReviewDone":        {"source": "legal_agent", "data": "RFP legal risk analysis"},
    "BidLegalRiskAssessed":      {"source": "legal_agent", "data": "bid legal risk score"},
    "ContractReviewed":          {"source": "legal_agent", "data": "clause-by-clause review"},
    "ContractDrafted":           {"source": "legal_agent", "data": "drafted contract"},
    "TeamingReviewed":           {"source": "legal_agent", "data": "teaming agreement review"},
    "OCIAssessed":               {"source": "legal_agent", "data": "OCI risk + mitigation"},
    "FARComplianceChecked":      {"source": "legal_agent", "data": "FAR/DFARS compliance report"},
    "ProposalLegalReviewDone":   {"source": "legal_agent", "data": "proposal legal sign-off"},
    "ProtestAssessed":           {"source": "legal_agent", "data": "protest viability assessment"},
    "RegulatoryAlertIssued":     {"source": "legal_agent", "data": "new FAR/DFARS rule alert"},

    # ── Teaming & Subcontractor Events (NEW) ─────────────
    "TeamingNeedsAnalyzed":      {"source": "teaming_agent", "data": "capability gaps + partner requirements"},
    "PartnersRanked":            {"source": "teaming_agent", "data": "ranked partner recommendations"},
    "TeamCompositionOptimized":  {"source": "teaming_agent", "data": "proposed team structure + work share"},
    "SBComplianceAnalyzed":      {"source": "teaming_agent", "data": "small business goal analysis"},
    "TeamingRiskAssessed":       {"source": "teaming_agent", "data": "team risk matrix + mitigations"},
    "TeamingDocGenerated":       {"source": "teaming_agent", "data": "NDA/LOI/teaming agreement draft"},
    "TeamApproved":              {"source": "human", "data": "team composition approved (HITL)"},
    "TeamingAlertRaised":        {"source": "teaming_agent", "data": "NDA expiry, partner risk, exclusivity violation"},

    # ── Security & Compliance Mapping Events (NEW) ────────
    "SecurityReqsIdentified":    {"source": "security_compliance_agent", "data": "classified security requirements"},
    "FrameworksDetermined":      {"source": "security_compliance_agent", "data": "applicable frameworks + levels"},
    "ControlsMapped":            {"source": "security_compliance_agent", "data": "requirement-to-control mapping matrix"},
    "ControlNarrativesDrafted":  {"source": "security_compliance_agent", "data": "SSP-style implementation narratives"},
    "ComplianceGapsFound":       {"source": "security_compliance_agent", "data": "gap analysis + remediation plan"},
    "SSPSectionsGenerated":      {"source": "security_compliance_agent", "data": "system security plan sections"},
    "ATOApproachReady":          {"source": "security_compliance_agent", "data": "ATO approach narrative"},
    "SecurityVolumeReady":       {"source": "security_compliance_agent", "data": "proposal security section"},
    "SecurityValidated":         {"source": "security_compliance_agent", "data": "security claims validation report"},

    # ── Q&A & Clarification Events (NEW) ──────────────────
    "ClarificationsDrafted":     {"source": "communication_agent", "data": "prioritized vendor questions for CO"},
    "ClarificationAnswered":     {"source": "communication_agent", "data": "CO answer + impact assessment"},
    "QAImpactMapped":            {"source": "communication_agent", "data": "answer → compliance/pricing changes"},

    # ── Proposal & Review Events ───────────────────────────
    "ManagementVolumeReady":     {"source": "proposal_writer", "data": "Volume II draft with org charts + staffing"},
    "SectionDrafted":            {"source": "proposal_writer", "data": "section content"},
    "QAComplete":                {"source": "qa_agent", "data": "issues found"},

    # ── Approval & Submission Events ───────────────────────
    "ApprovalRequested":         {"source": "any agent", "data": "approval request"},
    "ApprovalGranted":           {"source": "human", "data": "decision + feedback"},
    "SubmissionPackaged":        {"source": "submission_agent", "data": "package ready"},
    "OutcomeRecorded":           {"source": "learning_agent", "data": "win/loss + metrics"},
    "StrategyUpdateRecommended": {"source": "learning_agent", "data": "strategy evolution suggestions"},
}
```

### 11.5 MCP Server Pattern

```python
# Each MCP server exposes tools for agents
# Example: SAM.gov MCP Server
from mcp import Server

samgov_server = Server("samgov-tools")

@samgov_server.tool("search_opportunities")
async def search(naics: list[str], keywords: list[str], posted_from: str):
    """Search SAM.gov for matching opportunities"""
    ...

@samgov_server.tool("get_opportunity_details")
async def get_details(notice_id: str):
    """Get full details + attachments for a SAM.gov opportunity"""
    ...

@samgov_server.tool("check_amendments")
async def check_amendments(notice_id: str):
    """Check for new amendments on an opportunity"""
    ...
```

---

## 12. Phase 10 — Learning & Optimization

### 12.1 Feedback Loops

| Signal | Source | Updates |
|--------|--------|---------|
| Bid/No-Bid decisions | Human manager | Scoring model weights |
| Proposal review scores | Pink/Red team | Writing quality model |
| Win/Loss outcomes | Contract awards | All models |
| Price vs award price | FPDS data | Pricing model |
| Time-to-submit | System metrics | Process efficiency |
| Client feedback | CRM/communications | Relationship model |

### 12.2 Policy & Goal Manager

```python
class AIPolicy(models.Model):
    """Governs what the AI can do autonomously vs requiring approval"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(choices=[
        ('opportunity', 'Opportunity Scoring'),
        ('proposal', 'Proposal Generation'),
        ('pricing', 'Pricing Decisions'),
        ('submission', 'Submission Actions'),
        ('contract', 'Contract Actions'),
        ('communication', 'External Communications'),
    ])
    autonomous_allowed = models.BooleanField(default=False)
    hitl_required = models.BooleanField(default=True)
    confidence_threshold = models.FloatField(default=0.8)  # Auto-approve above this
    constraints = models.JSONField(default=dict)

class GoalSetting(models.Model):
    """Business goals that drive AI optimization"""
    name = models.CharField(max_length=100)
    metric = models.CharField(max_length=100)     # win_rate, margin, time_to_submit
    target_value = models.FloatField()
    weight = models.FloatField(default=1.0)        # Priority among goals
    direction = models.CharField(choices=[('maximize','Maximize'),('minimize','Minimize')])
```

### 12.3 Reinforcement Learning Strategy

**Safe RL approach (recommendations, not autonomous actions):**

1. **Offline RL**: Train on historical data (bid decisions, outcomes, pricing)
2. **Contextual Bandits**: For ranking and recommendation optimization
3. **Reward Engineering**:
   - `+10` for contract win
   - `+5` for shortlisted
   - `+1` for good review scores
   - `-1` for compliance defects
   - `-5` for missed deadlines
   - `-3` for significantly over/under priced
4. **Human-gated**: RL suggests, human decides; outcome updates policy

---

## 13. Data Model (Complete Entity List)

### Core System
- `User`, `Role`, `Permission`, `Organization`, `Team`
- `UserProfile` (picture, MFA, skills, clearances)
- `AuditLog`, `AITraceLog`
- `Notification`, `NotificationPreference`

### Company Strategy
- `CompanyStrategy` (living strategic plan — markets, goals, capacity, differentiators)
- `StrategicGoal` (quantified objectives with targets and deadlines)
- `PortfolioSnapshot` (periodic pipeline health vs strategy)

### Marketing & Sales Intelligence (NEW)
- `MarketIntelligence` (per-agency profile — budget, priorities, procurement patterns)
- `CompetitorProfile` (detailed competitor profiles — capabilities, pricing, wins/losses)
- `CaptureStrategy` (per-deal win themes, discriminators, ghost/counter strategies)

### Deep Research (NEW)
- `ResearchRequest` (research tasks from agents or humans)
- `ResearchReport` (completed reports with deliverables — PDF, CSV, DOCX)
- `ResearchActivity` (real-time activity feed during research)

### Business Legal (NEW)
- `LegalKnowledgeBase` (FAR/DFARS, GAO decisions, contract precedents, ethics — all RAG-indexed)
- `LegalClauseLibrary` (FAR/DFARS clauses with risk scores, negotiation guidance, flow-down flags)
- `LegalReview` (per-deal legal analysis with clause-by-clause risk scoring)
- `LegalEvaluation` (quality evaluation scores — tool correctness, task completion, coverage)
- `RegulatoryAlert` (monitored FAR/DFARS rule changes affecting active deals)

### Teaming & Subcontractors (NEW)
- `TeamingPartner` (partner database: capabilities, clearances, NAICS, SB status, reliability score, contract vehicles, rates)
- `TeamingRecommendation` (AI-recommended team composition per deal: partners, work share, SB analysis, risk)
- `TeamingAgreement` (NDA/LOI/teaming agreement tracking: status, terms, legal review, expiry)

### Security & Compliance Mapping (NEW)
- `SecurityControlFramework` (NIST 800-53, 800-171, FedRAMP, CMMC, HIPAA, HITRUST — with versions)
- `SecurityControl` (individual controls: ID, family, description, priority, baselines, implementation guidance)
- `SecurityControlMapping` (per-deal: RFP requirement → control → narrative → evidence → status)
- `SecurityComplianceReport` (generated reports: SSP sections, ATO approach, control matrix, gap analysis)
- `ComplianceEvidenceLibrary` (reusable evidence artifacts: policies, procedures, configs, test results)

### Opportunity Intelligence
- `OpportunitySource` (SAM.gov, labs, etc.)
- `Opportunity` (normalized, with embeddings)
- `OpportunityScore` (fit score + factors + explanation)
- `StrategicScore` (strategy alignment score per opportunity)
- `CompanyProfile` (UEI, CAGE, capabilities, embeddings)
- `DailyDigest` (Top 10 daily report)

### Deal Pipeline
- `Deal` (stage, owner, team, timeline)
- `DealStageHistory` (transition log)
- `Task`, `TaskTemplate`, `Checklist`
- `Approval` (type, status, rationale)
- `Comment`, `Activity`

### RFP Workspace
- `RFPDocument` (uploaded files + extracted data)
- `RFPRequirement` (extracted shall/must statements)
- `ComplianceMatrixItem` (requirement → response mapping)
- `Amendment` (version diffs)

### Past Performance
- `PastPerformance` (project + metrics + narrative + embedding)
- `PastPerformanceMatch` (opportunity → past perf relevance)

### Knowledge Vault (NEW — Multimodal RAG)
- `KnowledgeVault` (reference architectures, diagrams, patterns, best practices, images, docs)
- `KnowledgeChunk` (chunked + embedded pieces — text, image, table, code)
- `SolutioningFramework` (TOGAF, C4, arc42, well-architected, agentic patterns, RAG patterns)

### Solution Architect Outputs (NEW)
- `TechnicalSolution` (full synthesized solution per deal)
- `ArchitectureDiagram` (generated Mermaid/D2/PlantUML diagrams + rendered images)
- `RequirementAnalysis` (deep RFP requirement analysis)
- `SolutionValidationReport` (self-critique validation results)

### Proposals
- `Proposal` (deal → proposal, with version history)
- `ProposalTemplate` (volume/section structure)
- `ProposalSection` (per-section content + status)
- `ReviewCycle` (pink/red/gold team)
- `ReviewComment` (per-section feedback)

### Pricing (UPGRADED)
- `RateCard` (labor categories + rates + market benchmarks)
- `ConsultantProfile` (individual consultant cost, skills, availability)
- `LOEEstimate` (WBS-driven hours from SA agent's solution)
- `CostModel` (detailed cost build-up)
- `PricingScenario` (7 strategy types + P(win) + expected value + sensitivity)
- `PricingIntelligence` (market rates, competitor price estimates)
- `PricingApproval` (HITL gate)

### Contracts
- `Contract` (deal → contract, with status)
- `ContractTemplate` (MSA, SOW, etc.)
- `ContractClause` (library + risk levels)
- `ContractVersion` (redline history)

### Communications & Q&A Management (UPGRADED)
- `EmailDraft` (AI-generated, human-approved)
- `ClarificationQuestion` (structured Q&A: question text, category, status, RFP section ref, submitted date)
- `ClarificationAnswer` (CO answer text, received date, impact assessment, affected requirements)
- `QAImpactMapping` (links answers → ComplianceMatrixItem changes + PricingScenario assumption updates)
- `QALog` (complete Q&A audit trail: question → submission → answer → impact → action taken)
- `ClientInteraction` (log of all communications with sentiment + relationship score)
- `VendorQuestionStrategy` (AI-prioritized list of questions to ask CO, ranked by information value)

### AI System
- `AIPolicy` (autonomy rules)
- `GoalSetting` (business objectives)
- `LearningOutcome` (bid results → model updates)
- `AgentExecution` (run history + traces)

---

## 14. File/Folder Structure (Complete)

```
ai-deal-manager/
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── .gitignore
├── README.md
├── PLAN.md
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/                         # gitignored
│
├── backend/                          # Django
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/
│       ├── __init__.py
│       ├── accounts/
│       │   ├── models.py            # User, UserProfile, Role
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── permissions.py       # RBAC permission classes
│       │   ├── mfa.py               # MFA setup/verify
│       │   └── admin.py
│       ├── core/
│       │   ├── models.py            # AuditLog, BaseModel
│       │   ├── middleware.py         # Audit middleware
│       │   ├── utils.py
│       │   └── management/commands/ # Custom mgmt commands
│       ├── opportunities/
│       │   ├── models.py            # Opportunity, Score, CompanyProfile
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── samgov_client.py
│       │   │   ├── lab_monitors.py
│       │   │   ├── normalizer.py
│       │   │   ├── scorer.py
│       │   │   └── enricher.py
│       │   └── tasks.py             # Celery tasks
│       ├── deals/
│       │   ├── models.py            # Deal, Task, Approval
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── workflow.py          # State machine
│       │   └── tasks.py
│       ├── rfp/
│       │   ├── models.py            # RFPDocument, ComplianceMatrix
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── parser.py        # Document extraction
│       │   │   └── diff_tracker.py  # Amendment diffs
│       │   └── tasks.py
│       ├── past_performance/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       └── matcher.py       # RAG matching
│       ├── proposals/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── generator.py     # Section generation
│       │   │   └── reviewer.py      # Review workflow
│       │   ├── templates/           # Proposal DOCX templates
│       │   └── tasks.py
│       ├── pricing/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       ├── scenario_engine.py
│       │       └── price_to_win.py
│       ├── contracts/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       ├── generator.py
│       │       └── clause_scanner.py
│       ├── strategy/                     # Company Strategy
│       │   ├── models.py            # CompanyStrategy, StrategicGoal, PortfolioSnapshot
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       ├── portfolio_analyzer.py   # Pipeline health vs strategy
│       │       └── competitive_intel.py    # Competitor analysis
│       ├── marketing/                    # Marketing & Sales Intelligence (NEW)
│       │   ├── models.py            # MarketIntelligence, CompetitorProfile, CaptureStrategy
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       ├── agency_profiler.py    # Agency intelligence gathering
│       │       ├── competitor_profiler.py # Competitor analysis
│       │       └── capture_strategy.py   # Win theme & positioning engine
│       ├── research/                     # Deep Research (NEW)
│       │   ├── models.py            # ResearchRequest, ResearchReport, ResearchActivity
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── research_engine.py    # Core research pipeline
│       │   │   ├── web_searcher.py       # Multi-source web search
│       │   │   ├── gov_db_searcher.py    # FPDS, USASpending, SAM.gov search
│       │   │   └── report_generator.py   # PDF/CSV/DOCX deliverable generation
│       │   └── tasks.py             # Async research tasks (Celery)
│       ├── legal/                         # Business Legal (NEW)
│       │   ├── models.py            # LegalKnowledgeBase, LegalClauseLibrary, LegalReview
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── legal_rag.py         # Legal knowledge base RAG search
│       │   │   ├── clause_analyzer.py   # Clause-by-clause risk analysis
│       │   │   ├── compliance_checker.py # FAR/DFARS compliance engine
│       │   │   ├── contract_drafter.py  # Contract/NDA/teaming agreement drafting
│       │   │   ├── oci_assessor.py      # Organizational Conflict of Interest
│       │   │   ├── protest_advisor.py   # Bid protest viability assessment
│       │   │   └── evaluation.py        # Legal analysis quality evaluation (DeepEval)
│       │   ├── management/commands/
│       │   │   └── seed_legal_kb.py     # Seed FAR clauses, GAO decisions, precedents
│       │   └── tasks.py             # Async legal analysis tasks (Celery)
│       ├── teaming/                         # Teaming & Subcontractors (NEW)
│       │   ├── models.py            # TeamingPartner, TeamingRecommendation, TeamingAgreement
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── partner_matcher.py     # RAG-based partner search + ranking
│       │   │   ├── team_optimizer.py      # Team composition optimization
│       │   │   ├── sb_analyzer.py         # Small business goal compliance
│       │   │   ├── risk_assessor.py       # Teaming risk assessment
│       │   │   └── agreement_generator.py # NDA/LOI/teaming agreement drafting
│       │   ├── management/commands/
│       │   │   └── seed_partners.py       # Import partner database
│       │   └── tasks.py             # Async partner search + analysis (Celery)
│       ├── security_compliance/             # Security & Compliance Mapping (NEW)
│       │   ├── models.py            # SecurityControlFramework, SecurityControl, SecurityControlMapping
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── control_mapper.py      # Requirement-to-control mapping engine
│       │   │   ├── narrative_drafter.py   # SSP-style control narrative generation
│       │   │   ├── framework_rag.py       # Security framework RAG search
│       │   │   ├── cross_walker.py        # Framework cross-walk matrix
│       │   │   ├── gap_analyzer.py        # Compliance gap analysis
│       │   │   └── ssp_generator.py       # SSP/ATO document generation
│       │   ├── management/commands/
│       │   │   └── seed_frameworks.py     # Seed NIST 800-53, 800-171, FedRAMP, CMMC, HIPAA controls
│       │   └── tasks.py             # Async control mapping + narrative gen (Celery)
│       ├── knowledge_vault/              # Multimodal Knowledge Vault
│       │   ├── models.py            # KnowledgeVault, KnowledgeChunk
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   ├── services/
│       │   │   ├── ingestion.py     # Upload + chunking + embedding pipeline
│       │   │   ├── multimodal_rag.py # Text + image retrieval
│       │   │   └── image_embedder.py # CLIP embeddings for diagrams/images
│       │   └── tasks.py             # Async embedding generation
│       ├── communications/               # Communications & Q&A (UPGRADED)
│       │   ├── models.py            # EmailDraft, ClarificationQuestion, ClarificationAnswer, QALog
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── urls.py
│       │   └── services/
│       │       ├── qa_tracker.py        # Q&A lifecycle management
│       │       ├── impact_mapper.py     # Map CO answers → compliance/pricing changes
│       │       └── question_strategist.py # AI-prioritized clarification questions
│       ├── policies/
│       │   ├── models.py            # AIPolicy, GoalSetting
│       │   ├── serializers.py
│       │   ├── views.py
│       │   └── urls.py
│       └── analytics/
│           ├── models.py
│           ├── serializers.py
│           ├── views.py
│           └── urls.py
│
├── frontend/                         # React + TypeScript
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js               # or vite.config.ts
│   ├── tailwind.config.js
│   ├── public/
│   └── src/
│       ├── app/                     # Pages/routes
│       │   ├── layout.tsx
│       │   ├── page.tsx             # Dashboard
│       │   ├── login/
│       │   ├── opportunities/
│       │   ├── deals/
│       │   ├── rfp/
│       │   ├── proposals/
│       │   ├── pricing/
│       │   ├── contracts/
│       │   ├── past-performance/
│       │   ├── communications/
│       │   ├── knowledge-vault/      # Knowledge Vault management
│       │   ├── strategy/             # Company strategy dashboard
│       │   ├── marketing/            # Capture strategy & competitive intelligence (NEW)
│       │   ├── research/             # Deep research workspace
│       │   ├── legal/               # Legal workspace & clause library (NEW)
│       │   ├── teaming/            # Teaming partner database & team builder (NEW)
│       │   ├── security-compliance/ # Security control mapping & SSP workspace (NEW)
│       │   ├── analytics/
│       │   ├── settings/
│       │   └── admin/
│       ├── components/
│       │   ├── ui/                  # Button, Card, Table, etc.
│       │   ├── layout/             # Shell, Sidebar, Topbar
│       │   ├── auth/               # LoginForm, MFASetup, Profile
│       │   ├── dashboard/          # KPI cards, charts
│       │   ├── opportunities/      # OpportunityCard, ScoreBreakdown
│       │   ├── deals/              # KanbanBoard, DealDetail
│       │   ├── rfp/                # ComplianceMatrix, RequirementList
│       │   ├── proposals/          # SectionEditor, ReviewPanel
│       │   ├── pricing/            # ScenarioComparison, RateTable
│       │   ├── contracts/          # ClauseLibrary, RedlineViewer
│       │   ├── ai-workbench/       # AIChat, ActionPanel, TraceViewer
│       │   └── settings/           # PolicyManager, GoalSettings
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useDeals.ts
│       │   ├── useAI.ts
│       │   └── useWebSocket.ts
│       ├── services/
│       │   ├── api.ts              # Axios/fetch client
│       │   ├── auth.ts
│       │   ├── opportunities.ts
│       │   ├── deals.ts
│       │   ├── proposals.ts
│       │   └── ai.ts
│       ├── store/
│       │   ├── index.ts
│       │   ├── authSlice.ts
│       │   └── dealSlice.ts
│       ├── types/
│       │   ├── opportunity.ts
│       │   ├── deal.ts
│       │   ├── proposal.ts
│       │   └── api.ts
│       └── utils/
│
├── realtime/                         # Node.js WebSocket service
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── server.ts
│       ├── handlers/
│       │   ├── notifications.ts
│       │   ├── collaboration.ts
│       │   └── ai-stream.ts
│       └── middleware/
│           └── auth.ts
│
├── ai_orchestrator/                  # LangGraph + Agents
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py                  # FastAPI app
│       ├── agents/                  # All agent implementations
│       ├── mcp_servers/             # MCP tool servers
│       ├── graphs/                  # LangGraph workflow graphs
│       ├── rag/                     # Embedding + retrieval
│       └── learning/                # RL + policy updates
│
└── scripts/
    ├── seed_data.py                 # Initial data seeding
    ├── setup_dev.sh                 # Dev environment setup
    └── run_tests.sh
```

---

## Implementation Sequence (Build Order)

### Sprint 1-2: Foundation (Phase 1)
- [ ] Docker Compose with all services (Postgres, Redis, MinIO, Nginx)
- [ ] Django project setup with split settings
- [ ] Django accounts app (User, Profile, RBAC roles, MFA)
- [ ] Django core app (AuditLog, BaseModel, middleware)
- [ ] DRF setup with authentication (JWT + Session)
- [ ] React frontend scaffolding (Next.js + Tailwind + shadcn/ui)
- [ ] Login, registration, profile management pages
- [ ] App shell (sidebar navigation, topbar, layout)
- [ ] Node.js realtime service skeleton

### Sprint 3-4: Opportunity Intelligence (Phase 2)
- [ ] SAM.gov API client + Celery task for periodic scanning
- [ ] Opportunity model + normalization pipeline
- [ ] Company profile + capability statement management
- [ ] Fit scoring engine (rule-based v1)
- [ ] Daily Top 10 digest generation
- [ ] Frontend: Opportunity list, detail view, score breakdown
- [ ] Lab procurement page monitors (configurable)

### Sprint 5: Company AI Strategy Agent (Phase 4A)
- [ ] CompanyStrategy, StrategicGoal, PortfolioSnapshot models
- [ ] Strategy agent: strategic scoring of opportunities
- [ ] Strategy agent: bid/no-bid recommendation engine
- [ ] Strategy agent: portfolio analysis & balance scoring
- [ ] Strategy agent: win theme generation
- [ ] Strategy agent: competitive landscape assessment
- [ ] LangGraph strategy_graph.py (full pipeline)
- [ ] Frontend: Strategy dashboard + portfolio health view
- [ ] Frontend: Strategy settings (target agencies, domains, goals)
- [ ] Integration: strategic score injected into bid/no-bid HITL gate

### Sprint 6: Deep Research Agent (Phase 4C — NEW)
- [ ] ResearchRequest, ResearchReport, ResearchActivity models
- [ ] Research engine: query planning & decomposition
- [ ] Research engine: multi-source web search (web, news, academic)
- [ ] Research engine: government database search (FPDS, USASpending, SAM.gov)
- [ ] Research engine: Knowledge Vault integration (internal docs)
- [ ] Research engine: file/URL analysis (uploaded context)
- [ ] Research engine: fact extraction, cross-referencing, synthesis
- [ ] Research engine: report generation (markdown + structured findings)
- [ ] Research engine: deliverable generation (PDF, CSV, DOCX)
- [ ] Follow-up research (use previous report as context)
- [ ] Parallel research swarm (multiple tasks simultaneously)
- [ ] MCP tools: web_research_tools.py, competitive_intel_tools.py
- [ ] LangGraph research_graph.py (full pipeline with parallel branches)
- [ ] Frontend: Research workspace (launch, monitor progress, view reports)
- [ ] Frontend: Real-time activity feed during research
- [ ] Frontend: Research history & report library
- [ ] Celery tasks for async research execution

### Sprint 7: Marketing & Sales Expert Agent (Phase 4B — NEW)
- [ ] MarketIntelligence, CompetitorProfile, CaptureStrategy models
- [ ] Marketing agent: agency profiling (uses Deep Research Agent)
- [ ] Marketing agent: competitor profiling (FPDS + web research)
- [ ] Marketing agent: competitive analysis per deal
- [ ] Marketing agent: win strategy engine (themes, discriminators, ghost strategies)
- [ ] Marketing agent: executive summary generation (Shipley method)
- [ ] Marketing agent: section messaging guide generation
- [ ] Marketing agent: P(win) assessment
- [ ] Marketing agent: capture ROI analysis
- [ ] Marketing agent: review coaching (Pink/Red/Gold team AI coaching)
- [ ] Marketing frameworks library (Shipley, Lohfeld, Blue Ocean, Miller Heiman, SPIN)
- [ ] LangGraph marketing_graph.py (full pipeline)
- [ ] Frontend: Capture strategy workspace
- [ ] Frontend: Competitor intelligence dashboard
- [ ] Frontend: Win theme editor & messaging guide viewer

### Sprint 8: Business Legal Agent (Phase 4D — NEW)
- [ ] LegalKnowledgeBase + LegalClauseLibrary models
- [ ] Seed FAR clause library (FAR Part 52 clauses with risk levels)
- [ ] Seed DFARS clause library
- [ ] Seed GAO bid protest decisions (key precedents)
- [ ] Legal RAG search engine (pgvector on legal knowledge base)
- [ ] Legal Agent: RFP legal review (flag high-risk terms, OCI check)
- [ ] Legal Agent: bid legal risk assessment
- [ ] Legal Agent: contract review (clause-by-clause with risk scoring)
- [ ] Legal Agent: contract drafting (teaming, NDA, subcontract templates)
- [ ] Legal Agent: FAR/DFARS compliance checking engine
- [ ] Legal Agent: OCI assessment with mitigation plan
- [ ] Legal Agent: ethics compliance checking
- [ ] Legal Agent: bid protest viability assessment + precedent search
- [ ] Legal Agent: proposal legal review (pre-submission sign-off)
- [ ] Legal Agent: redline analysis with legal impact per change
- [ ] Legal Agent: evaluation framework (DeepEval-inspired A-F grading)
- [ ] Legal Agent: ReAct pattern LangGraph (agent→tools→agent loop, max 10 iter)
- [ ] MCP tools: legal_tools.py (9 tools — RAG, clause search, contract review, etc.)
- [ ] LangGraph legal_graph.py (full ReAct pipeline)
- [ ] Legal Agent integrated at EVERY pipeline stage (see integration points)
- [ ] Frontend: Legal workspace (review dashboard, clause library browser)
- [ ] Frontend: Contract review viewer (clause-by-clause with risk colors)
- [ ] Frontend: Legal chat interface (ReAct-powered legal Q&A)
- [ ] Regulatory change monitoring (via Deep Research Agent)

### Sprint 9: Teaming & Subcontractor Selection Agent (Phase 4E — NEW)
- [ ] TeamingPartner, TeamingRecommendation, TeamingAgreement models
- [ ] Partner database: CRUD, bulk import, capability embeddings for RAG matching
- [ ] Teaming Agent: identify teaming needs from RFP + SA solution
- [ ] Teaming Agent: partner search & ranking (internal DB + SAM.gov + FPDS)
- [ ] Teaming Agent: team composition optimization (capability coverage + cost)
- [ ] Teaming Agent: small business subcontracting goal compliance analysis
- [ ] Teaming Agent: work share optimization + limitation on subcontracting check
- [ ] Teaming Agent: teaming risk assessment (per partner + overall team)
- [ ] Teaming Agent: OCI check integration with Legal Agent
- [ ] Teaming Agent: NDA/LOI/teaming agreement generation → Legal Agent review
- [ ] Teaming Agent: partner engagement strategy recommendation
- [ ] Teaming Agent: ongoing agreement monitoring (expiry, compliance, risks)
- [ ] MCP tools: teaming_tools.py (partner search, SB analysis, work share calc)
- [ ] LangGraph teaming_graph.py (full pipeline with OCI loop + HITL approval)
- [ ] Frontend: Partner database management (add, edit, import, search)
- [ ] Frontend: Team builder workspace (drag-and-drop team composition)
- [ ] Frontend: SB compliance dashboard (goals vs actuals by category)
- [ ] Frontend: Teaming agreement tracker (status, expiry, alerts)

### Sprint 10: Security & Compliance Mapping Agent (Phase 4F — NEW)
- [ ] SecurityControlFramework, SecurityControl, SecurityControlMapping models
- [ ] Seed NIST SP 800-53 Rev 5 control library (1,189 controls, 20 families)
- [ ] Seed NIST SP 800-171 Rev 2/3 (110 CUI security requirements)
- [ ] Seed FedRAMP baselines (Low/Moderate/High)
- [ ] Seed CMMC v2.0 practices and assessment objectives
- [ ] Seed HIPAA Security Rule controls + HITRUST CSF
- [ ] Seed framework cross-walks (NIST ↔ FedRAMP ↔ CMMC ↔ HIPAA)
- [ ] Security Agent: identify & classify security requirements from RFP
- [ ] Security Agent: determine applicable frameworks and impact levels
- [ ] Security Agent: requirement-to-control mapping (RAG + keyword + baseline)
- [ ] Security Agent: draft SSP-style control implementation narratives
- [ ] Security Agent: cross-walk multiple frameworks (deduplicate controls)
- [ ] Security Agent: compliance gap analysis + remediation recommendations
- [ ] Security Agent: generate SSP sections (10 standard sections)
- [ ] Security Agent: generate ATO approach narrative
- [ ] Security Agent: CMMC readiness assessment (Level 2/3)
- [ ] Security Agent: generate security proposal section (Volume I security content)
- [ ] Security Agent: validate security claims against solution architecture
- [ ] Security Agent: feedback loop to SA Agent for gap remediation
- [ ] ComplianceEvidenceLibrary: evidence CRUD + reuse across proposals
- [ ] MCP tools: security_compliance_tools.py (control search, mapping, narrative gen)
- [ ] LangGraph security_compliance_graph.py (full pipeline with gap→refinement loop)
- [ ] Frontend: Security compliance workspace (framework browser, control matrix)
- [ ] Frontend: Control mapping viewer (requirement ↔ control with narratives)
- [ ] Frontend: Compliance gap dashboard (coverage %, gaps, risk colors)
- [ ] Frontend: Evidence library manager (upload, tag, link to controls)

### Sprint 11-12: Deal Pipeline (Phase 3)
- [ ] Deal model + workflow state machine
- [ ] Task & checklist system with templates
- [ ] Approval system with HITL gates (now includes strategic score)
- [ ] Frontend: Kanban pipeline board
- [ ] Frontend: Deal detail page with timeline
- [ ] Notifications (in-app + email) for stage changes

### Sprint 13-14: RFP & Past Performance (Phase 4-5)
- [ ] RFP document upload + AI extraction
- [ ] Compliance matrix generator
- [ ] Amendment diff tracker
- [ ] Past performance vault (CRUD + embeddings)
- [ ] RAG-powered past performance matching
- [ ] Frontend: RFP workspace with compliance matrix
- [ ] Frontend: Past performance library

### Sprint 15: Multimodal Knowledge Vault
- [ ] KnowledgeVault + KnowledgeChunk models
- [ ] Upload pipeline: PDF/DOCX/images/presentations → chunk → embed
- [ ] Text embedding pipeline (OpenAI/Anthropic embeddings → pgvector)
- [ ] Image embedding pipeline (CLIP model → image vectors)
- [ ] Multimodal RAG retriever (text + image + table + code search)
- [ ] MCP tools: knowledge_vault_tools.py, image_search_tools.py
- [ ] Frontend: Knowledge Vault management (upload, browse, tag, search)
- [ ] Seed vault with solutioning frameworks library (TOGAF, C4, arc42, etc.)

### Sprint 16-18: Fully Autonomous AI Solutions Architect + Proposal Studio (Phase 6)
- [ ] Solution Architect Agent: requirement deep-dive analysis
- [ ] Solution Architect Agent: multimodal knowledge retrieval (RAG)
- [ ] Solution Architect Agent: framework selection (C4, TOGAF, arc42, etc.)
- [ ] Solution Architect Agent: solution synthesis engine (15+ architecture areas)
- [ ] Diagram generation: Mermaid.js diagrams → SVG/PNG rendering
- [ ] Diagram generation: D2 diagrams → SVG/PNG rendering
- [ ] Diagram generation: PlantUML diagrams → rendering
- [ ] MCP tools: diagram_tools.py (generate + render + annotate)
- [ ] Solution Architect Agent: full technical volume generation
- [ ] Solution Architect Agent: self-critique validation loop
- [ ] LangGraph solution_arch_graph.py (full autonomous SA pipeline)
- [ ] Proposal templates (5 volumes)
- [ ] AI section generation (uses SA output + Marketing messaging + Past Perf)
- [ ] Review workflow (pink/red/gold team + AI coaching from Marketing agent)
- [ ] Frontend: Proposal editor with AI workbench + diagram viewer
- [ ] Frontend: Solution Architect workspace (view generated architectures)
- [ ] Frontend: Review interface with AI coaching + comments
- [ ] DOCX export with embedded diagrams + professional formatting
- [ ] Management Volume Engine: management approach generation (PM methodology, governance)
- [ ] Management Volume Engine: org chart generation (Mermaid/D2 with prime/sub/govt interfaces)
- [ ] Management Volume Engine: staffing plan timeline visualization
- [ ] Management Volume Engine: WBS chart generation + WBS dictionary
- [ ] Management Volume Engine: transition-in/out plan generation
- [ ] Management Volume Engine: quality assurance plan generation
- [ ] Management Volume Engine: risk management plan + risk matrix diagram
- [ ] Management Volume Engine: IMS/Gantt schedule with critical path
- [ ] Management Volume Engine: RACI matrix generation
- [ ] Management Volume Engine: 10+ management graphics (same quality as SA technical diagrams)
- [ ] Frontend: Management volume workspace (org chart editor, staffing visualizer)

### Sprint 19-20: Intelligent Pricing Engine (Phase 7)
- [ ] RateCard + ConsultantProfile models (with market benchmarks)
- [ ] LOE Estimation Engine: WBS derivation from SA solution
- [ ] LOE Estimation Engine: analogous/parametric/three-point estimation
- [ ] LOE Estimation Engine: consultant-to-staffing matching
- [ ] Pricing Agent: market intelligence gathering (uses Deep Research Agent)
- [ ] Pricing Agent: cost model builder (full cost build-up)
- [ ] Pricing Agent: game-theoretic profit optimization
- [ ] Pricing Agent: 7 scenario strategies (max profit → floor)
- [ ] Pricing Agent: Monte Carlo sensitivity analysis
- [ ] Pricing Agent: competitive price positioning
- [ ] Pricing Agent: Volume IV (cost volume) generation
- [ ] Pricing Agent: price defense preparation
- [ ] MCP tools: market_rate_tools.py (GSA rates, salary data)
- [ ] LangGraph pricing_graph.py (full intelligent pricing pipeline)
- [ ] Frontend: Pricing scenario comparison with P(win) vs margin charts
- [ ] Frontend: LOE breakdown with WBS drill-down
- [ ] Frontend: Staffing plan visualization (by month, by person)
- [ ] Frontend: Sensitivity analysis interactive charts

### Sprint 21: Contract Management (Phase 8 — now powered by Legal Agent)
- [ ] Contract templates + clause library
- [ ] Contract risk scanner
- [ ] Contract drafting from deal specifics
- [ ] Redline tracking with version history
- [ ] Frontend: Contract workspace

### Sprint 22-23: AI Orchestration & Learning (Phase 9-10)
- [ ] LangGraph multi-agent orchestration (19 agents)
- [ ] MCP tool servers (all integrations — 17 servers)
- [ ] A2A event system (65+ events)
- [ ] Communications agent (email drafting, engagement timeline)
- [ ] Q&A tracking system: AI-drafted vendor questions prioritized by information value
- [ ] Q&A tracking system: answer ingestion → impact assessment
- [ ] Q&A tracking system: answer impact mapping → Compliance Agent + Pricing Agent updates
- [ ] Q&A tracking system: complete audit trail (question → answer → impact → action)
- [ ] MCP tools: qa_tracking_tools.py (Q&A lifecycle, impact mapping)
- [ ] Policy & goal settings manager
- [ ] Learning agent (outcome tracking + policy updates + strategy evolution)
- [ ] Learning feeds back to ALL agents (strategy, marketing, SA, pricing)
- [ ] Submission packaging + audit trail
- [ ] Frontend: AI workbench, policy settings, analytics dashboards

---

## Environment Variables (.env.example)

```
# Django
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=dealmanager
POSTGRES_USER=dealmanager
POSTGRES_PASSWORD=change-me
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change-me
MINIO_ENDPOINT=minio:9000

# AI/LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6

# SAM.gov
SAMGOV_API_KEY=your-key

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=http://langfuse:8004

# JWT
JWT_SECRET_KEY=change-me
JWT_EXPIRATION_HOURS=24
```

---

## Success Criteria

1. **Daily Top 10 opportunities** automatically scored (technical fit + strategic alignment)
2. **Company AI Strategy Agent** maintains living strategy, influences every bid decision, balances portfolio
3. **Marketing & Sales Expert Agent** crafts winning capture strategies, generates win themes, coaches review teams, and positions every proposal to win
4. **Deep Research Agent** produces consulting-quality intelligence reports (with PDF/CSV/DOCX deliverables) on agencies, competitors, markets, and technologies — feeds every other agent
5. **End-to-end pipeline** from opportunity → research → strategy → teaming → capture → security → proposal → pricing → legal review → submission → contract
6. **Fully Autonomous AI Solutions Architect** produces complete technical solutions with 14+ architecture diagrams from your multimodal knowledge vault
7. **Intelligent Pricing Agent** maximizes profit while keeping prices unbeatable — derives LOE from solution, uses game-theoretic optimization, runs Monte Carlo sensitivity analysis, generates Volume IV
8. **Multimodal Knowledge Vault** stores and retrieves your reference architectures, images, diagrams, documents, patterns, and best practices via RAG
9. **AI generates** compliance matrices, proposal sections, pricing scenarios, contracts — all grounded in YOUR knowledge base
10. **Business Legal Agent** provides FAR/DFARS compliance, clause-by-clause contract review, OCI assessment, bid protest strategy, and legal sign-off at every pipeline stage — with DeepEval-inspired quality grading
11. **Teaming & Subcontractor Agent** identifies, evaluates, and recommends optimal teaming partners — handles SB compliance, work share optimization, OCI checks, NDA/LOI/teaming agreement generation, and risk assessment
12. **Security & Compliance Mapping Agent** performs control-by-control mapping (NIST 800-53, 800-171, FedRAMP, CMMC, HIPAA/HITRUST), drafts SSP narratives, generates ATO approach docs, validates all security claims against solution architecture
13. **Management Volume Engine** produces Volume II (management approach) with the same depth as the SA's Volume I — org charts, staffing timelines, transition plans, WBS, IMS, QA plans, risk matrices — all generated as professional diagrams
14. **Q&A & Clarification Tracking** system drafts prioritized vendor questions, tracks CO answers, maps answer impacts back to compliance matrix and pricing assumptions with full audit trail
15. **HITL gates** enforce human approval at all critical decisions
16. **Learning loop** improves scoring, writing, pricing, marketing, legal, AND evolves company strategy over time
17. **Professional output** (DOCX proposals with embedded architecture diagrams, proper formatting, branding)
18. **Full audit trail** for every action (human and AI)
19. **RBAC** with MFA protecting sensitive operations
20. **Docker Compose** single-command deployment with no port conflicts
21. **Real-time** collaboration and notifications via WebSocket
22. **19 specialized AI agents** orchestrated via LangGraph + MCP + A2A with 65+ inter-agent events across 23 sprints
