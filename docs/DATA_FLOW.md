# AI Deal Manager — Data Flow Diagrams

**Version:** 2.0
**Last Updated:** March 2026
**Audience:** Engineers, Architects, Integration Developers

---

## Table of Contents

1. [Overview](#1-overview)
2. [Opportunity Discovery & Ingestion Flow](#2-opportunity-discovery--ingestion-flow)
3. [Deal Lifecycle Flow](#3-deal-lifecycle-flow)
4. [Proposal Generation Flow](#4-proposal-generation-flow)
5. [AI Agent Execution Flow](#5-ai-agent-execution-flow)
6. [Knowledge Vault Ingestion Flow](#6-knowledge-vault-ingestion-flow)
7. [Semantic Search Flow](#7-semantic-search-flow)
8. [Pricing Analysis Flow](#8-pricing-analysis-flow)
9. [RFP Analysis & Compliance Matrix Flow](#9-rfp-analysis--compliance-matrix-flow)
10. [Real-Time Collaboration Flow](#10-real-time-collaboration-flow)
11. [Authentication & Authorization Flow](#11-authentication--authorization-flow)
12. [Document Upload & Processing Flow](#12-document-upload--processing-flow)
13. [Notification & Alert Flow](#13-notification--alert-flow)
14. [Analytics & Reporting Flow](#14-analytics--reporting-flow)
15. [Contract Management Flow](#15-contract-management-flow)

---

## 1. Overview

This document describes the major data flows within the AI Deal Manager platform. Each flow is presented as a sequence diagram showing how data moves between system components.

### System Component Legend

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Frontend │  │ Django   │  │ FastAPI  │  │ Celery   │  │ External │
│ (Next.js)│  │ API      │  │ AI Orch  │  │ Workers  │  │ Services │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│PostgreSQL│  │  Redis   │  │  MinIO   │  │ Socket.IO│
│ + pgvec  │  │          │  │          │  │  Server  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

---

## 2. Opportunity Discovery & Ingestion Flow

This flow describes how opportunities are discovered from SAM.gov and made available to users.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  OPPORTUNITY DISCOVERY FLOW                                 │
│                                                                             │
│  Trigger: Celery Beat schedule (every 6h) OR manual "Sync SAM.gov" button  │
└─────────────────────────────────────────────────────────────────────────────┘

  User/Timer         Django API        Celery Worker     AI Orchestrator    SAM.gov
     │                   │                  │                  │               │
     │  Sync Request     │                  │                  │               │
     │──────────────────►│                  │                  │               │
     │  (or Beat timer)  │                  │                  │               │
     │                   │  Enqueue Task    │                  │               │
     │                   │─────────────────►│                  │               │
     │                   │                  │                  │               │
     │  task_id          │                  │  SAM.gov API     │               │
     │◄──────────────────│                  │  search_opps()   │               │
     │                   │                  │─────────────────►│               │
     │                   │                  │                  │  GET /opps    │
     │                   │                  │                  │──────────────►│
     │                   │                  │                  │               │
     │                   │                  │                  │  JSON results │
     │                   │                  │                  │◄──────────────│
     │                   │                  │                  │               │
     │                   │                  │  Raw opps data   │               │
     │                   │                  │◄─────────────────│               │
     │                   │                  │                  │               │
     │                   │                  │  For each new opportunity:       │
     │                   │                  │                  │               │
     │                   │                  │  Score request   │               │
     │                   │                  │─────────────────►│               │
     │                   │                  │                  │               │
     │                   │                  │                  │  ┌──────────┐ │
     │                   │                  │                  │  │ Opp Agent│ │
     │                   │                  │                  │  │          │ │
     │                   │                  │                  │  │ Score vs │ │
     │                   │                  │                  │  │ company  │ │
     │                   │                  │                  │  │ profile  │ │
     │                   │                  │                  │  │          │ │
     │                   │                  │                  │  │ NAICS    │ │
     │                   │                  │                  │  │ Past Perf│ │
     │                   │                  │                  │  │ Set-aside│ │
     │                   │                  │                  │  │ Keywords │ │
     │                   │                  │                  │  └──────────┘ │
     │                   │                  │                  │               │
     │                   │                  │  Score + rec     │               │
     │                   │                  │◄─────────────────│               │
     │                   │                  │                  │               │
     │                   │                  │                  │               │
     │                   │  Save to DB      │                  │               │
     │                   │◄─────────────────│                  │               │
     │                   │                  │                  │               │
     │                   │    ┌─────────────────────┐          │               │
     │                   │    │ PostgreSQL           │          │               │
     │                   │    │ opportunities table  │          │               │
     │                   │    │ + opportunity_scores │          │               │
     │                   │    └─────────────────────┘          │               │
     │                   │                  │                  │               │
     │                   │  Notify users    │                  │               │
     │                   │─────────────────►│                  │               │
     │                   │  (via Socket.IO) │                  │               │
     │  New opps!        │                  │                  │               │
     │◄──────────────────│                  │                  │               │
```

### Data Transformations

| Stage | Input | Output |
|---|---|---|
| SAM.gov Fetch | API query params (NAICS, keywords, date range) | Raw solicitation JSON |
| Parsing | Raw solicitation JSON | Structured Opportunity model |
| AI Scoring | Opportunity + company profile + past performance | Fit score (0-100) + recommendation (Bid/No-Bid/Evaluate) |
| Storage | Scored opportunity | DB record + user notification |

---

## 3. Deal Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEAL LIFECYCLE FLOW                                   │
│                                                                             │
│  Deals flow through 12 active stages and 3 closed stages                   │
└─────────────────────────────────────────────────────────────────────────────┘

                          ACTIVE PIPELINE
    ┌───────────────────────────────────────────────────────────────┐
    │                                                               │
    │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐          │
    │  │INTAKE│─►│QUALFY│─►│BID/  │─►│CAPTUR│─►│PROPL │          │
    │  │      │  │      │  │NO-BID│  │PLAN  │  │DEV   │          │
    │  └──────┘  └──────┘  └──┬───┘  └──────┘  └──┬───┘          │
    │                         │                     │              │
    │                         │ No-Bid              │              │
    │                         ▼                     ▼              │
    │                    ┌──────┐             ┌──────┐             │
    │                    │NO_BID│             │RED   │             │
    │                    │(clsd)│             │TEAM  │             │
    │                    └──────┘             └──┬───┘             │
    │                                            │                │
    │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  │                │
    │  │DELIVR│◄─│CONTR │◄─│AWARD │◄─│POST  │◄─┤                │
    │  │      │  │SETUP │  │PENDNG│  │SUBMIT│  │                │
    │  └──┬───┘  └──────┘  └──┬───┘  └──────┘  │                │
    │     │                    │                 ▼                │
    │     ▼                    ▼            ┌──────┐              │
    │ ┌──────┐            ┌──────┐         │FINAL │              │
    │ │CLOSED│            │CLOSED│         │REVEW │              │
    │ │WON   │            │LOST  │         └──┬───┘              │
    │ └──────┘            └──────┘            │                  │
    │                                         ▼                  │
    │                                    ┌──────┐                │
    │                                    │SUBMIT│                │
    │                                    └──────┘                │
    └───────────────────────────────────────────────────────────────┘

  Stage Transition Data:
  ┌─────────────────────────────────────┐
  │  deal_id           UUID             │
  │  from_stage        enum             │
  │  to_stage          enum             │
  │  reason            text (required)  │
  │  transitioned_by   user_id          │
  │  timestamp         datetime         │
  │  attachments       file[]           │
  └─────────────────────────────────────┘
```

---

## 4. Proposal Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PROPOSAL GENERATION FLOW                                 │
│                                                                             │
│  Multi-agent workflow orchestrated by LangGraph                             │
└─────────────────────────────────────────────────────────────────────────────┘

  User               Django API       AI Orchestrator        Agents
   │                     │                  │                   │
   │  Generate Proposal  │                  │                   │
   │────────────────────►│                  │                   │
   │                     │                  │                   │
   │                     │  Start workflow  │                   │
   │                     │─────────────────►│                   │
   │                     │                  │                   │
   │  task_id            │                  │  ┌─────────────────────────────┐
   │◄────────────────────│                  │  │ PROPOSAL GENERATION GRAPH  │
   │                     │                  │  │                             │
   │                     │                  │  │  1. RFP Analyst Agent       │
   │                     │                  │  │     ├─ Parse RFP document   │
   │                     │                  │  │     ├─ Extract requirements │
   │                     │                  │  │     └─ Build compliance     │
   │                     │                  │  │       matrix                │
   │                     │                  │  │           │                 │
   │  ◄─ Progress: 20%   │                  │  │           ▼                 │
   │  (via Socket.IO)    │                  │  │  2. Strategy Agent          │
   │                     │                  │  │     ├─ Develop win themes   │
   │                     │                  │  │     ├─ Identify discrim.    │
   │                     │                  │  │     └─ Set section strategy │
   │                     │                  │  │           │                 │
   │                     │                  │  │           ▼                 │
   │  ◄─ Progress: 40%   │                  │  │  3. Proposal Writer Agent   │
   │                     │                  │  │     ├─ Draft tech approach  │
   │                     │                  │  │     ├─ Draft mgmt approach │
   │                     │                  │  │     ├─ Draft past perf     │
   │                     │                  │  │     └─ (queries KV for     │
   │                     │                  │  │        content & PP)       │
   │                     │                  │  │           │                 │
   │                     │                  │  │           ▼                 │
   │  ◄─ Progress: 60%   │                  │  │  4. Pricing Agent           │
   │                     │                  │  │     ├─ Map labor categories │
   │                     │                  │  │     ├─ Build cost model     │
   │                     │                  │  │     └─ Generate cost        │
   │                     │                  │  │       narrative             │
   │                     │                  │  │           │                 │
   │                     │                  │  │           ▼                 │
   │  ◄─ Progress: 75%   │                  │  │  5. QA Agent                │
   │                     │                  │  │     ├─ Compliance check     │
   │                     │                  │  │     ├─ Page count check     │
   │                     │                  │  │     ├─ Format validation    │
   │                     │                  │  │     └─ Quality scoring      │
   │                     │                  │  │           │                 │
   │                     │                  │  │           ▼                 │
   │  ◄─ Progress: 90%   │                  │  │  6. Compliance Agent        │
   │                     │                  │  │     ├─ Final shredding      │
   │                     │                  │  │     ├─ Cross-ref matrix     │
   │                     │                  │  │     └─ Generate report      │
   │                     │                  │  │           │                 │
   │                     │                  │  │           ▼                 │
   │                     │                  │  │  7. Human Review Check      │
   │                     │                  │  │     └─ If confidence < 0.7  │
   │                     │                  │  │       → route to human      │
   │                     │                  │  │                             │
   │                     │                  │  └─────────────────────────────┘
   │                     │                  │                   │
   │                     │  Save sections   │                   │
   │                     │◄─────────────────│                   │
   │                     │                  │                   │
   │                     │  Store in DB +   │                   │
   │                     │  MinIO           │                   │
   │                     │                  │                   │
   │  ◄─ Complete!       │                  │                   │
   │  (via Socket.IO)    │                  │                   │
   │                     │                  │                   │
   │  View proposal      │                  │                   │
   │────────────────────►│                  │                   │
   │                     │                  │                   │
   │  Proposal data      │                  │                   │
   │◄────────────────────│                  │                   │
```

---

## 5. AI Agent Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SINGLE AGENT EXECUTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

  Caller             AI Orchestrator       LangGraph Agent        MCP Server
    │                      │                     │                     │
    │  POST /agents/       │                     │                     │
    │  {name}/run          │                     │                     │
    │─────────────────────►│                     │                     │
    │                      │                     │                     │
    │                      │  Initialize graph   │                     │
    │                      │────────────────────►│                     │
    │                      │                     │                     │
    │                      │                     │  ┌──────────────┐   │
    │                      │                     │  │ RETRIEVE     │   │
    │                      │                     │  │ CONTEXT      │   │
    │                      │                     │  │              │   │
    │                      │                     │  │ • Load deal  │   │
    │                      │                     │  │   context    │   │
    │                      │                     │  │ • Query KV   │   │
    │                      │                     │  │ • Load prior │   │
    │                      │                     │  │   agent runs │   │
    │                      │                     │  └──────┬───────┘   │
    │                      │                     │         │           │
    │                      │                     │         ▼           │
    │                      │                     │  ┌──────────────┐   │
    │                      │                     │  │ REASON       │   │
    │                      │                     │  │              │   │
    │                      │                     │  │ LLM call to  │   │
    │                      │                     │  │ Claude with  │   │
    │                      │                     │  │ context +    │   │
    │                      │                     │  │ instructions │   │
    │                      │                     │  └──────┬───────┘   │
    │                      │                     │         │           │
    │                      │                     │    Needs tools?     │
    │                      │                     │    ┌────┴────┐      │
    │                      │                     │    │         │      │
    │                      │                     │   Yes        No     │
    │                      │                     │    │         │      │
    │                      │                     │    ▼         │      │
    │                      │                     │  ┌──────┐    │      │
    │                      │                     │  │ TOOL │    │      │
    │                      │                     │  │ CALL │    │      │
    │                      │                     │  └──┬───┘    │      │
    │                      │                     │     │        │      │
    │                      │                     │     │  MCP   │      │
    │                      │                     │     │  call  │      │
    │                      │                     │     │────────┼─────►│
    │                      │                     │     │        │      │
    │                      │                     │     │  result│      │
    │                      │                     │     │◄───────┼──────│
    │                      │                     │     │        │      │
    │                      │                     │     ▼        │      │
    │                      │                     │  ┌──────────────┐   │
    │                      │                     │  │ SYNTHESIZE   │◄──┘
    │                      │                     │  │              │
    │                      │                     │  │ Combine LLM  │
    │                      │                     │  │ reasoning +  │
    │                      │                     │  │ tool results │
    │                      │                     │  │ into final   │
    │                      │                     │  │ output       │
    │                      │                     │  └──────┬───────┘
    │                      │                     │         │
    │                      │                     │   confidence ≥ 0.7?
    │                      │                     │    ┌────┴────┐
    │                      │                     │   Yes        No
    │                      │                     │    │         │
    │                      │                     │    │    ┌────▼─────┐
    │                      │                     │    │    │ HUMAN    │
    │                      │                     │    │    │ REVIEW   │
    │                      │                     │    │    │ QUEUE    │
    │                      │                     │    │    └──────────┘
    │                      │                     │    │
    │                      │  Agent result       │    │
    │                      │◄────────────────────│    │
    │                      │                     │    │
    │                      │  Log to Langfuse    │    │
    │                      │──────────────────►  │    │
    │                      │                     │    │
    │  Agent response      │                     │    │
    │◄─────────────────────│                     │    │
```

---

## 6. Knowledge Vault Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  KNOWLEDGE VAULT INGESTION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

  User            Django API        MinIO          Celery Worker     PostgreSQL
   │                  │               │                 │                │
   │  Upload doc      │               │                 │                │
   │─────────────────►│               │                 │                │
   │                  │               │                 │                │
   │                  │  Store file   │                 │                │
   │                  │──────────────►│                 │                │
   │                  │               │                 │                │
   │                  │  file_url     │                 │                │
   │                  │◄──────────────│                 │                │
   │                  │               │                 │                │
   │                  │  Create DB record              │                │
   │                  │────────────────────────────────────────────────►│
   │                  │               │                 │                │
   │                  │  Enqueue embedding task         │                │
   │                  │─────────────────────────────────►│                │
   │                  │               │                 │                │
   │  Upload success  │               │                 │                │
   │◄─────────────────│               │                 │                │
   │                  │               │                 │                │
   │                  │               │  Fetch file     │                │
   │                  │               │◄────────────────│                │
   │                  │               │                 │                │
   │                  │               │  File content   │                │
   │                  │               │────────────────►│                │
   │                  │               │                 │                │
   │                  │               │                 │  ┌───────────┐ │
   │                  │               │                 │  │ PROCESS   │ │
   │                  │               │                 │  │           │ │
   │                  │               │                 │  │ 1. Parse  │ │
   │                  │               │                 │  │    text   │ │
   │                  │               │                 │  │ 2. Chunk  │ │
   │                  │               │                 │  │    (512   │ │
   │                  │               │                 │  │    tokens │ │
   │                  │               │                 │  │    w/     │ │
   │                  │               │                 │  │    overlap│ │
   │                  │               │                 │  │ 3. Embed  │ │
   │                  │               │                 │  │    each   │ │
   │                  │               │                 │  │    chunk  │ │
   │                  │               │                 │  └─────┬─────┘ │
   │                  │               │                 │        │       │
   │                  │               │                 │  Store chunks  │
   │                  │               │                 │  + embeddings  │
   │                  │               │                 │───────────────►│
   │                  │               │                 │        │       │
   │                  │               │                 │    ┌───┴───┐   │
   │                  │               │                 │    │pgvect │   │
   │                  │               │                 │    │HNSW   │   │
   │                  │               │                 │    │index  │   │
   │                  │               │                 │    └───────┘   │
```

---

## 7. Semantic Search Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SEMANTIC SEARCH FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  User/Agent         Django API         PostgreSQL (pgvector)
     │                   │                      │
     │  Search query:    │                      │
     │  "cloud migration │                      │
     │   federal health" │                      │
     │──────────────────►│                      │
     │                   │                      │
     │                   │  1. Embed query text  │
     │                   │  using same model as  │
     │                   │  document embeddings  │
     │                   │                      │
     │                   │  2. Vector similarity  │
     │                   │  search (cosine)      │
     │                   │─────────────────────►│
     │                   │                      │
     │                   │  SELECT doc_chunks    │
     │                   │  WHERE embedding      │
     │                   │  <=> query_embedding  │
     │                   │  ORDER BY distance    │
     │                   │  LIMIT 10             │
     │                   │                      │
     │                   │  Ranked results       │
     │                   │◄─────────────────────│
     │                   │                      │
     │                   │  3. Hydrate with      │
     │                   │  parent document      │
     │                   │  metadata             │
     │                   │                      │
     │  Ranked results   │                      │
     │  with relevance   │                      │
     │  scores           │                      │
     │◄──────────────────│                      │
```

---

## 8. Pricing Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PRICING ANALYSIS FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  User             Django API       AI Orchestrator     MCP Servers
   │                   │                  │                  │
   │  Create scenario  │                  │                  │
   │──────────────────►│                  │                  │
   │                   │                  │                  │
   │                   │  Trigger Pricing │                  │
   │                   │  Agent           │                  │
   │                   │─────────────────►│                  │
   │                   │                  │                  │
   │                   │                  │  pricing_tools:  │
   │                   │                  │  get_gsa_rates() │
   │                   │                  │─────────────────►│
   │                   │                  │                  │──► GSA API
   │                   │                  │  GSA rate data   │
   │                   │                  │◄─────────────────│◄── GSA API
   │                   │                  │                  │
   │                   │                  │  pricing_tools:  │
   │                   │                  │  search_fpds()   │
   │                   │                  │─────────────────►│
   │                   │                  │                  │──► FPDS-NG
   │                   │                  │  Award history   │
   │                   │                  │◄─────────────────│◄── FPDS-NG
   │                   │                  │                  │
   │                   │                  │  market_rate:    │
   │                   │                  │  get_bls_data()  │
   │                   │                  │─────────────────►│
   │                   │                  │                  │──► BLS API
   │                   │                  │  BLS wage data   │
   │                   │                  │◄─────────────────│◄── BLS API
   │                   │                  │                  │
   │                   │                  │  ┌──────────────────────────┐
   │                   │                  │  │  PRICING AGENT           │
   │                   │                  │  │                          │
   │                   │                  │  │  1. Map labor categories │
   │                   │                  │  │     to RFP requirements  │
   │                   │                  │  │                          │
   │                   │                  │  │  2. Benchmark rates      │
   │                   │                  │  │     against GSA + FPDS   │
   │                   │                  │  │     + BLS data           │
   │                   │                  │  │                          │
   │                   │                  │  │  3. Calculate fully      │
   │                   │                  │  │     burdened rates       │
   │                   │                  │  │     (direct + fringe +   │
   │                   │                  │  │     overhead + G&A +fee) │
   │                   │                  │  │                          │
   │                   │                  │  │  4. Generate win price   │
   │                   │                  │  │     range + probability  │
   │                   │                  │  │                          │
   │                   │                  │  │  5. Write cost narrative │
   │                   │                  │  └──────────────────────────┘
   │                   │                  │                  │
   │                   │  Scenario data   │                  │
   │                   │◄─────────────────│                  │
   │                   │                  │                  │
   │  Pricing scenario │                  │                  │
   │  + win price      │                  │                  │
   │  analysis         │                  │                  │
   │◄──────────────────│                  │                  │
```

---

## 9. RFP Analysis & Compliance Matrix Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  RFP ANALYSIS & COMPLIANCE MATRIX FLOW                        │
└─────────────────────────────────────────────────────────────────────────────┘

  User             Django API        MinIO        AI Orchestrator     DB
   │                   │               │               │              │
   │  Upload RFP PDF   │               │               │              │
   │──────────────────►│               │               │              │
   │                   │  Store file   │               │              │
   │                   │──────────────►│               │              │
   │                   │               │               │              │
   │                   │  Trigger analysis             │              │
   │                   │──────────────────────────────►│              │
   │                   │               │               │              │
   │                   │               │  Fetch PDF    │              │
   │                   │               │◄──────────────│              │
   │                   │               │               │              │
   │                   │               │               │  ┌─────────────────┐
   │                   │               │               │  │ RFP ANALYST     │
   │                   │               │               │  │ AGENT           │
   │                   │               │               │  │                 │
   │                   │               │               │  │ 1. Parse PDF    │
   │                   │               │               │  │    (document_   │
   │                   │               │               │  │    tools MCP)   │
   │                   │               │               │  │                 │
   │                   │               │               │  │ 2. Identify     │
   │                   │               │               │  │    sections &   │
   │                   │               │               │  │    headings     │
   │                   │               │               │  │                 │
   │                   │               │               │  │ 3. Extract      │
   │                   │               │               │  │    requirements │
   │                   │               │               │  │    (shall/      │
   │                   │               │               │  │    should/may)  │
   │                   │               │               │  │                 │
   │                   │               │               │  │ 4. Identify     │
   │                   │               │               │  │    eval criteria│
   │                   │               │               │  │                 │
   │                   │               │               │  │ 5. Extract key  │
   │                   │               │               │  │    dates        │
   │                   │               │               │  │                 │
   │                   │               │               │  │ 6. Build        │
   │                   │               │               │  │    compliance   │
   │                   │               │               │  │    matrix       │
   │                   │               │               │  │                 │
   │                   │               │               │  │ 7. Flag         │
   │                   │               │               │  │    ambiguities  │
   │                   │               │               │  └─────────────────┘
   │                   │               │               │              │
   │                   │  Compliance matrix + analysis │              │
   │                   │◄──────────────────────────────│              │
   │                   │               │               │              │
   │                   │  Save to DB   │               │              │
   │                   │─────────────────────────────────────────────►│
   │                   │               │               │              │
   │  RFP analysis     │               │               │              │
   │  + compliance     │               │               │              │
   │  matrix           │               │               │              │
   │◄──────────────────│               │               │              │
```

---

## 10. Real-Time Collaboration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  REAL-TIME COLLABORATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  User A (editor)     Socket.IO Server     Redis Pub/Sub     User B (viewer)
       │                     │                   │                  │
       │  connect()          │                   │                  │
       │  join("deal:123")   │                   │                  │
       │────────────────────►│                   │                  │
       │                     │  subscribe        │                  │
       │                     │  "deal:123"       │  connect()       │
       │                     │──────────────────►│  join("deal:123")│
       │                     │                   │◄─────────────────│
       │                     │                   │                  │
       │  presence:join      │                   │  presence:join   │
       │◄────────────────────│                   │─────────────────►│
       │                     │                   │                  │
       │  Edit proposal      │                   │                  │
       │  section text       │                   │                  │
       │────────────────────►│                   │                  │
       │                     │  publish to       │                  │
       │                     │  "deal:123"       │                  │
       │                     │──────────────────►│                  │
       │                     │                   │  proposal:edit   │
       │                     │                   │─────────────────►│
       │                     │                   │                  │
       │                     │                   │  (User B sees    │
       │                     │                   │   live update)   │
       │                     │                   │                  │
       │  Save proposal      │                   │                  │
       │────────────────────►│                   │                  │
       │                     │  POST /api/       │                  │
       │                     │  proposals/save   │                  │
       │                     │                   │  proposal:saved  │
       │                     │                   │─────────────────►│
```

---

## 11. Authentication & Authorization Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW                                         │
└─────────────────────────────────────────────────────────────────────────────┘

  Browser              Next.js           Django API          PostgreSQL
    │                     │                  │                    │
    │  Login form submit  │                  │                    │
    │────────────────────►│                  │                    │
    │                     │                  │                    │
    │                     │  POST /auth/     │                    │
    │                     │  token/          │                    │
    │                     │─────────────────►│                    │
    │                     │                  │                    │
    │                     │                  │  SELECT user       │
    │                     │                  │  WHERE email=...   │
    │                     │                  │───────────────────►│
    │                     │                  │                    │
    │                     │                  │  User + hashed pw  │
    │                     │                  │◄───────────────────│
    │                     │                  │                    │
    │                     │                  │  bcrypt.verify()   │
    │                     │                  │                    │
    │                     │  {access, refresh}                    │
    │                     │◄─────────────────│                    │
    │                     │                  │                    │
    │  Set tokens in      │                  │                    │
    │  httpOnly cookies   │                  │                    │
    │◄────────────────────│                  │                    │
    │                     │                  │                    │
    │  Subsequent requests│                  │                    │
    │  include JWT in     │                  │                    │
    │  Authorization hdr  │                  │                    │
    │                     │                  │                    │
    │                     │  GET /api/deals/ │                    │
    │                     │  Bearer <jwt>    │                    │
    │                     │─────────────────►│                    │
    │                     │                  │                    │
    │                     │                  │  1. Decode JWT     │
    │                     │                  │  2. Extract roles  │
    │                     │                  │  3. Check RBAC     │
    │                     │                  │     permission     │
    │                     │                  │  4. Filter queryset│
    │                     │                  │     by ownership   │
    │                     │                  │                    │
    │                     │  Filtered results │                   │
    │                     │◄─────────────────│                    │
    │                     │                  │                    │
    │  Rendered page       │                  │                    │
    │◄────────────────────│                  │                    │
```

---

## 12. Document Upload & Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  DOCUMENT UPLOAD FLOW                                         │
└─────────────────────────────────────────────────────────────────────────────┘

  User           Frontend         Django API         MinIO         Celery
   │                │                 │                │              │
   │  Select file   │                 │                │              │
   │───────────────►│                 │                │              │
   │                │                 │                │              │
   │                │  POST /api/     │                │              │
   │                │  documents/     │                │              │
   │                │  (multipart)    │                │              │
   │                │────────────────►│                │              │
   │                │                 │                │              │
   │                │                 │  1. Validate   │              │
   │                │                 │     file type  │              │
   │                │                 │     & size     │              │
   │                │                 │                │              │
   │                │                 │  2. Generate   │              │
   │                │                 │     presigned  │              │
   │                │                 │     URL        │              │
   │                │                 │                │              │
   │                │                 │  PUT file      │              │
   │                │                 │───────────────►│              │
   │                │                 │                │              │
   │                │                 │  Storage URL   │              │
   │                │                 │◄───────────────│              │
   │                │                 │                │              │
   │                │                 │  3. Save DB    │              │
   │                │                 │     record     │              │
   │                │                 │                │              │
   │                │                 │  4. Enqueue    │              │
   │                │                 │     processing │              │
   │                │                 │───────────────────────────────►│
   │                │                 │                │              │
   │                │  {id, status:   │                │              │
   │                │   processing}   │                │              │
   │                │◄────────────────│                │              │
   │                │                 │                │              │
   │  Upload done   │                 │                │  Process:    │
   │◄───────────────│                 │                │  • Extract   │
   │                │                 │                │    text      │
   │                │                 │                │  • OCR if    │
   │                │                 │                │    scanned   │
   │                │                 │                │  • Chunk     │
   │                │                 │                │  • Embed     │
   │                │                 │                │  • Index     │
```

---

## 13. Notification & Alert Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  NOTIFICATION FLOW                                            │
└─────────────────────────────────────────────────────────────────────────────┘

  Event Source       Django Signal      Notification        Delivery
                                        Service             Channels
       │                  │                │                    │
       │  Deal stage      │                │                    │
       │  changed         │                │                    │
       │─────────────────►│                │                    │
       │                  │                │                    │
       │                  │  post_save     │                    │
       │                  │  signal fired  │                    │
       │                  │───────────────►│                    │
       │                  │                │                    │
       │                  │                │  Determine         │
       │                  │                │  recipients        │
       │                  │                │  based on:         │
       │                  │                │  • Deal ownership  │
       │                  │                │  • Role            │
       │                  │                │  • Preferences     │
       │                  │                │                    │
       │                  │                │  For each recipient│
       │                  │                │                    │
       │                  │                │  ┌──────────────┐  │
       │                  │                │  │ In-App       │──►Socket.IO push
       │                  │                │  └──────────────┘  │
       │                  │                │                    │
       │                  │                │  ┌──────────────┐  │
       │                  │                │  │ Email        │──►SMTP/Email service
       │                  │                │  └──────────────┘  │
       │                  │                │                    │
       │                  │                │  ┌──────────────┐  │
       │                  │                │  │ DB Record    │──►notifications table
       │                  │                │  └──────────────┘  │
```

---

## 14. Analytics & Reporting Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  ANALYTICS DATA FLOW                                         │
└─────────────────────────────────────────────────────────────────────────────┘

  Data Sources                Analytics Engine              Dashboard
                                                            (Frontend)
  ┌──────────────┐
  │ Deals        │──┐
  │ (stages,     │  │
  │  values)     │  │     ┌───────────────────────┐         ┌──────────────┐
  └──────────────┘  │     │                       │         │              │
                    ├────►│  Pipeline Metrics      │────────►│  KPI Cards   │
  ┌──────────────┐  │     │  • Total value         │         │  Pipeline    │
  │ Proposals    │──┤     │  • Stage distribution  │         │  Chart       │
  │ (status,     │  │     │  • Velocity            │         │              │
  │  scores)     │  │     └───────────────────────┘         └──────────────┘
  └──────────────┘  │
                    │     ┌───────────────────────┐         ┌──────────────┐
  ┌──────────────┐  │     │                       │         │              │
  │ Win/Loss     │──┼────►│  Win Rate Analysis    │────────►│  Win Rate    │
  │ Records      │  │     │  • YTD win rate        │         │  Gauge       │
  └──────────────┘  │     │  • By agency/type      │         │  Trends      │
                    │     │  • Historical trends   │         │              │
  ┌──────────────┐  │     └───────────────────────┘         └──────────────┘
  │ Agent Perf   │──┤
  │ Logs         │  │     ┌───────────────────────┐         ┌──────────────┐
  └──────────────┘  │     │                       │         │              │
                    ├────►│  Agent Performance     │────────►│  Agent       │
  ┌──────────────┐  │     │  • Avg latency         │         │  Dashboard   │
  │ Langfuse     │──┘     │  • Cost per run        │         │              │
  │ Traces       │        │  • Error rates         │         └──────────────┘
  └──────────────┘        │  • Quality scores      │
                          └───────────────────────┘         ┌──────────────┐
                                                            │              │
  ┌──────────────┐        ┌───────────────────────┐         │  Deadline    │
  │ Deadlines    │───────►│  Deadline Tracker      │────────►│  Calendar   │
  │ (RFP, prop,  │        │  • Upcoming items      │         │  Alerts     │
  │  contract)   │        │  • Urgency scoring     │         │              │
  └──────────────┘        └───────────────────────┘         └──────────────┘
```

---

## 15. Contract Management Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  CONTRACT LIFECYCLE FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
  │  TEMPLATE  │────►│  DRAFT       │────►│  REVIEW      │────►│  REDLINE   │
  │  SELECTION │     │  GENERATION  │     │              │     │  COMPARISON│
  │            │     │              │     │  Legal Agent  │     │            │
  │  Choose    │     │  Fill tokens │     │  reviews and  │     │  Upload    │
  │  template  │     │  from deal   │     │  flags risks  │     │  counter-  │
  │  from      │     │  metadata    │     │              │     │  party ver │
  │  library   │     │              │     │  Human legal  │     │            │
  │            │     │  Insert      │     │  review for   │     │  Side-by-  │
  │            │     │  clauses     │     │  high-risk    │     │  side diff │
  └────────────┘     └──────────────┘     └──────────────┘     └────────────┘
                                                                      │
                                                                      ▼
  ┌────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
  │  ACTIVE    │◄────│  EXECUTED    │◄────│  NEGOTIATION │◄────│  ACCEPT/   │
  │  CONTRACT  │     │  (SIGNED)    │     │              │     │  REJECT    │
  │            │     │              │     │  Back and     │     │  CHANGES   │
  │  Contracts │     │  Final       │     │  forth with   │     │            │
  │  Post-Award│     │  version     │     │  counterparty │     │  Per-change│
  │  Agent     │     │  stored in   │     │              │     │  accept or │
  │  monitors  │     │  MinIO       │     │              │     │  reject    │
  │  deliverables    │              │     │              │     │            │
  └────────────┘     └──────────────┘     └──────────────┘     └────────────┘
```

---

## Data Flow Summary Table

| Flow | Trigger | Key Components | Output |
|---|---|---|---|
| Opportunity Discovery | Celery Beat / Manual | SAM.gov API, Opportunity Agent, PostgreSQL | Scored opportunities |
| Deal Lifecycle | User action | Django API, Deal model, stage history | Stage transitions + audit log |
| Proposal Generation | User request | 6+ agents (RFP, Strategy, Writer, Pricing, QA, Compliance) | Complete proposal draft |
| Knowledge Vault Ingestion | Document upload | MinIO, Celery, embedding pipeline, pgvector | Indexed, searchable content |
| Semantic Search | User/Agent query | pgvector HNSW index, cosine similarity | Ranked results with scores |
| Pricing Analysis | User request | Pricing Agent, GSA/FPDS/BLS MCP tools | Cost scenario + win price |
| RFP Analysis | RFP upload | RFP Analyst Agent, document_tools MCP | Compliance matrix |
| Real-Time Collaboration | User edit | Socket.IO, Redis pub/sub | Live updates to all users |
| Authentication | Login | Django SimpleJWT, bcrypt, PostgreSQL | JWT access + refresh tokens |
| Notifications | System events | Django signals, Socket.IO, email | Multi-channel delivery |

---

*For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md). For API specifics, see [API_REFERENCE.md](API_REFERENCE.md).*

*This document is maintained by the platform engineering team. Last reviewed: March 2026.*
