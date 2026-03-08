"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ClipboardCheck,
  ShieldCheck,
  FileWarning,
  ChevronDown,
  ChevronRight,
  Filter,
  BarChart3,
  ListChecks,
  AlertOctagon,
  CircleDot,
  CheckSquare,
  Square,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ComplianceStatus = "fully_addressed" | "partially_addressed" | "not_addressed";
type Severity = "high" | "medium" | "low";
type RedTeamSeverity = "critical" | "major" | "minor" | "observation";

interface ComplianceRequirement {
  id: string;
  requirementId: string;
  description: string;
  status: ComplianceStatus;
  severity: Severity;
  sectionRef: string;
  recommendation: string;
  proposal: string;
}

interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
}

interface RedTeamFinding {
  id: string;
  finding: string;
  severity: RedTeamSeverity;
  section: string;
  recommendation: string;
  resolved: boolean;
}

// ---------------------------------------------------------------------------
// Status & Severity Config
// ---------------------------------------------------------------------------

const STATUS_LABELS: Record<ComplianceStatus, string> = {
  fully_addressed: "Fully Addressed",
  partially_addressed: "Partially Addressed",
  not_addressed: "Not Addressed",
};

const STATUS_CLASSES: Record<ComplianceStatus, string> = {
  fully_addressed: "bg-green-100 text-green-700 border-green-200",
  partially_addressed: "bg-yellow-100 text-yellow-700 border-yellow-200",
  not_addressed: "bg-red-100 text-red-700 border-red-200",
};

const STATUS_ICONS: Record<ComplianceStatus, typeof CheckCircle2> = {
  fully_addressed: CheckCircle2,
  partially_addressed: AlertTriangle,
  not_addressed: XCircle,
};

const SEVERITY_CLASSES: Record<Severity, string> = {
  high: "bg-red-50 text-red-700 border-red-200",
  medium: "bg-orange-50 text-orange-700 border-orange-200",
  low: "bg-blue-50 text-blue-700 border-blue-200",
};

const RED_TEAM_SEVERITY_CLASSES: Record<RedTeamSeverity, string> = {
  critical: "bg-red-100 text-red-800 border-red-300",
  major: "bg-orange-100 text-orange-800 border-orange-300",
  minor: "bg-yellow-100 text-yellow-800 border-yellow-300",
  observation: "bg-blue-100 text-blue-800 border-blue-300",
};

// ---------------------------------------------------------------------------
// Mock Data
// ---------------------------------------------------------------------------

const PROPOSALS = [
  "All Proposals",
  "DOD Cloud Migration (FA8529-26-R-0042)",
  "VA Health IT Modernization (36C10X26R0015)",
  "DHS Cybersecurity Support (70RCSA26R00003)",
];

