# GovCon-Policies Integration Enhancement Plan

## Overview

This plan integrates all 8 Bidvantage GovCon-Policies documents into the AI-GovCon-System to create a **super-smart, end-to-end proposal creation platform** that maximizes win rates for SAM.gov government contracts.

**Documents Analyzed:**
1. Capability Statement Example (visual template)
2. Capability Statement Guide (structure & best practices)
3. Proposal Submission Checklist (pre-proposal + proposal checklists)
4. SAM Registration Guide (10-step registration process)
5. The Vault eBook (36-page comprehensive GovCon guide covering subcontracting, NAICS, SBA certifications, evaluation methods, contract types, teaming, capability statements, sources sought)
6. Email Proposal Submission Templates (proposal + RFQ email templates)
7. Past Performance & Experience Template (structured table format with example)
8. Proposal Template (full proposal structure: exec summary, technical approach, management, past performance, business compliance, reporting)

---

## ENHANCEMENT 1: SAM.gov Registration & Compliance Wizard

**Source:** SAM Registration Guide + The Vault (Ch. II - SAM.gov Tips)

**What:** A guided wizard that walks users through SAM.gov registration readiness and monitors compliance.

### Backend Changes

**File:** `backend/apps/opportunities/models.py` - Add new model:

```python
class SAMRegistration(models.Model):
    company_profile = models.OneToOneField('CompanyProfile', on_delete=models.CASCADE)
    # Core registration data
    legal_business_name = models.CharField(max_length=500)
    physical_address = models.JSONField(default=dict)  # street, city, state, zip
    taxpayer_id_type = models.CharField(choices=[('ein','EIN'),('ssn','SSN')])
    uei_number = models.CharField(max_length=20, blank=True)
    cage_code = models.CharField(max_length=10, blank=True)
    entity_type = models.CharField(max_length=100)  # LLC, Corp, etc.
    # Registration status tracking
    registration_status = models.CharField(choices=[
        ('not_started','Not Started'), ('in_progress','In Progress'),
        ('submitted','Submitted'), ('active','Active'), ('expired','Expired')
    ])
    registration_date = models.DateField(null=True)
    expiration_date = models.DateField(null=True)
    renewal_reminder_sent = models.BooleanField(default=False)
    # Validation checklist from The Vault
    name_matches_irs = models.BooleanField(default=False)
    address_matches_irs = models.BooleanField(default=False)
    ein_verified = models.BooleanField(default=False)
    bank_info_business_account = models.BooleanField(default=False)
    correct_entity_type = models.BooleanField(default=False)
    naics_codes_added = models.BooleanField(default=False)
    reps_certs_complete = models.BooleanField(default=False)
    pocs_added = models.BooleanField(default=False)
```

**File:** `backend/apps/opportunities/views.py` - Add SAMRegistrationViewSet with:
- CRUD + `check_expiration` action (alerts 30 days before expiry per guide)
- `validation_checklist` action returning completion status of all fields

### Frontend Changes

