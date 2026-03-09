"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getProposal, getProposalSections, getReviewCycles } from "@/services/proposals";
import { Proposal, ProposalSection, ReviewCycle } from "@/types/proposal";
import {
  Loader2,
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  Shield,
  Star,
  Users,
  Send,
  Package,
} from "lucide-react";

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface CheckItem {
  id: string;
  label: string;
  status: "pass" | "fail" | "warn" | "pending";
  detail?: string;
}

function CheckRow({ item }: { item: CheckItem }) {
  const icon =
    item.status === "pass" ? (
      <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
    ) : item.status === "fail" ? (
      <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
    ) : item.status === "warn" ? (
      <AlertTriangle className="h-5 w-5 text-yellow-500 flex-shrink-0" />
    ) : (
      <Clock className="h-5 w-5 text-gray-400 flex-shrink-0" />
    );

  const bg =
    item.status === "pass"
      ? "bg-green-50"
      : item.status === "fail"
      ? "bg-red-50"
      : item.status === "warn"
      ? "bg-yellow-50"
      : "bg-gray-50";

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg ${bg}`}>
      {icon}
      <div>
        <p className="text-sm font-medium">{item.label}</p>
        {item.detail && <p className="text-xs text-muted-foreground mt-0.5">{item.detail}</p>}
      </div>
    </div>
  );
}

function buildChecklist(
  proposal: Proposal,
  sections: ProposalSection[],
  reviews: ReviewCycle[]
): CheckItem[] {
  const checks: CheckItem[] = [];

  // Status check
  checks.push({
    id: "status",
    label: "Proposal status is Final or later",
    status:
      proposal.status === "final" || proposal.status === "submitted"
        ? "pass"
        : proposal.status === "gold_team"
        ? "warn"
        : "fail",
    detail: `Current status: ${proposal.status.replace("_", " ")}`,
  });

  // All sections approved
  const notApproved = sections.filter((s) => s.status !== "approved");
  checks.push({
    id: "sections",
    label: "All sections approved",
    status:
      sections.length === 0
        ? "pending"
        : notApproved.length === 0
        ? "pass"
        : notApproved.length <= 2
        ? "warn"
        : "fail",
    detail:
      notApproved.length === 0
        ? `All ${sections.length} sections approved`
        : `${notApproved.length} section(s) not yet approved`,
  });

  // Compliance threshold
  const compPct = proposal.compliance_percentage || 0;
  checks.push({
    id: "compliance",
    label: "Compliance matrix ≥ 95%",
    status: compPct >= 95 ? "pass" : compPct >= 85 ? "warn" : "fail",
    detail: `${compPct.toFixed(1)}% compliant (${proposal.compliant_count}/${proposal.total_requirements} requirements)`,
  });

  // Red team review completed
  const redTeam = reviews.find((r) => r.review_type === "red");
  checks.push({
    id: "red_team",
    label: "Red team review completed",
    status:
      redTeam?.status === "completed"
        ? "pass"
        : redTeam?.status === "in_progress"
        ? "warn"
        : "fail",
    detail: redTeam
      ? `Red team ${redTeam.status} — Score: ${redTeam.overall_score ?? "N/A"}`
      : "No red team review scheduled",
  });

  // Gold team review
  const goldTeam = reviews.find((r) => r.review_type === "gold");
  checks.push({
    id: "gold_team",
    label: "Gold team review completed",
    status:
      goldTeam?.status === "completed"
        ? "pass"
        : goldTeam?.status === "in_progress"
        ? "warn"
        : "pending",
    detail: goldTeam
      ? `Gold team ${goldTeam.status}${goldTeam.overall_score != null ? ` — Score: ${goldTeam.overall_score}` : ""}`
      : "No gold team review scheduled",
  });

  // Executive summary
  checks.push({
    id: "exec_summary",
    label: "Executive summary written",
    status: proposal.executive_summary && proposal.executive_summary.length > 50 ? "pass" : "warn",
    detail: proposal.executive_summary
      ? `${proposal.executive_summary.length} characters`
      : "No executive summary",
  });

  // Win themes
  checks.push({
    id: "win_themes",
    label: "Win themes defined",
    status: (proposal.win_themes?.length || 0) >= 3 ? "pass" : (proposal.win_themes?.length || 0) > 0 ? "warn" : "fail",
    detail: `${proposal.win_themes?.length || 0} win theme(s) defined (recommend ≥ 3)`,
  });

  // Not already submitted
  checks.push({
    id: "not_submitted",
    label: "Not already submitted",
    status: proposal.status !== "submitted" ? "pass" : "warn",
    detail: proposal.status === "submitted" ? "Already submitted" : "Ready for first submission",
  });

  return checks;
}

export default function ProposalSubmitPage() {
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
      setError("Failed to load submission readiness data.");
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

  const checks = buildChecklist(proposal, sections, reviews);
  const passed = checks.filter((c) => c.status === "pass").length;
  const failed = checks.filter((c) => c.status === "fail").length;
  const warned = checks.filter((c) => c.status === "warn").length;
  const total = checks.length;
  const readyToSubmit = failed === 0;
  const readinessPct = Math.round((passed / total) * 100);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href={`/proposals/${id}/studio`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" /> Studio
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Submission Readiness</h1>
          <p className="text-muted-foreground mt-0.5">{proposal.title}</p>
        </div>
      </div>

      {/* Readiness Score */}
      <Card className={readyToSubmit ? "border-green-300 bg-green-50" : "border-yellow-300 bg-yellow-50"}>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
            <div className="text-center">
              <div className={`text-5xl font-bold ${readyToSubmit ? "text-green-600" : "text-yellow-600"}`}>
                {readinessPct}%
              </div>
              <div className="text-sm text-muted-foreground mt-1">Ready</div>
            </div>
            <div className="flex-1 w-full">
              <div className="h-3 bg-white rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full rounded-full ${readyToSubmit ? "bg-green-500" : "bg-yellow-500"}`}
                  style={{ width: `${readinessPct}%` }}
                />
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                <span className="flex items-center gap-1 text-green-700">
                  <CheckCircle className="h-4 w-4" /> {passed} passed
                </span>
                {warned > 0 && (
                  <span className="flex items-center gap-1 text-yellow-700">
                    <AlertTriangle className="h-4 w-4" /> {warned} warnings
                  </span>
                )}
                {failed > 0 && (
                  <span className="flex items-center gap-1 text-red-700">
                    <XCircle className="h-4 w-4" /> {failed} failed
                  </span>
                )}
              </div>
            </div>
            <div>
              {readyToSubmit ? (
                <div className="flex items-center gap-2 text-green-700 font-semibold">
                  <CheckCircle className="h-5 w-5" /> Ready for Submission
                </div>
              ) : (
                <div className="flex items-center gap-2 text-red-600 font-semibold">
                  <XCircle className="h-5 w-5" /> {failed} item(s) must be resolved
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Checklist */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-4 w-4" /> Submission Checklist
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {checks.map((c) => (
              <CheckRow key={c.id} item={c} />
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          {/* Proposal Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4" /> Proposal Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Status</span>
                <span className="text-sm font-medium capitalize">
                  {proposal.status.replace("_", " ")}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Version</span>
                <span className="text-sm font-medium">v{proposal.version}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Sections</span>
                <span className="text-sm font-medium">{sections.length} total</span>
              </div>
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Compliance</span>
                <span className="text-sm font-medium">
                  {(proposal.compliance_percentage || 0).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b">
                <span className="text-sm text-muted-foreground">Win Themes</span>
                <span className="text-sm font-medium">{proposal.win_themes?.length || 0}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-sm text-muted-foreground">Last Updated</span>
                <span className="text-sm font-medium">{formatDate(proposal.updated_at)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Review Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="h-4 w-4" /> Review Gate Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {["pink", "red", "gold"].map((type) => {
                const review = reviews.find((r) => r.review_type === type);
                return (
                  <div key={type} className="flex items-center gap-3 py-1.5 border-b last:border-0">
                    <span className="text-sm w-24 capitalize font-medium">{type} Team</span>
                    {review ? (
                      <div className="flex-1 flex items-center gap-2">
                        <span className="text-sm text-muted-foreground capitalize">{review.status}</span>
                        {review.overall_score != null && (
                          <span className="text-sm font-medium">{review.overall_score}/100</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-muted-foreground">Not scheduled</span>
                    )}
                    {review?.status === "completed" ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : review?.status === "in_progress" ? (
                      <Clock className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-gray-300" />
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Action */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Send className="h-4 w-4" /> Submit Proposal
              </CardTitle>
            </CardHeader>
            <CardContent>
              {readyToSubmit ? (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    All required checks passed. Proceeding will lock the proposal and create a submission record.
                  </p>
                  <Button className="w-full bg-green-600 hover:bg-green-700">
                    <Send className="h-4 w-4 mr-2" /> Submit Proposal
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    Resolve {failed} blocking issue(s) before submission.
                  </p>
                  <Button disabled className="w-full">
                    <Send className="h-4 w-4 mr-2" /> Submit Proposal
                  </Button>
                  <Link href={`/proposals/${id}/studio`}>
                    <Button variant="outline" className="w-full">
                      <FileText className="h-4 w-4 mr-2" /> Return to Studio
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