const INITIAL_REQUIREMENTS: ComplianceRequirement[] = [
  {
    id: "1",
    requirementId: "L-001",
    description: "Contractor shall provide a detailed transition plan within 30 days of award",
    status: "fully_addressed",
    severity: "high",
    sectionRef: "Section L.4.1",
    recommendation: "Requirement fully addressed in Technical Volume, Section 3.2",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "2",
    requirementId: "L-002",
    description: "Key personnel must possess active TS/SCI clearance",
    status: "fully_addressed",
    severity: "high",
    sectionRef: "Section L.5.2",
    recommendation: "All proposed key personnel clearances verified",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "3",
    requirementId: "L-003",
    description: "Demonstrate FedRAMP High authorization for proposed cloud solution",
    status: "partially_addressed",
    severity: "high",
    sectionRef: "Section L.4.3",
    recommendation: "FedRAMP High ATO pending; include timeline and interim authorization details",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "4",
    requirementId: "L-004",
    description: "Provide three past performance references of similar scope within last 5 years",
    status: "fully_addressed",
    severity: "medium",
    sectionRef: "Section L.6.1",
    recommendation: "Three relevant references provided with CPARS ratings",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "5",
    requirementId: "L-005",
    description: "Small business subcontracting plan required per FAR 19.702",
    status: "partially_addressed",
    severity: "medium",
    sectionRef: "Section L.7.1",
    recommendation: "Subcontracting plan drafted; needs specific SDVOSB percentage targets",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "6",
    requirementId: "L-006",
    description: "Organizational conflict of interest mitigation plan",
    status: "not_addressed",
    severity: "high",
    sectionRef: "Section L.8.2",
    recommendation: "OCI mitigation plan must be developed and included before submission",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "7",
    requirementId: "L-007",
    description: "Quality assurance surveillance plan (QASP) response",
    status: "fully_addressed",
    severity: "medium",
    sectionRef: "Section L.4.5",
    recommendation: "QASP response aligns with government metrics",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "8",
    requirementId: "L-008",
    description: "Cybersecurity framework compliance per NIST 800-171",
    status: "partially_addressed",
    severity: "high",
    sectionRef: "Section L.9.1",
    recommendation: "NIST 800-171 SSP provided; POA&M items need resolution timeline",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "9",
    requirementId: "M-001",
    description: "Technical approach evaluation criteria per Section M.2",
    status: "fully_addressed",
    severity: "high",
    sectionRef: "Section M.2",
    recommendation: "Technical approach addresses all evaluation sub-factors",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "10",
    requirementId: "M-002",
    description: "Price reasonableness documentation",
    status: "not_addressed",
    severity: "medium",
    sectionRef: "Section M.4",
    recommendation: "Basis of estimate and price justification narrative required",
    proposal: "DOD Cloud Migration (FA8529-26-R-0042)",
  },
  {
    id: "11",
    requirementId: "VA-001",
    description: "508 Compliance certification for all deliverables",
    status: "fully_addressed",
    severity: "high",
    sectionRef: "Section C.3.1",
    recommendation: "508 compliance plan included with VPAT documentation",
    proposal: "VA Health IT Modernization (36C10X26R0015)",
  },
  {
    id: "12",
    requirementId: "VA-002",
    description: "HIPAA compliance and BAA execution plan",
    status: "partially_addressed",
    severity: "high",
    sectionRef: "Section C.4.2",
    recommendation: "BAA template included; need specific PHI handling procedures",
    proposal: "VA Health IT Modernization (36C10X26R0015)",
  },
];

const INITIAL_PRE_PROPOSAL: ChecklistItem[] = [
  { id: "pre-1", label: "Read entire solicitation", checked: true },
  { id: "pre-2", label: "Identify all requirements (Sections L & M)", checked: true },
  { id: "pre-3", label: "Create compliance matrix", checked: true },
  { id: "pre-4", label: "Review evaluation criteria", checked: true },
  { id: "pre-5", label: "Identify key personnel needs", checked: false },
  { id: "pre-6", label: "Assess past performance requirements", checked: true },
];

const INITIAL_PROPOSAL: ChecklistItem[] = [
  { id: "prop-1", label: "Executive summary written", checked: true },
  { id: "prop-2", label: "Technical approach complete", checked: true },
  { id: "prop-3", label: "Past performance volume complete", checked: true },
  { id: "prop-4", label: "Management plan complete", checked: false },
  { id: "prop-5", label: "Price/cost volume complete", checked: false },
  { id: "prop-6", label: "All sections formatted per instructions", checked: false },
  { id: "prop-7", label: "Page limits verified", checked: false },
  { id: "prop-8", label: "Table of contents updated", checked: false },
  { id: "prop-9", label: "All attachments included", checked: false },
  { id: "prop-10", label: "Final review completed", checked: false },
];

