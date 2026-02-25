"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getProposals, getProposalSections, createProposal } from "@/services/proposals";
import { Proposal, ProposalSection, ProposalStatus } from "@/types/proposal";
import { fetchAllDeals } from "@/services/analytics";
import { Deal } from "@/types/deal";
import {
  Search,
  Loader2,
  Plus,
  ChevronDown,
  ChevronRight,
  FileText,
  X,
} from "lucide-react";

const STATUS_LABELS: Record<ProposalStatus, string> = {
  draft: "Draft",
  pink_team: "Pink Team",
  red_team: "Red Team",
  gold_team: "Gold Team",
  final: "Final",
  submitted: "Submitted",
};

const STATUS_CLASSES: Record<ProposalStatus, string> = {
  draft: "bg-gray-100 text-gray-700",
  pink_team: "bg-pink-100 text-pink-700",
  red_team: "bg-red-100 text-red-700",
  gold_team: "bg-yellow-100 text-yellow-700",
  final: "bg-blue-100 text-blue-700",
  submitted: "bg-green-100 text-green-700",
};

const SECTION_STATUS_CLASSES: Record<string, string> = {
  not_started: "bg-gray-100 text-gray-600",
  ai_drafted: "bg-purple-100 text-purple-700",
  in_review: "bg-yellow-100 text-yellow-700",
  revised: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
};

const SECTION_STATUS_LABELS: Record<string, string> = {
  not_started: "Not Started",
  ai_drafted: "AI Drafted",
  in_review: "In Review",
  revised: "Revised",
  approved: "Approved",
};

function StatusBadge({ status }: { status: ProposalStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_CLASSES[status] || "bg-gray-100 text-gray-700"}`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function SectionStatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SECTION_STATUS_CLASSES[status] || "bg-gray-100 text-gray-600"}`}
    >
      {SECTION_STATUS_LABELS[status] || status}
    </span>
  );
}

