"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getProposal,
  getProposalSections,
  getReviewCycles,
  updateProposal,
  updateProposalSection,
  createReviewCycle,
} from "@/services/proposals";
import {
  getTechnicalSolution,
  getArchitectureDiagrams,
  getValidationReport,
} from "@/services/architecture";
import {
  Proposal,
  ProposalSection,
  ProposalStatus,
  SectionStatus,
  ReviewCycle,
} from "@/types/proposal";
import {
  ArchitectureResult,
  ArchitectureDiagram as ArchDiagram,
  TechnicalSolution,
  TechnicalVolume,
  ValidationReport,
} from "@/types/architecture";
import { MarkdownContent, MermaidRenderer, DiagramCard } from "@/components/proposals/solution-content";
import ReactMarkdown from "react-markdown";
import {
  Loader2,
  ArrowLeft,
  FileText,
  CheckCircle,
  Clock,
  Edit3,
  Star,
  Shield,
  BookOpen,
  ChevronDown,
  ChevronRight,
  BarChart3,
  Zap,
  Users,
  Save,
  X,
  Plus,
  Trash2,
  RotateCcw,
  Layers,
  Cpu,
  ShieldCheck,
  AlertTriangle,
  Wand2,
  Send,
  Eye,
  PenLine,
} from "lucide-react";

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  pink_team: "bg-pink-100 text-pink-700",
  red_team: "bg-red-100 text-red-700",
  gold_team: "bg-yellow-100 text-yellow-700",
  final: "bg-green-100 text-green-700",
  submitted: "bg-blue-100 text-blue-700",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  pink_team: "Pink Team",
  red_team: "Red Team",
  gold_team: "Gold Team",
  final: "Final",
  submitted: "Submitted",
};

const SECTION_STATUS_COLORS: Record<string, string> = {
  not_started: "bg-gray-100 text-gray-600",
  ai_drafted: "bg-blue-100 text-blue-700",
  in_review: "bg-yellow-100 text-yellow-700",
  revised: "bg-orange-100 text-orange-700",
  approved: "bg-green-100 text-green-700",
};

const SECTION_STATUS_LABELS: Record<string, string> = {
  not_started: "Not Started",
  ai_drafted: "AI Drafted",
  in_review: "In Review",
  revised: "Revised",
  approved: "Approved",
};

const REVIEW_TYPE_COLORS: Record<string, string> = {
  pink: "bg-pink-100 text-pink-700",
  red: "bg-red-100 text-red-700",
  gold: "bg-yellow-100 text-yellow-700",
};

const REVIEW_STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-gray-100 text-gray-600",
  in_progress: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
};

const ALL_PROPOSAL_STATUSES: ProposalStatus[] = [
  "draft",
  "pink_team",
  "red_team",
  "gold_team",
  "final",
  "submitted",
];

const ALL_SECTION_STATUSES: SectionStatus[] = [
  "not_started",
  "ai_drafted",
  "in_review",
  "revised",
  "approved",
];

