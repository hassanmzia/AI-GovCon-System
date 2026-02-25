"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getResearchProjects,
  getResearchProject,
  createResearchProject,
  getCompetitorProfiles,
  getMarketIntelligence,
} from "@/services/research";
import { getDeals } from "@/services/deals";
import {
  ResearchProject,
  CompetitorProfile,
  MarketIntelligence,
  ResearchType,
  ResearchStatus,
  CreateResearchProjectPayload,
} from "@/types/research";
import { Deal } from "@/types/deal";
import {
  Search,
  Loader2,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Users,
  BarChart2,
  FileSearch,
} from "lucide-react";

// ─── constants ──────────────────────────────────────────────────────────────

const RESEARCH_TYPE_LABELS: Record<ResearchType, string> = {
  market_analysis: "Market Analysis",
  competitive_intel: "Competitive Intelligence",
  agency_analysis: "Agency Analysis",
  technology_trends: "Technology Trends",
  incumbent_analysis: "Incumbent Analysis",
  regulatory_landscape: "Regulatory Landscape",
};

const RESEARCH_TYPE_COLORS: Record<ResearchType, string> = {
  market_analysis: "bg-blue-100 text-blue-800",
  competitive_intel: "bg-purple-100 text-purple-800",
  agency_analysis: "bg-indigo-100 text-indigo-800",
  technology_trends: "bg-cyan-100 text-cyan-800",
  incumbent_analysis: "bg-orange-100 text-orange-800",
  regulatory_landscape: "bg-rose-100 text-rose-800",
};

const STATUS_CONFIGS: Record<
  ResearchStatus,
  { label: string; cls: string; pulse?: boolean }
> = {
  pending: { label: "Pending", cls: "bg-gray-100 text-gray-700" },
  running: {
    label: "Running",
    cls: "bg-blue-100 text-blue-700",
    pulse: true,
  },
  completed: { label: "Completed", cls: "bg-green-100 text-green-700" },
  failed: { label: "Failed", cls: "bg-red-100 text-red-700" },
};

// ─── helper components ──────────────────────────────────────────────────────

function ResearchTypeBadge({ type }: { type: ResearchType }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        RESEARCH_TYPE_COLORS[type] ?? "bg-gray-100 text-gray-700"
      }`}
    >
      {RESEARCH_TYPE_LABELS[type] ?? type}
    </span>
  );
}

function StatusBadge({ status }: { status: ResearchStatus }) {
  const cfg = STATUS_CONFIGS[status] ?? {
    label: status,
    cls: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cfg.cls} ${
        cfg.pulse ? "animate-pulse" : ""
      }`}
    >
      {cfg.label}
    </span>
  );
}