**File:** `frontend/src/app/(dashboard)/sam-registration/page.tsx` - New page:
- Step-by-step wizard matching the 10 steps from the SAM Registration Guide
- Validation checklist with green/red indicators per The Vault's "Tips to Get Approved First Time"
- Common mistakes warnings (don't mark as gov entity, match IRS name exactly, etc.)
- Expiration countdown + auto-renewal reminders
- "You Don't Need SBA Certification to Start Bidding" info banner

---

## ENHANCEMENT 2: Capability Statement Generator

**Source:** Capability Statement Guide + Capability Statement Example

**What:** AI-powered capability statement builder that follows the exact Bidvantage structure.

### Backend Changes

**File:** `backend/apps/marketing/models.py` - Add new model:

```python
class CapabilityStatement(models.Model):
    company_profile = models.ForeignKey('opportunities.CompanyProfile', on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)
    # Sections per the Capability Statement Guide
    company_overview = models.TextField()  # Mission, values, achievements
    core_competencies = models.JSONField(default=list)  # 3-5 capabilities with action verbs
    differentiators = models.JSONField(default=list)  # Unique value props
    past_performance_highlights = models.JSONField(default=list)
    # Company Data section
    duns_number = models.CharField(max_length=20, blank=True)
    cage_code = models.CharField(max_length=10)
    naics_codes = models.JSONField(default=list)
    sba_designations = models.JSONField(default=list)  # SB, WOSB, SDVOSB, 8(a), HUBZone
    certifications = models.JSONField(default=list)
    contract_vehicles = models.JSONField(default=list)  # GSA Schedule, SEWP V, etc.
    # Contact info
    poc_name = models.CharField(max_length=200)
    poc_title = models.CharField(max_length=200)
    poc_phone = models.CharField(max_length=20)
    poc_email = models.EmailField()
    website_url = models.URLField(blank=True)
    physical_address = models.TextField()
    # Targeting (per Guide: "Tailor to the opportunity")
    target_agency = models.CharField(max_length=300, blank=True)
    target_opportunity = models.ForeignKey('opportunities.Opportunity', null=True, blank=True, on_delete=models.SET_NULL)
    # Status
    status = models.CharField(choices=[('draft','Draft'),('review','In Review'),('final','Final')])
    generated_pdf_url = models.URLField(blank=True)
```

### AI Agent Changes

**File:** `ai_orchestrator/src/agents/capability_statement_agent.py` - New agent:
- Takes company profile + optional target agency/opportunity
- Generates compelling company overview using action verbs (per Guide)
- Selects and writes 3-5 core competencies aligned to target
- Crafts differentiators emphasizing certifications, tech, customer service
- Auto-populates company data from CompanyProfile
- Follows the one-page concise format per the Guide's "Final Tips"

### Frontend Changes

**File:** `frontend/src/app/(dashboard)/capability-statements/page.tsx` - New page:
- Visual builder matching the Bidvantage Example layout
- Section-by-section editing with AI suggestions
- Live preview (matching the blue/white Bidvantage design)
- One-click PDF export
- "Tailor for Agency" button to customize per opportunity
- SBA designation selector with eligibility guide (from The Vault Ch. II)

---

## ENHANCEMENT 3: Smart Proposal Builder (Full Bidvantage Template)

**Source:** Proposal Template + Proposal Submission Checklist + The Vault (Ch. IV & V)

**What:** Complete proposal generation following the exact Bidvantage proposal structure with AI-powered section drafting.

### Backend Changes

**File:** `backend/apps/proposals/models.py` - Enhance existing models:

```python
# Add to Proposal model:
class Proposal:
    # New fields from Proposal Template
    solicitation_number = models.CharField(max_length=100)
    project_title = models.CharField(max_length=500)
    soliciting_agency = models.CharField(max_length=300)
    proposal_valid_days = models.IntegerField(default=90)
    signature_authority_name = models.CharField(max_length=200)
    signature_authority_title = models.CharField(max_length=200)
    signature_authority_phone = models.CharField(max_length=20)
    signature_authority_email = models.EmailField(blank=True)
    # Evaluation method awareness (from The Vault Ch. V)
    evaluation_method = models.CharField(choices=[
        ('lpta', 'Lowest Price Technically Acceptable'),
        ('price_eval', 'Price Evaluation'),
        ('best_value', 'Best Value / Tradeoff'),
    ], blank=True)
    # Contract type (from The Vault Ch. VI)
    contract_type = models.CharField(choices=[
        ('ffp', 'Firm Fixed Price'),
        ('tm', 'Time & Materials'),
        ('cpff', 'Cost Plus Fixed Fee'),
    ], blank=True)
    # Submission tracking
    submission_method = models.CharField(max_length=100, blank=True)  # email, PIEE, SAM, FedConnect
    submission_email = models.EmailField(blank=True)
    submitted_at = models.DateTimeField(null=True)
    submission_confirmation = models.TextField(blank=True)

# New model for structured proposal sections matching the template
class ProposalVolume(models.Model):
    """Maps to the exact Bidvantage Proposal Template structure"""
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    volume_type = models.CharField(choices=[
        ('cover', 'Cover Page'),
        ('executive_summary', '1. Executive Summary'),
        ('technical_approach', '2. Technical Approach'),
        ('technical_how', '2.1 How Work Will Be Performed'),
        ('technical_manpower', '2.2 Manpower and Resources'),
        ('past_performance', '3. Past Performance'),
        ('management_structure', '4. Management Structure'),
        ('project_oversight', '4.1 Project Oversight'),
        ('key_personnel', '4.2 Key Personnel'),
        ('business_compliance', '5. Business Management & Compliance'),
        ('required_documents', '5.1 Required Documents'),
        ('reporting', '5.2 Reporting'),
        ('sam_registration', '5.3 SAM Registration'),
        ('insurance', '5.4 Insurance Compliance'),
        ('pricing', 'Cost/Price Volume'),
    ])
    ai_draft = models.TextField(blank=True)
    human_content = models.TextField(blank=True)
    final_content = models.TextField(blank=True)
    status = models.CharField(choices=[
        ('not_started','Not Started'), ('ai_drafted','AI Drafted'),
        ('in_review','In Review'), ('revised','Revised'), ('approved','Approved')
    ])
    word_count = models.IntegerField(default=0)
    page_limit = models.IntegerField(null=True)
    assigned_to = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)
```

### AI Agent Enhancement

**File:** `ai_orchestrator/src/agents/proposal_writer_agent.py` - Major upgrade:
- Add all missing sections from the Bidvantage template
- Each section gets a dedicated drafting node with template-specific prompts
- Evaluation method awareness: AI adjusts writing style based on LPTA vs Best Value vs Price Eval (from The Vault Ch. V)
  - LPTA: Focus on compliance, meet requirements, avoid extras
  - Best Value: Highlight differentiators, past performance, innovation
  - Price Eval: Clear pricing breakdowns and justifications
- Contract type awareness: T&M proposals include labor category rates; FFP includes fixed-price justification (from The Vault Ch. VI)
- Cover page auto-generation with solicitation #, UEI, CAGE, SBA status
- Executive summary templates with company introduction + key differentiators + commitment statement
- Technical approach structured as phased methodology per the template
- Manpower section with org chart data and resource planning
- Management structure with oversight approach + communication plan
- Business compliance section with attachments checklist
- Reporting section with monthly status report template
- Proprietary notice auto-insertion (from the template)
- "Proposal valid for 90 days" auto-insertion

### Persistence Layer

**File:** `backend/apps/proposals/services/generator.py` - New service:
- `generate_section(proposal_id, section_type)` - Generates and saves to ProposalSection
- `generate_full_proposal(proposal_id)` - Orchestrates all sections
- Saves AI drafts to database immediately after generation
- Updates compliance percentage on each section completion

**File:** `backend/apps/proposals/services/docx_renderer.py` - New service:
- Renders final proposal to DOCX matching the Bidvantage template format
- Cover page with logo, company data, solicitation info, proprietary notice
- Automatic Table of Contents with hyperlinks
- Solicitation number in header/footer on every page (per Checklist)
- Past performance tables matching the Bidvantage Past Performance Template format
- Proper formatting: font, margins, spacing per solicitation requirements

---

## ENHANCEMENT 4: Past Performance Manager

**Source:** Past Performance & Experience Template

**What:** Structured past performance repository with the exact Bidvantage table format and AI-powered matching.

### Backend Changes

**File:** `backend/apps/past_performance/models.py` - Enhance:

```python
class PastPerformance:
    # Add fields matching the Bidvantage template exactly
    subcontract_number = models.CharField(max_length=100, blank=True)
    technical_poc_name = models.CharField(max_length=200)
    technical_poc_phone = models.CharField(max_length=20)
    period_of_performance_start = models.DateField()
    period_of_performance_end = models.DateField(null=True)
    contract_value = models.DecimalField(max_digits=14, decimal_places=2)
    contract_type = models.CharField(choices=[
        ('ffp','Firm Fixed Price'), ('tm','Time & Materials'),
        ('cpff','Cost Plus Fixed Fee'), ('idiq','IDIQ'), ('bpa','BPA')
    ])
    relevance_summary = models.TextField()  # Short relevance statement
    performance_summary = models.TextField()  # How well work was performed
    scope_of_work_bullets = models.JSONField(default=list)  # Bullet list of completed scope
    # CPARS integration
    cpars_rating = models.CharField(choices=[
        ('exceptional','Exceptional'), ('very_good','Very Good'),
        ('satisfactory','Satisfactory'), ('marginal','Marginal'),
        ('unsatisfactory','Unsatisfactory')
    ], blank=True)
```

### AI Agent

**File:** `ai_orchestrator/src/agents/past_performance_matcher_agent.py` - New agent:
- Semantic matching using pgvector embeddings
- Matches by: NAICS code, scope similarity, contract size, contract type, agency
- Auto-generates relevance narratives tailored to the specific solicitation
- Ranks past performance entries by relevance score
- Formats output into the exact Bidvantage table structure

### Frontend Changes

**File:** `frontend/src/app/(dashboard)/past-performance/page.tsx` - Enhance:
- Data entry form matching the Bidvantage template table format
- "Quick Add" with the template's fill-in fields
- AI-powered scope bullet generation from descriptions
- Relevance scoring visualization per opportunity
- One-click insert into proposal

---

## ENHANCEMENT 5: Proposal Submission Checklist Engine

**Source:** Proposal Submission Checklist (Pre-Proposal + Proposal checklists)

**What:** Interactive, AI-validated checklist that prevents non-compliant submissions.

### Backend Changes

**File:** `backend/apps/proposals/models.py` - Enhance SubmissionChecklist:

```python
class SubmissionChecklist:
    # Pre-populated from the Bidvantage checklist
    CHECKLIST_ITEMS = {
        'pre_proposal': [
            ('sam_active', 'Verify SAM registration is active and not expired'),
            ('sam_profile_current', 'Check address, POCs, and details are current'),
            ('understand_eval_criteria', 'Understand LPTA, best value, tradeoff criteria'),
            ('assess_volumes', 'Determine technical, pricing, past performance volumes needed'),
            ('naics_alignment', 'Verify NAICS code aligns with capabilities'),
            ('solicitation_alignment', 'Confirm solicitation aligns with capabilities'),
            ('set_aside_eligibility', 'Identify applicable set-asides (WOSB, SDVOSB, HUBZone, 8(a))'),
            ('pre_proposal_events', 'Attend Pre-Proposal Conference/Site Visit'),
            ('document_clarifications', 'Record Q&A clarifications'),
            ('submit_questions', 'Submit questions before Q&A deadline'),
            ('track_responses', 'Save government responses for compliance'),
        ],
        'proposal': [
            ('due_date_noted', 'Record exact deadline with date, time, timezone'),
            ('delivery_method_confirmed', 'Verify submission method (email, PIEE, SAM, FedConnect)'),
            ('compliance_matrix_created', 'Create compliance matrix mapping requirements to responses'),
            ('proposal_calendar', 'Plan internal deadlines for drafts, pricing, reviews'),
            ('cover_page', 'Cover page: solicitation #, title, company, UEI, CAGE, SBA status, signature'),
            ('formatting_compliance', 'Check font, margins, spacing, page limits per section'),
            ('reps_certs_complete', 'Complete Representations & Certifications'),
            ('amendments_acknowledged', 'Acknowledge all amendments'),
            ('solicitation_signed', 'Sign solicitation documents'),
            ('technical_approach', 'Technical approach tailored to SOW'),
            ('management_approach', 'Management approach with staffing, org chart, risk, schedule'),
            ('past_performance', 'Past performance matched to scope/NAICS/size with CPARS'),
            ('key_personnel_resumes', 'Key personnel resumes match roles and highlight experience'),
            ('pricing_detailed', 'Pricing table: labor categories, hours, rates, totals, CLIN structure'),
            ('toc_included', 'Table of Contents with hyperlinks and final page numbers'),
            ('sol_number_header', 'Solicitation number in header/footer on every page'),
            ('attachments_reviewed', 'All required forms, certifications, submittals included'),
            ('final_compliance_check', 'Verified against solicitation instructions and eval criteria'),
            ('files_converted', 'Converted to PDF, flattened, named as instructed'),
            ('submitted_on_time', 'Submitted with confirmation/timestamped receipt'),
        ]
    }
```

### AI Integration

- Auto-check items where possible (e.g., check SAM status via API, verify solicitation # in headers)
- AI scans proposal content to validate technical approach covers SOW
- AI validates NAICS alignment between company profile and solicitation
- Red/yellow/green compliance score based on checklist completion
- Blocks submission if critical items are incomplete

### Frontend Changes

**File:** `frontend/src/app/(dashboard)/proposals/[id]/checklist/page.tsx` - New page:
- Two-phase checklist: Pre-Proposal then Proposal
- Auto-checked items with manual override
- Progress bar per phase
- "Cannot Submit" warning if critical items incomplete
- Print-friendly version for team review

---

## ENHANCEMENT 6: Email Submission Templates

**Source:** Email Proposal Submission Templates

**What:** Auto-generated, pre-filled submission emails.

### Backend Changes

**File:** `backend/apps/proposals/models.py` - Add:

```python
class SubmissionEmail(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    email_type = models.CharField(choices=[
        ('proposal', 'Full Proposal Submission'),
        ('rfq', 'RFQ Quote Submission'),
    ])
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=500)
    body = models.TextField()
    attachments_list = models.JSONField(default=list)
    sent_at = models.DateTimeField(null=True)
    confirmation_received = models.BooleanField(default=False)
```

### AI Auto-Population

- Pre-fills from the Bidvantage email templates
- Auto-populates: solicitation #, company name, project title, contact info
- Lists all attachments (SF-1449, amendments, technical, cost, past performance, insurance)
- Compliance areas auto-detected from solicitation
- "Copy to Clipboard" for quick email composition

---

## ENHANCEMENT 7: Bid-Readiness & Opportunity Scoring

**Source:** The Vault (Ch. II - Preparing Your Business, Ch. III - Finding Opportunities, Purchase Thresholds)

**What:** AI-powered bid-readiness assessment and opportunity scoring with purchase threshold intelligence.

### Backend Changes

**File:** `backend/apps/opportunities/models.py` - Enhance OpportunityScore:

```python
class OpportunityScore:
    # Add purchase threshold intelligence
    purchase_category = models.CharField(choices=[
        ('micro', 'Micro-Purchase (< $10K)'),
        ('simplified', 'Simplified Acquisition ($10K-$250K)'),
        ('commercial', 'Commercial Items (< $10M)'),
        ('full_open', 'Full & Open Competition'),
    ], blank=True)
    # Set-aside analysis
    small_business_set_aside = models.BooleanField(default=False)
    set_aside_match = models.BooleanField(default=False)
    # Bid-readiness factors
    company_naics_match = models.BooleanField(default=False)
    has_relevant_past_performance = models.BooleanField(default=False)
    meets_clearance_requirements = models.BooleanField(default=False)
    within_size_standard = models.BooleanField(default=False)
    # Strategic recommendation
    entry_strategy = models.CharField(choices=[
        ('prime', 'Bid as Prime'),
        ('sub', 'Pursue as Subcontractor'),
        ('team', 'Form Teaming Arrangement'),
        ('jv', 'Form Joint Venture'),
        ('sources_sought', 'Respond to Sources Sought First'),
        ('no_bid', 'No Bid'),
    ], blank=True)
    entry_strategy_rationale = models.TextField(blank=True)
```

### AI Agent Enhancement

**File:** `ai_orchestrator/src/agents/opportunity_scorer_agent.py` - Enhanced agent:
- Purchase threshold categorization (Micro $10K / SAT $250K / Commercial $10M)
- Auto-detect if $10K-$250K = automatic small business set-aside
- SBA certification matching (WOSB, SDVOSB, HUBZone, 8(a)) per The Vault Ch. II
- Teaming vs JV recommendation based on opportunity size and capabilities (per The Vault Ch. VII)
- Sources Sought response recommendation when pre-solicitation notices found
- "Can you bid without SBA certification?" logic (per The Vault: YES, you can bid with just active SAM)

### Frontend Changes

**File:** `frontend/src/app/(dashboard)/opportunities/page.tsx` - Enhance:
- Purchase threshold badge (Micro/Simplified/Commercial/Full Open)
- "Small Business Set-Aside" indicator
- "Your Match" score with breakdown
- "Recommended Strategy" chip (Prime / Sub / Team / JV / Sources Sought)
- "Bid Readiness" checklist for each opportunity
- NAICS code match highlighting

---

## ENHANCEMENT 8: Sources Sought Response Generator

**Source:** The Vault (Ch. VIII - Sources Sought)

**What:** AI-powered Sources Sought response generator following the exact Bidvantage template.

### Backend Changes

**File:** `backend/apps/proposals/models.py` - Add:

```python
class SourcesSoughtResponse(models.Model):
    opportunity = models.ForeignKey('opportunities.Opportunity', on_delete=models.CASCADE)
    company_profile = models.ForeignKey('opportunities.CompanyProfile', on_delete=models.CASCADE)
    # Response sections per The Vault template
    capability_summary = models.TextField()
    relevant_past_performance = models.JSONField(default=list)
    staffing_and_resources = models.TextField()
    business_info = models.JSONField(default=dict)  # corp type, location, POC
    # Optional additions
    geographic_service_area = models.TextField(blank=True)
    security_clearances = models.TextField(blank=True)
    certifications_list = models.JSONField(default=list)
    surge_capability = models.TextField(blank=True)
    # Status
    status = models.CharField(choices=[
        ('draft','Draft'), ('review','In Review'), ('submitted','Submitted')
    ])
    submitted_at = models.DateTimeField(null=True)
    generated_pdf_url = models.URLField(blank=True)
```

### AI Agent

**File:** `ai_orchestrator/src/agents/sources_sought_agent.py` - New agent:
- Auto-generates 1-3 page response per The Vault's format
- Pulls company data from CompanyProfile
- Matches relevant past performance using pgvector
- Writes capability summary aligned to agency needs
- Includes UEI, CAGE, NAICS, certifications
- Generates PDF output

---

## ENHANCEMENT 9: SBA Certification & Set-Aside Tracker

**Source:** The Vault (Ch. II - SBA Categories)

**What:** Track all 8 SBA certification types with eligibility checking.

### Backend Changes

**File:** `backend/apps/opportunities/models.py` - Add:

```python
class SBACertification(models.Model):
    company_profile = models.ForeignKey('CompanyProfile', on_delete=models.CASCADE)
    certification_type = models.CharField(choices=[
        ('sb', 'Small Business'),
        ('sdb', 'Small Disadvantaged Business'),
        ('8a', '8(a) Business Development'),
        ('wosb', 'Woman-Owned Small Business'),
        ('edwosb', 'Economically Disadvantaged WOSB'),
        ('vosb', 'Veteran-Owned Small Business'),
        ('sdvosb', 'Service-Disabled Veteran-Owned'),
        ('hubzone', 'HUBZone'),
    ])
    status = models.CharField(choices=[
        ('not_applicable','N/A'), ('eligible','Eligible'),
        ('applied','Applied'), ('certified','Certified'), ('expired','Expired')
    ])
    certification_date = models.DateField(null=True)
    expiration_date = models.DateField(null=True)
    certification_number = models.CharField(max_length=100, blank=True)
    eligibility_notes = models.TextField(blank=True)
```

### Frontend Changes

- Certification dashboard with eligibility guide per The Vault
- VOSB vs SDVOSB distinction explained (per The Vault: only SDVOSB gets federal set-asides)
- Set-aside opportunity filter matching your certifications
- "You can bid without certification" education banner

---

## ENHANCEMENT 10: Teaming & Subcontracting Intelligence

**Source:** The Vault (Ch. VII - Teaming Partner vs Joint Venture, Lower Tier Subcontractors)

**What:** Smart teaming partner discovery and subcontractor management.

### Backend Changes

**File:** `backend/apps/teaming/models.py` - Enhance:

```python
class TeamingArrangement(models.Model):
    opportunity = models.ForeignKey('opportunities.Opportunity', on_delete=models.CASCADE)
    arrangement_type = models.CharField(choices=[
        ('teaming', 'Teaming Partner'),
        ('jv', 'Joint Venture'),
        ('subcontractor', 'Subcontractor (Lower Tier)'),
    ])
    partner_company = models.CharField(max_length=300)
    partner_role = models.CharField(choices=[
        ('prime', 'Prime Contractor'),
        ('sub', 'Subcontractor'),
        ('equal', 'Equal Partner (JV)'),
    ])
    # Per The Vault: how to include in proposal
    disclosure_sections = models.JSONField(default=list)  # ['technical_approach', 'staffing', 'past_performance']
    partner_capabilities = models.TextField()
    percentage_of_work = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    teaming_agreement_signed = models.BooleanField(default=False)
```

### AI Agent Enhancement

- Recommend teaming vs JV vs subcontractor based on:
  - Project scope (short-term = teaming, long-term = JV)
  - Resource requirements
  - SBA size standard implications
- Auto-populate proposal sections per The Vault guidance on where to disclose subcontractors
- Generate teaming partner capability summaries for proposal integration

---

## ENHANCEMENT 11: Compliance Matrix & Evaluation-Aware Scoring

**Source:** The Vault (Ch. V - Evaluation Methods) + Proposal Checklist

**What:** Build a compliance matrix that maps every solicitation requirement to a proposal response, and tailor strategy by evaluation method.

### AI Agent Enhancement

**File:** `ai_orchestrator/src/agents/compliance_agent.py` - Major upgrade:
- Parse solicitation requirements from Sections L and M
- Build compliance matrix: requirement -> proposal section -> status
- Score by evaluation method:
  - **LPTA**: Score = compliance completeness (meet all requirements, nothing extra)
  - **Best Value**: Score = compliance + innovation + past performance + differentiators
  - **Price Eval**: Score = pricing competitiveness + transparency
- Store matrix in database as structured JSON
- Create RedTeamFinding records for every gap
- Auto-check: SBA status on cover page, solicitation # in headers, page count compliance
- Generate remediation recommendations

### Frontend Changes

**File:** `frontend/src/app/(dashboard)/proposals/[id]/compliance/page.tsx` - New page:
- Interactive compliance matrix table
- Red/Yellow/Green status per requirement
- Gap detail drill-down with AI remediation suggestions
- Evaluation method indicator with strategy tips
- Real-time score as sections are completed

---

## ENHANCEMENT 12: NAICS Code Intelligence

**Source:** The Vault (Ch. II - NAICS Codes)

**What:** Smart NAICS code management, matching, and size standard awareness.

### Backend Changes

**File:** `backend/apps/opportunities/models.py` - Add:

```python
class NAICSCode(models.Model):
    code = models.CharField(max_length=6, unique=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    size_standard = models.CharField(max_length=100)  # $ or employee count
    size_standard_type = models.CharField(choices=[('revenue','Revenue'),('employees','Employees')])
    sector = models.CharField(max_length=2)  # First 2 digits
```

### AI Integration

- Auto-match opportunity NAICS to company NAICS codes
- Size standard checking (per The Vault: wrong NAICS = automatic disqualification)
- Recommend additional NAICS codes based on company capabilities
- Alert when solicitation NAICS doesn't match company codes

---

## Implementation Priority Order

| Priority | Enhancement | Impact on Win Rate | Effort |
|----------|------------|-------------------|--------|
| 1 | **E3: Smart Proposal Builder** | Very High | Large |
| 2 | **E5: Submission Checklist Engine** | Very High | Medium |
| 3 | **E4: Past Performance Manager** | High | Medium |
| 4 | **E11: Compliance Matrix** | Very High | Large |
| 5 | **E7: Bid-Readiness & Scoring** | High | Medium |
| 6 | **E2: Capability Statement Generator** | High | Medium |
| 7 | **E8: Sources Sought Generator** | High | Small |
| 8 | **E6: Email Submission Templates** | Medium | Small |
| 9 | **E1: SAM Registration Wizard** | Medium | Medium |
| 10 | **E10: Teaming Intelligence** | Medium | Medium |
| 11 | **E9: SBA Certification Tracker** | Medium | Small |
| 12 | **E12: NAICS Intelligence** | Medium | Small |

---

## Key Architecture Decisions

1. **All AI agents save to database immediately** - No more orphaned drafts
2. **Evaluation method drives proposal strategy** - LPTA vs Best Value vs Price Eval changes how every section is written
3. **The Bidvantage Proposal Template becomes the default template** - Exact section structure (Exec Summary, Technical Approach, Manpower, Past Performance, Management, Business Compliance, Reporting)
4. **Past performance uses the exact Bidvantage table format** - Structured fields matching the template
5. **Compliance checklist is mandatory before submission** - Blocks non-compliant proposals
6. **Purchase thresholds drive opportunity strategy** - Micro/SAT/Commercial categorization
7. **Sources Sought responses are first-class citizens** - Not just proposals, but pre-solicitation positioning

---

## Files to Create/Modify Summary

### New Files (18):
- `backend/apps/proposals/services/generator.py`
- `backend/apps/proposals/services/docx_renderer.py`
- `backend/apps/proposals/services/checklist_engine.py`
- `ai_orchestrator/src/agents/capability_statement_agent.py`
- `ai_orchestrator/src/agents/past_performance_matcher_agent.py`
- `ai_orchestrator/src/agents/sources_sought_agent.py`
- `ai_orchestrator/src/agents/opportunity_scorer_agent.py`
- `ai_orchestrator/src/agents/naics_agent.py`
- `ai_orchestrator/src/graphs/capability_statement_graph.py`
- `ai_orchestrator/src/graphs/sources_sought_graph.py`
- `frontend/src/app/(dashboard)/sam-registration/page.tsx`
- `frontend/src/app/(dashboard)/capability-statements/page.tsx`
- `frontend/src/app/(dashboard)/proposals/[id]/checklist/page.tsx`
- `frontend/src/app/(dashboard)/proposals/[id]/compliance/page.tsx`
- `frontend/src/app/(dashboard)/past-performance/new/page.tsx`
- `frontend/src/app/(dashboard)/sources-sought/page.tsx`
- `frontend/src/app/(dashboard)/certifications/page.tsx`
- `frontend/src/services/govcon-policies.ts`

### Modified Files (15):
- `backend/apps/opportunities/models.py` - SAMRegistration, NAICSCode, SBACertification, OpportunityScore enhancements
- `backend/apps/opportunities/views.py` - New viewsets + actions
- `backend/apps/proposals/models.py` - Proposal enhancements, ProposalVolume, SourcesSoughtResponse, SubmissionEmail
- `backend/apps/proposals/views.py` - New viewsets for enhanced models
- `backend/apps/proposals/serializers.py` - New serializers
- `backend/apps/past_performance/models.py` - Bidvantage template fields
- `backend/apps/past_performance/views.py` - New viewsets
- `backend/apps/marketing/models.py` - CapabilityStatement model
- `backend/apps/teaming/models.py` - TeamingArrangement enhancements
- `backend/config/urls.py` - New URL routes
- `ai_orchestrator/src/agents/proposal_writer_agent.py` - Full template integration
- `ai_orchestrator/src/agents/compliance_agent.py` - Matrix + evaluation method awareness
- `ai_orchestrator/src/graphs/proposal_graph.py` - Persistence + new sections
- `ai_orchestrator/src/main.py` - New agent endpoints
- `frontend/src/app/(dashboard)/proposals/page.tsx` - Enhanced with new features