const INITIAL_RED_TEAM_FINDINGS: RedTeamFinding[] = [
  {
    id: "rt-1",
    finding: "Technical approach lacks specific staffing timeline for Phase 2 migration",
    severity: "critical",
    section: "Technical Volume, Section 3.4",
    recommendation: "Add Gantt chart showing resource loading by sprint for Phase 2",
    resolved: false,
  },
  {
    id: "rt-2",
    finding: "Past performance reference #2 contract value does not meet minimum threshold",
    severity: "major",
    section: "Past Performance Volume, Section 2.2",
    recommendation: "Replace with DISA SETI contract (HC1028-22-C-0034) which exceeds threshold",
    resolved: false,
  },
  {
    id: "rt-3",
    finding: "Executive summary does not reference all evaluation sub-factors from Section M",
    severity: "major",
    section: "Executive Summary",
    recommendation: "Restructure executive summary to map to each evaluation factor explicitly",
    resolved: true,
  },
  {
    id: "rt-4",
    finding: "Risk mitigation table missing probability and impact ratings",
    severity: "minor",
    section: "Technical Volume, Section 5.1",
    recommendation: "Add 5x5 risk matrix with probability/impact scores for each identified risk",
    resolved: true,
  },
  {
    id: "rt-5",
    finding: "Acronym list incomplete - 12 undefined acronyms found in technical volume",
    severity: "minor",
    section: "Appendix A",
    recommendation: "Run acronym checker across all volumes and update master acronym list",
    resolved: false,
  },
  {
    id: "rt-6",
    finding: "Proposal uses inconsistent naming for the cloud platform across sections",
    severity: "observation",
    section: "All Volumes",
    recommendation: "Standardize to 'SecureCloud GovPlatform' throughout; update style guide",
    resolved: true,
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: ComplianceStatus }) {
  const Icon = STATUS_ICONS[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_CLASSES[status]}`}
    >
      <Icon className="h-3 w-3" />
      {STATUS_LABELS[status]}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${SEVERITY_CLASSES[severity]}`}
    >
      {severity}
    </span>
  );
}

