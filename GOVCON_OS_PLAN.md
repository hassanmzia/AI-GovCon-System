# GovCon AI Operating System — Unified Implementation Plan

## Current State Assessment

### What Already Exists (Strong Foundation)

The current codebase is a **production-grade, multi-service platform** with:

| Layer | Technology | Status |
|-------|-----------|--------|
| **Backend** | Django 5.1 + DRF, 19 apps, PostgreSQL+pgvector | Built |
| **Frontend** | Next.js 14, React 18, TypeScript, 22+ pages | Built |
| **AI Orchestrator** | FastAPI + LangGraph, 21 agents, 16 MCP tools | Built |
| **Realtime** | Node.js + Socket.IO + Redis adapter | Built |
| **Infrastructure** | Docker Compose (11 services), Nginx, MinIO, Langfuse | Built |
| **Auth** | JWT + RBAC (8 roles) + optional MFA | Built |
| **RAG** | pgvector embeddings, chunker, retriever | Built |
| **Learning** | Thompson Sampling bandit, policy updater, reward tracker | Built |

### Existing Django Apps (19)
`core`, `accounts`, `opportunities`, `deals`, `rfp`, `past_performance`, `proposals`, `pricing`, `contracts`, `strategy`, `marketing`, `research`, `legal`, `teaming`, `security_compliance`, `knowledge_vault`, `communications`, `policies`, `analytics`

### Existing AI Agents (21)
`opportunity`, `deal_pipeline`, `proposal_writer`, `rfp_analyst`, `past_performance`, `solution_architect`, `pricing`, `contract`, `compliance`, `security_compliance`, `strategy`, `research`, `marketing`, `legal`, `teaming`, `qa`, `submission`, `communication`, `learning`

### Existing MCP Tool Servers (16)
`samgov`, `vector_search`, `document`, `pricing`, `workflow`, `legal`, `qa_tracking`, `competitive_intel`, `teaming`, `knowledge_vault`, `web_research`, `security_compliance`, `market_rate`, `image_search`, `template_render`, `email`, `diagram`

---

## Gap Analysis: Current State → GovCon OS Vision

### Domain 1: Opportunity Intelligence (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| SAM.gov ingestion | ✅ Built | — |
| Opportunity scoring (10 factors) | ✅ Built | Needs capacity-aware ranking |
| Daily scan + digest | ✅ Built | — |
| Thompson Sampling selection | ✅ Built | — |
| Multi-source ingestion (FPDS, USASpending, forecasts) | 🟡 Partial | OpportunitySource model exists, but only SAM.gov client is implemented |
| Amendment detection | 🟡 Partial | RFP Amendment model exists, opportunity-level amendment tracking missing |
| Scout/Fit/Ranking/Alert named agents | 🔴 Missing | Single opportunity_agent exists; needs decomposition into specialized sub-agents |
| Precision@10 monitoring | 🔴 Missing | Needs metric tracking for recommendation quality |
| Environmental change triggers | 🔴 Missing | No event-driven re-scoring when market conditions change |
| Capacity-aware ranking | 🔴 Missing | Scoring doesn't consider current workforce/pipeline load |

### Domain 2: Capture & Pipeline (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| Deal pipeline (15 stages) | ✅ Built | — |
| Stage transitions + workflow engine | ✅ Built | — |
| Task templates per stage | ✅ Built | — |
| HITL approval gates | ✅ Built | — |
| Activity audit trail | ✅ Built | — |
| Capture plan generator | 🔴 Missing | No auto-generated capture plan document |
| Competitor intelligence integration | 🟡 Partial | competitive_intel_tools exist, not wired into capture workflow |
| Agency relationship tracker | 🔴 Missing | No model for tracking agency contacts/meetings/history |
| Gate review automation | 🟡 Partial | Approvals exist but gate criteria aren't auto-evaluated |
| Stakeholder mapping | 🔴 Missing | No model for mapping decision-makers and influencers |

### Domain 3: Proposal Automation (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| Proposal model + sections | ✅ Built | — |
| RFP parser + requirement extraction | ✅ Built | — |
| Compliance matrix builder | ✅ Built | — |
| Past performance matching | ✅ Built | — |
| Proposal writer agent | ✅ Built | — |
| Solution architect agent | ✅ Built | — |
| Review cycles (pink/red/gold) | ✅ Built | — |
| DOCX generation | ✅ Built | — |
| Auto-trigger on deal stage transition | 🔴 Missing | Proposal workspace doesn't auto-create when deal enters proposal stage |
| Red team agent | 🟡 Partial | qa_agent does consistency checks, but no adversarial red-team agent |
| Submission agent packaging | 🟡 Partial | submission_agent exists but implementation is thin |
| Human gate chain (draft → pricing → final) | 🟡 Partial | Approvals exist but not chained in a defined sequence |