function Chip({
  label,
  color,
}: {
  label: string;
  color: string;
}) {
  return (
    <span
      className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${color}`}
    >
      {label}
    </span>
  );
}

const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const truncate = (str: string, maxLen: number): string => {
  if (!str) return "--";
  return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
};

// ─── new research modal ─────────────────────────────────────────────────────

function NewResearchModal({
  deals,
  onClose,
  onCreated,
}: {
  deals: Deal[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [researchType, setResearchType] = useState<ResearchType>("market_analysis");
  const [query, setQuery] = useState("");
  const [dealId, setDealId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setFormError("Title is required.");
      return;
    }
    if (!dealId) {
      setFormError("Please select a deal.");
      return;
    }
    setFormError(null);
    setSubmitting(true);
    try {
      const payload: CreateResearchProjectPayload = {
        title: title.trim(),
        research_type: researchType,
        deal: dealId,
        description: query.trim(),
      };
      await createResearchProject(payload);
      onCreated();
      onClose();
    } catch (err) {
      console.error("Error creating research project:", err);
      setFormError("Failed to create research project. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-background rounded-xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">New Research Project</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {formError && (
            <p className="text-sm text-red-600 rounded-md bg-red-50 px-3 py-2">
              {formError}
            </p>
          )}

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Title</label>
            <Input
              placeholder="e.g. DoD Cloud Market Analysis Q2 2026"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Research Type</label>
            <select
              value={researchType}
              onChange={(e) => setResearchType(e.target.value as ResearchType)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              {(Object.keys(RESEARCH_TYPE_LABELS) as ResearchType[]).map(
                (rt) => (
                  <option key={rt} value={rt}>
                    {RESEARCH_TYPE_LABELS[rt]}
                  </option>
                )
              )}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Deal</label>
            <select
              value={dealId}
              onChange={(e) => setDealId(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">Select a deal...</option>
              {deals.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Research Query{" "}
              <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <textarea
              placeholder="Describe the specific question or area to investigate..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create Project
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── project expanded panel ─────────────────────────────────────────────────

function ProjectExpandedPanel({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<ResearchProject | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getResearchProject(projectId)
      .then(setProject)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4 px-4 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading findings...
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="px-4 pb-4 space-y-4 border-t bg-muted/20">
      {/* Executive Summary */}
      {project.executive_summary && (
        <div className="pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1.5">
            Executive Summary
          </p>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {project.executive_summary}
          </p>
        </div>
      )}

      {/* Sources */}
      {project.sources && project.sources.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Sources ({project.sources.length})
          </p>
          <div className="space-y-2">
            {project.sources.map((src, idx) => (
              <div
                key={idx}
                className="rounded-md border bg-background p-3 text-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="font-medium line-clamp-1">{src.title}</p>
                    {src.snippet && (
                      <p className="text-muted-foreground text-xs mt-1 line-clamp-2">
                        {src.snippet}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {src.relevance_score != null && (
                      <span className="text-xs text-muted-foreground">
                        {(src.relevance_score * 100).toFixed(0)}% relevant
                      </span>
                    )}
                    {src.url && (
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!project.executive_summary &&
        (!project.sources || project.sources.length === 0) && (
          <p className="text-sm text-muted-foreground py-2">
            No findings available yet.
          </p>
        )}
    </div>
  );
}

// ─── competitor card ─────────────────────────────────────────────────────────

function CompetitorCard({ competitor }: { competitor: CompetitorProfile }) {
  const growthTrend = competitor.win_rate;
  return (
    <Card>
      <CardContent className="pt-4 pb-4 space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-semibold">{competitor.name}</p>
            {competitor.revenue_range && (
              <p className="text-xs text-muted-foreground">
                Revenue: {competitor.revenue_range}
              </p>
            )}
          </div>
          {growthTrend != null && (
            <div className="text-right">
              <p className="text-sm font-bold text-blue-700">
                {(growthTrend * 100).toFixed(0)}%
              </p>
              <p className="text-xs text-muted-foreground">Win Rate</p>
            </div>
          )}
        </div>

        {competitor.strengths.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-green-700 mb-1">
              Strengths
            </p>
            <div className="flex flex-wrap gap-1">
              {competitor.strengths.slice(0, 4).map((s, i) => (
                <Chip key={i} label={s} color="bg-green-50 text-green-700" />
              ))}
            </div>
          </div>
        )}

        {competitor.weaknesses.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-red-700 mb-1">Weaknesses</p>
            <div className="flex flex-wrap gap-1">
              {competitor.weaknesses.slice(0, 4).map((w, i) => (
                <Chip key={i} label={w} color="bg-red-50 text-red-700" />
              ))}
            </div>
          </div>
        )}

        {competitor.past_performance_summary && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {competitor.past_performance_summary}
          </p>
        )}

        {competitor.naics_codes.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {competitor.naics_codes.slice(0, 5).map((code, i) => (
              <Chip
                key={i}
                label={code}
                color="bg-gray-100 text-gray-600"
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── market intel card ──────────────────────────────────────────────────────

const INTEL_CATEGORY_COLORS: Record<string, string> = {
  budget_trends: "bg-blue-100 text-blue-800",
  policy_changes: "bg-yellow-100 text-yellow-800",
  technology_shifts: "bg-cyan-100 text-cyan-800",
  procurement_patterns: "bg-purple-100 text-purple-800",
  workforce_trends: "bg-orange-100 text-orange-800",
};

const INTEL_CATEGORY_LABELS: Record<string, string> = {
  budget_trends: "Budget Trends",
  policy_changes: "Policy Changes",
  technology_shifts: "Technology Shifts",
  procurement_patterns: "Procurement Patterns",
  workforce_trends: "Workforce Trends",
};

function MarketIntelCard({ intel }: { intel: MarketIntelligence }) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <p className="font-medium text-sm">{intel.title}</p>
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium shrink-0 ${
              INTEL_CATEGORY_COLORS[intel.category] ??
              "bg-gray-100 text-gray-700"
            }`}
          >
            {INTEL_CATEGORY_LABELS[intel.category] ?? intel.category}
          </span>
        </div>

        <p className="text-sm text-muted-foreground line-clamp-3">
          {intel.summary}
        </p>

        {intel.impact_assessment && (
          <p className="text-xs italic text-muted-foreground line-clamp-2">
            Impact: {intel.impact_assessment}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
          <div className="flex flex-wrap gap-1">
            {intel.affected_agencies.slice(0, 3).map((a, i) => (
              <Chip key={i} label={a} color="bg-gray-100 text-gray-600" />
            ))}
          </div>
          {intel.published_date && (
            <span>{formatDate(intel.published_date)}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── tabs ────────────────────────────────────────────────────────────────────

type Tab = "projects" | "competitors" | "market";

// ─── main page ──────────────────────────────────────────────────────────────

export default function ResearchPage() {
  const [activeTab, setActiveTab] = useState<Tab>("projects");
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [marketIntel, setMarketIntel] = useState<MarketIntelligence[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedProjectId, setExpandedProjectId] = useState<string | null>(null);
  const [showNewModal, setShowNewModal] = useState(false);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (typeFilter) params.research_type = typeFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await getResearchProjects(params);
      setProjects(data.results ?? []);
    } catch (err) {
      setError("Failed to load research projects.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search, typeFilter, statusFilter]);

  const fetchTabData = useCallback(async () => {
    if (activeTab === "competitors" && competitors.length === 0) {
      try {
        const data = await getCompetitorProfiles();
        setCompetitors(data.results ?? []);
      } catch (err) {
        console.error("Error fetching competitors:", err);
      }
    }
    if (activeTab === "market" && marketIntel.length === 0) {
      try {
        const data = await getMarketIntelligence();
        setMarketIntel(data.results ?? []);
      } catch (err) {
        console.error("Error fetching market intel:", err);
      }
    }
  }, [activeTab, competitors.length, marketIntel.length]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    fetchTabData();
  }, [fetchTabData]);

  // Pre-fetch deals for modal
  useEffect(() => {
    getDeals()
      .then((d) => setDeals(d.results ?? []))
      .catch(console.error);
  }, []);

  const toggleExpand = (id: string) => {
    setExpandedProjectId((prev) => (prev === id ? null : id));
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    {
      id: "projects",
      label: "Research Projects",
      icon: <FileSearch className="h-4 w-4" />,
    },
    {
      id: "competitors",
      label: "Competitor Profiles",
      icon: <Users className="h-4 w-4" />,
    },
    {
      id: "market",
      label: "Market Intelligence",
      icon: <BarChart2 className="h-4 w-4" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Deep Research</h1>
          <p className="text-muted-foreground">
            AI-powered market intelligence and competitive analysis
          </p>
        </div>
        <Button onClick={() => setShowNewModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Research Project
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Projects Tab ────────────────────────────────────────────────── */}
      {activeTab === "projects" && (
        <>
          {/* Filter bar */}
          <Card>
            <CardContent className="pt-5">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search projects..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
                >
                  <option value="">All Types</option>
                  {(Object.keys(RESEARCH_TYPE_LABELS) as ResearchType[]).map(
                    (rt) => (
                      <option key={rt} value={rt}>
                        {RESEARCH_TYPE_LABELS[rt]}
                      </option>
                    )
                  )}
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
                >
                  <option value="">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="running">Running</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Projects list */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Research Projects
                {!loading && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({projects.length} results)
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="ml-3 text-muted-foreground">
                    Loading research projects...
                  </span>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <p className="text-red-600 mb-4">{error}</p>
                  <Button variant="outline" onClick={fetchProjects}>
                    Retry
                  </Button>
                </div>
              ) : projects.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <FileSearch className="h-10 w-10 text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">
                    No research projects found.
                  </p>
                </div>
              ) : (
                <div className="divide-y">
                  {projects.map((project) => (
                    <div key={project.id} className="group">
                      {/* Row */}
                      <button
                        onClick={() => toggleExpand(project.id)}
                        className="w-full text-left px-5 py-4 hover:bg-muted/40 transition-colors flex items-start gap-4"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <span className="font-medium text-sm">
                              {project.title}
                            </span>
                            <ResearchTypeBadge type={project.research_type} />
                            <StatusBadge status={project.status} />
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                            {project.deal_title && (
                              <span>Deal: {project.deal_title}</span>
                            )}
                            {project.sources && (
                              <span>{project.sources.length} sources</span>
                            )}
                            <span>Created {formatDate(project.created_at)}</span>
                          </div>
                          {project.executive_summary && (
                            <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">
                              {truncate(project.executive_summary, 160)}
                            </p>
                          )}
                        </div>
                        <div className="shrink-0 text-muted-foreground">
                          {expandedProjectId === project.id ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </div>
                      </button>

                      {/* Expanded panel */}
                      {expandedProjectId === project.id && (
                        <ProjectExpandedPanel projectId={project.id} />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* ── Competitors Tab ─────────────────────────────────────────────── */}
      {activeTab === "competitors" && (
        <>
          {competitors.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Users className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">
                  No competitor profiles available.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {competitors.map((c) => (
                <CompetitorCard key={c.id} competitor={c} />
              ))}
            </div>
          )}
        </>
      )}

      {/* ── Market Intelligence Tab ─────────────────────────────────────── */}
      {activeTab === "market" && (
        <>
          {marketIntel.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <BarChart2 className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">
                  No market intelligence available.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {marketIntel.map((intel) => (
                <MarketIntelCard key={intel.id} intel={intel} />
              ))}
            </div>
          )}
        </>
      )}

      {/* New Research Modal */}
      {showNewModal && (
        <NewResearchModal
          deals={deals}
          onClose={() => setShowNewModal(false)}
          onCreated={fetchProjects}
        />
      )}
    </div>
  );
}
