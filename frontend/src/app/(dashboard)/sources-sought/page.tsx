"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Search,
  Plus,
  FileText,
  Send,
  Clock,
  Star,
  ChevronDown,
  ChevronUp,
  Trash2,
  Copy,
  CheckCircle,
  Eye,
  Mail,
  X,
  Edit3,
  AlertCircle,
  Briefcase,
} from "lucide-react";

// ── Types ───────────────────────────────────────────────────────────────────

type InterestLevel = "strongly_interested" | "moderately_interested" | "low_interest" | "info_only";
type ResponseStatus = "draft" | "in_review" | "submitted" | "no_response";

interface SourcesSoughtResponse {
  id: string;
  title: string;
  solicitationNumber: string;
  interestLevel: InterestLevel;
  status: ResponseStatus;
  dealName: string;
  submittedDate: string | null;
  companyOverview: string;
  relevantExperience: string;
  technicalApproach: string;
  capabilityGaps: string;
  questionsForGovernment: string[];
  createdAt: string;
  updatedAt: string;
}

// ── Constants ───────────────────────────────────────────────────────────────

const INTEREST_LEVEL_CONFIG: Record<InterestLevel, { label: string; color: string }> = {
  strongly_interested: { label: "Strongly Interested", color: "bg-green-100 text-green-700 border-green-200" },
  moderately_interested: { label: "Moderately Interested", color: "bg-blue-100 text-blue-700 border-blue-200" },
  low_interest: { label: "Low Interest", color: "bg-yellow-100 text-yellow-700 border-yellow-200" },
  info_only: { label: "Info Only", color: "bg-gray-100 text-gray-600 border-gray-200" },
};

const STATUS_CONFIG: Record<ResponseStatus, { label: string; color: string }> = {
  draft: { label: "Draft", color: "bg-slate-100 text-slate-600" },
  in_review: { label: "In Review", color: "bg-amber-100 text-amber-700" },
  submitted: { label: "Submitted", color: "bg-green-100 text-green-700" },
  no_response: { label: "No Response", color: "bg-red-100 text-red-600" },
};

// ── Mock Data ───────────────────────────────────────────────────────────────