### Domain 4: Pricing Optimization (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| Rate cards + labor categories | ✅ Built | — |
| LOE estimation | ✅ Built | — |
| Cost model (labor + fringe + OH + G&A) | ✅ Built | — |
| 7 pricing scenarios | ✅ Built | — |
| Price-to-win analysis | ✅ Built | — |
| Monte Carlo sensitivity analysis | ✅ Built | — |
| Pricing approval gate | ✅ Built | — |
| Win probability curve visualization | 🔴 Missing | Data exists in backend, no frontend chart |
| Pricing-to-proposal integration | 🟡 Partial | Models linked via deal, but no automated flow |
| Historical pricing learning | 🔴 Missing | No feedback loop from outcomes to pricing models |

### Domain 5: Contract Lifecycle (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| Contract templates (7 types) | ✅ Built | — |
| Clause library (FAR/DFARS) | ✅ Built | — |
| Contract generation | ✅ Built | — |
| Clause risk analysis | ✅ Built | — |
| Contract versions | ✅ Built | — |
| Milestones + deliverables | ✅ Built | — |
| Modifications tracker | ✅ Built | — |
| Auto-trigger on Deal → Awarded | 🔴 Missing | No automatic contract creation on deal win |
| Option year tracking | 🔴 Missing | No model for tracking option period exercises |
| Deliverables monitoring dashboard | 🟡 Partial | Model exists, no dedicated monitoring view |
| Contract health scoring | 🔴 Missing | No aggregate health metric |

### Domain 6: Compliance & Continuous ATO (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| Security frameworks (NIST, FedRAMP, CMMC) | ✅ Built | — |
| Control mapping | ✅ Built | — |
| Compliance reports | ✅ Built | — |
| Gap analysis | ✅ Built | — |
| Evidence collection automation | 🔴 Missing | No automated evidence gathering from systems |
| Drift detection | 🔴 Missing | No continuous monitoring for compliance drift |
| Remediation planner with POAM | 🟡 Partial | POAM report type exists, no actionable remediation workflow |
| Integration with active contracts | 🔴 Missing | Compliance not linked to contract lifecycle |
| Continuous ATO monitoring | 🔴 Missing | No ongoing authorization monitoring |

### Domain 7: Workforce & HR Intelligence (Mostly Missing)
| Feature | Status | Gap |
|---------|--------|-----|
| ConsultantProfile (skills, certs, clearances) | ✅ Built (in pricing app) | — |
| Skill matrix | 🟡 Partial | Skills on ConsultantProfile, no matrix view |
| Clearance tracker | 🟡 Partial | Clearance field exists, no expiry/renewal tracking |
| Hiring forecast from pipeline | 🔴 Missing | No demand forecasting from deal pipeline |
| Labor category management | 🟡 Partial | RateCard has categories, not a full workforce module |
| Workforce utilization dashboard | 🔴 Missing | ConsultantProfile has utilization field, no dashboard |
| Performance tracker | 🔴 Missing | No consultant performance history |

### Domain 8: Corporate Knowledge & Learning (Existing → Enhance)
| Feature | Status | Gap |
|---------|--------|-----|
| Knowledge vault (docs, templates, guides) | ✅ Built | — |
| Vector embeddings + semantic search | ✅ Built | — |
| Learning agent | ✅ Built | — |
| Reward tracker (win/loss signals) | ✅ Built | — |
| Thompson Sampling bandit | ✅ Built | — |
| Policy updater | ✅ Built | — |
| Win/loss analysis storage | 🔴 Missing | Learning agent analyzes but doesn't persist structured analysis |
| Pricing adjustment from history | 🔴 Missing | No feedback from pricing outcomes to future scenarios |
| Red team feedback integration | 🔴 Missing | Review comments not fed back to learning engine |
| Cross-domain learning feeds | 🔴 Missing | Learning engine doesn't feed strategy/pricing/ranking |

### Cross-Cutting: Unified Orchestration Flow
| Feature | Status | Gap |
|---------|--------|-----|
| A2A event bus (Redis pub/sub) | ✅ Built | — |
| SSE streaming for agent events | ✅ Built | — |
| Agent-to-agent communication | ✅ Built (events.py with 65+ event types) | — |
| Deal-triggered agent chains | 🔴 Missing | No automated agent-to-agent pipeline on stage transitions |
| Unified executive dashboard | 🟡 Partial | Dashboard page exists, needs cross-domain KPIs |
| AI autonomy policies | 🟡 Partial | policies app exists, not integrated with agent execution |
| Langfuse observability | ✅ Built | — |

---

## Implementation Plan — 4 Phases Over 18 Months

---

## Phase 1: Foundation Strengthening (Months 0–4)

**Goal:** Expand Opportunity Intelligence, strengthen Deal Pipeline as the central nervous system, wire up RFP parsing + compliance matrix, and build the Past Performance Vault into a true retrieval engine.

### 1.1 — Opportunity Intelligence Enhancement

#### 1.1.1 Multi-Source Ingestion Engine
**Files to create/modify:**
- `backend/apps/opportunities/services/fpds_client.py` — NEW: FPDS.gov API client
- `backend/apps/opportunities/services/usaspending_client.py` — NEW: USASpending.gov API client
- `backend/apps/opportunities/services/forecast_client.py` — NEW: Agency forecast portal scraper
- `backend/apps/opportunities/tasks.py` — MODIFY: Add Celery tasks for each source
- `backend/apps/opportunities/models.py` — MODIFY: Add `source_type` tracking, amendment history field
- `ai_orchestrator/src/mcp_servers/fpds_tools.py` — NEW: FPDS MCP tools
- `ai_orchestrator/src/mcp_servers/usaspending_tools.py` — NEW: USASpending MCP tools

