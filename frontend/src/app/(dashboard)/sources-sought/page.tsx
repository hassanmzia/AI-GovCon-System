"use client";

import { useState, useEffect, useCallback } from "react";
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
  Mail,
  X,
  Edit3,
  AlertCircle,
  Briefcase,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import {
  type SourcesSoughtResponse,
  type InterestLevel,
  type ResponseStatus,
  type SourcesSoughtPayload,
  getSourcesSought,
  createSourcesSought,
  updateSourcesSought,
  deleteSourcesSought,
} from "@/services/sources-sought";

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
  const interest = INTEREST_LEVEL_CONFIG[response.interest_level];
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
                {response.solicitation_number}
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
          {response.deal_name && (
            <span className="flex items-center gap-1">
              <Briefcase className="h-3 w-3" />
              {response.deal_name}
            </span>
          )}
          {response.submitted_at && (
            <span className="flex items-center gap-1">
              <Send className="h-3 w-3" />
              Submitted {formatDate(response.submitted_at)}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Updated {formatDate(response.updated_at)}
          </span>
        </div>

        {/* Company overview preview */}
        {!expanded && response.company_overview && (
          <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
            {response.company_overview}
          </p>
        )}

        {/* Questions count */}
        {!expanded && response.questions_for_government.length > 0 && (
          <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
            <AlertCircle className="h-3 w-3" />
            {response.questions_for_government.length} question{response.questions_for_government.length !== 1 ? "s" : ""} for Government
          </div>
        )}

        {/* Expanded detail */}
        {expanded && (
          <div className="mt-4 space-y-4 border-t pt-4">
            {response.company_overview && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Company Overview
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.company_overview}
                </p>
              </div>
            )}

            {response.relevant_experience && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Relevant Experience
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.relevant_experience}
                </p>
              </div>
            )}

            {response.technical_approach_summary && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Technical Approach Summary
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.technical_approach_summary}
                </p>
              </div>
            )}

            {response.capability_gaps && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Capability Gaps
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {response.capability_gaps}
                </p>
              </div>
            )}

            {response.questions_for_government.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Questions for Government
                </p>
                <ol className="space-y-1.5 list-decimal list-inside">
                  {response.questions_for_government.map((q, i) => (
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
  solicitation_number: string;
  interest_level: InterestLevel;
  status: ResponseStatus;
  deal_name: string;
  company_overview: string;
  relevant_experience: string;
  technical_approach_summary: string;
  capability_gaps: string;
  questions_for_government: string[];
}

const EMPTY_FORM: FormData = {
  title: "",
  solicitation_number: "",
  interest_level: "strongly_interested",
  status: "draft",
  deal_name: "",
  company_overview: "",
  relevant_experience: "",
  technical_approach_summary: "",
  capability_gaps: "",
  questions_for_government: [],
};

function ResponseForm({
  initialData,
  onSave,
  onCancel,
  saving,
}: {
  initialData: FormData | null;
  onSave: (data: FormData) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const [form, setForm] = useState<FormData>(initialData ?? EMPTY_FORM);
  const [questionInput, setQuestionInput] = useState("");

  const isEditing = initialData !== null;

  const set = <K extends keyof FormData>(key: K, value: FormData[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const addQuestion = () => {
    if (!questionInput.trim()) return;
    set("questions_for_government", [...form.questions_for_government, questionInput.trim()]);
    setQuestionInput("");
  };

  const removeQuestion = (idx: number) => {
    set(
      "questions_for_government",
      form.questions_for_government.filter((_, i) => i !== idx)
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.solicitation_number.trim()) return;
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
                value={form.solicitation_number}
                onChange={(e) => set("solicitation_number", e.target.value)}
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
                value={form.interest_level}
                onChange={(e) => set("interest_level", e.target.value as InterestLevel)}
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
                value={form.deal_name}
                onChange={(e) => set("deal_name", e.target.value)}
                placeholder="e.g. Army Cloud Modernization"
              />
            </div>
          </div>

          {/* Company Overview */}
          <div>
            <label className={labelCls}>Company Overview</label>
            <textarea
              className={textareaCls}
              value={form.company_overview}
              onChange={(e) => set("company_overview", e.target.value)}
              placeholder="Provide a brief company overview including business size, certifications, and core competencies relevant to this opportunity..."
            />
          </div>

          {/* Relevant Experience */}
          <div>
            <label className={labelCls}>Relevant Experience</label>
            <textarea
              className={textareaCls}
              value={form.relevant_experience}
              onChange={(e) => set("relevant_experience", e.target.value)}
              placeholder="Describe 2-3 relevant past performance examples demonstrating your capability to perform similar work..."
            />
          </div>

          {/* Technical Approach Summary */}
          <div>
            <label className={labelCls}>Technical Approach Summary</label>
            <textarea
              className={textareaCls}
              value={form.technical_approach_summary}
              onChange={(e) => set("technical_approach_summary", e.target.value)}
              placeholder="Outline your proposed technical approach, methodology, and key differentiators..."
            />
          </div>

          {/* Capability Gaps */}
          <div>
            <label className={labelCls}>Capability Gaps</label>
            <textarea
              className={`${textareaCls} min-h-[80px]`}
              value={form.capability_gaps}
              onChange={(e) => set("capability_gaps", e.target.value)}
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
            {form.questions_for_government.length > 0 && (
              <ol className="mt-3 space-y-2">
                {form.questions_for_government.map((q, i) => (
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
            <Button type="submit" disabled={!form.title.trim() || !form.solicitation_number.trim() || saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
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

  const interest = INTEREST_LEVEL_CONFIG[response.interest_level];

  const questionsBlock = response.questions_for_government.length > 0
    ? `\n\nQUESTIONS FOR THE GOVERNMENT:\n${response.questions_for_government.map((q, i) => `${i + 1}. ${q}`).join("\n")}`
    : "";

  const emailTemplate = `Subject: Response to Sources Sought / RFI - ${response.solicitation_number} - ${response.title}

To Whom It May Concern,

Please find below our response to the subject Sources Sought Notice / Request for Information (${response.solicitation_number}) for ${response.title}.

INTEREST LEVEL: ${interest.label}

1. COMPANY OVERVIEW
${response.company_overview || "[Company overview not yet provided]"}

DUNS Number: [INSERT DUNS]
CAGE Code: [INSERT CAGE CODE]
Business Size: [INSERT SIZE STANDARD]
NAICS Code(s): [INSERT APPLICABLE NAICS]
Socioeconomic Categories: [INSERT CATEGORIES - e.g., SDVOSB, 8(a), HUBZone]
GSA Schedule / Contract Vehicles: [INSERT APPLICABLE VEHICLES]

2. RELEVANT EXPERIENCE
${response.relevant_experience || "[Relevant experience not yet provided]"}

3. TECHNICAL APPROACH SUMMARY
${response.technical_approach_summary || "[Technical approach not yet provided]"}

4. CAPABILITY GAPS & TEAMING CONSIDERATIONS
${response.capability_gaps || "[Capability gaps assessment not yet provided]"}${questionsBlock}

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
        <div className="flex items-center justify-between border-b px-4 sm:px-6 py-4 shrink-0">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Mail className="h-5 w-5 text-primary" />
              Email Template
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Pre-formatted submission email for {response.solicitation_number}
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
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
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
  const [responses, setResponses] = useState<SourcesSoughtResponse[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<ResponseStatus | "">("");
  const [interestFilter, setInterestFilter] = useState<InterestLevel | "">("");
  const [showForm, setShowForm] = useState(false);
  const [editingResponse, setEditingResponse] = useState<SourcesSoughtResponse | null>(null);
  const [emailResponse, setEmailResponse] = useState<SourcesSoughtResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // ── Load data ─────────────────────────────────────────────────────────

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getSourcesSought();
      setResponses(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load responses";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filtering
  const filtered = responses.filter((r) => {
    const matchesSearch =
      !search ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.solicitation_number.toLowerCase().includes(search.toLowerCase()) ||
      r.deal_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || r.status === statusFilter;
    const matchesInterest = !interestFilter || r.interest_level === interestFilter;
    return matchesSearch && matchesStatus && matchesInterest;
  });

  // Stats
  const totalResponses = responses.length;
  const submitted = responses.filter((r) => r.status === "submitted").length;
  const inDraft = responses.filter((r) => r.status === "draft").length;
  const strongInterest = responses.filter((r) => r.interest_level === "strongly_interested").length;

  const handleSave = async (data: FormData) => {
    setSaving(true);
    try {
      const payload: SourcesSoughtPayload = {
        title: data.title,
        solicitation_number: data.solicitation_number,
        deal_name: data.deal_name,
        interest_level: data.interest_level,
        status: data.status,
        company_overview: data.company_overview,
        relevant_experience: data.relevant_experience,
        technical_approach_summary: data.technical_approach_summary,
        capability_gaps: data.capability_gaps,
        questions_for_government: data.questions_for_government,
      };

      if (editingResponse) {
        const updated = await updateSourcesSought(editingResponse.id, payload);
        setResponses((prev) => prev.map((r) => (r.id === editingResponse.id ? updated : r)));
        setEditingResponse(null);
      } else {
        const created = await createSourcesSought(payload);
        setResponses((prev) => [created, ...prev]);
        setShowForm(false);
      }
    } catch {
      // handle error
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (response: SourcesSoughtResponse) => {
    setEditingResponse(response);
    setShowForm(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this response?")) return;
    try {
      await deleteSourcesSought(id);
      setResponses((prev) => prev.filter((r) => r.id !== id));
      if (editingResponse?.id === id) setEditingResponse(null);
    } catch {
      // handle error
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingResponse(null);
  };

  const selectCls =
    "h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto";

  // ── Loading / Error ───────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={loadData}>Retry</Button>
      </div>
    );
  }

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
          { label: "Total Responses", value: String(totalResponses), icon: FileText, iconColor: "text-blue-600" },
          { label: "Submitted", value: String(submitted), icon: Send, iconColor: "text-green-600" },
          { label: "In Draft", value: String(inDraft), icon: Clock, iconColor: "text-amber-600" },
          { label: "Strong Interest", value: String(strongInterest), icon: Star, iconColor: "text-purple-600" },
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
                  solicitation_number: editingResponse.solicitation_number,
                  interest_level: editingResponse.interest_level,
                  status: editingResponse.status,
                  deal_name: editingResponse.deal_name,
                  company_overview: editingResponse.company_overview,
                  relevant_experience: editingResponse.relevant_experience,
                  technical_approach_summary: editingResponse.technical_approach_summary,
                  capability_gaps: editingResponse.capability_gaps,
                  questions_for_government: editingResponse.questions_for_government,
                }
              : null
          }
          onSave={handleSave}
          onCancel={handleCancel}
          saving={saving}
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