const INITIAL_RESPONSES: SourcesSoughtResponse[] = [
  {
    id: "ss-001",
    title: "Enterprise Cloud Migration Services",
    solicitationNumber: "W911NF-26-SS-0042",
    interestLevel: "strongly_interested",
    status: "submitted",
    dealName: "Army Cloud Modernization",
    submittedDate: "2026-02-28",
    companyOverview:
      "Acme Federal Solutions is a Service-Disabled Veteran-Owned Small Business (SDVOSB) with over 12 years of experience delivering enterprise IT modernization solutions to DoD and civilian agencies. We hold a FedRAMP High ATO and maintain AWS GovCloud and Azure Government competencies.",
    relevantExperience:
      "We have successfully delivered three cloud migration programs for DoD customers totaling over $45M in contract value, including the Army ITES-3S Cloud Migration Task Order where we migrated 200+ applications to AWS GovCloud within 18 months. Our CPARS ratings across these efforts average Very Good to Exceptional.",
    technicalApproach:
      "Our approach leverages our proprietary Cloud Migration Assessment Framework (CMAF) to evaluate workload readiness, identify dependencies, and sequence migrations for minimal operational disruption. We employ a factory model with automated tooling for repeatable, efficient migrations at scale.",
    capabilityGaps:
      "We would seek a teaming partner with specialized Oracle database migration expertise for legacy ERP systems. We are currently pursuing Oracle Cloud Infrastructure (OCI) certifications to address this gap organically.",
    questionsForGovernment: [
      "Is the Government open to a phased migration approach that prioritizes mission-critical applications?",
      "What is the current state of the network infrastructure between on-premise data centers and the target cloud environment?",
      "Will the Government provide access to existing application documentation and architecture diagrams?",
    ],
    createdAt: "2026-02-15",
    updatedAt: "2026-02-28",
  },
  {
    id: "ss-002",
    title: "Cybersecurity Operations Center Support",
    solicitationNumber: "FA8771-26-RFI-0103",
    interestLevel: "moderately_interested",
    status: "in_review",
    dealName: "USAF SOC Modernization",
    submittedDate: null,
    companyOverview:
      "Acme Federal Solutions maintains a robust cybersecurity practice with 85+ cleared professionals holding CISSP, CEH, and GIAC certifications. We operate a 24/7 Security Operations Center supporting multiple federal agencies.",
    relevantExperience:
      "Currently performing Tier 1-3 SOC support for DHS CISA under a $12M IDIQ task order. Previously provided MDR services to DISA under the ENCORE III vehicle. Our team has direct experience with Splunk, CrowdStrike, and Palo Alto XSOAR in federal environments.",
    technicalApproach:
      "We propose a modern SOC architecture built on SOAR automation, AI-driven threat detection, and zero-trust principles. Our approach reduces mean-time-to-detect (MTTD) by 60% through automated triage and correlation of security events.",
    capabilityGaps:
      "No significant gaps identified. We may augment our team with additional TS/SCI-cleared analysts depending on the scope and location requirements.",
    questionsForGovernment: [
      "What is the anticipated contract vehicle for this requirement (new standalone or existing IDIQ)?",
      "Are there existing SIEM/SOAR tools deployed that the contractor must integrate with?",
    ],
    createdAt: "2026-02-20",
    updatedAt: "2026-03-05",
  },
  {
    id: "ss-003",
    title: "Data Analytics Platform for VA Health Systems",
    solicitationNumber: "36C10X-26-SS-0087",
    interestLevel: "low_interest",
    status: "draft",
    dealName: "VA Data Analytics",
    submittedDate: null,
    companyOverview:
      "Acme Federal Solutions provides advanced data analytics and AI/ML solutions to federal health agencies. We are a verified SDVOSB with VA CVE certification and extensive experience with VistA and VA health data systems.",
    relevantExperience:
      "Limited direct experience with VA health data systems. Our primary health IT experience is with MHS GENESIS (DoD) where we developed clinical data dashboards and predictive analytics models for patient flow optimization.",
    technicalApproach: "",
    capabilityGaps:
      "Significant gaps in VA-specific domain knowledge, VistA integration, and HIPAA compliance frameworks specific to VA. Would require substantial teaming or subcontracting to be competitive.",
    questionsForGovernment: [
      "Is the Government considering set-aside categories for this procurement?",
    ],
    createdAt: "2026-03-01",
    updatedAt: "2026-03-01",
  },
];

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── Response Card ───────────────────────────────────────────────────────────