**What this does:**
- Implements FPDS.gov client for contract award history lookup
- Implements USASpending.gov client for spending analysis and incumbent identification
- Adds forecast portal ingestion for pre-RFP pipeline
- All sources normalize into the existing Opportunity model via the existing normalizer pattern
- Each source runs as a scheduled Celery task alongside the existing SAM.gov daily scan

#### 1.1.2 Decompose Opportunity Agent into Specialized Sub-Agents
**Files to create/modify:**
- `ai_orchestrator/src/agents/scout_agent.py` — NEW: Discovers opportunities across all sources
- `ai_orchestrator/src/agents/fit_agent.py` — NEW: Scores fit using company profile + capacity
- `ai_orchestrator/src/agents/ranking_agent.py` — NEW: Strategic ranking with capacity-awareness
- `ai_orchestrator/src/agents/alert_agent.py` — NEW: Monitors changes, amendments, deadline shifts
- `ai_orchestrator/src/agents/opportunity_agent.py` — MODIFY: Becomes orchestrator of sub-agents
- `ai_orchestrator/src/graphs/opportunity_graph.py` — MODIFY: Rewire to call sub-agents in sequence
- `ai_orchestrator/src/graphs/daily_scan_graph.py` — MODIFY: Use new sub-agents

**What this does:**
- **Scout Agent**: Scans all sources (SAM.gov, FPDS, USASpending, forecasts), deduplicates, normalizes
- **Fit Agent**: Scores opportunities against company profile (extends existing scorer) + adds capacity check against current pipeline load
- **Ranking Agent**: Applies strategic scoring + Thompson Sampling + capacity-aware filtering for Top 10
- **Alert Agent**: Watches for amendments, deadline changes, new Q&A, solicitation updates; emits events
- The existing opportunity_agent becomes the orchestrator that chains these sub-agents via the event bus

#### 1.1.3 Capacity-Aware Scoring
**Files to create/modify:**
- `backend/apps/opportunities/services/scorer.py` — MODIFY: Add capacity factor to scoring
- `backend/apps/opportunities/services/capacity_checker.py` — NEW: Pipeline load calculator
- `backend/apps/deals/services/__init__.py` — NEW
- `backend/apps/deals/services/pipeline_analytics.py` — NEW: Pipeline load queries

**What this does:**
- Calculates current pipeline load: active deals by stage, committed workforce, revenue capacity
- Adds `capacity_score` factor to the existing 10-factor scoring (becomes 11 factors)
- Demotes opportunities that would overload current workforce or conflict with active proposals

#### 1.1.4 Precision@10 Monitoring
**Files to create/modify:**
- `ai_orchestrator/src/learning/precision_tracker.py` — NEW: Track recommendation quality
- `backend/apps/analytics/models.py` — MODIFY: Add RecommendationMetric model
- `backend/apps/analytics/views.py` — MODIFY: Add precision metrics endpoint
- `frontend/src/app/(dashboard)/analytics/page.tsx` — MODIFY: Add Precision@10 chart

**What this does:**
- Tracks which recommended opportunities were actually pursued (Bid) vs passed
- Computes Precision@10 (of top 10 daily recommendations, how many led to bids)
- Tracks Precision@Win (of recommended+pursued, how many were won)
- Displays trend charts on analytics dashboard
- Feeds into learning engine as a meta-reward signal

#### 1.1.5 Amendment & Environmental Change Detection
**Files to create/modify:**
- `backend/apps/opportunities/models.py` — MODIFY: Add OpportunityAmendment model
- `backend/apps/opportunities/tasks.py` — MODIFY: Add amendment polling task
- `ai_orchestrator/src/agents/alert_agent.py` — (created in 1.1.2) Add change detection logic
- `ai_orchestrator/src/events.py` — MODIFY: Add AMENDMENT_DETECTED, DEADLINE_CHANGED, SCOPE_CHANGED event types

**What this does:**
- Polls SAM.gov for amendments on tracked opportunities
- Detects material changes (scope, deadline, evaluation criteria, set-aside changes)
- Alert Agent emits typed events that trigger re-scoring and notifications
- Environmental triggers (new competitor award, agency budget change) re-rank the pipeline

---

### 1.2 — Deal Pipeline as Central Nervous System

#### 1.2.1 Stage-Triggered Agent Chains
**Files to create/modify:**
- `backend/apps/deals/signals.py` — NEW: Django signals for stage transitions
- `backend/apps/deals/services/stage_orchestrator.py` — NEW: Maps stages to agent chains
- `ai_orchestrator/src/graphs/stage_trigger_graph.py` — NEW: Master orchestration graph
- `backend/apps/deals/views.py` — MODIFY: Emit events on stage transition

