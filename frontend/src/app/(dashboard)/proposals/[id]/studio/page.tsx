"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getProposal,
  getProposalSections,
  getReviewCycles,
  updateProposal,
} from "@/services/proposals";
import { Proposal, ProposalSection, ReviewCycle } from "@/types/proposal";
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
function SectionRow({ section }: { section: ProposalSection }) {
  const [expanded, setExpanded] = useState(false);
  const hasContent = section.final_content || section.human_content || section.ai_draft;

  return (
    <div className="border rounded-lg overflow-hidden">
      <div
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <button className="text-muted-foreground flex-shrink-0">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <span className="font-mono text-xs text-muted-foreground w-10">{section.section_number}</span>
        <span className="flex-1 text-sm font-medium">{section.title}</span>
        <span className={`px-2 py-0.5 text-xs rounded-full ${SECTION_STATUS_COLORS[section.status]}`}>
          {SECTION_STATUS_LABELS[section.status]}
        </span>
        {section.page_limit && (
          <span className="hidden sm:inline text-xs text-muted-foreground">{section.word_count}w / {section.page_limit}pg</span>
        )}
        {section.assigned_to && (
          <span className="hidden md:flex text-xs text-muted-foreground items-center gap-1">
            <Users className="h-3 w-3" />
            Assigned
          </span>
        )}
      </div>
      {expanded && (
        <div className="border-t bg-gray-50 p-4">
          {hasContent ? (
            <div className="space-y-3">
              {(section.final_content || section.human_content) && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wide">
                    {section.final_content ? "Final Content" : "Human Draft"}
                  </p>
                  <p className="text-sm whitespace-pre-wrap line-clamp-6">
                    {section.final_content || section.human_content}
                  </p>
                </div>
              )}
              {section.ai_draft && !section.final_content && !section.human_content && (
                <div>
                  <p className="text-xs font-semibold text-blue-600 mb-1 uppercase tracking-wide flex items-center gap-1">
                    <Zap className="h-3 w-3" /> AI Draft
                  </p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap line-clamp-6">
                    {section.ai_draft}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Edit3 className="h-4 w-4" />
              No content yet — trigger AI draft or add manually
            </div>
          )}
        </div>
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

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = await getProposal(id);
      setProposal(p);
      const [sRes, rRes] = await Promise.all([
        getProposalSections(id),
        getReviewCycles(id),
      ]);
      setSections(sRes.results);
      setReviews(rRes.results);
    } catch {
      setError("Failed to load proposal studio.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

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
            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${STATUS_COLORS[proposal.status]}`}>
              {STATUS_LABELS[proposal.status]}
            </span>
            <span className="text-xs text-muted-foreground">v{proposal.version}</span>
          </div>
          {proposal.deal_name && (
            <p className="text-muted-foreground mt-0.5">Deal: {proposal.deal_name}</p>
          )}
        </div>
        <Link href={`/proposals/${id}/submit`}>
          <Button className="hidden sm:inline-flex">
            <CheckCircle className="h-4 w-4 mr-2" /> Submission Readiness
          </Button>
          <Button size="sm" className="sm:hidden">
            <CheckCircle className="h-4 w-4" />
          </Button>
        </Link>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Sections by Volume */}
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
                      <SectionRow key={s.id} section={s} />
                    ))}
                </CardContent>
              </Card>
            ))
          )}
        </div>

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

          {/* Win Themes */}
          {(proposal.win_themes?.length > 0 || proposal.discriminators?.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Star className="h-4 w-4" /> Strategy
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {proposal.win_themes?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                      Win Themes
                    </p>
                    <ul className="space-y-1">
                      {proposal.win_themes.map((t, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle className="h-3.5 w-3.5 text-green-500 mt-0.5 flex-shrink-0" />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {proposal.discriminators?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                      Discriminators
                    </p>
                    <ul className="space-y-1">
                      {proposal.discriminators.map((d, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Zap className="h-3.5 w-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                          {d}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

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
                          {r.status}
                        </span>
                        {r.scheduled_date && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDate(r.scheduled_date)}
                          </p>
                        )}
                        {r.overall_score != null && (
                          <p className="text-xs font-medium mt-1">Score: {r.overall_score}/100</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Executive Summary */}
          {proposal.executive_summary && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Executive Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground line-clamp-8">
                  {proposal.executive_summary}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
