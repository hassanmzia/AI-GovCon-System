# AI Deal Manager — User Guide

**Platform:** AI Deal Manager (Enterprise Government Contracting)
**Version:** 2.0
**Last Updated:** March 2026
**Audience:** All platform users

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard Overview](#2-dashboard-overview)
3. [User Management (Admin)](#3-user-management-admin)
4. [Opportunity Intelligence Module](#4-opportunity-intelligence-module)
5. [Deals Pipeline Module](#5-deals-pipeline-module)
6. [RFP Module](#6-rfp-module)
7. [Proposals Module](#7-proposals-module)
8. [Pricing Module](#8-pricing-module)
9. [Contracts Module](#9-contracts-module)
10. [Analytics Module](#10-analytics-module)
11. [Past Performance Vault](#11-past-performance-vault)
12. [Knowledge Vault](#12-knowledge-vault)
13. [AI Agents & Automation](#13-ai-agents--automation)
14. [Strategy Module](#14-strategy-module)
15. [Teaming & Partners Module](#15-teaming--partners-module)
16. [Legal & Compliance Module](#16-legal--compliance-module)
17. [Security & Compliance Module](#17-security--compliance-module)
18. [Communications Module](#18-communications-module)
19. [Policies Module](#19-policies-module)
20. [Research & Competitive Intelligence](#20-research--competitive-intelligence)
21. [Settings & Preferences](#21-settings--preferences)
22. [Keyboard Shortcuts & Tips](#22-keyboard-shortcuts--tips)
23. [Troubleshooting](#23-troubleshooting)
24. [Appendix A: Module Quick Reference](#appendix-a-module-quick-reference)
25. [Appendix B: Glossary](#appendix-b-glossary)

---

## 1. Getting Started

### 1.1 System Requirements

AI Deal Manager is a browser-based platform. No installation is required.

| Component | Requirement |
|---|---|
| Browser | Chrome 110+, Firefox 115+, Edge 110+, Safari 16+ |
| Internet Connection | Broadband (5 Mbps or higher recommended) |
| Screen Resolution | 1280 x 720 minimum; 1920 x 1080 recommended |
| Mobile | iOS 15+ (Safari), Android 10+ (Chrome) |
| JavaScript | Must be enabled |
| Cookies / LocalStorage | Must be enabled (theme and session preferences) |

> **Note:** Internet Explorer is not supported.

---

### 1.2 Accessing the Platform

1. Open your supported web browser.
2. Navigate to the URL provided by your administrator (e.g., `https://dealmanager.yourcompany.gov`).
3. The login screen will load automatically.

---

### 1.3 First Login

1. Enter your **Email Address** and **Password**.
2. Click **Sign In**.
3. On first login, you may be prompted to:
   - Verify your email via a confirmation link.
   - Change your temporary password (minimum 12 characters, must include uppercase, lowercase, number, and special character).
4. After authentication, you land on the **Dashboard**.

> **Tip:** Click **Forgot Password?** to receive a reset link valid for 24 hours.

> **Warning:** After 5 consecutive failed login attempts, your account is temporarily locked for 15 minutes.

---

### 1.4 Light / Dark Mode

The platform supports light and dark themes. Your preference is saved in localStorage and persists across sessions.

**To switch themes:**
- Click the **theme toggle icon** in the top-right corner of the topbar (Moon icon for dark, Sun icon for light).
- Or go to **Settings > Appearance** to set explicitly.

---

### 1.5 Navigation

**Desktop:** The left sidebar provides access to all platform modules. The sidebar is always visible.

**Mobile (< 768px):** The sidebar is hidden by default.
1. Tap the **hamburger menu** in the top-left corner.
2. The sidebar slides in from the left.
3. Tap any navigation item — the sidebar closes automatically.

---

### 1.6 Understanding Your Role

Your role determines what you can see and do in the platform. AI Deal Manager uses 9 roles:

| Role | What You Can Do |
|---|---|
| `admin` | Everything, including user management |
| `executive` | View all deals, analytics, and approve strategies |
| `capture_manager` | Manage deals, configure agents, approve proposals |
| `proposal_manager` | Manage proposal workflows, assign writers/reviewers |
| `pricing_manager` | Manage rate cards, cost scenarios, pricing analysis |
| `writer` | Author and edit proposal content |
| `reviewer` | Review and comment on proposals (read-only editing) |
| `contracts_manager` | Manage contracts, clause library, redlines |
| `viewer` | Read-only access to assigned deals |

If you cannot see a module you expect, your role may not have access. Contact your administrator.

---

## 2. Dashboard Overview

The Dashboard is your central command center, providing a real-time summary of your pipeline's health.

### 2.1 KPI Cards

At the top, a row of **Key Performance Indicator cards** displays:

| Card | What It Measures |
|---|---|
| Total Pipeline Value | Sum of estimated contract values for all active deals |
| Active Deals | Count of deals in non-closed stages |
| Win Rate (YTD) | Percentage of submitted bids awarded year-to-date |
| Opportunities Tracked | Total SAM.gov opportunities being monitored |
| Proposals in Progress | Deals in `proposal_dev` or `red_team` stage |
| Pending Approvals | Items awaiting your review/approval |

**Trend indicators:** Green arrow = improved, Red arrow = declined, Gray dash = no change.

### 2.2 Pipeline Distribution Chart

Shows how active deals are distributed across pipeline stages (donut or bar chart). Click any segment to jump to that stage in the Deals Pipeline.

### 2.3 Recent Activity Feed

Chronological log of actions: opportunity ingestion, stage transitions, proposal reviews, comments. Click any entry to navigate to the related record.

### 2.4 Upcoming Deadlines

Time-sensitive items sorted by proximity. Items within **72 hours** are highlighted amber. **Past due** items are highlighted red.

### 2.5 Pending Approvals

Lists items requiring your action. Role-sensitive — you only see items assigned to you.

- Click **Approve** (checkmark) or **Reject** (X) directly.
- Rejections require a comment; approvals optionally accept a comment.
- Click the item title to view full context before deciding.

---

## 3. User Management (Admin)

> **Access:** Admin role only.

### 3.1 Creating a New User

1. Go to **Admin > Manage Users**.
2. Click **+ Invite User**.
3. Fill in: First Name, Last Name, Email, Role.
4. Click **Send Invitation**. The user receives an email to set their password.

### 3.2 Editing a User's Role

1. Go to **Admin > Manage Users**.
2. Find the user, click the **...** menu, select **Edit Role**.
3. Choose the new role and click **Save**.

> **Warning:** Downgrading a role may cause loss of access to owned records.

### 3.3 Deactivating a User

1. Click the **...** menu for the user, select **Deactivate Account**.
2. The user's session terminates immediately. Records are preserved.

---

## 4. Opportunity Intelligence Module

Navigate to **Opportunities** in the sidebar.

### 4.1 Finding Opportunities

The module ingests solicitations from **SAM.gov** and presents them with AI-generated fit scores and recommendations.

### 4.2 SAM.gov Sync

- Automatic sync runs every 6 hours.
- Manual sync: click the **Sync SAM.gov** button (refresh icon) in the top-right. Completes in 30-120 seconds.

### 4.3 Filtering & Searching

| Filter | Options |
|---|---|
| Agency | Multi-select (DoD, DHS, VA, etc.) |
| NAICS Code | Search/browse NAICS codes |
| Set-Aside | Small Business, 8(a), WOSB, HUBZone, SDVOSB |
| Status | Open, Upcoming, Closed, Pre-Solicitation |
| Recommendation | Bid, No-Bid, Evaluate |
| Fit Score | Slider (0-100) |
| Response Deadline | Date range picker |

Use the **Search** bar for keyword search across titles, descriptions, and agencies.

**Saved filters:** Apply filters, click **Save Filter**, name it — reuse from the **Saved Filters** dropdown.

### 4.4 Fit Scores

Each opportunity has an AI-generated **Fit Score** (0-100):

| Score | Interpretation |
|---|---|
| 80-100 | Strong fit — highly recommended |
| 60-79 | Good fit — worth evaluating |
| 40-59 | Partial fit — proceed with caution |
| 0-39 | Weak fit — likely not a match |

Scores improve over time as the AI learns from your wins, losses, and bid/no-bid decisions.

### 4.5 Opportunity Details

Click an opportunity to view:
- **Synopsis** — AI-summarized description
- **Key Dates** — Questions due, proposals due, award date
- **Agency & Office** — Contracting office, NAICS code
- **Solicitation Documents** — Links to SAM.gov
- **AI Recommendation** — Bid/No-Bid/Evaluate with reasoning
- **Fit Score Breakdown** — Factor-level contributions
- **Similar Past Performance** — Matched records from your vault

### 4.6 Creating a Deal from an Opportunity

1. Open the Opportunity Detail View.
2. Click **Create Deal** — a form pre-populates with opportunity data.
3. Review/adjust fields and click **Create Deal**.

---

## 5. Deals Pipeline Module

Navigate to **Deals Pipeline** in the sidebar.

### 5.1 Kanban Board

The pipeline is a **Kanban board** with columns for each stage. Deals flow left-to-right:

| # | Stage | Purpose |
|---|---|---|
| 1 | Intake | New deal logged |
| 2 | Qualify | Initial qualification |
| 3 | Bid / No-Bid | Formal go/no-go decision |
| 4 | Capture Plan | Strategic planning |
| 5 | Proposal Development | Writing the proposal |
| 6 | Red Team | Independent review |
| 7 | Final Review | Leadership sign-off |
| 8 | Submitted | Delivered to government |
| 9 | Post-Submit | Q&A, BAFO, clarifications |
| 10 | Award Pending | Awaiting decision |
| 11 | Contract Setup | Onboarding and execution |
| 12 | Delivery | Active performance |

**Closed stages:** `closed_won`, `closed_lost`, `no_bid` (accessible via Closed Deals tab).

### 5.2 Creating a Deal

Click **+ New Deal** and complete: Deal Name, Agency, NAICS, Estimated Value, Capture Manager, Proposal Due Date, Set-Aside Type.

### 5.3 Moving Deals

**Drag and drop** a card to the target column, or use the **Move to Next Stage** button in the detail view.

Every transition requires a **Reason** — this feeds AI learning and creates an audit trail.

### 5.4 Deal Details

Click a deal title to open tabs: Overview, RFP, Proposal, Pricing, Team, Activity, Documents.

### 5.5 Swimlane View

Toggle **Swimlanes** to group by Capture Manager or Agency instead of stage columns.

---

## 6. RFP Module

Navigate to **RFP** in the sidebar, or via the RFP tab in a deal.

### 6.1 Uploading an RFP

1. Click **+ Upload RFP**, select the deal, drag-drop the PDF/DOCX file.
2. The platform automatically: extracts text, identifies requirements, generates a compliance matrix, flags key dates.
3. Processing takes 15-60 seconds.

> File size limit: 50 MB.

### 6.2 Compliance Matrix

Auto-generated after upload. Columns: Section, Requirement, Type (Shall/Should/May), Proposal Section, Status, Owner.

Click a row to expand, update Status and Owner, click **Save Row**.

### 6.3 Q&A Tracking

Log questions for the contracting officer under the **Q&A** tab. Track submission status and import official responses.

---

## 7. Proposals Module

Navigate to **Proposals** in the sidebar.

### 7.1 Creating a Proposal

Select the deal, choose a template (or start blank), enter title and deadline, click **Create**.

### 7.2 AI-Assisted Writing

Each section has an **AI Assist** button:
- **Generate Draft** — Full draft grounded in RFP requirements, knowledge vault, and win themes
- **Improve Selected Text** — Enhance clarity and compliance language
- **Shorten / Expand** — Adjust passage length
- **Check Compliance** — Verify section addresses all matrix requirements

> **Warning:** AI-generated content must be reviewed by a human before submission.

### 7.3 Review Workflow

1. Author sets section status to **In Review**.
2. Reviewer receives notification, adds inline comments.
3. Author addresses comments, marks **Resolved**.
4. Reviewer marks **Approved**.
5. When all sections approved, Proposal Manager clicks **Submit for Final Review**.

### 7.4 Export

Export proposals as DOCX or PDF via the **Export** button. The system applies formatting rules and page count validation.

---

## 8. Pricing Module

Navigate to **Pricing** in the sidebar.

### 8.1 Rate Cards

Store standard labor rates by contract vehicle, fiscal year, or customer. For each labor category, enter: Direct Rate, Fringe %, Overhead %, G&A %, Fee %. **Fully Burdened Rate** auto-calculates.

### 8.2 Cost Scenarios

Model different staffing and pricing strategies per deal. Add labor line items and ODCs. Compare scenarios side-by-side.

### 8.3 Win Price Analysis

AI analyzes historical awards, competitor pricing, and IGCE data to recommend a **price-to-win range** with probability curve.

---

## 9. Contracts Module

Navigate to **Contracts** in the sidebar.

### 9.1 Templates

Browse and create contract templates using placeholder tokens (e.g., `{{contractor_name}}`).

### 9.2 Clause Library

Searchable repository of standard and custom clauses. Search by keyword, FAR/DFARS reference, or type. Insert directly into contracts.

### 9.3 Redline Tracking

Upload counterparty versions for side-by-side comparison (insertions in green, deletions in red). Accept/reject changes individually or in bulk.

---

## 10. Analytics Module

Navigate to **Analytics** in the sidebar.

### 10.1 KPI Metrics Panel

Organization-wide KPIs with trend sparklines: pipeline value, deal count by stage, average cycle time, submission rate.

### 10.2 Win Rate Gauge

Year-to-date win rate. Color-coded: Red (0-30%), Amber (30-50%), Green (50%+). Filter by time period, agency, contract type, or deal size.

### 10.3 Pipeline Distribution

Deals by stage — toggle between **By Count** and **By Value**. Click to drill down.

### 10.4 Pending Approvals Queue

Consolidated approval view across all modules with approve/reject actions.

### 10.5 Deadlines Tracker

All tracked deadlines across active deals, color-coded by urgency. Export to CSV.

### 10.6 Agent Performance Dashboard

View AI agent metrics: average latency, cost per run, error rates, quality scores. Powered by Langfuse tracing data.

---

## 11. Past Performance Vault

Navigate to **Past Performance** in the sidebar.

### 11.1 Adding Records

Click **+ Add Record** and fill in: Contract Name, Customer/Agency, Contract Number, Type (FFP/T&M/CPFF), Value, Period of Performance, NAICS, Description of Work (200+ words recommended), Key Personnel, Customer Reference, CPARs Rating.

### 11.2 Semantic Search

Use the search bar with natural language queries (e.g., "cloud migration for a federal health agency"). Results are ranked by **meaning**, not just keyword match, using vector search.

### 11.3 Generating Narratives

Select records, click **Generate Narrative**, specify the target opportunity — AI generates a CPARs-aligned past performance narrative for proposal use.

---

## 12. Knowledge Vault

Navigate to **Knowledge Vault** in the sidebar.

### 12.1 Adding Knowledge Articles

Click **+ New Article**. Fill in: Title, Category, Content (rich text editor), Tags, Visibility (Public or Restricted).

Upload documents directly via **Upload File**.

### 12.2 Searching

Semantic search — query by concept, not just keyword. Filter by Category, Tag, or Author.

> **Tip:** The Knowledge Vault is automatically queried by AI Assist in Proposals. Keeping it current directly improves AI-generated drafts.

---

## 13. AI Agents & Automation

AI Deal Manager deploys **21 specialized AI agents** that work autonomously across the platform. Here's how to interact with them.

### 13.1 How Agents Work

Agents are triggered automatically by platform actions (e.g., uploading an RFP triggers the RFP Analyst Agent) or manually via the AI buttons in each module.

### 13.2 Agent Status & Progress

When an agent is running:
- A **progress indicator** appears with percentage completion.
- Status updates stream in real-time via Socket.IO.
- You'll receive a notification when the agent completes.

### 13.3 Human-in-the-Loop Review

When an agent's confidence is below threshold, it pauses and creates a **review request**:
1. You'll see the request in your **Pending Approvals** widget.
2. Review the agent's work and provide feedback.
3. Approve to continue, or reject with guidance for the agent to retry.

### 13.4 Agent Overview

| Agent | Triggered By | Output |
|---|---|---|
| Opportunity | SAM.gov sync | Scored opportunities with recommendations |
| RFP Analyst | RFP upload | Compliance matrix, requirement extraction |
| Strategy | Deal creation | Capture plan, win themes, discriminators |
| Proposal Writer | "Generate Draft" button | Proposal section drafts |
| Pricing | "Analyze Pricing" button | Cost scenarios, win price analysis |
| Legal | Contract upload | Risk flagged clauses, redlines |
| QA | Proposal review cycle | Compliance check, quality score |
| Compliance | Pre-submission | Final compliance shredding report |
| Research | Manual trigger | Market research, competitor profiles |
| Past Performance | Proposal generation | Relevant PP narrative selection |

### 13.5 Agent Configuration (Admin)

Admins can configure agents via the AI Orchestrator settings:
- **Model selection** — Claude Sonnet 4.6 (faster) or Opus 4.6 (more capable)
- **Confidence thresholds** — When to require human review
- **Tool access** — Which MCP tools each agent can use

---

## 14. Strategy Module

Navigate to **Strategy** in the sidebar.

Manage capture strategy documents, win themes, discriminators, and competitive positioning. The Strategy Agent auto-generates initial capture plans based on opportunity analysis.

---

## 15. Teaming & Partners Module

Navigate to **Teaming** in the sidebar.

Identify teaming partners, manage teaming agreements, track subcontractors, and monitor small business compliance. The Teaming Agent suggests partners based on capability gaps and set-aside requirements.

---

## 16. Legal & Compliance Module

Navigate to **Legal** in the sidebar.

Submit documents for legal review, manage review workflows, track risk flags, and handle redlines. The Legal Agent automatically identifies high-risk clauses in uploaded contracts.

---

## 17. Security & Compliance Module

Navigate to **Security** in the sidebar.

Track CMMC, NIST 800-171, FedRAMP, and FAR/DFARS compliance. Manage evidence collection, gap analysis, and remediation tasks. The Security Agent assesses compliance posture and generates remediation plans.

---

## 18. Communications Module

Navigate to **Communications** in the sidebar.

Manage stakeholder communications, email drafts, RFI responses, and follow-up tracking. The Communication Agent drafts emails and maintains communication logs linked to deals.

---

## 19. Policies Module

Navigate to **Policies** in the sidebar.

Manage company policy documents with version control, acknowledgment tracking, and policy-to-requirement mapping. Ensure team compliance with internal policies across all active deals.

---

## 20. Research & Competitive Intelligence

Navigate to **Research** in the sidebar.

Access market research, competitor profiles, and industry analysis. The Research and Competitive Intelligence agents conduct web and database research, building structured intelligence reports on agencies, incumbents, and competitors.

---

## 21. Settings & Preferences

Navigate to **Settings** (gear icon) in the sidebar.

### 21.1 Profile Management

Update: Display Name, Email, Profile Photo (JPG/PNG, max 2 MB), Job Title, Phone.

### 21.2 Password Change

Go to **Settings > Security**. Enter current password, enter and confirm new password.

### 21.3 Notification Preferences

| Notification | Description |
|---|---|
| Deal Stage Changes | When a deal you own moves stages |
| Approval Requests | When an item needs your approval |
| Deadline Alerts | N days before a tracked deadline |
| Proposal Comments | When a comment is added to your section |
| New Opportunities | High-fit SAM.gov opportunities ingested |
| System Announcements | Platform-wide notices |
| Agent Completions | When an AI agent finishes a task |

Set **Deadline Alert Lead Time** (e.g., 7 days and 3 days before). Choose delivery: **In-App**, **Email**, or **Both**.

### 21.4 Theme Selection

Go to **Settings > Appearance**. Select Light or Dark mode.

---

## 22. Keyboard Shortcuts & Tips

### Shortcuts

| Shortcut | Action |
|---|---|
| `?` | Open keyboard shortcuts help |
| `G` then `D` | Go to Dashboard |
| `G` then `O` | Go to Opportunities |
| `G` then `P` | Go to Deals Pipeline |
| `G` then `A` | Go to Analytics |
| `N` | New Deal form (on Pipeline page) |
| `Esc` | Close modal or panel |
| `/` | Focus global search bar |
| `Ctrl+S` / `Cmd+S` | Save current form or document |

### Tips

- Use **Global Search** (`/`) to find any deal, opportunity, document, or article from anywhere.
- Export the compliance matrix to Excel for offline work, then re-import updates in bulk.
- Always fill in the **Reason** field when moving deals — it feeds AI learning.
- Use **Swimlane** toggle on Kanban to group by Capture Manager or Agency.
- Avoid opening the same deal in multiple tabs — concurrent edits may overwrite.

---

## 23. Troubleshooting

### Page is blank or loading indefinitely

1. Hard refresh: `Ctrl+Shift+R` / `Cmd+Shift+R`.
2. Clear browser cache and cookies.
3. Try incognito/private browsing.
4. Contact your system administrator if the issue persists.

### Cannot log in with correct credentials

1. Check Caps Lock.
2. Use **Forgot Password?**.
3. Contact admin to verify account status.

### SAM.gov sync not returning results

1. Check sync timestamp — a sync may have run recently.
2. Verify SAM.gov API key hasn't expired (annual renewal).
3. Check SAM.gov status page.

### AI Assist not generating content

1. Verify internet connection.
2. Ensure the deal has an analyzed RFP (not just uploaded).
3. Add context (bullet points) to very short sections.
4. Contact admin — the AI service may be temporarily disrupted.

### Wrong stage move — need to go back

Open the deal, use the stage dropdown to select the correct stage, provide a reason for the correction. Both moves are logged in audit history.

### File upload fails

1. Verify file is under 50 MB.
2. Confirm supported types: PDF, DOCX, XLSX, PPTX, PNG, JPG.
3. Try converting to PDF.
4. Switch to a more stable network connection.

### Dark mode doesn't persist

1. Ensure browser doesn't clear localStorage on exit.
2. Set theme explicitly via **Settings > Appearance**.
3. On shared computers, localStorage may be cleared by device policy.

### Missing module in sidebar

Your role controls sidebar visibility. Check your role in **Settings > Profile** and reference the roles table in Section 1.6.

---

## Appendix A: Module Quick Reference

| Module | Primary Users | Key Actions |
|---|---|---|
| Dashboard | All | Monitor KPIs, approvals, deadlines |
| Opportunities | Capture Manager, Executive | Discover, score, track SAM.gov opportunities |
| Deals Pipeline | Capture Manager, All | Manage deal lifecycle via Kanban |
| Solutions | Capture Manager, Proposal Manager | AI-powered solution architecture |
| RFP | Proposal Manager, Writer | Upload RFP, manage compliance matrix |
| Proposals | Proposal Manager, Writer | Draft, review, submit proposals |
| Pricing | Pricing Manager | Rate cards, cost modeling, win price |
| Contracts | Contracts Manager | Templates, clause library, redlines |
| Strategy | Executive, Capture Manager | Bid/no-bid strategy, win themes |
| Marketing | Marketing, Writer | Competitive positioning, capabilities |
| Research | Capture Manager | Competitive intelligence, market research |
| Legal | Legal, Contracts Manager | Compliance review, legal risk flags |
| Teaming | Capture Manager | Subcontractor and partner management |
| Security | Security, Contracts Manager | Security requirement mapping |
| Knowledge Vault | All | Institutional knowledge base |
| Communications | Writer, Proposal Manager | Email drafts, narratives |
| Policies | Admin, All | Company policy management |
| Past Performance | Capture Manager, Writer | PP records, semantic search, narratives |
| Analytics | Executive, Admin, Capture Manager | Pipeline health, win rates, deadlines |
| Settings | All | Profile, notifications, theme |
| Admin > Users | Admin | User creation, role assignment |

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| BAFO | Best and Final Offer — final pricing submission requested after initial review |
| Capture | The business development process of pursuing a specific opportunity |
| CMMC | Cybersecurity Maturity Model Certification — DoD cybersecurity framework |
| CPARs | Contractor Performance Assessment Reporting System — official government ratings |
| FAR | Federal Acquisition Regulation — primary rules governing federal procurement |
| DFARS | Defense Federal Acquisition Regulation Supplement — DoD-specific rules |
| FedRAMP | Federal Risk and Authorization Management Program — cloud security authorization |
| Fit Score | AI-generated score (0-100) representing opportunity alignment with your profile |
| FPDS-NG | Federal Procurement Data System - Next Generation — government contract data |
| GSA | General Services Administration — federal procurement and schedules |
| IGCE | Independent Government Cost Estimate — government's internal cost estimate |
| Kanban | Visual project management using columns (stages) and cards (deals) |
| LangGraph | Framework for building stateful multi-agent AI workflows |
| MCP | Model Context Protocol — standardized interface for AI tool access |
| NAICS | North American Industry Classification System — business activity codes |
| NIST 800-171 | National Institute of Standards and Technology security controls |
| RFP | Request for Proposal — formal government solicitation document |
| SAM.gov | System for Award Management — federal contracting opportunity portal |
| Set-Aside | Procurement reserved for specific small business categories |
| Vector Search | Semantic search that finds results based on meaning, not just keywords |

---

*For technical architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).*

*This document is maintained by the platform administration team. Last reviewed: March 2026.*
