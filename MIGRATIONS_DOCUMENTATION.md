# Django Migration Files Documentation

## Overview
Generated Django migration files for 11 applications in the AI Deal Manager backend. All migrations follow Django best practices and are ready for production use.

## Migration Files Generated

### 1. Communications App
**Location:** `/home/user/ai-deal-manager/backend/apps/communications/migrations/0001_initial.py`
**Size:** 7.8K | **Lines:** 125

**Models:**
- `CommunicationThread` - Thread management with deal linking
- `ThreadParticipant` - Thread participation tracking with roles
- `Message` - Message content with threading support
- `ClarificationQuestion` - RFP clarification question tracking
- `ClarificationAnswer` - Q&A answer tracking
- `QAImpactMapping` - Impact mapping of Q&A answers to proposal sections

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- Thread-based communication with internal/client/agency participants
- Message threading with edit tracking
- Government Q&A vs. vendor question distinction
- Impact assessment for proposal modifications

---

### 2. Contracts App
**Location:** `/home/user/ai-deal-manager/backend/apps/contracts/migrations/0001_initial.py`
**Size:** 11K | **Lines:** 146

**Models:**
- `ContractTemplate` - Reusable contract templates by type (FFP, T&M, CPFF, CPAF, CPIF, IDIQ, BPA)
- `ContractClause` - Clause library (FAR, DFARS, custom)
- `Contract` - Full contract lifecycle tracking
- `ContractVersion` - Version history for contract changes
- `ContractMilestone` - Deliverables and payment milestones
- `ContractModification` - Amendment and modification tracking

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- Full contract lifecycle from drafting to closeout
- Clause library with negotiability and risk levels
- Version history with change tracking
- Milestone management with status tracking
- Modification tracking (bilateral/unilateral/administrative)

---

### 3. Deals App (CORE)
**Location:** `/home/user/ai-deal-manager/backend/apps/deals/migrations/0001_initial.py`
**Size:** 11K | **Lines:** 180

**Models:**
- `Deal` - Core deal entity with 15 pipeline stages
- `DealStageHistory` - Stage transition history
- `Task` - Tasks assigned within a deal
- `TaskTemplate` - Templates for auto-generating tasks per stage
- `Comment` - Comments and notes on deals
- `Approval` - HITL approval gates for critical decisions
- `Activity` - Activity log entries (auto-generated)