**What this does:**
- When a deal transitions stages, automatically trigger the appropriate agent chain:
  - `identified` → Scout + Fit agents assess opportunity
  - `qualification` → Strategy agent runs bid/no-bid assessment
  - `capture` → Capture plan generator + competitive intel
  - `rfp_analysis` → RFP parser + compliance matrix builder
  - `proposal` → Proposal workspace auto-creates, proposal writer begins
  - `review` → Red team agent evaluates
  - `submitted` → Submission agent validates
  - `awarded` → Contract auto-creates, workforce planning triggers
  - `closed_lost` → Learning agent records outcome
- This is THE core innovation: the deal pipeline becomes the central nervous system that orchestrates all agents

#### 1.2.2 Capture Plan Generator
**Files to create/modify:**
- `backend/apps/deals/models.py` — MODIFY: Add CapturePlan model
- `backend/apps/deals/serializers.py` — MODIFY: Add CapturePlan serializer
- `backend/apps/deals/views.py` — MODIFY: Add capture plan endpoints
- `ai_orchestrator/src/agents/capture_agent.py` — NEW: Generates capture plans
- `ai_orchestrator/src/graphs/capture_graph.py` — NEW: Capture planning workflow
- `frontend/src/app/(dashboard)/deals/[id]/capture-plan/page.tsx` — NEW: Capture plan UI

**What this does:**
- Auto-generates capture plan when deal enters `capture` stage
- Capture plan includes: win strategy, competitive landscape, teaming strategy, pricing approach, timeline, action items
- Pulls from competitive_intel_tools, teaming_tools, strategy agent
- Human review gate before capture plan is finalized

#### 1.2.3 Agency Relationship Tracker
**Files to create/modify:**
- `backend/apps/deals/models.py` — MODIFY: Add AgencyContact, AgencyInteraction models
- `backend/apps/deals/serializers.py` — MODIFY: Add relationship serializers
- `backend/apps/deals/views.py` — MODIFY: Add relationship endpoints
- `frontend/src/app/(dashboard)/deals/[id]/relationships/page.tsx` — NEW: Relationship map UI

**What this does:**
- Track contacts at agencies: COR, CO, TPOC, program managers
- Log interactions: meetings, emails, conferences, industry days
- Relationship strength scoring based on interaction frequency/recency
- Feed relationship scores into opportunity scoring (agency_relationship_score already exists in bandit features)

#### 1.2.4 Stakeholder Mapping
**Files to create/modify:**
- `backend/apps/deals/models.py` — MODIFY: Add Stakeholder model
- `backend/apps/deals/serializers.py` — MODIFY: Add Stakeholder serializer
- `frontend/src/components/deals/stakeholder-map.tsx` — NEW: Visual stakeholder map component

**What this does:**
- Map decision-makers and influencers for each deal
- Track their priorities, concerns, relationships to each other
- Visual network graph showing influence flows
- Feed into win theme generation (marketing agent)

#### 1.2.5 Gate Review Automation
**Files to create/modify:**
- `backend/apps/deals/services/gate_evaluator.py` — NEW: Auto-evaluate gate readiness
- `backend/apps/deals/models.py` — MODIFY: Add GateReviewCriteria model
- `backend/apps/deals/views.py` — MODIFY: Add gate evaluation endpoint

**What this does:**
- Define criteria for each gate (bid/no-bid, pricing approval, submission)
- Auto-evaluate readiness: check if all required documents exist, scores above threshold, approvals obtained
- Traffic-light status (red/amber/green) for each criterion
- Block stage transition if critical gate criteria not met

---

### 1.3 — RFP Parser + Compliance Matrix Strengthening

#### 1.3.1 Enhanced RFP Parsing
**Files to modify:**
- `backend/apps/rfp/services/parser.py` — MODIFY: Improve section extraction, evaluation criteria parsing
- `ai_orchestrator/src/agents/rfp_analyst_agent.py` — MODIFY: Better shall/must/will statement extraction
- `ai_orchestrator/src/mcp_servers/document_tools.py` — MODIFY: Improve PDF table extraction

**What this does:**
- Better extraction of Section L (Instructions) and Section M (Evaluation Criteria)
- Improved shall/must/will statement parsing with requirement categorization
- Table extraction from PDFs for pricing templates and CDRLs
- Amendment diff tracking (highlight changes between RFP versions)

#### 1.3.2 Compliance Matrix Automation
**Files to modify:**
- `backend/apps/rfp/models.py` — MODIFY: Add compliance status tracking fields
- `ai_orchestrator/src/agents/compliance_agent.py` — MODIFY: Auto-populate compliance matrix
- `frontend/src/app/(dashboard)/rfp/page.tsx` — MODIFY: Interactive compliance matrix editor

**What this does:**
- Auto-generate compliance matrix from extracted requirements
- Map each requirement to proposal section + response strategy
- Track compliance status: ADDRESSED | PARTIAL | NOT_ADDRESSED | N/A
- Calculate overall compliance score
- Highlight gaps for human review

---

### 1.4 — Past Performance Vault Enhancement

