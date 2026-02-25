# AI Deal Manager — User Guide

**Platform:** AI Deal Manager (Enterprise Government Contracting)
**Version:** 1.0
**Last Updated:** February 2026
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
13. [Settings & Preferences](#13-settings--preferences)
14. [Keyboard Shortcuts & Tips](#14-keyboard-shortcuts--tips)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Getting Started

### 1.1 System Requirements

AI Deal Manager is a browser-based platform. No installation is required. The following environments are supported:

| Component | Requirement |
|---|---|
| Browser | Chrome 110+, Firefox 115+, Edge 110+, Safari 16+ |
| Internet Connection | Broadband (5 Mbps or higher recommended) |
| Screen Resolution | 1280 × 720 minimum; 1920 × 1080 recommended |
| Mobile | iOS 15+ (Safari), Android 10+ (Chrome) |
| JavaScript | Must be enabled |
| Cookies / LocalStorage | Must be enabled (theme and session preferences) |

> **Note:** Internet Explorer is not supported. If you experience rendering issues, ensure your browser is up to date.

---

### 1.2 Accessing the Platform

1. Open your supported web browser.
2. Navigate to the URL provided by your organization's administrator (e.g., `https://dealmanager.yourcompany.gov` or the internal IP/domain configured by your IT team).
3. The login screen will load automatically. If you are redirected to a blank page, clear your browser cache and try again.

---

### 1.3 First Login

1. On the login screen, enter your **Email Address** in the first field.
2. Enter your **Password** in the second field.
3. Click **Sign In**.
4. On your very first login, you may be prompted to:
   - Verify your email address via a confirmation link sent to your inbox.
   - Change your temporary password to a permanent one (minimum 12 characters, must include uppercase, lowercase, number, and special character).
5. After successful authentication you will land on the **Dashboard**.

> **Tip:** If you forget your password, click **Forgot Password?** on the login screen. You will receive a reset link valid for 24 hours.

> **Warning:** After 5 consecutive failed login attempts your account will be temporarily locked for 15 minutes. Contact your administrator if you are locked out repeatedly.

---

### 1.4 Light / Dark Mode

The platform supports both a light theme and a dark theme. Your preference is saved automatically in your browser's local storage and will persist across sessions on the same device.

**To switch themes:**

1. Locate the **theme toggle icon** in the top-right corner of the topbar, to the left of your user avatar.
   - When the platform is in **Light Mode**, a **Moon icon** (🌙) is displayed. Click it to switch to Dark Mode.
   - When the platform is in **Dark Mode**, a **Sun icon** (☀️) is displayed. Click it to switch to Light Mode.
2. The entire UI repaints instantly. No page reload is required.

> **Note:** Theme preference is stored per browser/device. If you switch devices, you will need to re-apply your preferred theme.

---

### 1.5 Mobile Navigation

On mobile phones (viewport width below ~768 px), the left sidebar is hidden by default to maximize screen real estate.

**Opening the sidebar on mobile:**

1. Tap the **hamburger menu icon (☰)** located in the **top-left corner** of the topbar.
2. The sidebar slides in from the left, overlaying the main content.
3. Tap any navigation item to navigate to that module. The sidebar will close automatically after selection.
4. Alternatively, tap the **X button** at the top of the sidebar to close it without navigating.

> **Tip:** On tablets in landscape orientation, the sidebar may remain visible. Rotate to portrait mode to access the hamburger toggle.

---

## 2. Dashboard Overview

The Dashboard is your central command center. It is the first page you see after logging in and provides a real-time summary of your pipeline's health.

`[SCREENSHOT PLACEHOLDER: Full Dashboard view showing KPI cards, pipeline chart, activity feed, and deadline panels]`

---

### 2.1 KPI Cards

At the top of the Dashboard you will find a row of **Key Performance Indicator (KPI) cards**. Each card displays a single metric with a trend indicator.

| Card | What It Measures |
|---|---|
| Total Pipeline Value | Sum of estimated contract values for all active deals |
| Active Deals | Count of deals in non-closed stages |
| Win Rate (YTD) | Percentage of submitted bids awarded year-to-date |
| Opportunities Tracked | Total SAM.gov opportunities being monitored |
| Proposals in Progress | Deals currently in `proposal_dev` or `red_team` stage |
| Pending Approvals | Number of items awaiting your review/approval |

**Reading trend indicators:**
- A green upward arrow means the metric improved compared to the prior period.
- A red downward arrow means the metric declined.
- A gray dash means no change or insufficient historical data.

> **Tip:** Hovering over a KPI card on desktop reveals a small tooltip showing the prior-period value for context.

---

### 2.2 Pipeline Distribution Chart

Below the KPI cards is a **Pipeline Distribution Chart** (donut or bar chart depending on your settings). This chart shows how your active deals are distributed across pipeline stages.

- Each segment/bar represents one pipeline stage.
- The size of each segment corresponds to the count of deals in that stage.
- Hover over a segment to see the stage name, deal count, and total dollar value.
- Click a segment to jump directly to the Deals Pipeline view filtered to that stage.

---

### 2.3 Recent Activity Feed

The **Recent Activity** panel (bottom-left) displays a chronological log of actions taken across the platform, including:

- Opportunity scored and ingested from SAM.gov
- Deal stage transitions
- Proposal sections submitted for review
- Comments and annotations added
- User logins and administrative changes

Each entry shows the **timestamp**, the **user who performed the action**, and a short **description**. Click any entry to navigate to the related record.

---

### 2.4 Upcoming Deadlines

The **Upcoming Deadlines** panel displays all time-sensitive items sorted by proximity, including:

- RFP question submission deadlines
- Proposal due dates
- Contract option periods
- Review milestones set by capture managers

Items within **72 hours** are highlighted in amber. Items **past due** are highlighted in red.

> **Warning:** Deadlines shown are pulled from data entered manually or from SAM.gov. Always verify against the official solicitation documents.

---

### 2.5 Pending Approvals

The **Pending Approvals** widget lists items that require your action. This panel is role-sensitive — you only see items assigned to you or your role group.

**To approve an item directly from the Dashboard:**

1. Locate the item in the Pending Approvals panel.
2. Click the green **Approve** button (checkmark icon) to approve.
3. Click the red **Reject** button (X icon) to reject.
4. A dialog will prompt you to enter a **comment** (required for rejections, optional for approvals).
5. Click **Confirm** to finalize your decision.

**To view full context before deciding:**

1. Click the item's **title link** to open the full record.
2. Review all details, attachments, and prior comments.
3. Use the approval controls within the detail view.

> **Note:** Executives have approval authority across all modules. Other roles may have approval authority within their domain (e.g., pricing managers can approve cost scenarios).

---

## 3. User Management (Admin)

> **Access:** This section is only available to users with the **admin** role. The Admin menu appears at the bottom of the left sidebar.

`[SCREENSHOT PLACEHOLDER: Admin > Manage Users page showing user table with role badges]`

---

### 3.1 Role Reference

| Role | Description |
|---|---|
| `admin` | Full access to all modules including user management |
| `executive` | Read-only strategic views plus approval authority |
| `capture_manager` | Opportunity discovery and deal management |
| `proposal_manager` | Proposal authoring and workflow management |
| `pricing_manager` | Rate cards, cost modeling, and win price analysis |
| `writer` | Content authoring only (proposals, narratives) |
| `reviewer` | Read and comment access; no create/edit rights |
| `contracts_manager` | Contract templates, clause library, redline tracking |
| `viewer` | Read-only access across all permitted modules |

---

### 3.2 Creating a New User

1. Click **Admin** in the bottom of the left sidebar.
2. Select **Manage Users** from the submenu.
3. Click the **+ Invite User** button in the top-right corner of the Users table.
4. In the dialog that opens, fill in:
   - **First Name** (required)
   - **Last Name** (required)
   - **Email Address** (required; must be unique in the system)
   - **Role** — select from the dropdown (see Role Reference table above)
5. Click **Send Invitation**.
6. The system sends an invitation email to the specified address with a link to set their password and complete registration.
7. The new user will appear in the Users table with a status of **Pending** until they complete registration.

> **Tip:** You can resend the invitation email by clicking the **...** menu in the user's row and selecting **Resend Invite**.

---

### 3.3 Editing a User's Role

1. Navigate to **Admin > Manage Users**.
2. Find the user in the table. Use the search bar at the top to filter by name or email.
3. Click the **...** (actions) menu at the right end of the user's row.
4. Select **Edit Role**.
5. Choose the new role from the dropdown.
6. Click **Save**. The change takes effect immediately; the user's next page load will reflect their new permissions.

> **Warning:** Downgrading a user's role (e.g., from `capture_manager` to `viewer`) may cause them to lose access to records they currently own. Review ownership assignments before downgrading.

---

### 3.4 Deactivating a User

1. Navigate to **Admin > Manage Users**.
2. Click the **...** menu for the target user.
3. Select **Deactivate Account**.
4. Confirm the action in the dialog. The user's session is terminated and they cannot log in until reactivated.
5. All records owned by the deactivated user remain intact and can be reassigned.

---

## 4. Opportunity Intelligence Module

Navigate to **Opportunities** in the left sidebar.

`[SCREENSHOT PLACEHOLDER: Opportunities list view with fit score badges, filters panel on the left, and a sample opportunity card]`

---

### 4.1 Finding Opportunities

The Opportunities module ingests solicitations from **SAM.gov** and presents them with AI-generated fit scores and recommendations. On page load you will see a paginated list or card grid of opportunities currently being tracked.

---

### 4.2 Triggering a SAM.gov Scan

The platform periodically syncs with SAM.gov automatically. To trigger an on-demand sync:

1. Click the **Sync SAM.gov** button (refresh icon) near the top-right of the Opportunities page.
2. A progress indicator will appear. Scans typically complete within 30–120 seconds depending on the number of new notices.
3. Once complete, newly discovered opportunities will appear at the top of the list, tagged **New**.

> **Note:** On-demand syncs are rate-limited. If the button is grayed out, a sync was run recently. Hover over it to see when the next manual sync is available.

---

### 4.3 Filtering and Searching Opportunities

Use the **Filters** panel on the left side of the Opportunities page to narrow results:

| Filter | Options |
|---|---|
| Agency | Multi-select list of federal agencies (DoD, DHS, VA, etc.) |
| NAICS Code | Search or browse NAICS codes |
| Set-Aside | Small Business, 8(a), WOSB, HUBZone, SDVOSB, etc. |
| Status | Open, Upcoming, Closed, Pre-Solicitation |
| Recommendation | Bid, No-Bid, Evaluate |
| Fit Score | Slider (0–100) |
| Response Deadline | Date range picker |

**To search by keyword:**

1. Type keywords in the **Search** bar at the top (e.g., "cloud migration" or "IT support services").
2. Results update in real time. The search matches opportunity titles, descriptions, and agency names.

**To save a filter preset:**

1. Apply your desired filters.
2. Click **Save Filter** (bookmark icon) next to the filter panel header.
3. Name your preset and click **Save**. Saved presets appear in the **Saved Filters** dropdown for quick reuse.

---

### 4.4 Understanding Fit Scores

Each opportunity displays a **Fit Score** from 0 to 100, calculated by the AI engine based on:

- Alignment with your company's NAICS codes and past performance history
- Keyword match between the solicitation and your capability statements
- Historical win rate for similar agency/contract-type combinations
- Set-aside eligibility match

| Score Range | Interpretation |
|---|---|
| 80–100 | Strong fit — highly recommended to pursue |
| 60–79 | Good fit — worth evaluating further |
| 40–59 | Partial fit — proceed with caution |
| 0–39 | Weak fit — likely not a strategic match |

> **Tip:** Fit scores improve over time as the AI learns from your wins, losses, and bid/no-bid decisions. Always provide a reason when closing a deal as Won or Lost.

---

### 4.5 Viewing Opportunity Details

1. Click any opportunity card or row to open its **Detail View**.
2. The detail view shows:
   - **Synopsis** — AI-summarized description of the requirement
   - **Key Dates** — Questions due, proposals due, award date (if known)
   - **Agency & Office** — Contracting office and NAICS code
   - **Solicitation Documents** — Links to the official solicitation on SAM.gov
   - **AI Recommendation** — Bid / No-Bid / Evaluate with reasoning
   - **Fit Score Breakdown** — Which factors contributed most to the score
   - **Similar Past Performance** — Matched records from your Past Performance Vault

---

### 4.6 Creating a Deal from an Opportunity

1. Open the Opportunity Detail View.
2. Click **Create Deal** in the top-right action bar.
3. A **New Deal** form will pre-populate with data from the opportunity (title, agency, NAICS, value estimate, deadline).
4. Review and adjust the pre-filled fields as needed:
   - **Deal Name** — edit if needed
   - **Estimated Value** — enter or update the contract value estimate
   - **Capture Manager** — assign a team member (defaults to you)
   - **Initial Stage** — defaults to `intake`
5. Click **Create Deal**. You will be redirected to the new deal's record in the Deals Pipeline.

---

## 5. Deals Pipeline Module

Navigate to **Deals Pipeline** in the left sidebar.

`[SCREENSHOT PLACEHOLDER: Kanban board view showing columns for all 12 active stages with deal cards]`

---

### 5.1 Understanding the Kanban Board

The Deals Pipeline is a **Kanban board** with columns representing each stage of your business development lifecycle. Deals flow left-to-right as they mature.

**Active Stages (in order):**

| # | Stage Key | Stage Name | Purpose |
|---|---|---|---|
| 1 | `intake` | Intake | New deal or opportunity logged |
| 2 | `qualify` | Qualify | Initial qualification assessment |
| 3 | `bid_no_bid` | Bid / No-Bid | Formal go/no-go decision |
| 4 | `capture_plan` | Capture Plan | Strategic capture planning |
| 5 | `proposal_dev` | Proposal Development | Writing and assembling the proposal |
| 6 | `red_team` | Red Team | Independent review of the proposal |
| 7 | `final_review` | Final Review | Leadership sign-off before submission |
| 8 | `submit` | Submitted | Proposal delivered to the government |
| 9 | `post_submit` | Post-Submit | Q&A, BAFO, and clarification period |
| 10 | `award_pending` | Award Pending | Awaiting award decision |
| 11 | `contract_setup` | Contract Setup | Onboarding and contract execution |
| 12 | `delivery` | Delivery | Active contract performance |

**Closed Stages (accessible via the Closed Deals tab):**

| Stage Key | Meaning |
|---|---|
| `closed_won` | Contract awarded and fully onboarded |
| `closed_lost` | Award went to a competitor |
| `no_bid` | Company elected not to pursue |

---

### 5.2 Creating a New Deal

**Method 1 — From the Deals Pipeline page:**

1. Click **+ New Deal** in the top-right corner of the Deals Pipeline page.
2. Complete the New Deal form:
   - **Deal Name** (required)
   - **Opportunity Link** — search and link an existing SAM.gov opportunity (optional)
   - **Agency** (required)
   - **NAICS Code** (required)
   - **Estimated Contract Value** (required)
   - **Capture Manager** — assign from user list
   - **Proposal Due Date** — enter the government's deadline
   - **Set-Aside Type** — select if applicable
3. Click **Create Deal**. The deal appears in the `intake` column.

**Method 2 — From an Opportunity** (see Section 4.6).

---

### 5.3 Moving Deals Through Stages

**Drag and Drop:**

1. Click and hold a deal card on the Kanban board.
2. Drag it to the target stage column.
3. Release. A **Stage Transition dialog** will appear.

**Using the Move button:**

1. Open a deal by clicking its card title.
2. In the deal detail view, click **Move to Next Stage** (or use the stage dropdown selector).
3. A **Stage Transition dialog** will appear.

**Completing the Stage Transition dialog:**

1. The dialog displays the current stage and the target stage.
2. **Reason for Transition** — enter a brief explanation (required for all transitions). Example: *"Qualified based on incumbent analysis and scope alignment with NAICS 541512."*
3. Optionally attach a document or note.
4. Click **Confirm Move**.
5. The deal card moves to the new column. The reason and timestamp are logged in the deal's activity history.

> **Warning:** Moving a deal backwards (regression) also requires a reason. Frequent regressions are flagged in the Analytics module as pipeline health indicators.

> **Tip:** For the `bid_no_bid` stage, the reason field is critical — it feeds the AI model that improves future bid recommendations.

---

### 5.4 Viewing Deal Details

Click any deal card title to open its full detail view. The detail view is organized into tabs:

| Tab | Contents |
|---|---|
| Overview | Key facts, dates, assigned team, and stage history |
| RFP | Linked RFP documents and compliance matrix |
| Proposal | Proposal sections and authoring workspace |
| Pricing | Cost scenarios and win price analysis |
| Team | Assigned capture, proposal, pricing, and legal team members |
| Activity | Full audit log of all actions and stage transitions |
| Documents | All files attached to this deal |

---

### 5.5 Closed Deals Tab

1. Click the **Closed Deals** tab at the top of the Deals Pipeline page.
2. Closed deals (`closed_won`, `closed_lost`, `no_bid`) are shown in a table view with filter options.
3. Use the **Status** filter to view only won deals, only lost deals, or only no-bids.
4. Click a closed deal row to view its full history and performance data, which feeds the Past Performance Vault and win/loss analytics.

---

## 6. RFP Module

Navigate to **RFP** in the left sidebar, or access it from the **RFP tab** within a deal's detail view.

---

### 6.1 Uploading an RFP Document

1. Open the RFP module and click **+ Upload RFP**.
2. Select the target **Deal** from the dropdown (if not already in a deal context).
3. Drag and drop the RFP PDF or DOCX file, or click **Browse Files** to select it from your file system.
4. The platform will automatically:
   - Extract text and section headings
   - Identify key requirements and evaluation criteria
   - Generate a draft **Compliance Matrix**
   - Flag key dates (questions due, proposal due, award date)
5. Click **Upload & Analyze**. Processing typically takes 15–60 seconds for a standard RFP.

> **Note:** File size limit is 50 MB per upload. For very large solicitation packages, upload individual volumes separately.

---

### 6.2 Compliance Matrix

The Compliance Matrix is auto-generated after RFP upload. It lists every requirement found in the solicitation and maps it to your proposal response.

**Matrix columns:**

| Column | Description |
|---|---|
| Section | RFP section reference (e.g., L.4.2) |
| Requirement | Extracted requirement text |
| Requirement Type | Shall / Should / May |
| Proposal Section | Where in your proposal this is addressed |
| Status | Not Started / In Progress / Complete / N/A |
| Owner | Team member responsible |

**To update a compliance matrix row:**

1. Click the row to expand it.
2. Update the **Status** dropdown and **Proposal Section** field.
3. Assign an **Owner** from the user list.
4. Click **Save Row**.

> **Tip:** Filter the matrix by Status = "Not Started" to quickly identify gaps before the proposal deadline.

---

### 6.3 Q&A Tracking

1. In the RFP module, click the **Q&A** tab.
2. Click **+ Add Question** to log a question you plan to submit to the contracting officer.
3. Fill in:
   - **Question Text** — your question as it will be submitted
   - **RFP Section Reference** — the section the question relates to
   - **Priority** — High / Medium / Low
   - **Submission Status** — Draft / Submitted / Answered
4. When the government releases the official Q&A amendments, click **Import Answers** to paste or upload the official responses.
5. Answered questions are linked to the relevant compliance matrix rows.

---

## 7. Proposals Module

Navigate to **Proposals** in the left sidebar, or via the Proposal tab in a deal.

---

### 7.1 Creating a Proposal

1. In the Proposals module, click **+ New Proposal**.
2. Select the **Deal** this proposal is for.
3. Choose a **Proposal Template** (if your organization has templates configured) or start blank.
4. Enter the **Proposal Title** and confirm the **Submission Deadline**.
5. Click **Create**. The proposal authoring workspace opens.

---

### 7.2 AI-Assisted Writing

Each proposal section has an **AI Assist** button (sparkle icon) next to it.

**Using AI Assist to draft a section:**

1. Click into a section (e.g., "Technical Approach").
2. Click the **AI Assist** button.
3. In the AI panel that slides in from the right, you can:
   - **Generate Draft** — AI writes a full draft using your company's capability data, past performance, and the RFP requirements.
   - **Improve Selected Text** — highlight text and click Improve to enhance clarity and compliance language.
   - **Shorten / Expand** — adjust the length of a selected passage.
   - **Check Compliance** — verifies the section addresses all matrix requirements tagged to it.
4. Click **Insert Draft** to paste the AI-generated content into the editor, where you can then edit freely.

> **Warning:** AI-generated content must be reviewed and edited by a human before submission. Always validate technical accuracy and ensure pricing figures are not included in technical volumes.

---

### 7.3 Review Workflow

1. When a section is ready for review, the author changes its status to **In Review** using the section status dropdown.
2. The assigned reviewer receives a notification.
3. Reviewers can add inline comments by highlighting text and clicking the **Comment** icon.
4. The author addresses comments and marks them **Resolved**.
5. The reviewer marks the section **Approved**.
6. When all sections are approved, the Proposal Manager can submit the proposal for **Executive Approval** by clicking **Submit for Final Review** at the top of the proposal workspace.

---

## 8. Pricing Module

Navigate to **Pricing** in the left sidebar.

---

### 8.1 Rate Cards

Rate cards store your standard labor category rates, overhead rates, and fee structures.

1. Navigate to **Pricing > Rate Cards**.
2. Click **+ New Rate Card** to create a rate card for a specific contract vehicle, fiscal year, or customer.
3. For each labor category, enter:
   - **Labor Category Name** (e.g., Senior Systems Engineer)
   - **Direct Labor Rate** (hourly)
   - **Fringe Rate** (%)
   - **Overhead Rate** (%)
   - **G&A Rate** (%)
   - **Fee / Profit** (%)
4. The platform auto-calculates the **Fully Burdened Rate** as you type.
5. Click **Save Rate Card**.

---

### 8.2 Cost Scenarios

Cost scenarios allow you to model different staffing and pricing strategies for a deal.

1. Open a deal and go to the **Pricing** tab, or navigate to the Pricing module and select the deal.
2. Click **+ New Scenario**.
3. Name the scenario (e.g., "Base Offer – Conservative" or "Best and Final").
4. Add **labor line items** by selecting a labor category from your rate card and entering estimated hours per period of performance.
5. Add **ODC (Other Direct Cost)** line items for travel, materials, subcontracts, etc.
6. The platform calculates **Total Evaluated Price** automatically.
7. Compare multiple scenarios side by side using the **Compare Scenarios** button.

---

### 8.3 Win Price Analysis

1. In the Pricing module, click **Win Price Analysis** for a given deal.
2. The AI engine analyzes:
   - Historical award data for similar contracts on the same vehicle
   - Competitor pricing intelligence (if available in your Research module)
   - Government Independent Cost Estimate (IGCE) if provided
3. The output shows a recommended **price-to-win range** and probability curve.
4. Use this insight to pressure-test your cost scenarios before final submission.

> **Tip:** Feed more historical win/loss data into the platform to improve the accuracy of win price predictions.

---

## 9. Contracts Module

Navigate to **Contracts** in the left sidebar.

---

### 9.1 Contract Templates

1. Navigate to **Contracts > Templates**.
2. Browse existing templates (e.g., FFP Task Order, T&M Subcontract, NDA).
3. Click **+ New Template** to create a new template from scratch or by uploading a DOCX file.
4. Templates use placeholder tokens (e.g., `{{contractor_name}}`, `{{period_of_performance}}`) that are auto-filled when a contract record is generated.

---

### 9.2 Clause Library

The Clause Library is a searchable repository of standard and custom contract clauses.

1. Navigate to **Contracts > Clause Library**.
2. Search for clauses by keyword, FAR/DFARS reference, or clause type.
3. Click a clause to view its full text and any associated notes or exceptions.
4. Click **Insert into Contract** (when editing a contract) to add the clause.
5. To add a new clause, click **+ Add Clause** and paste the clause text, add its citation, and tag it by category (e.g., "Cybersecurity", "IP Rights", "Payment Terms").

---

### 9.3 Redline Tracking

1. Open a contract record from the **Contracts** list.
2. Click **Upload Counterparty Version** to import the other party's marked-up version.
3. The platform generates a **redline comparison** view showing insertions (green) and deletions (red).
4. Reviewers can accept or reject each change individually.
5. Click **Accept All** or **Reject All** for bulk actions, then fine-tune as needed.
6. When negotiation is complete, click **Finalize Contract** to create the executed version.

---

## 10. Analytics Module

Navigate to **Analytics** in the left sidebar.

`[SCREENSHOT PLACEHOLDER: Analytics dashboard showing win rate gauge, pipeline distribution bar chart, and approval queue table]`

---

### 10.1 KPI Metrics Panel

The top section of the Analytics module shows organization-wide KPIs with trend sparklines, including pipeline value, deal count by stage, average deal cycle time, and proposal submission rate.

---

### 10.2 Win Rate Gauge

The Win Rate gauge shows your **year-to-date win rate** as a percentage of submitted proposals. The gauge is color-coded:

- **Red (0–30%)** — below target
- **Amber (30–50%)** — approaching target
- **Green (50%+)** — at or above target

Filter the win rate by **time period**, **agency**, **contract type**, or **deal size** using the dropdowns above the gauge.

---

### 10.3 Pipeline Distribution

The Pipeline Distribution chart (bar or donut) breaks down all active deals by stage. Switch between:

- **By Count** — number of deals per stage
- **By Value** — total estimated dollar value per stage

Click any stage bar/segment to drill down to the filtered Deals Pipeline Kanban view.

---

### 10.4 Pending Approvals Queue

The Pending Approvals table in Analytics gives approvers a consolidated view across all modules:

| Column | Description |
|---|---|
| Item | Name and type of item awaiting approval |
| Submitted By | User who submitted for approval |
| Submitted Date | When the approval request was created |
| Due | Approval deadline (if any) |
| Action | Approve / Reject buttons |

Sort by **Due** date to prioritize time-sensitive approvals.

---

### 10.5 Upcoming Deadlines Tracker

The Deadlines table lists all tracked deadlines across all active deals, sortable by date. Items are color-coded by urgency. Export this table to CSV using the **Export** button for offline tracking or executive reporting.

---

## 11. Past Performance Vault

Navigate to **Past Performance** in the left sidebar.

---

### 11.1 Adding Past Performance Records

1. Click **+ Add Record** in the Past Performance Vault.
2. Fill in the record details:
   - **Contract Name / Title**
   - **Customer / Agency**
   - **Contract Number**
   - **Contract Type** (FFP, T&M, CPFF, etc.)
   - **Contract Value**
   - **Period of Performance** (start and end dates)
   - **NAICS Code(s)**
   - **Description of Work** — write a detailed narrative (minimum 200 words recommended for best search results)
   - **Key Personnel** involved
   - **Customer Reference** — name, title, email, and phone of a reference contact
   - **CPARs Rating** (if applicable)
3. Click **Save Record**. The platform will index the record for semantic search.

> **Tip:** The more detailed and specific the Description of Work, the better the AI can surface this record as a relevant match when scoring new opportunities and generating proposal sections.

---

### 11.2 Semantic Search

1. In the Past Performance Vault, use the **Search** bar.
2. Type a natural language query such as: *"cloud migration for a federal health agency"* or *"zero trust architecture implementation."*
3. The platform uses **vector search** (semantic similarity) — results are ranked by meaning, not just keyword match, so you'll find relevant records even if they use different terminology.
4. Results show a **relevance score** and a highlighted excerpt of the matching description.

---

### 11.3 Generating Narratives

1. Select one or more past performance records using the checkboxes.
2. Click **Generate Narrative**.
3. Specify the **Target Opportunity** or **NAICS focus** to tailor the narrative.
4. The AI generates a formatted past performance narrative suitable for proposal submission (typically CPARS-aligned format).
5. Review, edit, and click **Copy to Clipboard** or **Insert into Proposal** to use it directly.

---

## 12. Knowledge Vault

Navigate to **Knowledge Vault** in the left sidebar.

---

### 12.1 Adding Knowledge Articles

The Knowledge Vault stores institutional knowledge — capability statements, technical white papers, standard operating procedures, boilerplate language, and lessons learned.

1. Click **+ New Article**.
2. Fill in:
   - **Title** — a clear, descriptive name
   - **Category** — select from tags (e.g., Technical, Pricing, Legal, HR, BD)
   - **Content** — use the rich text editor to write or paste content
   - **Tags** — add searchable keywords
   - **Visibility** — Public (all users) or Restricted (specific roles)
3. Click **Publish**. The article is immediately available for search.
4. To upload a document as a knowledge article, click **Upload File** instead of writing inline.

---

### 12.2 Searching the Knowledge Base

1. Use the **Search** bar at the top of the Knowledge Vault page.
2. Like the Past Performance Vault, search uses semantic similarity — query by concept, not just keyword.
3. Filter results by **Category**, **Tag**, or **Author**.
4. Click an article to read it. Use **Copy Link** to share a direct URL with a colleague.

> **Tip:** The Knowledge Vault is automatically queried by the AI Assist feature in the Proposals module. Keeping your knowledge base current and well-written directly improves the quality of AI-generated proposal drafts.

---

## 13. Settings & Preferences

Navigate to **Settings** in the left sidebar (gear icon, near the bottom).

---

### 13.1 Profile Management

1. Go to **Settings > Profile**.
2. Update your:
   - **Display Name**
   - **Email Address** (requires email verification)
   - **Profile Photo** — click the avatar to upload a new image (JPG or PNG, max 2 MB)
   - **Job Title**
   - **Phone Number**
3. Click **Save Changes**.

**Changing your password:**

1. Go to **Settings > Security**.
2. Enter your **Current Password**.
3. Enter and confirm your **New Password**.
4. Click **Update Password**.

---

### 13.2 Notification Preferences

1. Go to **Settings > Notifications**.
2. Toggle individual notification types on or off:

| Notification | Description |
|---|---|
| Deal Stage Changes | Notify when a deal you own moves stages |
| Approval Requests | Notify when an item needs your approval |
| Deadline Alerts | Remind you N days before a tracked deadline |
| Proposal Comments | Notify when a comment is added to your section |
| New Opportunities | Notify when high-fit SAM.gov opportunities are ingested |
| System Announcements | Platform-wide notices from administrators |

3. Set your **Deadline Alert Lead Time** (e.g., notify me 7 days and 3 days before a deadline).
4. Choose your notification delivery method: **In-App**, **Email**, or **Both**.
5. Click **Save Preferences**.

---

### 13.3 Theme Selection

1. Go to **Settings > Appearance**.
2. Select **Light Mode** or **Dark Mode** using the radio buttons or the visual preview tiles.
3. Click **Apply**. This is equivalent to using the topbar toggle but persists your selection explicitly.

---

## 14. Keyboard Shortcuts & Tips

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `?` | Open keyboard shortcuts help modal |
| `G` then `D` | Go to Dashboard |
| `G` then `O` | Go to Opportunities |
| `G` then `P` | Go to Deals Pipeline |
| `G` then `A` | Go to Analytics |
| `N` | Open New Deal form (on Pipeline page) |
| `Esc` | Close open modal or panel |
| `/` | Focus the global search bar |
| `Ctrl + S` (Windows) / `Cmd + S` (Mac) | Save the current form or document |

---

### General Tips

> **Tip:** Use the **Global Search** bar (press `/` to activate) to find any deal, opportunity, document, or knowledge article from anywhere in the platform. Results are grouped by type.

> **Tip:** When reviewing a long RFP compliance matrix, use the **Export to Excel** button to work with it offline, then re-import the updated statuses in bulk using the **Import Updates** feature.

> **Tip:** The AI's recommendations improve over time. Make it a habit to always fill in the **Reason** field when moving deals through stages and when recording wins and losses.

> **Tip:** On the Kanban board, use the **Swimlane** toggle (in the view options) to group deals by Capture Manager or by Agency instead of the default stage-column view.

> **Tip:** Set browser bookmark shortcuts to frequently visited deal records so you can jump directly to them without navigating through the pipeline.

> **Warning:** Avoid opening the same deal in multiple browser tabs simultaneously. Concurrent edits may cause the last save to overwrite earlier changes. The platform shows a warning banner if it detects the same record is open elsewhere.

---

## 15. Troubleshooting

### Common Issues and Resolutions

---

**Issue: The page is blank or shows a loading spinner indefinitely.**

1. Perform a hard refresh: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac).
2. Clear browser cache and cookies, then reload.
3. Check your internet connection.
4. Try an incognito/private browsing window.
5. If the issue persists, contact your system administrator — there may be a backend service outage.

---

**Issue: I cannot log in even though my credentials are correct.**

1. Ensure Caps Lock is not accidentally enabled.
2. Try resetting your password using **Forgot Password?**.
3. Check if your account has been deactivated by an admin.
4. Ensure third-party browser extensions (particularly password managers or ad blockers) are not interfering with the login form.

---

**Issue: SAM.gov sync is not returning new opportunities.**

1. Check the sync timestamp displayed on the Opportunities page — a sync may have run very recently.
2. Ensure your SAM.gov API key (configured in Admin settings) has not expired. API keys must be renewed annually on SAM.gov.
3. Check for any SAM.gov outage announcements at `status.sam.gov`.
4. Contact your administrator to verify the API credentials are correctly configured in the platform settings.

---

**Issue: AI Assist is not generating content or returns an error.**

1. Check your internet connection. AI features require active connectivity.
2. Ensure the deal has an associated RFP and that the RFP has been analyzed (not just uploaded). Re-run the analysis from the RFP module if needed.
3. Very short or empty proposal sections may not give the AI enough context. Add at minimum a few bullet points as a starting framework before invoking AI Assist.
4. If the error persists, contact your administrator — the AI service may be experiencing a temporary disruption.

---

**Issue: I moved a deal to the wrong stage and need to move it back.**

1. Open the deal's detail view.
2. Use the stage selector dropdown to move it to the correct stage.
3. Enter a reason in the Stage Transition dialog (e.g., "Incorrect stage assignment — correcting to Qualify").
4. The correction is fully logged in the activity history. Auditors will see both the incorrect move and the correction with their respective reasons.

---

**Issue: A file upload fails or appears to hang.**

1. Verify the file size is under 50 MB.
2. Confirm the file type is supported (PDF, DOCX, XLSX, PPTX, PNG, JPG).
3. Try converting the file to PDF and re-uploading.
4. If on a slow or VPN connection, uploads may time out. Switch to a more stable network connection.

---

**Issue: Dark mode does not persist between sessions.**

1. Ensure your browser is not set to clear local storage on exit (common in privacy-hardened configurations).
2. Set the theme explicitly via **Settings > Appearance** as well as using the topbar toggle.
3. If using a shared/kiosk computer, note that local storage may be cleared between sessions by the device policy — this is expected behavior.

---

**Issue: I cannot see a module I expect to have access to.**

Your role controls which modules are visible in the sidebar. Reference the Role Reference table in Section 3.1. If you believe your role assignment is incorrect, contact your administrator to review and update your permissions.

---

## Appendix A: Platform Module Quick Reference

| Module | Primary Users | Key Actions |
|---|---|---|
| Dashboard | All | Monitor KPIs, approvals, deadlines |
| Opportunities | Capture Manager, Executive | Discover, score, track SAM.gov opportunities |
| Deals Pipeline | Capture Manager, All | Manage deal lifecycle via Kanban |
| Solutions | Capture Manager, Proposal Manager | AI-powered solution architecture |
| RFP | Proposal Manager, Writer | Upload RFP, manage compliance matrix |
| Proposals | Proposal Manager, Writer | Draft, review, and submit proposals |
| Pricing | Pricing Manager | Rate cards, cost modeling, win price |
| Contracts | Contracts Manager | Templates, clause library, redlines |
| Strategy | Executive, Capture Manager | Bid/no-bid strategy and win themes |
| Marketing | Marketing, Writer | Competitive positioning, capabilities |
| Research | Capture Manager | Competitive intelligence and market research |
| Legal | Legal, Contracts Manager | Compliance review, legal risk flags |
| Teaming | Capture Manager | Subcontractor and partner management |
| Security | Security, Contracts Manager | Security requirement mapping |
| Knowledge Vault | All | Institutional knowledge base |
| Communications | Writer, Proposal Manager | Email drafts and narratives |
| Past Performance | Capture Manager, Writer | PP records, semantic search, narratives |
| Analytics | Executive, Admin, Capture Manager | Pipeline health, win rates, deadlines |
| Settings | All | Profile, notifications, theme |
| Admin > Users | Admin | User creation, role assignment |

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| BAFO | Best and Final Offer — a final pricing submission requested by the government after initial proposal review |
| Capture | The business development process of pursuing a specific opportunity |
| CPARS | Contractor Performance Assessment Reporting System — official government performance ratings |
| FAR | Federal Acquisition Regulation — the primary set of rules governing federal procurement |
| DFARS | Defense Federal Acquisition Regulation Supplement — DoD-specific acquisition rules |
| Fit Score | AI-generated score (0–100) representing how well an opportunity aligns with your company's profile |
| IGCE | Independent Government Cost Estimate — the government's internal cost estimate for a procurement |
| Kanban | A visual project management method using columns (stages) and cards (deals) |
| NAICS | North American Industry Classification System — codes that classify business activities |
| RFP | Request for Proposal — the government's formal solicitation document |
| SAM.gov | System for Award Management — the federal government's official contracting opportunity portal |
| Set-Aside | A procurement reserved for specific small business categories (e.g., 8(a), WOSB, SDVOSB) |
| Vector Search | A semantic search method that finds results based on meaning rather than exact keyword matches |

---

*For technical support, contact your platform administrator or refer to the internal IT helpdesk portal.*

*This document is maintained by the platform administration team. Last reviewed: February 2026.*