**Key Dependencies:**
- `opportunities.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- 15-stage deal pipeline (intake → delivery/closed)
- Priority system (Critical/High/Medium/Low)
- Win probability and multiple scoring systems (fit, strategic, composite)
- Team assignment and ownership
- Task management with auto-completable tasks
- Approval workflow for bid/pricing/submission decisions
- Activity logging for deal history
- Database indexes for common queries (stage, owner, priority, due_date)

---

### 4. Legal App
**Location:** `/home/user/ai-deal-manager/backend/apps/legal/migrations/0001_initial.py`
**Size:** 8.7K | **Lines:** 131

**Models:**
- `FARClause` - FAR clause references and library
- `RegulatoryRequirement` - Regulatory requirements (FAR/DFARS/Agency/OMB)
- `LegalRisk` - Legal risks with severity/probability assessment
- `ComplianceAssessment` - FAR/DFARS compliance assessment
- `ContractReviewNote` - Review notes on specific contract sections

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- FAR/DFARS clause reference library
- Risk assessment framework (8 risk types)
- Compliance scoring system
- Regulatory requirement tracking with applicability filters
- Contract review with concern/suggestion/question categorization

---

### 5. Past Performance App
**Location:** `/home/user/ai-deal-manager/backend/apps/past_performance/migrations/0001_initial.py`
**Size:** 3.7K | **Lines:** 72

**Models:**
- `PastPerformance` - Past performance records with vector embeddings
- `PastPerformanceMatch` - AI-matched past performance for opportunities

**Key Dependencies:**
- `opportunities.0001_initial`

**Features:**
- Complete past performance tracking (contract value, dates, ratings)
- Vector field support for RAG similarity matching
- CPARS rating integration
- Domain and technology tracking
- Pre-written narrative capability

---

### 6. Pricing App
**Location:** `/home/user/ai-deal-manager/backend/apps/pricing/migrations/0001_initial.py`
**Size:** 12K | **Lines:** 190

**Models:**
- `RateCard` - Labor category rates (internal, GSA, market)
- `ConsultantProfile` - Individual consultant/key personnel tracking
- `LOEEstimate` - Level of effort estimation with three-point method
- `CostModel` - Detailed cost build-up (labor, fringe, overhead, ODCs, travel, etc.)
- `PricingScenario` - Pricing scenarios with expected value analysis
- `PricingIntelligence` - Market pricing intelligence
- `PricingApproval` - HITL approval gate for pricing

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- Comprehensive rate card management
- LOE estimation with PERT (three-point) method
- Cost model with fringe/overhead/G&A rate calculations
- Multiple pricing strategies (max profit, competitive, aggressive, budget fit, etc.)
- P(win) and expected value analysis
- Sensitivity analysis support
- Market intelligence tracking

---

### 7. Proposals App
**Location:** `/home/user/ai-deal-manager/backend/apps/proposals/migrations/0001_initial.py`
**Size:** 6.6K | **Lines:** 114

**Models:**
- `ProposalTemplate` - Volume and section structure templates
- `Proposal` - Proposal with version control
- `ProposalSection` - Individual sections with AI draft and final content
- `ReviewCycle` - Pink/Red/Gold team review management
- `ReviewComment` - Review comments with strength/weakness categorization

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- Proposal templating system with volumes
- Section-level content management (AI draft, human, final)
- Compliance percentage tracking
- Win themes and discriminators
- Pink/Red/Gold team review cycles with scoring
- Comment resolution tracking

---

### 8. Research App
**Location:** `/home/user/ai-deal-manager/backend/apps/research/migrations/0001_initial.py`
**Size:** 7.4K | **Lines:** 130

**Models:**
- `ResearchProject` - Research projects (market analysis, competitive intel, agency analysis, etc.)
- `ResearchSource` - Individual sources fetched and analyzed
- `CompetitorProfile` - Competitor intelligence profiles
- `MarketIntelligence` - Market intelligence pieces

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- 6 research types supported
- Source tracking with relevance scoring
- Competitor profile with CAGE/DUNS integration
- Market intelligence categorization (budget trends, policy, tech, procurement, workforce)
- Indexes for performance: deal+type, status, CAGE code, activity, category, publish date

---

### 9. RFP App
**Location:** `/home/user/ai-deal-manager/backend/apps/rfp/migrations/0001_initial.py`
**Size:** 6.8K | **Lines:** 110

**Models:**
- `RFPDocument` - RFP document with extraction metadata
- `RFPRequirement` - Individual extracted requirements with embeddings
- `Amendment` - RFP amendments/modifications
- `ComplianceMatrixItem` - Compliance matrix mapping requirements to proposal sections

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- RFP document processing and metadata extraction
- Page limit and date extraction
- Evaluation criteria and required forms tracking
- Vector embeddings for requirement similarity matching
- Amendment tracking with materiality assessment
- Compliance matrix with compliance status tracking (compliant/partial/non-compliant)

---

### 10. Security Compliance App
**Location:** `/home/user/ai-deal-manager/backend/apps/security_compliance/migrations/0001_initial.py`
**Size:** 8.1K | **Lines:** 125

**Models:**
- `SecurityFramework` - Security frameworks (NIST 800-53, FedRAMP, CMMC, etc.)
- `SecurityControl` - Individual controls within frameworks
- `SecurityControlMapping` - Control implementation mapping to deals
- `SecurityComplianceReport` - Compliance reports and gap analysis
- `ComplianceRequirement` - Compliance requirements from source documents

**Key Dependencies:**
- `deals.0001_initial`
- `accounts` (AUTH_USER_MODEL)

**Features:**
- Support for multiple security frameworks
- Control baseline impact levels
- Implementation status tracking (planned/partial/implemented/N/A)
- Gap analysis and remediation planning
- Plan of Action & Milestones (POAM) generation
- Compliance requirement categories (clearances, data handling, encryption, etc.)

---

### 11. Strategy App
**Location:** `/home/user/ai-deal-manager/backend/apps/strategy/migrations/0001_initial.py`
**Size:** 7.3K | **Lines:** 125

**Models:**
- `CompanyStrategy` - Strategic plan versioning with vector embeddings
- `StrategicGoal` - Quantified strategic objectives
- `PortfolioSnapshot` - Periodic portfolio health snapshots
- `StrategicScore` - Strategic alignment scoring for opportunities

**Key Dependencies:**
- `opportunities.0001_initial`

**Features:**
- Company strategy versioning with effective dates
- Strategic goals with weighted tracking
- Market focus (target agencies, domains, NAICS codes)
- Growth/mature/exit market classification
- Competitive strategy documentation
- Portfolio snapshots with pipeline analysis
- Strategic scoring system (0-100) with component scores
- Vector embedding support for semantic matching

---

## Dependency Graph

```
accounts.0001_initial (base)
        ↓