function ComplianceMeter({ percentage }: { percentage: number }) {
  const pct = Math.min(100, Math.max(0, percentage));
  const color =
    pct >= 80
      ? "bg-green-500"
      : pct >= 50
        ? "bg-yellow-500"
        : "bg-red-500";
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs tabular-nums text-muted-foreground w-8 text-right">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

interface ProposalDetailPanelProps {
  proposal: Proposal;
  onClose: () => void;
}

function ProposalDetailPanel({ proposal, onClose }: ProposalDetailPanelProps) {
  const [sections, setSections] = useState<ProposalSection[]>([]);
  const [loadingSections, setLoadingSections] = useState(true);
  const [sectionsError, setSectionsError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSections = async () => {
      setLoadingSections(true);
      setSectionsError(null);
      try {
        const data = await getProposalSections(proposal.id);
        setSections(data.results || []);
      } catch {
        setSectionsError("Failed to load sections.");
      } finally {
        setLoadingSections(false);
      }
    };
    fetchSections();
  }, [proposal.id]);

  // Group sections by volume
  const sectionsByVolume = sections.reduce<Record<string, ProposalSection[]>>(
    (acc, sec) => {
      const vol = sec.volume || "General";
      if (!acc[vol]) acc[vol] = [];
      acc[vol].push(sec);
      return acc;
    },
    {}
  );

  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base font-semibold truncate">
              {proposal.title}
            </CardTitle>
            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <StatusBadge status={proposal.status} />
              <span className="text-xs text-muted-foreground">
                v{proposal.version}
              </span>
              <ComplianceMeter percentage={proposal.compliance_percentage} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="ml-3 rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close panel"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Executive Summary */}
        {proposal.executive_summary ? (
          <div>
            <h4 className="text-sm font-semibold mb-1.5">Executive Summary</h4>
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {proposal.executive_summary}
            </p>
          </div>
        ) : (
          <div>
            <h4 className="text-sm font-semibold mb-1.5">Executive Summary</h4>
            <p className="text-sm text-muted-foreground italic">
              No executive summary yet.
            </p>
          </div>
        )}

        {/* Win Themes */}
        {proposal.win_themes && proposal.win_themes.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold mb-1.5">
              Win Themes ({proposal.win_themes.length})
            </h4>
            <ul className="space-y-1">
              {proposal.win_themes.map((theme, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary flex-shrink-0" />
                  <span className="text-muted-foreground">{theme}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Discriminators */}
        {proposal.discriminators && proposal.discriminators.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold mb-1.5">
              Discriminators ({proposal.discriminators.length})
            </h4>
            <ul className="space-y-1">
              {proposal.discriminators.map((disc, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" />
                  <span className="text-muted-foreground">{disc}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Proposal Sections */}
        <div>
          <h4 className="text-sm font-semibold mb-2">
            Proposal Sections
            {!loadingSections && sections.length > 0 && (
              <span className="ml-1 font-normal text-muted-foreground">
                ({sections.length})
              </span>
            )}
          </h4>
          {loadingSections ? (
            <div className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading sections...
            </div>
          ) : sectionsError ? (
            <p className="text-sm text-red-600">{sectionsError}</p>
          ) : sections.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">
              No sections created yet.
            </p>
          ) : (
            <div className="space-y-3">
              {Object.entries(sectionsByVolume).map(([volume, vSections]) => (
                <div key={volume}>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                    {volume}
                  </p>
                  <div className="space-y-1">
                    {vSections.map((sec) => (
                      <div
                        key={sec.id}
                        className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="font-mono text-xs text-muted-foreground flex-shrink-0">
                            {sec.section_number}
                          </span>
                          <span className="truncate">{sec.title}</span>
                        </div>
                        <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                          {sec.word_count > 0 && (
                            <span className="text-xs text-muted-foreground">
                              {sec.word_count.toLocaleString()}w
                            </span>
                          )}
                          <SectionStatusBadge status={sec.status} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ── New Proposal Modal ────────────────────────────────────────────────────

interface NewProposalModalProps {
  onClose: () => void;
  onCreated: (proposal: Proposal) => void;
}

function NewProposalModal({ onClose, onCreated }: NewProposalModalProps) {
  const [title, setTitle] = useState("");
  const [dealId, setDealId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllDeals()
      .then((d) => setDeals(d))
      .catch(() => {})
      .finally(() => setDealsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !dealId) {
      setError("Title and deal are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const proposal = await createProposal({ title: title.trim(), deal: dealId });
      onCreated(proposal);
    } catch {
      setError("Failed to create proposal. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">New Proposal</h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Proposal Title <span className="text-red-500">*</span>
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Technical Proposal – OASIS+ SB"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">
              Deal <span className="text-red-500">*</span>
            </label>
            {dealsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading deals...
              </div>
            ) : (
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
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || dealsLoading}>
              {submitting ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</>
              ) : (
                "Create Proposal"
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(
    null
  );
  const [showNewModal, setShowNewModal] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const fetchProposals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;

      const data = await getProposals(params);
      setProposals(data.results || []);
    } catch {
      setError("Failed to load proposals. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  const handleRowClick = (proposal: Proposal) => {
    setSelectedProposal((prev) =>
      prev?.id === proposal.id ? null : proposal
    );
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const truncate = (str: string, maxLen: number) => {
    if (!str) return "--";
    return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
  };

  const allStatuses: ProposalStatus[] = [
    "draft",
    "pink_team",
    "red_team",
    "gold_team",
    "final",
    "submitted",
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Proposals</h1>
          <p className="text-muted-foreground">
            Manage and track all proposal documents and review cycles
          </p>
        </div>
        <Button onClick={() => setShowNewModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Proposal
        </Button>
      </div>

      {showNewModal && (
        <NewProposalModal
          onClose={() => setShowNewModal(false)}
          onCreated={(proposal) => {
            setProposals((prev) => [proposal, ...prev]);
            setShowNewModal(false);
          }}
        />
      )}

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search proposals..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Statuses</option>
              {allStatuses.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Main content: table + optional detail panel */}
      <div
        className={`grid gap-6 ${selectedProposal ? "lg:grid-cols-[1fr_400px]" : "grid-cols-1"}`}
      >
        {/* Proposals Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Proposals
              {!loading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({proposals.length} results)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-3 text-muted-foreground">
                  Loading proposals...
                </span>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-12">
                <p className="text-red-600 mb-4">{error}</p>
                <Button variant="outline" onClick={fetchProposals}>
                  Retry
                </Button>
              </div>
            ) : proposals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mb-3 opacity-50" />
                <p className="text-muted-foreground font-medium">
                  No proposals found
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {search || statusFilter
                    ? "Try adjusting your filters."
                    : "Create your first proposal to get started."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Title
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Deal
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Version
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Status
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Compliance
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Win Themes
                      </th>
                      <th className="pb-3 font-medium text-muted-foreground">
                        Last Updated
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {proposals.map((proposal) => {
                      const isSelected = selectedProposal?.id === proposal.id;
                      return (
                        <tr
                          key={proposal.id}
                          onClick={() => handleRowClick(proposal)}
                          className={`border-b cursor-pointer transition-colors hover:bg-muted/50 ${
                            isSelected ? "bg-muted/70" : ""
                          }`}
                        >
                          <td className="py-3 pr-4">
                            <div className="flex items-center gap-1.5">
                              {isSelected ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              )}
                              <span className="font-medium">
                                {truncate(proposal.title, 45)}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 pr-4">
                            {proposal.deal_name ? (
                              <span className="text-primary hover:underline cursor-pointer">
                                {truncate(proposal.deal_name, 30)}
                              </span>
                            ) : (
                              <span className="text-muted-foreground text-xs">
                                {proposal.deal
                                  ? truncate(proposal.deal, 20)
                                  : "--"}
                              </span>
                            )}
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground">
                            v{proposal.version}
                          </td>
                          <td className="py-3 pr-4">
                            <StatusBadge status={proposal.status} />
                          </td>
                          <td className="py-3 pr-4">
                            <ComplianceMeter
                              percentage={proposal.compliance_percentage}
                            />
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground">
                            {proposal.win_themes?.length ?? 0}
                          </td>
                          <td className="py-3 text-muted-foreground">
                            {formatDate(proposal.updated_at)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detail Panel */}
        {selectedProposal && (
          <ProposalDetailPanel
            proposal={selectedProposal}
            onClose={() => setSelectedProposal(null)}
          />
        )}
      </div>
    </div>
  );
}