#### 1.4.1 Structured Past Performance Repository
**Files to modify:**
- `backend/apps/past_performance/models.py` — MODIFY: Add richer fields (CPARS ratings, award fees, key personnel, lessons learned)
- `backend/apps/past_performance/views.py` — MODIFY: Add search and match endpoints
- `ai_orchestrator/src/agents/past_performance_agent.py` — MODIFY: Better relevance scoring
- `frontend/src/app/(dashboard)/past-performance/page.tsx` — MODIFY: Enhanced search/filter UI

**What this does:**
- Enrich past performance records with CPARS-style ratings per category
- Add key personnel tracking (who worked on what)
- Lessons learned per project
- Improved semantic matching: match by NAICS, scope similarity, agency, contract type, size
- Auto-suggest top 3-5 most relevant past performances for any opportunity

---

## Phase 2: Proposal & Pricing Engine (Months 4–8)

**Goal:** Build the Proposal Studio, wire pricing into proposals, and create submission workflow.

### 2.1 — Proposal Studio

#### 2.1.1 Auto-Triggering Proposal Workspace
**Files to create/modify:**
- `backend/apps/deals/signals.py` — MODIFY: Auto-create proposal on stage transition to `proposal`
- `backend/apps/proposals/services/workspace_creator.py` — NEW: Initialize proposal workspace from deal context
- `frontend/src/app/(dashboard)/proposals/[id]/studio/page.tsx` — NEW: Full proposal studio UI

**What this does:**
- When deal enters proposal stage, auto-create Proposal record linked to deal
- Pull in: RFP requirements, compliance matrix, past performance matches, solution architecture, pricing scenarios
- Create section structure from ProposalTemplate matching RFP requirements
- Studio UI with: section editor, compliance tracker sidebar, AI assistant panel

#### 2.1.2 Section-by-Section AI Drafting with Templates
**Files to create/modify:**
- `backend/apps/proposals/models.py` — MODIFY: Add section templates, AI drafting status
- `ai_orchestrator/src/agents/proposal_writer_agent.py` — MODIFY: Template-aware drafting
- `frontend/src/components/proposals/section-editor.tsx` — NEW: Rich text section editor with AI assist

**What this does:**
- AI drafts each section using: RFP requirements, compliance matrix, past performance, solution architecture
- Template library for common sections (executive summary, management approach, etc.)
- Track AI draft → human edit → reviewed → final status per section
- Real-time collaboration via Socket.IO for multiple editors

#### 2.1.3 Red Team Agent
**Files to create/modify:**
- `ai_orchestrator/src/agents/red_team_agent.py` — NEW: Adversarial proposal evaluator
- `ai_orchestrator/src/graphs/red_team_graph.py` — NEW: Red team workflow
- `backend/apps/proposals/models.py` — MODIFY: Add RedTeamFinding model

**What this does:**
- Evaluates proposal against RFP evaluation criteria as if scoring for the government
- Identifies: weaknesses, missing requirements, unclear language, non-responsive sections
- Scores each evaluation factor
- Compares against hypothetical competitor proposals
- Generates actionable improvement recommendations
- Feeds findings back to proposal writer for revision

#### 2.1.4 Submission Workflow
**Files to modify:**
- `ai_orchestrator/src/agents/submission_agent.py` — MODIFY: Full implementation
- `backend/apps/proposals/models.py` — MODIFY: Add SubmissionChecklist model
- `frontend/src/app/(dashboard)/proposals/[id]/submit/page.tsx` — NEW: Submission readiness dashboard

**What this does:**
- Pre-submission checklist: all sections complete, compliance matrix 100%, pricing approved, reviews done
- Volume assembly with correct formatting, page limits, fonts
- DOCX/PDF generation with Table of Contents, cross-references
- Final human gate before submission
- Record submission timestamp and method

### 2.2 — Pricing Engine v1

#### 2.2.1 Pricing-Proposal Integration
**Files to modify:**
- `backend/apps/pricing/models.py` — MODIFY: Add PricingVolume model linking to proposal
- `frontend/src/app/(dashboard)/pricing/[id]/page.tsx` — NEW: Detailed pricing scenario view

**What this does:**
- When proposal workspace creates, pricing workspace auto-initializes
- Import labor categories from RFP requirements
- LOE estimates feed into cost model
- Selected pricing scenario links to proposal Volume IV
- Price defense document generation

#### 2.2.2 Win Probability Visualization
**Files to create/modify:**
- `frontend/src/components/pricing/win-probability-chart.tsx` — NEW: Interactive P(win) curve
- `frontend/src/components/pricing/sensitivity-chart.tsx` — NEW: Sensitivity analysis visualization

**What this does:**
- Interactive chart showing win probability vs. price point
- Sensitivity analysis visualization (tornado chart)
- Side-by-side scenario comparison
- Monte Carlo simulation results display

### 2.3 — Audit Log System Strengthening

#### 2.3.1 Immutable Audit Trail Enhancement
**Files to modify:**
- `backend/apps/core/models.py` — MODIFY: Enhance AuditLog with more event types
- `backend/apps/core/middleware.py` — NEW: Auto-audit middleware for all API writes
- `backend/apps/core/views.py` — MODIFY: Add audit log query endpoints
- `frontend/src/app/(dashboard)/admin/audit-log/page.tsx` — NEW: Audit log viewer