function RedTeamSeverityBadge({ severity }: { severity: RedTeamSeverity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${RED_TEAM_SEVERITY_CLASSES[severity]}`}
    >
      {severity}
    </span>
  );
}

function ProgressBar({
  value,
  className = "",
  colorClass,
}: {
  value: number;
  className?: string;
  colorClass?: string;
}) {
  const pct = Math.min(100, Math.max(0, value));
  const color =
    colorClass ??
    (pct >= 80
      ? "bg-green-500"
      : pct >= 50
        ? "bg-yellow-500"
        : "bg-red-500");
  return (
    <div className={`h-2.5 w-full rounded-full bg-gray-200 ${className}`}>
      <div
        className={`h-2.5 rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function CircularProgress({ value }: { value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (pct / 100) * circumference;
  const color =
    pct >= 80
      ? "text-green-500"
      : pct >= 50
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg className="h-32 w-32 -rotate-90 transform" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-gray-200"
        />
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`${color} transition-all duration-700`}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold text-gray-900">{pct}%</span>
        <span className="text-xs text-gray-500">Compliant</span>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  colorClass,
}: {
  label: string;
  value: number;
  icon: typeof CheckCircle2;
  colorClass: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-white p-4">
      <div className={`rounded-lg p-2 ${colorClass}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type TabKey = "matrix" | "checklist" | "redteam";

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<TabKey>("matrix");
  const [search, setSearch] = useState("");
  const [selectedProposal, setSelectedProposal] = useState(PROPOSALS[0]);
  const [proposalDropdownOpen, setProposalDropdownOpen] = useState(false);
  const [requirements] = useState<ComplianceRequirement[]>(INITIAL_REQUIREMENTS);
  const [preProposal, setPreProposal] = useState<ChecklistItem[]>(INITIAL_PRE_PROPOSAL);
  const [proposal, setProposal] = useState<ChecklistItem[]>(INITIAL_PROPOSAL);
  const [redTeamFindings, setRedTeamFindings] = useState<RedTeamFinding[]>(INITIAL_RED_TEAM_FINDINGS);
  const [checklistExpandedPhases, setChecklistExpandedPhases] = useState<Record<string, boolean>>({
    pre: true,
    prop: true,
  });

  // -- Filtered requirements
  const filtered = requirements.filter((r) => {
    const matchesProposal =
      selectedProposal === "All Proposals" || r.proposal === selectedProposal;
    const matchesSearch =
      search === "" ||
      r.requirementId.toLowerCase().includes(search.toLowerCase()) ||
      r.description.toLowerCase().includes(search.toLowerCase()) ||
      r.sectionRef.toLowerCase().includes(search.toLowerCase());
    return matchesProposal && matchesSearch;
  });

  // -- Stats
  const total = filtered.length;
  const fully = filtered.filter((r) => r.status === "fully_addressed").length;
  const partially = filtered.filter((r) => r.status === "partially_addressed").length;
  const notAddr = filtered.filter((r) => r.status === "not_addressed").length;
  const compliancePct = total > 0 ? Math.round((fully / total) * 100) : 0;

  // -- Checklist helpers
  const toggleChecklistItem = (
    phase: "pre" | "prop",
    id: string,
  ) => {
    const setter = phase === "pre" ? setPreProposal : setProposal;
    setter((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, checked: !item.checked } : item,
      ),
    );
  };

  const togglePhase = (phase: string) => {
    setChecklistExpandedPhases((prev) => ({
      ...prev,
      [phase]: !prev[phase],
    }));
  };

  const preChecked = preProposal.filter((i) => i.checked).length;
  const propChecked = proposal.filter((i) => i.checked).length;
  const totalChecklist = preProposal.length + proposal.length;
  const totalChecked = preChecked + propChecked;
  const overallChecklistPct =
    totalChecklist > 0 ? Math.round((totalChecked / totalChecklist) * 100) : 0;

  // -- Red team helpers
  const toggleRedTeamResolved = (id: string) => {
    setRedTeamFindings((prev) =>
      prev.map((f) => (f.id === id ? { ...f, resolved: !f.resolved } : f)),
    );
  };

  const resolvedCount = redTeamFindings.filter((f) => f.resolved).length;
  const unresolvedCount = redTeamFindings.length - resolvedCount;

  // -- Tab config
  const tabs: { key: TabKey; label: string; icon: typeof ClipboardCheck }[] = [
    { key: "matrix", label: "Compliance Matrix", icon: ClipboardCheck },
    { key: "checklist", label: "Submission Checklist", icon: ListChecks },
    { key: "redteam", label: "Red Team Findings", icon: AlertOctagon },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Compliance &amp; Submission
          </h1>
          <p className="text-sm text-gray-500">
            Track proposal compliance and submission readiness
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-8 w-8 text-blue-600" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border bg-gray-50 p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* TAB: Compliance Matrix                                              */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "matrix" && (
        <div className="space-y-6">
          {/* Top stats row */}
          <div className="grid gap-6 lg:grid-cols-5">
            {/* Circular progress */}
            <Card className="lg:col-span-2">
              <CardContent className="flex flex-col items-center justify-center gap-4 py-8">
                <CircularProgress value={compliancePct} />
                <p className="text-sm font-medium text-gray-600">
                  Overall Compliance Score
                </p>
                <ProgressBar value={compliancePct} className="max-w-xs" />
              </CardContent>
            </Card>

            {/* Stat cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-2">
              <StatCard
                label="Total Requirements"
                value={total}
                icon={BarChart3}
                colorClass="bg-blue-100 text-blue-600"
              />
              <StatCard
                label="Fully Addressed"
                value={fully}
                icon={CheckCircle2}
                colorClass="bg-green-100 text-green-600"
              />
              <StatCard
                label="Partially Addressed"
                value={partially}
                icon={AlertTriangle}
                colorClass="bg-yellow-100 text-yellow-600"
              />
              <StatCard
                label="Not Addressed"
                value={notAddr}
                icon={XCircle}
                colorClass="bg-red-100 text-red-600"
              />
            </div>
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="py-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                  <Input
                    placeholder="Search requirements..."
                    value={search}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setSearch(e.target.value)
                    }
                    className="pl-9"
                  />
                </div>
                {/* Proposal filter dropdown */}
                <div className="relative">
                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                    onClick={() => setProposalDropdownOpen(!proposalDropdownOpen)}
                  >
                    <Filter className="h-4 w-4" />
                    <span className="max-w-[200px] truncate text-sm">
                      {selectedProposal}
                    </span>
                    <ChevronDown className="h-3 w-3" />
                  </Button>
                  {proposalDropdownOpen && (
                    <div className="absolute right-0 z-10 mt-1 w-80 rounded-md border bg-white shadow-lg">
                      {PROPOSALS.map((p) => (
                        <button
                          key={p}
                          className={`block w-full px-4 py-2 text-left text-sm hover:bg-gray-50 ${
                            selectedProposal === p
                              ? "bg-blue-50 font-medium text-blue-700"
                              : "text-gray-700"
                          }`}
                          onClick={() => {
                            setSelectedProposal(p);
                            setProposalDropdownOpen(false);
                          }}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Requirements table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ClipboardCheck className="h-5 w-5 text-blue-600" />
                Requirements Traceability
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-4 py-3">Req ID</th>
                      <th className="px-4 py-3">Description</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Section Ref</th>
                      <th className="px-4 py-3">Recommendation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filtered.length === 0 && (
                      <tr>
                        <td
                          colSpan={6}
                          className="px-4 py-8 text-center text-gray-400"
                        >
                          No requirements match the current filters.
                        </td>
                      </tr>
                    )}
                    {filtered.map((req) => (
                      <tr
                        key={req.id}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="whitespace-nowrap px-4 py-3 font-mono font-medium text-gray-900">
                          {req.requirementId}
                        </td>
                        <td className="max-w-xs px-4 py-3 text-gray-700">
                          {req.description}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <StatusBadge status={req.status} />
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <SeverityBadge severity={req.severity} />
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                          {req.sectionRef}
                        </td>
                        <td className="max-w-xs px-4 py-3 text-gray-600">
                          {req.recommendation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* TAB: Submission Checklist                                           */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "checklist" && (
        <div className="space-y-6">
          {/* Overall progress */}
          <Card>
            <CardContent className="py-6">
              <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-100">
                    <ListChecks className="h-7 w-7 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">
                      Overall Submission Readiness
                    </p>
                    <p className="text-3xl font-bold text-gray-900">
                      {totalChecked}
                      <span className="text-lg font-normal text-gray-400">
                        {" "}
                        / {totalChecklist}
                      </span>
                    </p>
                  </div>
                </div>
                <div className="w-full max-w-sm">
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-gray-500">Progress</span>
                    <span className="font-medium text-gray-700">
                      {overallChecklistPct}%
                    </span>
                  </div>
                  <ProgressBar value={overallChecklistPct} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Pre-Proposal Phase */}
          <Card>
            <CardHeader
              className="cursor-pointer select-none"
              onClick={() => togglePhase("pre")}
            >
              <CardTitle className="flex items-center justify-between text-lg">
                <div className="flex items-center gap-2">
                  {checklistExpandedPhases.pre ? (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  )}
                  <FileWarning className="h-5 w-5 text-orange-500" />
                  Pre-Proposal Phase
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-normal text-gray-500">
                    {preChecked} / {preProposal.length}
                  </span>
                  <div className="w-24">
                    <ProgressBar
                      value={
                        preProposal.length > 0
                          ? Math.round(
                              (preChecked / preProposal.length) * 100,
                            )
                          : 0
                      }
                      colorClass="bg-orange-500"
                    />
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            {checklistExpandedPhases.pre && (
              <CardContent className="pt-0">
                <ul className="divide-y">
                  {preProposal.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center gap-3 py-3 cursor-pointer hover:bg-gray-50 rounded px-2 -mx-2 transition-colors"
                      onClick={() => toggleChecklistItem("pre", item.id)}
                    >
                      {item.checked ? (
                        <CheckSquare className="h-5 w-5 flex-shrink-0 text-green-500" />
                      ) : (
                        <Square className="h-5 w-5 flex-shrink-0 text-gray-300" />
                      )}
                      <span
                        className={`text-sm ${
                          item.checked
                            ? "text-gray-400 line-through"
                            : "text-gray-700"
                        }`}
                      >
                        {item.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            )}
          </Card>

          {/* Proposal Phase */}
          <Card>
            <CardHeader
              className="cursor-pointer select-none"
              onClick={() => togglePhase("prop")}
            >
              <CardTitle className="flex items-center justify-between text-lg">
                <div className="flex items-center gap-2">
                  {checklistExpandedPhases.prop ? (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  )}
                  <ClipboardCheck className="h-5 w-5 text-blue-500" />
                  Proposal Phase
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-normal text-gray-500">
                    {propChecked} / {proposal.length}
                  </span>
                  <div className="w-24">
                    <ProgressBar
                      value={
                        proposal.length > 0
                          ? Math.round(
                              (propChecked / proposal.length) * 100,
                            )
                          : 0
                      }
                      colorClass="bg-blue-500"
                    />
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            {checklistExpandedPhases.prop && (
              <CardContent className="pt-0">
                <ul className="divide-y">
                  {proposal.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center gap-3 py-3 cursor-pointer hover:bg-gray-50 rounded px-2 -mx-2 transition-colors"
                      onClick={() => toggleChecklistItem("prop", item.id)}
                    >
                      {item.checked ? (
                        <CheckSquare className="h-5 w-5 flex-shrink-0 text-green-500" />
                      ) : (
                        <Square className="h-5 w-5 flex-shrink-0 text-gray-300" />
                      )}
                      <span
                        className={`text-sm ${
                          item.checked
                            ? "text-gray-400 line-through"
                            : "text-gray-700"
                        }`}
                      >
                        {item.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            )}
          </Card>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* TAB: Red Team Findings                                             */}
      {/* ------------------------------------------------------------------ */}
      {activeTab === "redteam" && (
        <div className="space-y-6">
          {/* Summary bar */}
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard
              label="Total Findings"
              value={redTeamFindings.length}
              icon={AlertOctagon}
              colorClass="bg-purple-100 text-purple-600"
            />
            <StatCard
              label="Resolved"
              value={resolvedCount}
              icon={CheckCircle2}
              colorClass="bg-green-100 text-green-600"
            />
            <StatCard
              label="Unresolved"
              value={unresolvedCount}
              icon={CircleDot}
              colorClass="bg-red-100 text-red-600"
            />
          </div>

          {/* Resolution progress */}
          <Card>
            <CardContent className="py-4">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-gray-500">Resolution Progress</span>
                <span className="font-medium text-gray-700">
                  {redTeamFindings.length > 0
                    ? Math.round(
                        (resolvedCount / redTeamFindings.length) * 100,
                      )
                    : 0}
                  %
                </span>
              </div>
              <ProgressBar
                value={
                  redTeamFindings.length > 0
                    ? Math.round(
                        (resolvedCount / redTeamFindings.length) * 100,
                      )
                    : 0
                }
                colorClass="bg-purple-500"
              />
            </CardContent>
          </Card>

          {/* Findings list */}
          <div className="space-y-3">
            {redTeamFindings.map((finding) => (
              <Card
                key={finding.id}
                className={`transition-opacity ${finding.resolved ? "opacity-60" : ""}`}
              >
                <CardContent className="py-4">
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <RedTeamSeverityBadge severity={finding.severity} />
                        <span className="text-xs text-gray-400">
                          {finding.section}
                        </span>
                      </div>
                      <Button
                        variant={finding.resolved ? "outline" : "default"}
                        size="sm"
                        className={`text-xs ${
                          finding.resolved
                            ? "border-green-300 text-green-700 hover:bg-green-50"
                            : ""
                        }`}
                        onClick={() => toggleRedTeamResolved(finding.id)}
                      >
                        {finding.resolved ? (
                          <>
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Resolved
                          </>
                        ) : (
                          "Mark Resolved"
                        )}
                      </Button>
                    </div>
                    <p
                      className={`text-sm font-medium ${
                        finding.resolved
                          ? "text-gray-400 line-through"
                          : "text-gray-900"
                      }`}
                    >
                      {finding.finding}
                    </p>
                    <div className="rounded-md bg-gray-50 px-3 py-2">
                      <p className="text-xs font-medium text-gray-500">
                        Recommendation
                      </p>
                      <p className="text-sm text-gray-700">
                        {finding.recommendation}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