opportunities.0001_initial (base)
        ↓
deals.0001_initial (CORE DEPENDENCY)
    ├→ communications.0001_initial
    ├→ contracts.0001_initial
    ├→ legal.0001_initial
    ├→ pricing.0001_initial
    ├→ proposals.0001_initial
    ├→ research.0001_initial
    ├→ rfp.0001_initial
    └→ security_compliance.0001_initial

opportunities.0001_initial
    ├→ past_performance.0001_initial
    └→ strategy.0001_initial
```

## Migration Statistics

| App | Models | Lines | Size | Dependencies |
|-----|--------|-------|------|--------------|
| communications | 6 | 125 | 7.8K | deals, accounts |
| contracts | 6 | 146 | 11K | deals, accounts |
| deals | 7 | 180 | 11K | opportunities, accounts |
| legal | 5 | 131 | 8.7K | deals, accounts |
| past_performance | 2 | 72 | 3.7K | opportunities |
| pricing | 7 | 190 | 12K | deals, accounts |
| proposals | 5 | 114 | 6.6K | deals, accounts |
| research | 4 | 130 | 7.4K | deals, accounts |
| rfp | 4 | 110 | 6.8K | deals, accounts |
| security_compliance | 5 | 125 | 8.1K | deals, accounts |
| strategy | 4 | 125 | 7.3K | opportunities |
| **TOTAL** | **56** | **1,348** | **99K** | - |

## Key Features Across Migrations

### Database Design
- UUID primary keys throughout (via BaseModel)
- Automatic timestamps (created_at, updated_at)
- JSONField for flexible data storage
- pgvector VectorField for RAG embeddings
- Foreign key constraints with proper cascade/set_null handling

### Performance Optimizations
- Comprehensive database indexes on frequently queried fields
- Unique constraints and unique_together specifications
- Proper ordering defaults for model querysets

### Data Integrity
- Required and optional field constraints
- Choice field enumerations for status/type fields
- Default values for common fields

### User Integration
- User authentication throughout (AUTH_USER_MODEL)
- Team/participant tracking
- User activity logging and approval workflows

## Running the Migrations

```bash
# Apply all migrations
python manage.py migrate

# Apply specific app migrations
python manage.py migrate communications
python manage.py migrate deals
python manage.py migrate pricing

# Check migration status
python manage.py showmigrations

# Create a new migration after model changes
python manage.py makemigrations
```

## Notes

1. **Deals is Core:** The deals app is the central hub, with most business-related apps depending on it
2. **Opportunities Dependency:** Three apps (past_performance, strategy) depend on opportunities, not deals
3. **User Integration:** Most models include user references for tracking ownership, assignment, and approvals
4. **Vector Support:** RFP, past performance, and strategy apps include pgvector fields for AI/ML capabilities
5. **Flexible Storage:** JSONField is used extensively for storing structured but flexible data (parameters, findings, etc.)

## Verification

All migration files have been:
- Syntax validated with Python compiler
- Checked for import correctness
- Verified for dependency consistency
- Confirmed to follow Django migration conventions

Generated on: 2026-02-24