**What this does:**
- Every create/update/delete on any model auto-logged with: user, timestamp, old values, new values, IP
- AI agent actions logged with: model, prompt, cost, latency (existing AITraceLog)
- Queryable audit log with filtering by entity, user, action, date range
- Export capability for compliance audits

---

## Phase 3: Contracts, Workforce & Executive View (Months 8–12)

**Goal:** Contract lifecycle automation, workforce planning, executive dashboard, and learning engine v1.

### 3.1 — Contract Lifecycle Automation

#### 3.1.1 Auto-Contract Creation on Award
**Files to modify:**
- `backend/apps/deals/signals.py` — MODIFY: Auto-create contract when deal → awarded
- `backend/apps/contracts/services/generator.py` — MODIFY: Pre-populate from deal + proposal data
- `backend/apps/contracts/models.py` — MODIFY: Add OptionYear, ContractHealth models

**What this does:**
- When deal reaches `awarded` stage, auto-generate contract shell from deal data
- Pull in: pricing scenario, contract type, period of performance, key clauses
- Option year tracking with exercise/decline status
- Contract health score based on: milestone delivery, modification count, burn rate, compliance status

#### 3.1.2 Deliverables Monitoring Dashboard
**Files to create/modify:**
- `frontend/src/app/(dashboard)/contracts/[id]/page.tsx` — NEW: Contract detail with deliverables timeline
- `backend/apps/contracts/tasks.py` — MODIFY: Add deliverable deadline alerts
- `frontend/src/components/contracts/deliverables-timeline.tsx` — NEW: Gantt-style deliverable tracker

**What this does:**
- Visual timeline of all deliverables and milestones
- Status tracking: not started → in progress → submitted → accepted
- Automated alerts for upcoming deadlines (7/3/1 day warnings)
- Link deliverables to workforce assignments

### 3.2 — Workforce & HR Intelligence

#### 3.2.1 Workforce Module
**Files to create/modify:**
- `backend/apps/workforce/__init__.py` — NEW app
- `backend/apps/workforce/models.py` — NEW: Employee, SkillMatrix, ClearanceRecord, Assignment, HiringRequisition
- `backend/apps/workforce/views.py` — NEW: Workforce CRUD + analytics endpoints
- `backend/apps/workforce/serializers.py` — NEW
- `backend/apps/workforce/urls.py` — NEW
- `backend/apps/workforce/services/demand_forecaster.py` — NEW: Pipeline-based demand forecasting
- `frontend/src/app/(dashboard)/workforce/page.tsx` — NEW: Workforce management UI
- `frontend/src/types/workforce.ts` — NEW
- `frontend/src/services/workforce.ts` — NEW

**What this does:**
- **Skill Matrix**: Track skills, certifications, training across all staff
- **Clearance Tracker**: Clearance type, status, expiry, renewal dates, investigation status
- **Assignment Tracking**: Who is assigned to what contract, utilization %
- **Hiring Forecast**: Based on pipeline (deals in proposal+ stages), forecast hiring needs by labor category
- **Demand vs. Supply**: Visual dashboard showing skill gaps between pipeline needs and current workforce
- Migrate existing ConsultantProfile data from pricing app into new workforce module

#### 3.2.2 Pipeline-Driven Workforce Planning
**Files to create/modify:**
- `ai_orchestrator/src/agents/workforce_agent.py` — NEW: Workforce planning agent
- `ai_orchestrator/src/graphs/workforce_graph.py` — NEW: Workforce planning workflow
- `backend/apps/workforce/services/demand_forecaster.py` — NEW

**What this does:**
- Analyze all deals in proposal/review/submitted stages
- Extract labor category needs from pricing scenarios
- Weight by win probability
- Generate: hiring forecast, training recommendations, clearance processing priorities
- Alert when upcoming awards have unfilled positions

### 3.3 — Executive Dashboard

#### 3.3.1 Cross-Domain Executive View
**Files to modify:**
- `frontend/src/app/(dashboard)/dashboard/page.tsx` — MODIFY: Major enhancement
- `backend/apps/analytics/views.py` — MODIFY: Add cross-domain analytics endpoints
- `backend/apps/analytics/services/kpi_calculator.py` — NEW: Enterprise KPI computation
- `frontend/src/components/dashboard/pipeline-funnel.tsx` — NEW
- `frontend/src/components/dashboard/revenue-forecast.tsx` — NEW
- `frontend/src/components/dashboard/win-rate-trend.tsx` — NEW
- `frontend/src/components/dashboard/workforce-heatmap.tsx` — NEW

**What this does:**
- **Pipeline Funnel**: Visual deal flow from opportunity → award with conversion rates
- **Revenue Forecast**: Weighted pipeline value (deal value × P(win)) by quarter
- **Win Rate Trend**: Historical win rate over time with moving average
- **Workforce Heatmap**: Utilization by team/skill/clearance
- **Compliance Status**: Aggregate compliance health across all active contracts
- **Active Proposals**: Status of all in-progress proposals with deadlines
- **Key Alerts**: Upcoming deadlines, gate approvals needed, at-risk contracts