function ResponseCard({
  response,
  onEdit,
  onDelete,
  onViewEmail,
}: {
  response: SourcesSoughtResponse;
  onEdit: (r: SourcesSoughtResponse) => void;
  onDelete: (id: string) => void;
  onViewEmail: (r: SourcesSoughtResponse) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const interest = INTEREST_LEVEL_CONFIG[response.interestLevel];
  const status = STATUS_CONFIG[response.status];

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-md">
      <CardContent className="pt-5">
        {/* Top row */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className="text-base font-semibold text-foreground">
                {response.title}
              </h3>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {response.solicitationNumber}
              </span>
              <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${interest.color}`}>
                {interest.label}
              </span>
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${status.color}`}>
                {status.label}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <Button size="sm" variant="ghost" onClick={() => onViewEmail(response)} title="Generate Email">
              <Mail className="h-3.5 w-3.5" />
            </Button>
            <Button size="sm" variant="ghost" onClick={() => onEdit(response)} title="Edit">
              <Edit3 className="h-3.5 w-3.5" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onDelete(response.id)}
              className="text-destructive hover:bg-destructive/10"
              title="Delete"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setExpanded((v) => !v)}>
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Meta row */}
        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Briefcase className="h-3 w-3" />
            {response.dealName}
          </span>
          {response.submittedDate && (
            <span className="flex items-center gap-1">
              <Send className="h-3 w-3" />
              Submitted {formatDate(response.submittedDate)}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Updated {formatDate(response.updatedAt)}
          </span>
        </div>

        {/* Company overview preview */}
        {!expanded && response.companyOverview && (
          <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
            {response.companyOverview}
          </p>
        )}

        {/* Questions count */}
        {!expanded && response.questionsForGovernment.length > 0 && (
          <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
            <AlertCircle className="h-3 w-3" />
            {response.questionsForGovernment.length} question{response.questionsForGovernment.length !== 1 ? "s" : ""} for Government
          </div>
        )}

        {/* Expanded detail */}
        {expanded && (
          <div className="mt-4 space-y-4 border-t pt-4">
            {response.companyOverview && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Company Overview
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.companyOverview}
                </p>
              </div>
            )}

            {response.relevantExperience && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Relevant Experience
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.relevantExperience}
                </p>
              </div>
            )}

            {response.technicalApproach && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Technical Approach Summary
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.technicalApproach}
                </p>
              </div>
            )}

            {response.capabilityGaps && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Capability Gaps
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.capabilityGaps}
                </p>
              </div>
            )}

            {response.questionsForGovernment.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Questions for Government
                </p>
                <ol className="space-y-1.5 list-decimal list-inside">
                  {response.questionsForGovernment.map((q, i) => (
                    <li key={i} className="text-sm text-muted-foreground">
                      {q}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Create / Edit Form ──────────────────────────────────────────────────────

interface FormData {
  title: string;
  solicitationNumber: string;
  interestLevel: InterestLevel;
  status: ResponseStatus;
  dealName: string;
  companyOverview: string;
  relevantExperience: string;
  technicalApproach: string;
  capabilityGaps: string;
  questionsForGovernment: string[];
}

const EMPTY_FORM: FormData = {
  title: "",
  solicitationNumber: "",
  interestLevel: "strongly_interested",
  status: "draft",
  dealName: "",
  companyOverview: "",
  relevantExperience: "",
  technicalApproach: "",
  capabilityGaps: "",
  questionsForGovernment: [],
};

function ResponseForm({
  initialData,
  onSave,
  onCancel,
}: {
  initialData: FormData | null;
  onSave: (data: FormData) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<FormData>(initialData ?? EMPTY_FORM);
  const [questionInput, setQuestionInput] = useState("");

  const isEditing = initialData !== null;

  const set = <K extends keyof FormData>(key: K, value: FormData[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const addQuestion = () => {
    if (!questionInput.trim()) return;
    set("questionsForGovernment", [...form.questionsForGovernment, questionInput.trim()]);
    setQuestionInput("");
  };

  const removeQuestion = (idx: number) => {
    set(
      "questionsForGovernment",
      form.questionsForGovernment.filter((_, i) => i !== idx)
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.solicitationNumber.trim()) return;
    onSave(form);
  };

  const labelCls = "block text-xs font-medium text-muted-foreground mb-1";
  const selectCls =
    "w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";
  const textareaCls =
    "w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[100px] resize-y";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {isEditing ? "Edit Response" : "Create New Sources Sought Response"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Row 1: Title and Solicitation Number */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={labelCls}>
                Title <span className="text-red-500">*</span>
              </label>
              <Input
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
                placeholder="e.g. Enterprise Cloud Migration Services"
              />
            </div>
            <div>
              <label className={labelCls}>
                Solicitation Number <span className="text-red-500">*</span>
              </label>
              <Input
                value={form.solicitationNumber}
                onChange={(e) => set("solicitationNumber", e.target.value)}
                placeholder="e.g. W911NF-26-SS-0042"
              />
            </div>
          </div>

          {/* Row 2: Interest Level, Status, Deal */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className={labelCls}>Interest Level</label>
              <select
                className={selectCls}
                value={form.interestLevel}
                onChange={(e) => set("interestLevel", e.target.value as InterestLevel)}
              >
                <option value="strongly_interested">Strongly Interested</option>
                <option value="moderately_interested">Moderately Interested</option>
                <option value="low_interest">Low Interest</option>
                <option value="info_only">Info Only</option>
              </select>
            </div>
            <div>
              <label className={labelCls}>Status</label>
              <select
                className={selectCls}
                value={form.status}
                onChange={(e) => set("status", e.target.value as ResponseStatus)}
              >
                <option value="draft">Draft</option>
                <option value="in_review">In Review</option>
                <option value="submitted">Submitted</option>
                <option value="no_response">No Response</option>
              </select>
            </div>
            <div>
              <label className={labelCls}>Deal Association</label>
              <Input
                value={form.dealName}
                onChange={(e) => set("dealName", e.target.value)}
                placeholder="e.g. Army Cloud Modernization"
              />
            </div>
          </div>

          {/* Company Overview */}
          <div>
            <label className={labelCls}>Company Overview</label>
            <textarea
              className={textareaCls}
              value={form.companyOverview}
              onChange={(e) => set("companyOverview", e.target.value)}
              placeholder="Provide a brief company overview including business size, certifications, and core competencies relevant to this opportunity..."
            />
          </div>

          {/* Relevant Experience */}
          <div>
            <label className={labelCls}>Relevant Experience</label>
            <textarea
              className={textareaCls}
              value={form.relevantExperience}
              onChange={(e) => set("relevantExperience", e.target.value)}
              placeholder="Describe 2-3 relevant past performance examples demonstrating your capability to perform similar work..."
            />
          </div>

          {/* Technical Approach Summary */}
          <div>
            <label className={labelCls}>Technical Approach Summary</label>
            <textarea
              className={textareaCls}
              value={form.technicalApproach}
              onChange={(e) => set("technicalApproach", e.target.value)}
              placeholder="Outline your proposed technical approach, methodology, and key differentiators..."
            />
          </div>

          {/* Capability Gaps */}
          <div>
            <label className={labelCls}>Capability Gaps</label>
            <textarea
              className={`${textareaCls} min-h-[80px]`}
              value={form.capabilityGaps}
              onChange={(e) => set("capabilityGaps", e.target.value)}
              placeholder="Identify any capability gaps and describe your mitigation strategy (e.g., teaming partners, hiring plans)..."
            />
          </div>

          {/* Questions for Government */}
          <div>
            <label className={labelCls}>Questions for Government</label>
            <div className="flex gap-2">
              <Input
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                placeholder="Type a question for the Government..."
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addQuestion();
                  }
                }}
              />
              <Button type="button" variant="outline" size="sm" onClick={addQuestion}>
                <Plus className="mr-1 h-3 w-3" />
                Add
              </Button>
            </div>
            {form.questionsForGovernment.length > 0 && (
              <ol className="mt-3 space-y-2">
                {form.questionsForGovernment.map((q, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm rounded-md border bg-muted/30 px-3 py-2">
                    <span className="text-muted-foreground font-mono text-xs mt-0.5 shrink-0">
                      {i + 1}.
                    </span>
                    <span className="flex-1 text-muted-foreground">{q}</span>
                    <button
                      type="button"
                      onClick={() => removeQuestion(i)}
                      className="text-destructive hover:opacity-80 shrink-0 mt-0.5"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={!form.title.trim() || !form.solicitationNumber.trim()}>
              {isEditing ? "Update Response" : "Create Response"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

// ── Email Template Generator ────────────────────────────────────────────────

function EmailTemplateModal({
  response,
  onClose,
}: {
  response: SourcesSoughtResponse;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const interest = INTEREST_LEVEL_CONFIG[response.interestLevel];

  const questionsBlock = response.questionsForGovernment.length > 0
    ? `\n\nQUESTIONS FOR THE GOVERNMENT:\n${response.questionsForGovernment.map((q, i) => `${i + 1}. ${q}`).join("\n")}`
    : "";

  const emailTemplate = `Subject: Response to Sources Sought / RFI - ${response.solicitationNumber} - ${response.title}

To Whom It May Concern,

Please find below our response to the subject Sources Sought Notice / Request for Information (${response.solicitationNumber}) for ${response.title}.

INTEREST LEVEL: ${interest.label}

1. COMPANY OVERVIEW
${response.companyOverview || "[Company overview not yet provided]"}

DUNS Number: [INSERT DUNS]
CAGE Code: [INSERT CAGE CODE]
Business Size: [INSERT SIZE STANDARD]
NAICS Code(s): [INSERT APPLICABLE NAICS]
Socioeconomic Categories: [INSERT CATEGORIES - e.g., SDVOSB, 8(a), HUBZone]
GSA Schedule / Contract Vehicles: [INSERT APPLICABLE VEHICLES]

2. RELEVANT EXPERIENCE
${response.relevantExperience || "[Relevant experience not yet provided]"}

3. TECHNICAL APPROACH SUMMARY
${response.technicalApproach || "[Technical approach not yet provided]"}

4. CAPABILITY GAPS & TEAMING CONSIDERATIONS
${response.capabilityGaps || "[Capability gaps assessment not yet provided]"}${questionsBlock}

We appreciate the opportunity to respond to this Sources Sought notice and look forward to the potential to support this important mission. Please do not hesitate to contact us with any additional questions.

Respectfully,

[YOUR NAME]
[YOUR TITLE]
[COMPANY NAME]
[PHONE]
[EMAIL]`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(emailTemplate);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for environments without clipboard API
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-3xl max-h-[90vh] rounded-lg border bg-background shadow-lg flex flex-col">
        <div className="flex items-center justify-between border-b px-6 py-4 shrink-0">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Mail className="h-5 w-5 text-primary" />
              Email Template
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Pre-formatted submission email for {response.solicitationNumber}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleCopy}>
              {copied ? (
                <>
                  <CheckCircle className="mr-1.5 h-3.5 w-3.5 text-green-600" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="mr-1.5 h-3.5 w-3.5" />
                  Copy
                </>
              )}
            </Button>
            <button
              onClick={onClose}
              className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <div className="rounded-lg border bg-muted/30 p-4">
            <pre className="whitespace-pre-wrap text-sm font-mono text-foreground leading-relaxed">
              {emailTemplate}
            </pre>
          </div>
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Before sending</p>
                <ul className="mt-1 space-y-0.5 text-xs list-disc list-inside">
                  <li>Replace all bracketed placeholder fields with your actual company information</li>
                  <li>Verify the solicitation number and title match the published notice</li>
                  <li>Confirm the submission deadline has not passed</li>
                  <li>Check if the notice requires responses in a specific format (some agencies require PDF attachments)</li>
                  <li>Ensure you are sending to the correct Contracting Officer email address</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function SourcesSoughtPage() {
  const [responses, setResponses] = useState<SourcesSoughtResponse[]>(INITIAL_RESPONSES);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ResponseStatus | "">("");
  const [interestFilter, setInterestFilter] = useState<InterestLevel | "">("");
  const [showForm, setShowForm] = useState(false);
  const [editingResponse, setEditingResponse] = useState<SourcesSoughtResponse | null>(null);
  const [emailResponse, setEmailResponse] = useState<SourcesSoughtResponse | null>(null);

  // Filtering
  const filtered = responses.filter((r) => {
    const matchesSearch =
      !search ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.solicitationNumber.toLowerCase().includes(search.toLowerCase()) ||
      r.dealName.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || r.status === statusFilter;
    const matchesInterest = !interestFilter || r.interestLevel === interestFilter;
    return matchesSearch && matchesStatus && matchesInterest;
  });

  // Stats
  const totalResponses = responses.length;
  const submitted = responses.filter((r) => r.status === "submitted").length;
  const inDraft = responses.filter((r) => r.status === "draft").length;
  const strongInterest = responses.filter((r) => r.interestLevel === "strongly_interested").length;

  const handleSave = (data: FormData) => {
    if (editingResponse) {
      // Update existing
      setResponses((prev) =>
        prev.map((r) =>
          r.id === editingResponse.id
            ? {
                ...r,
                ...data,
                updatedAt: new Date().toISOString().split("T")[0],
                submittedDate: data.status === "submitted" && !r.submittedDate
                  ? new Date().toISOString().split("T")[0]
                  : r.submittedDate,
              }
            : r
        )
      );
      setEditingResponse(null);
    } else {
      // Create new
      const newResponse: SourcesSoughtResponse = {
        id: `ss-${Date.now()}`,
        ...data,
        submittedDate: data.status === "submitted" ? new Date().toISOString().split("T")[0] : null,
        createdAt: new Date().toISOString().split("T")[0],
        updatedAt: new Date().toISOString().split("T")[0],
      };
      setResponses((prev) => [newResponse, ...prev]);
      setShowForm(false);
    }
  };

  const handleEdit = (response: SourcesSoughtResponse) => {
    setEditingResponse(response);
    setShowForm(false);
  };

  const handleDelete = (id: string) => {
    if (!confirm("Are you sure you want to delete this response?")) return;
    setResponses((prev) => prev.filter((r) => r.id !== id));
    if (editingResponse?.id === id) setEditingResponse(null);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingResponse(null);
  };

  const selectCls =
    "h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Sources Sought Responses
          </h1>
          <p className="text-muted-foreground">
            Manage RFI and Sources Sought responses as strategic intelligence-gathering
          </p>
        </div>
        <Button onClick={() => { setShowForm(true); setEditingResponse(null); }} disabled={showForm && !editingResponse}>
          <Plus className="mr-2 h-4 w-4" />
          New Response
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          {
            label: "Total Responses",
            value: String(totalResponses),
            icon: FileText,
            iconColor: "text-blue-600",
          },
          {
            label: "Submitted",
            value: String(submitted),
            icon: Send,
            iconColor: "text-green-600",
          },
          {
            label: "In Draft",
            value: String(inDraft),
            icon: Clock,
            iconColor: "text-amber-600",
          },
          {
            label: "Strong Interest",
            value: String(strongInterest),
            icon: Star,
            iconColor: "text-purple-600",
          },
        ].map(({ label, value, icon: Icon, iconColor }) => (
          <Card key={label}>
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-foreground">{value}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{label}</p>
                </div>
                <div className="rounded-lg bg-muted p-2.5">
                  <Icon className={`h-5 w-5 ${iconColor}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create / Edit Form */}
      {(showForm || editingResponse) && (
        <ResponseForm
          initialData={
            editingResponse
              ? {
                  title: editingResponse.title,
                  solicitationNumber: editingResponse.solicitationNumber,
                  interestLevel: editingResponse.interestLevel,
                  status: editingResponse.status,
                  dealName: editingResponse.dealName,
                  companyOverview: editingResponse.companyOverview,
                  relevantExperience: editingResponse.relevantExperience,
                  technicalApproach: editingResponse.technicalApproach,
                  capabilityGaps: editingResponse.capabilityGaps,
                  questionsForGovernment: editingResponse.questionsForGovernment,
                }
              : null
          }
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-5">
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, solicitation #, or deal..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ResponseStatus | "")}
              className={selectCls}
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="in_review">In Review</option>
              <option value="submitted">Submitted</option>
              <option value="no_response">No Response</option>
            </select>
            <select
              value={interestFilter}
              onChange={(e) => setInterestFilter(e.target.value as InterestLevel | "")}
              className={selectCls}
            >
              <option value="">All Interest Levels</option>
              <option value="strongly_interested">Strongly Interested</option>
              <option value="moderately_interested">Moderately Interested</option>
              <option value="low_interest">Low Interest</option>
              <option value="info_only">Info Only</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Response List */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <FileText className="h-10 w-10 text-muted-foreground" />
          <p className="text-muted-foreground">
            {responses.length === 0
              ? "No sources sought responses yet. Create your first one!"
              : "No responses match your filters."}
          </p>
          {responses.length === 0 && (
            <Button onClick={() => setShowForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create First Response
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-xs text-muted-foreground">
            {filtered.length} response{filtered.length !== 1 ? "s" : ""}
            {filtered.length !== responses.length && ` of ${responses.length} total`}
          </p>
          {filtered.map((response) => (
            <ResponseCard
              key={response.id}
              response={response}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onViewEmail={setEmailResponse}
            />
          ))}
        </div>
      )}

      {/* Email Template Modal */}
      {emailResponse && (
        <EmailTemplateModal
          response={emailResponse}
          onClose={() => setEmailResponse(null)}
        />
      )}
    </div>
  );
}