// ── Compliance Meter ─────────────────────────────────────────────────────────
function ComplianceMeter({ proposal }: { proposal: Proposal }) {
  const pct = proposal.compliance_percentage || 0;
  const color =
    pct >= 90 ? "text-green-600" : pct >= 70 ? "text-yellow-600" : "text-red-600";
  const strokeColor =
    pct >= 90 ? "#16a34a" : pct >= 70 ? "#d97706" : "#dc2626";

  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex items-center gap-4">
      <div className="relative">
        <svg width={88} height={88} className="-rotate-90">
          <circle cx={44} cy={44} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={8} />
          <circle
            cx={44}
            cy={44}
            r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth={8}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-lg font-bold ${color}`}>{pct.toFixed(0)}%</span>
        </div>
      </div>
      <div>
        <p className="font-semibold">Compliance</p>
        <p className="text-sm text-muted-foreground">
          {proposal.compliant_count} / {proposal.total_requirements} requirements
        </p>
      </div>
    </div>
  );
}

// ── Section Editor Row ───────────────────────────────────────────────────────
function SectionRow({
  section,
  onSave,
  onStatusChange,
}: {
  section: ProposalSection;
  onSave: (id: string, data: Partial<ProposalSection>) => Promise<void>;
  onStatusChange: (id: string, status: SectionStatus) => Promise<void>;
}) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<"ai_draft" | "human_content" | "final_content">("ai_draft");
  const [localContent, setLocalContent] = useState({
    ai_draft: section.ai_draft || "",
    human_content: section.human_content || "",
    final_content: section.final_content || "",
  });
  const [saving, setSaving] = useState(false);

  const hasContent = section.final_content || section.human_content || section.ai_draft;

  // Determine which tab to show by default
  useEffect(() => {
    if (section.final_content) setActiveTab("final_content");
    else if (section.human_content) setActiveTab("human_content");
    else setActiveTab("ai_draft");
  }, [section.final_content, section.human_content]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const wordCount = (localContent[activeTab] || "").trim().split(/\s+/).filter(Boolean).length;
      await onSave(section.id, {
        ...localContent,
        word_count: wordCount,
      });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setLocalContent({
      ai_draft: section.ai_draft || "",
      human_content: section.human_content || "",
      final_content: section.final_content || "",
    });
    setEditing(false);
  };

  const currentContent = localContent[activeTab] || "";
  const wordCount = currentContent.trim() ? currentContent.trim().split(/\s+/).length : 0;

  const contentTabs = [
    { key: "ai_draft" as const, label: "AI Draft", icon: Wand2, color: "text-purple-600", hasContent: !!section.ai_draft },
    { key: "human_content" as const, label: "Human Draft", icon: PenLine, color: "text-blue-600", hasContent: !!section.human_content },
    { key: "final_content" as const, label: "Final", icon: CheckCircle, color: "text-green-600", hasContent: !!section.final_content },
  ];

  return (
    <div className="border rounded-lg overflow-hidden">
      <div
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <button className="text-muted-foreground flex-shrink-0">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <span className="font-mono text-xs text-muted-foreground w-12">{section.section_number}</span>
        <span className="flex-1 text-sm font-medium">{section.title}</span>

        {/* Progress indicator dots */}
        <div className="flex items-center gap-1">
          {contentTabs.map((t) => (
            <div
              key={t.key}
              className={`h-2 w-2 rounded-full ${t.hasContent ? "bg-green-500" : "bg-gray-200"}`}
              title={`${t.label}: ${t.hasContent ? "Has content" : "Empty"}`}
            />
          ))}
        </div>

        {/* Status dropdown (click stops propagation) */}
        <select
          value={section.status}
          onChange={(e) => {
            e.stopPropagation();
            onStatusChange(section.id, e.target.value as SectionStatus);
          }}
          onClick={(e) => e.stopPropagation()}
          className={`text-xs rounded-full px-2 py-0.5 border-0 cursor-pointer ${SECTION_STATUS_COLORS[section.status]}`}
        >
          {ALL_SECTION_STATUSES.map((s) => (
            <option key={s} value={s}>
              {SECTION_STATUS_LABELS[s]}
            </option>
          ))}
        </select>

        {section.page_limit && (
          <span className={`text-xs text-muted-foreground ${section.word_count > (section.page_limit * 300) ? "text-red-600 font-semibold" : ""}`}>
            {section.word_count}w / {section.page_limit}pg
          </span>
        )}
      </div>

      {expanded && (
        <div className="border-t bg-gray-50 p-4 space-y-3">
          {/* Content tabs */}
          <div className="flex items-center gap-1 border-b pb-2">
            {contentTabs.map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.key}
                  onClick={() => setActiveTab(t.key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
                    activeTab === t.key
                      ? `bg-white border border-b-white -mb-[1px] ${t.color}`
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="h-3 w-3" />
                  {t.label}
                  {t.hasContent && <span className="h-1.5 w-1.5 rounded-full bg-green-500" />}
                </button>
              );
            })}
            <div className="flex-1" />
            {!editing ? (
              <Button size="sm" variant="outline" onClick={() => setEditing(true)} className="gap-1 h-7 text-xs">
                <Edit3 className="h-3 w-3" /> Edit
              </Button>
            ) : (
              <div className="flex items-center gap-1">
                <Button size="sm" onClick={handleSave} disabled={saving} className="gap-1 h-7 text-xs">
                  <Save className="h-3 w-3" /> {saving ? "Saving..." : "Save"}
                </Button>
                <Button size="sm" variant="ghost" onClick={handleCancel} className="h-7 text-xs">
                  <X className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>

          {/* Content area */}
          {editing ? (
            <textarea
              className="w-full min-h-[250px] text-sm border rounded p-4 font-mono resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
              value={localContent[activeTab]}
              onChange={(e) =>
                setLocalContent((prev) => ({ ...prev, [activeTab]: e.target.value }))
              }
              placeholder={`Enter ${contentTabs.find((t) => t.key === activeTab)?.label || "content"}...`}
            />
          ) : currentContent ? (
            <div className="bg-white rounded border max-h-[500px] overflow-y-auto p-5">
              <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-headings:font-semibold prose-h2:text-base prose-h3:text-sm prose-p:text-gray-800 prose-p:leading-relaxed prose-li:text-gray-800 prose-strong:text-gray-900 prose-strong:font-semibold prose-table:text-sm prose-th:bg-gray-50 prose-th:text-gray-700 prose-th:font-semibold prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 prose-td:text-gray-700 prose-td:border-gray-200 prose-hr:border-gray-200 prose-a:text-blue-600">
                <ReactMarkdown>{currentContent}</ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-gray-500 bg-white rounded border border-dashed">
              <Edit3 className="h-6 w-6 mb-2" />
              <p className="text-sm">No {contentTabs.find((t) => t.key === activeTab)?.label || "content"} yet</p>
              <Button size="sm" variant="outline" onClick={() => setEditing(true)} className="mt-2 gap-1 text-xs">
                <PenLine className="h-3 w-3" /> Start Writing
              </Button>
            </div>
          )}

          {/* Footer info */}
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
            <span>{wordCount} words</span>
            {section.page_limit && (
              <span>~{Math.ceil(wordCount / 300)} of {section.page_limit} pages</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Editable List (win themes / discriminators) ─────────────────────────────
function EditableList({
  title,
  items,
  icon: Icon,
  iconColor,
  onSave,
}: {
  title: string;
  items: string[];
  icon: React.ElementType;
  iconColor: string;
  onSave: (items: string[]) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [localItems, setLocalItems] = useState(items);
  const [saving, setSaving] = useState(false);
  const [newItem, setNewItem] = useState("");

  useEffect(() => {
    setLocalItems(items);
  }, [items]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(localItems.filter((t) => t.trim()));
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  const addItem = () => {
    if (newItem.trim()) {
      setLocalItems([...localItems, newItem.trim()]);
      setNewItem("");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          {title}
        </p>
        {!editing ? (
          <button onClick={() => setEditing(true)} className="text-xs text-blue-600 hover:underline">
            Edit
          </button>
        ) : (
          <div className="flex gap-1">
            <button
              onClick={handleSave}
              disabled={saving}
              className="text-xs text-green-600 hover:underline"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => {
                setLocalItems(items);
                setEditing(false);
              }}
              className="text-xs text-muted-foreground hover:underline"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
      {editing ? (
        <div className="space-y-1.5">
          {localItems.map((item, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <Input
                value={item}
                onChange={(e) => {
                  const updated = [...localItems];
                  updated[i] = e.target.value;
                  setLocalItems(updated);
                }}
                className="h-7 text-xs"
              />
              <button
                onClick={() => setLocalItems(localItems.filter((_, idx) => idx !== i))}
                className="text-red-400 hover:text-red-600 mt-1 flex-shrink-0"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
          <div className="flex items-center gap-1.5">
            <Input
              value={newItem}
              onChange={(e) => setNewItem(e.target.value)}
              placeholder={`Add ${title.toLowerCase().replace(/s$/, "")}...`}
              className="h-7 text-xs"
              onKeyDown={(e) => e.key === "Enter" && addItem()}
            />
            <button onClick={addItem} className="text-blue-500 hover:text-blue-700 flex-shrink-0">
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>
      ) : items.length > 0 ? (
        <ul className="space-y-1">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <Icon className={`h-3.5 w-3.5 mt-0.5 flex-shrink-0 ${iconColor}`} />
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-muted-foreground italic">None defined</p>
      )}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function ProposalStudioPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [sections, setSections] = useState<ProposalSection[]>([]);
  const [reviews, setReviews] = useState<ReviewCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Main tab: "sections" or "solution"
  type MainTab = "sections" | "diagrams" | "solution" | "validation";
  const [mainTab, setMainTab] = useState<MainTab>("sections");

  // Solution data
  const [solutionResult, setSolutionResult] = useState<ArchitectureResult | null>(null);
  const [diagrams, setDiagrams] = useState<ArchDiagram[]>([]);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [solutionLoading, setSolutionLoading] = useState(false);

  // Executive summary editing
  const [editingExecSummary, setEditingExecSummary] = useState(false);
  const [execSummaryDraft, setExecSummaryDraft] = useState("");
  const [savingExecSummary, setSavingExecSummary] = useState(false);

  // Status editing
  const [savingStatus, setSavingStatus] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = await getProposal(id);
      setProposal(p);
      setExecSummaryDraft(p.executive_summary || "");
      const [sRes, rRes] = await Promise.all([
        getProposalSections(id),
        getReviewCycles(id),
      ]);
      setSections(sRes.results);
      setReviews(rRes.results);

      // Load solution data for this deal
      if (p.deal) {
        setSolutionLoading(true);
        try {
          const sol = await getTechnicalSolution(p.deal);
          if (sol) {
            setSolutionResult(sol);
            // Load diagrams and validation if we have a persisted solution ID
            if (sol.id) {
              const [diags, valReport] = await Promise.all([
                getArchitectureDiagrams(sol.id).catch(() => []),
                getValidationReport(sol.id).catch(() => null),
              ]);
              // Merge persisted diagrams with agent result diagrams
              const mergedDiagrams = diags.length > 0
                ? diags.map((d: { mermaid_code: string; diagram_type: string; title: string; description: string }) => ({
                    mermaid: d.mermaid_code,
                    mermaid_code: d.mermaid_code,
                    type: d.diagram_type,
                    title: d.title,
                    description: d.description,
                  }))
                : sol.diagrams || [];
              setDiagrams(mergedDiagrams);
              if (valReport) setValidationReport(valReport as unknown as ValidationReport);
              else if (sol.validation_report) setValidationReport(sol.validation_report);
            } else {
              setDiagrams(sol.diagrams || []);
              if (sol.validation_report) setValidationReport(sol.validation_report);
            }
          }
        } catch {
          // Solution data is optional - don't fail the whole page
        } finally {
          setSolutionLoading(false);
        }
      }
    } catch {
      setError("Failed to load proposal studio.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Save section content
  const handleSaveSection = async (sectionId: string, data: Partial<ProposalSection>) => {
    const updated = await updateProposalSection(sectionId, data);
    setSections((prev) => prev.map((s) => (s.id === sectionId ? { ...s, ...updated } : s)));
  };

  // Change section status
  const handleSectionStatusChange = async (sectionId: string, status: SectionStatus) => {
    const updated = await updateProposalSection(sectionId, { status });
    setSections((prev) => prev.map((s) => (s.id === sectionId ? { ...s, ...updated } : s)));
  };

  // Save proposal status
  const handleStatusChange = async (newStatus: ProposalStatus) => {
    if (!proposal) return;
    setSavingStatus(true);
    try {
      const updated = await updateProposal(id, { status: newStatus });
      setProposal(updated);
    } finally {
      setSavingStatus(false);
    }
  };

  // Save win themes
  const handleSaveWinThemes = async (themes: string[]) => {
    const updated = await updateProposal(id, { win_themes: themes } as Partial<Proposal>);
    setProposal(updated);
  };

  // Save discriminators
  const handleSaveDiscriminators = async (discs: string[]) => {
    const updated = await updateProposal(id, { discriminators: discs } as Partial<Proposal>);
    setProposal(updated);
  };

  // Save executive summary
  const handleSaveExecSummary = async () => {
    setSavingExecSummary(true);
    try {
      const updated = await updateProposal(id, { executive_summary: execSummaryDraft } as Partial<Proposal>);
      setProposal(updated);
      setEditingExecSummary(false);
    } finally {
      setSavingExecSummary(false);
    }
  };

  // Schedule review cycle
  const handleScheduleReview = async (reviewType: string) => {
    await createReviewCycle({
      proposal: id,
      review_type: reviewType,
    });
    const rRes = await getReviewCycles(id);
    setReviews(rRes.results);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !proposal) {
    return (
      <div className="p-6">
        <p className="text-red-600">{error || "Proposal not found."}</p>
        <Button variant="outline" onClick={() => router.back()} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>
      </div>
    );
  }

  // Group sections by volume
  const byVolume: Record<string, ProposalSection[]> = {};
  sections.forEach((s) => {
    const vol = s.volume || "Main";
    if (!byVolume[vol]) byVolume[vol] = [];
    byVolume[vol].push(s);
  });

  const approvedCount = sections.filter((s) => s.status === "approved").length;
  const draftedCount = sections.filter((s) => s.status !== "not_started").length;
  const totalWords = sections.reduce((sum, s) => sum + (s.word_count || 0), 0);

  // Determine which review types are available to schedule
  const existingReviewTypes = reviews.map((r) => r.review_type);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/proposals">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" /> Proposals
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold">{proposal.title}</h1>
            {/* Editable status dropdown */}
            <select
              value={proposal.status}
              onChange={(e) => handleStatusChange(e.target.value as ProposalStatus)}
              disabled={savingStatus}
              className={`text-xs rounded-full px-3 py-1 font-medium border-0 cursor-pointer ${STATUS_COLORS[proposal.status]}`}
            >
              {ALL_PROPOSAL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
            <span className="text-xs text-muted-foreground">v{proposal.version}</span>
          </div>
          {proposal.deal_name && (
            <p className="text-muted-foreground mt-0.5">Deal: {proposal.deal_name}</p>
          )}
        </div>
        <Link href={`/proposals/${id}/submit`}>
          <Button>
            <Send className="h-4 w-4 mr-2" /> Submission Readiness
          </Button>
        </Link>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <FileText className="h-4 w-4" />
              <span className="text-xs">Sections</span>
            </div>
            <div className="text-2xl font-bold">{sections.length}</div>
            <p className="text-xs text-muted-foreground">{approvedCount} approved</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Edit3 className="h-4 w-4" />
              <span className="text-xs">Drafted</span>
            </div>
            <div className="text-2xl font-bold">{draftedCount}</div>
            <p className="text-xs text-muted-foreground">of {sections.length} sections</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <BookOpen className="h-4 w-4" />
              <span className="text-xs">Total Words</span>
            </div>
            <div className="text-2xl font-bold">{totalWords.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">~{Math.ceil(totalWords / 300)} pages</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Shield className="h-4 w-4" />
              <span className="text-xs">Compliance</span>
            </div>
            <div className="text-2xl font-bold">{(proposal.compliance_percentage || 0).toFixed(0)}%</div>
            <p className="text-xs text-muted-foreground">{proposal.compliant_count}/{proposal.total_requirements} reqs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Star className="h-4 w-4" />
              <span className="text-xs">Win Themes</span>
            </div>
            <div className="text-2xl font-bold">{(proposal.win_themes || []).length}</div>
            <p className="text-xs text-muted-foreground">{(proposal.discriminators || []).length} discriminators</p>
          </CardContent>
        </Card>
      </div>

      {/* Progress bar */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm font-medium">{sections.length > 0 ? Math.round((draftedCount / sections.length) * 100) : 0}%</span>
          </div>
          <div className="h-3 w-full rounded-full bg-gray-100 overflow-hidden flex">
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${sections.length > 0 ? (approvedCount / sections.length) * 100 : 0}%` }}
              title={`${approvedCount} approved`}
            />
            <div
              className="h-full bg-blue-400 transition-all"
              style={{ width: `${sections.length > 0 ? ((draftedCount - approvedCount) / sections.length) * 100 : 0}%` }}
              title={`${draftedCount - approvedCount} in progress`}
            />
          </div>
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-green-500" /> Approved ({approvedCount})</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-blue-400" /> In Progress ({draftedCount - approvedCount})</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-gray-200" /> Not Started ({sections.length - draftedCount})</span>
          </div>
        </CardContent>
      </Card>

      {/* Main Tab Navigation */}
      <div className="border-b">
        <div className="flex gap-0">
          {([
            { id: "sections" as MainTab, label: "Proposal Sections", icon: FileText, count: sections.length },
            { id: "diagrams" as MainTab, label: "Diagrams", icon: Layers, count: diagrams.length },
            { id: "solution" as MainTab, label: "Technical Solution", icon: Cpu, count: solutionResult ? Object.keys(solutionResult.technical_solution || {}).filter(k => solutionResult.technical_solution?.[k]).length : 0 },
            { id: "validation" as MainTab, label: "Validation", icon: ShieldCheck, count: validationReport ? 1 : 0 },
          ]).map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setMainTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  mainTab === tab.id
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
                {tab.count > 0 && (
                  <span className="ml-1 text-xs text-muted-foreground">({tab.count})</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content area */}
        <div className="lg:col-span-2 space-y-6">

          {/* ── Sections Tab ── */}
          {mainTab === "sections" && (
            <>
              {Object.keys(byVolume).length === 0 ? (
                <Card>
                  <CardContent className="flex items-center justify-center h-32 text-muted-foreground text-sm">
                    No sections created yet
                  </CardContent>
                </Card>
              ) : (
                Object.entries(byVolume).map(([vol, secs]) => (
                  <Card key={vol}>
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <BookOpen className="h-4 w-4" /> {vol}
                        <span className="text-xs text-muted-foreground font-normal ml-1">
                          ({secs.filter((s) => s.status === "approved").length}/{secs.length} approved)
                        </span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {secs
                        .sort((a, b) => a.order - b.order)
                        .map((s) => (
                          <SectionRow
                            key={s.id}
                            section={s}
                            onSave={handleSaveSection}
                            onStatusChange={handleSectionStatusChange}
                          />
                        ))}
                    </CardContent>
                  </Card>
                ))
              )}
            </>
          )}

          {/* ── Diagrams Tab ── */}
          {mainTab === "diagrams" && (
            <>
              {solutionLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading diagrams...</span>
                </div>
              ) : diagrams.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Layers className="h-10 w-10 mb-3 opacity-40" />
                    <p className="text-sm font-medium">No architecture diagrams available</p>
                    <p className="text-xs mt-1">Run the Solution Architect agent on the linked deal to generate diagrams.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-6">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Layers className="h-4 w-4" />
                    {diagrams.length} architecture diagram{diagrams.length !== 1 ? "s" : ""} from Solution Architect
                  </div>
                  {diagrams.map((d, i) => (
                    <DiagramCard key={i} diagram={d} index={i} />
                  ))}
                </div>
              )}
            </>
          )}

          {/* ── Technical Solution Tab ── */}
          {mainTab === "solution" && (
            <>
              {solutionLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading solution...</span>
                </div>
              ) : !solutionResult?.technical_solution ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Cpu className="h-10 w-10 mb-3 opacity-40" />
                    <p className="text-sm font-medium">No technical solution available</p>
                    <p className="text-xs mt-1">Run the Solution Architect agent on the linked deal to generate the solution.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {solutionResult.selected_frameworks && solutionResult.selected_frameworks.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {solutionResult.selected_frameworks.map((fw, i) => (
                        <span key={i} className="inline-flex items-center rounded-full bg-blue-100 text-blue-700 px-2.5 py-0.5 text-xs font-medium">
                          {fw}
                        </span>
                      ))}
                    </div>
                  )}
                  {Object.entries(solutionResult.technical_solution)
                    .filter(([, v]) => typeof v === "string" && (v as string).trim())
                    .map(([key, value]) => (
                      <Card key={key}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                            <Cpu className="h-4 w-4 text-blue-500" />
                            {key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <MarkdownContent content={value as string} />
                        </CardContent>
                      </Card>
                    ))}

                  {/* Technical Volume sections */}
                  {solutionResult.technical_volume?.sections && Object.keys(solutionResult.technical_volume.sections).length > 0 && (
                    <>
                      <h3 className="text-sm font-semibold text-gray-900 mt-6 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-green-500" />
                        Technical Volume Sections
                        <span className="text-xs font-normal text-muted-foreground">
                          ({Object.keys(solutionResult.technical_volume.sections).length} sections
                          {solutionResult.technical_volume.word_count ? `, ~${solutionResult.technical_volume.word_count} words` : ""})
                        </span>
                      </h3>
                      {Object.entries(solutionResult.technical_volume.sections).map(([title, content]) => (
                        <Card key={title}>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-semibold text-gray-900">{title}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <MarkdownContent content={content} />
                          </CardContent>
                        </Card>
                      ))}
                    </>
                  )}
                </div>
              )}
            </>
          )}

          {/* ── Validation Tab ── */}
          {mainTab === "validation" && (
            <>
              {solutionLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading validation...</span>
                </div>
              ) : !validationReport ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <ShieldCheck className="h-10 w-10 mb-3 opacity-40" />
                    <p className="text-sm font-medium">No validation report available</p>
                    <p className="text-xs mt-1">Run the Solution Architect agent on the linked deal to generate a validation report.</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {/* Overall Score */}
                  <Card>
                    <CardContent className="pt-5">
                      <div className="flex items-center gap-4">
                        <div className={`flex h-16 w-16 items-center justify-center rounded-full ${
                          validationReport.pass !== false ? "bg-green-100" : "bg-red-100"
                        }`}>
                          {validationReport.pass !== false ? (
                            <CheckCircle className="h-8 w-8 text-green-600" />
                          ) : (
                            <AlertTriangle className="h-8 w-8 text-red-600" />
                          )}
                        </div>
                        <div>
                          <p className="text-lg font-bold text-gray-900">
                            {validationReport.verdict || (validationReport.pass !== false ? "PASS" : "NEEDS REVISION")}
                          </p>
                          <p className="text-sm text-gray-600">
                            Quality: <span className="font-medium capitalize">{validationReport.overall_quality}</span>
                            {validationReport.score != null && (
                              <> &middot; Score: <span className="font-medium">{validationReport.score}/100</span></>
                            )}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Issues */}
                  {validationReport.issues && validationReport.issues.length > 0 && (
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-500" />
                          Issues ({validationReport.issues.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {validationReport.issues.map((issue, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-800">
                              <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
                              {issue}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}

                  {/* Compliance Gaps */}
                  {validationReport.compliance_gaps && validationReport.compliance_gaps.length > 0 && (
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                          <Shield className="h-4 w-4 text-red-500" />
                          Compliance Gaps ({validationReport.compliance_gaps.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {validationReport.compliance_gaps.map((gap, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-800">
                              <Shield className="h-3.5 w-3.5 text-red-500 mt-0.5 flex-shrink-0" />
                              {gap}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}

                  {/* Suggestions */}
                  {validationReport.suggestions && validationReport.suggestions.length > 0 && (
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                          <Zap className="h-4 w-4 text-blue-500" />
                          Suggestions ({validationReport.suggestions.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {validationReport.suggestions.map((sug, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-gray-800">
                              <Zap className="h-3.5 w-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                              {sug}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}

                  {/* Review Text */}
                  {validationReport.review_text && (
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold text-gray-900">Full Validation Review</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <MarkdownContent content={validationReport.review_text} />
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Compliance */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4" /> Compliance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ComplianceMeter proposal={proposal} />
            </CardContent>
          </Card>

          {/* Strategy - Win Themes & Discriminators */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Star className="h-4 w-4" /> Strategy
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <EditableList
                title="Win Themes"
                items={proposal.win_themes || []}
                icon={CheckCircle}
                iconColor="text-green-500"
                onSave={handleSaveWinThemes}
              />
              <EditableList
                title="Discriminators"
                items={proposal.discriminators || []}
                icon={Zap}
                iconColor="text-blue-500"
                onSave={handleSaveDiscriminators}
              />
            </CardContent>
          </Card>

          {/* Review Cycles */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="h-4 w-4" /> Review Cycles
              </CardTitle>
            </CardHeader>
            <CardContent>
              {reviews.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-4">
                  No review cycles scheduled
                </div>
              ) : (
                <div className="space-y-3">
                  {reviews.map((r) => (
                    <div key={r.id} className="flex items-start gap-3 p-2 rounded-lg border">
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${REVIEW_TYPE_COLORS[r.review_type]}`}>
                        {r.review_type.charAt(0).toUpperCase() + r.review_type.slice(1)} Team
                      </span>
                      <div className="flex-1 min-w-0">
                        <span className={`px-2 py-0.5 text-xs rounded-full ${REVIEW_STATUS_COLORS[r.status]}`}>
                          {r.status.replace("_", " ")}
                        </span>
                        {r.scheduled_date && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(r.scheduled_date)}
                          </p>
                        )}
                        {r.overall_score != null && (
                          <p className="text-xs font-medium mt-1">Score: {r.overall_score}/100</p>
                        )}
                        {r.summary && (
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{r.summary}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {/* Schedule new review */}
              {(["pink", "red", "gold"] as const).filter((t) => !existingReviewTypes.includes(t)).length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs font-medium text-muted-foreground mb-2">Schedule Review</p>
                  <div className="flex flex-wrap gap-1.5">
                    {(["pink", "red", "gold"] as const)
                      .filter((t) => !existingReviewTypes.includes(t))
                      .map((t) => (
                        <Button
                          key={t}
                          size="sm"
                          variant="outline"
                          className={`text-xs h-7 gap-1 ${REVIEW_TYPE_COLORS[t]}`}
                          onClick={() => handleScheduleReview(t)}
                        >
                          <Plus className="h-3 w-3" />
                          {t.charAt(0).toUpperCase() + t.slice(1)} Team
                        </Button>
                      ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Executive Summary */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Executive Summary</CardTitle>
                {!editingExecSummary ? (
                  <button
                    onClick={() => setEditingExecSummary(true)}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Edit
                  </button>
                ) : (
                  <div className="flex gap-1">
                    <button
                      onClick={handleSaveExecSummary}
                      disabled={savingExecSummary}
                      className="text-xs text-green-600 hover:underline"
                    >
                      {savingExecSummary ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={() => {
                        setExecSummaryDraft(proposal.executive_summary || "");
                        setEditingExecSummary(false);
                      }}
                      className="text-xs text-muted-foreground hover:underline"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {editingExecSummary ? (
                <textarea
                  className="w-full min-h-[150px] text-sm border rounded p-3 resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={execSummaryDraft}
                  onChange={(e) => setExecSummaryDraft(e.target.value)}
                  placeholder="Write the executive summary..."
                />
              ) : proposal.executive_summary ? (
                <div className="prose prose-sm max-w-none prose-p:text-gray-700 prose-p:leading-relaxed prose-strong:text-gray-900 prose-li:text-gray-700">
                  <ReactMarkdown>{proposal.executive_summary}</ReactMarkdown>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-muted-foreground mb-2">No executive summary yet</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingExecSummary(true)}
                    className="gap-1 text-xs"
                  >
                    <PenLine className="h-3 w-3" /> Write Summary
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