### 3.4 — Learning Engine v1

#### 3.4.1 Win/Loss Analysis Persistence
**Files to create/modify:**
- `backend/apps/analytics/models.py` — MODIFY: Add WinLossAnalysis, LessonLearned models
- `ai_orchestrator/src/agents/learning_agent.py` — MODIFY: Persist analysis results
- `ai_orchestrator/src/learning/reward_tracker.py` — MODIFY: Feed outcomes to all relevant engines

**What this does:**
- When deal closes (won or lost), learning agent runs full analysis
- Persists: win/loss factors, pricing comparison, proposal scores, competitive positioning
- Stores lessons learned categorized by domain (pricing, teaming, technical, capture)
- Feeds into: scoring weights update, pricing model adjustment, proposal template improvement

#### 3.4.2 Cross-Domain Learning Feeds
**Files to modify:**
- `ai_orchestrator/src/learning/policy_updater.py` — MODIFY: Update policies across domains
- `ai_orchestrator/src/learning/bandit.py` — MODIFY: Update bandit parameters from outcomes
- `ai_orchestrator/src/agents/strategy_agent.py` — MODIFY: Incorporate historical patterns

**What this does:**
- Win/loss data feeds into opportunity scoring weights
- Pricing outcomes adjust future scenario generation
- Proposal review feedback improves proposal writer prompts
- Red team findings inform future compliance checking
- All learned through the existing policy updater + bandit framework

---

## Phase 4: Advanced Intelligence (Months 12–18)

**Goal:** RL optimization, advanced forecasting, competitive intelligence simulation, continuous ATO.

### 4.1 — Reinforcement Learning Optimization

#### 4.1.1 Offline RL for Agent Policies
**Files to create/modify:**
- `ai_orchestrator/src/learning/offline_rl.py` — NEW: Offline RL training pipeline
- `ai_orchestrator/src/learning/reward_tracker.py` — MODIFY: Enhanced reward signals
- `ai_orchestrator/src/learning/policy_updater.py` — MODIFY: RL-based policy updates

**What this does:**
- Collect agent decision trajectories as training data
- Offline RL training (no live exploration, learns from logged data)
- Reward signals: win (+10), shortlist (+5), on-time submission (+1), compliance defect (-1), pricing error (-3)
- Update: scoring weights, pricing scenario preferences, section drafting strategies
- Always maintain HITL at critical decision points

#### 4.1.2 Bandit Optimization for Pricing
**Files to modify:**
- `ai_orchestrator/src/learning/bandit.py` — MODIFY: Add pricing bandits
- `ai_orchestrator/src/agents/pricing_agent.py` — MODIFY: Use bandit for scenario selection

**What this does:**
- Apply contextual bandits to pricing scenario selection
- Features: contract type, agency, competition level, incumbent status, value range
- Learn which pricing strategies win in which contexts
- Maintain exploration to discover new winning strategies

### 4.2 — Advanced Forecasting

#### 4.2.1 Revenue & Pipeline Forecasting
**Files to create/modify:**
- `backend/apps/analytics/services/forecaster.py` — NEW: ML-based forecasting
- `ai_orchestrator/src/agents/forecasting_agent.py` — NEW: Predictive analytics agent
- `frontend/src/components/dashboard/forecast-chart.tsx` — NEW: Forecast visualization

**What this does:**
- Predict deal outcomes based on historical patterns
- Revenue forecasting by quarter with confidence intervals
- Pipeline velocity analysis (average time per stage)
- Seasonal patterns and agency budget cycle awareness
- "What-if" scenario modeling for business development planning

### 4.3 — Competitive Intelligence Simulation

#### 4.3.1 Competitor Modeling
**Files to create/modify:**
- `backend/apps/research/models.py` — MODIFY: Add CompetitorProfile, CompetitorBehavior models
- `ai_orchestrator/src/agents/competitor_sim_agent.py` — NEW: Competitor simulation agent
- `ai_orchestrator/src/graphs/competitor_sim_graph.py` — NEW: Simulation workflow

**What this does:**
- Build competitor profiles from FPDS/USASpending data
- Model competitor pricing behavior from historical awards
- Simulate competitive scenarios for specific opportunities
- Ghost strategy development (counter-positioning)
- Feed competitive insights into pricing and proposal strategy

### 4.4 — Continuous ATO Automation

#### 4.4.1 Continuous Compliance Monitoring
**Files to create/modify:**
- `backend/apps/security_compliance/services/drift_detector.py` — NEW: Compliance drift detection
- `backend/apps/security_compliance/services/evidence_collector.py` — NEW: Automated evidence gathering
- `backend/apps/security_compliance/tasks.py` — NEW: Scheduled compliance scans
- `ai_orchestrator/src/agents/ato_agent.py` — NEW: Continuous ATO monitoring agent

**What this does:**
- Scheduled scans of control implementation status
- Drift detection: alert when controls go out of compliance
- Automated evidence collection from integrated systems
- POAM management with automated progress tracking
- ATO renewal timeline management
- Integration with active contracts for scope-appropriate compliance

---

## Technical Architecture Decisions

### Event-Driven Architecture Enhancement

```
React UI ←→ API Gateway (Nginx)
                |
    ┌───────────┼───────────────┐
    |           |               |
Django Core   Node Realtime   AI Orchestrator
(RBAC +       (WebSocket +    (LangGraph +
 Workflow +    Collaboration)   MCP Tools)
 Contracts)        |               |
    |              |               |
    └──────────────┼───────────────┘
                   |
            Event Bus (Redis)
                   |
    ┌──────────────┼──────────────┐
    |              |              |
  Celery     LangGraph      Notification
  Workers    Agents          Service
    |              |              |
    └──────────────┼──────────────┘
                   |
    ┌──────────────┼──────────────┐
    |              |              |
PostgreSQL    MinIO          Vector DB
(pgvector)   (Documents)    (pgvector)
```

### Key Architecture Principles

1. **Deal Pipeline as Central Nervous System**: Every domain module is triggered by and reports back to the deal pipeline. The deal is the unit of work.

2. **Event-Driven Agent Orchestration**: Stage transitions emit events → Event bus distributes → Agents execute → Results flow back to Django → UI updates via WebSocket.

3. **Human-in-the-Loop at Decision Gates**:
   - Bid/No-Bid decision
   - Capture plan approval
   - Pricing approval
   - Proposal section approval
   - Final submission approval
   - Contract terms approval

4. **Learning Feedback Loops**: Every closed deal (won or lost) triggers the learning engine, which updates scoring weights, pricing strategies, and proposal approaches.

5. **Single System of Record**: Django/PostgreSQL remains the source of truth. AI agents read from and write back to Django via REST APIs.

6. **Progressive AI Autonomy**: The policies app governs how much autonomy agents have. Start conservative (recommend only), increase based on accuracy.

---

## Implementation Priority Order (Phase 1 Detail)

For Phase 1 (Months 0–4), implement in this sequence:

### Sprint 1-2 (Weeks 1-4): Core Pipeline Orchestration
1. **1.2.1** Stage-Triggered Agent Chains — This is the backbone
2. **1.2.5** Gate Review Automation — Control quality gates
3. **1.1.2** Decompose Opportunity Agent into sub-agents

### Sprint 3-4 (Weeks 5-8): Opportunity Intelligence
4. **1.1.1** Multi-Source Ingestion (FPDS + USASpending clients)
5. **1.1.3** Capacity-Aware Scoring
6. **1.1.5** Amendment & Change Detection

### Sprint 5-6 (Weeks 9-12): Capture & Compliance
7. **1.2.2** Capture Plan Generator
8. **1.3.1** Enhanced RFP Parsing
9. **1.3.2** Compliance Matrix Automation

### Sprint 7-8 (Weeks 13-16): Relationships & Learning
10. **1.2.3** Agency Relationship Tracker
11. **1.2.4** Stakeholder Mapping
12. **1.4.1** Past Performance Vault Enhancement
13. **1.1.4** Precision@10 Monitoring

---

## File Count Estimate

| Phase | New Files | Modified Files | Total |
|-------|-----------|----------------|-------|
| Phase 1 | ~35 | ~25 | ~60 |
| Phase 2 | ~25 | ~20 | ~45 |
| Phase 3 | ~30 | ~20 | ~50 |
| Phase 4 | ~20 | ~15 | ~35 |
| **Total** | **~110** | **~80** | **~190** |

---

## Migration Strategy

- All new Django models get their own migrations
- No breaking changes to existing models — only additions
- Existing data preserved; new fields have defaults or are nullable
- New apps (workforce) are additive to INSTALLED_APPS
- Docker Compose updated incrementally per phase
- Frontend changes are additive — new pages and components, existing pages enhanced

---

## Success Metrics

### Phase 1
- [ ] Deal stage transitions automatically trigger appropriate agents
- [ ] Opportunities scored from 3+ sources (SAM.gov, FPDS, USASpending)
- [ ] Capacity-aware scoring reduces overcommitment
- [ ] Amendment detection catches 90%+ of tracked opportunity changes
- [ ] Gate reviews block premature stage transitions
- [ ] Precision@10 tracked and visible on dashboard

### Phase 2
- [ ] Proposal workspace auto-creates on stage transition
- [ ] AI drafts all proposal sections from templates
- [ ] Red team agent identifies weaknesses before human review
- [ ] Pricing scenarios visualized with win probability curves
- [ ] Submission checklist validates 100% completeness before submission
- [ ] Immutable audit trail for all system actions

### Phase 3
- [ ] Contract auto-created on deal award
- [ ] Deliverables tracked with deadline alerts
- [ ] Workforce demand forecast from pipeline
- [ ] Executive dashboard shows cross-domain KPIs
- [ ] Learning engine updates scoring weights from outcomes

### Phase 4
- [ ] Offline RL improves agent decisions over time
- [ ] Revenue forecasting within 15% accuracy
- [ ] Competitor modeling informs pricing strategy
- [ ] Continuous compliance monitoring with drift detection
