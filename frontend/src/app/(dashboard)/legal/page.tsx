"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getFARClauses,
  getComplianceAssessments,
  getLegalRisks,
  getContractReviewNotes,
} from "@/services/legal";
import {
  FARClause,
  ComplianceAssessment,
  LegalRisk,
  ContractReviewNote,
} from "@/types/legal";
import {
  Search,
  Loader2,
  AlertTriangle,
  ShieldCheck,
  FileText,
  Scale,
  RefreshCw,
} from "lucide-react";

type TabId = "risks" | "far_clauses" | "assessments" | "contract_reviews";

// ---------- Helpers ----------

function truncate(str: string | undefined | null, maxLen: number): string {
  if (!str) return "--";
  return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getDealName(
  deal: string | { id: string; name: string; title?: string } | undefined
): string {
  if (!deal) return "--";
  if (typeof deal === "string") return deal;
  return deal.name || deal.title || "--";
}

// ---------- Severity / Status Badge ----------

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: "bg-red-100 text-red-800 border border-red-200",
    high: "bg-orange-100 text-orange-800 border border-orange-200",
    medium: "bg-yellow-100 text-yellow-800 border border-yellow-200",
    low: "bg-blue-100 text-blue-800 border border-blue-200",
  };
  const labels: Record<string, string> = {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
  };
  const cls = colors[severity] ?? "bg-gray-100 text-gray-700 border border-gray-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {labels[severity] ?? severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    identified: "bg-gray-100 text-gray-700",
    mitigating: "bg-blue-100 text-blue-800",
    mitigated: "bg-green-100 text-green-800",
    accepted: "bg-purple-100 text-purple-800",
    resolved: "bg-green-100 text-green-800",
    compliant: "bg-green-100 text-green-800",
    non_compliant: "bg-red-100 text-red-800",
    partial: "bg-yellow-100 text-yellow-800",
    not_assessed: "bg-gray-100 text-gray-700",
    pending: "bg-yellow-100 text-yellow-800",
    in_progress: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
  };
  const labels: Record<string, string> = {
    identified: "Identified",
    mitigating: "Mitigating",
    mitigated: "Mitigated",
    accepted: "Accepted",
    resolved: "Resolved",
    compliant: "Compliant",
    non_compliant: "Non-Compliant",
    partial: "Partial",
    not_assessed: "Not Assessed",
    pending: "Pending",
    in_progress: "In Progress",
    completed: "Completed",
  };
  const cls = colors[status] ?? "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {labels[status] ?? status}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  const isDFARS =
    source?.toLowerCase().includes("dfars") ||
    source === "DFARS";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        isDFARS
          ? "bg-purple-100 text-purple-800 border border-purple-200"
          : "bg-blue-100 text-blue-800 border border-blue-200"
      }`}
    >
      {isDFARS ? "DFARS" : "FAR"}
    </span>
  );
}

function NoteTypeBadge({ noteType }: { noteType: string }) {
  const colors: Record<string, string> = {
    concern: "bg-red-100 text-red-800",
    suggestion: "bg-blue-100 text-blue-800",
    approval: "bg-green-100 text-green-800",
    question: "bg-yellow-100 text-yellow-800",
  };
  const cls = colors[noteType] ?? "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {noteType.charAt(0).toUpperCase() + noteType.slice(1)}
    </span>
  );
}

// ---------- KPI Summary ----------

function RiskKPIs({ risks }: { risks: LegalRisk[] }) {
  const total = risks.length;
  const criticalHigh = risks.filter(
    (r) => r.severity === "critical" || r.severity === "high"
  ).length;
  const mitigating = risks.filter((r) => r.status === "mitigating").length;
  const resolved = risks.filter(
    (r) => r.status === "resolved" || r.status === "mitigated"
  ).length;

  const kpis = [
    {
      label: "Total Risks",
      value: total,
      icon: <AlertTriangle className="h-5 w-5 text-muted-foreground" />,
    },
    {
      label: "Critical / High",
      value: criticalHigh,
      icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
      highlight: criticalHigh > 0,
    },
    {
      label: "Mitigating",
      value: mitigating,
      icon: <ShieldCheck className="h-5 w-5 text-blue-500" />,
    },
    {
      label: "Resolved",
      value: resolved,
      icon: <ShieldCheck className="h-5 w-5 text-green-500" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{kpi.label}</p>
                <p
                  className={`text-2xl font-bold mt-1 ${
                    kpi.highlight ? "text-red-600" : ""
                  }`}
                >
                  {kpi.value}
                </p>
              </div>
              {kpi.icon}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ---------- Legal Risks Tab ----------

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

function LegalRisksTab({ risks, loading }: { risks: LegalRisk[]; loading: boolean }) {
  const sorted = [...risks].sort(
    (a, b) =>
      (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading legal risks...</span>
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <ShieldCheck className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No legal risks found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Deal</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Risk Type</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Description</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Severity</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Probability</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Status</th>
            <th className="pb-3 font-medium text-muted-foreground">Mitigation</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((risk) => (
            <tr
              key={risk.id}
              className="border-b transition-colors hover:bg-muted/50"
            >
              <td className="py-3 pr-4 font-medium">
                {getDealName(risk.deal) !== "--"
                  ? getDealName(risk.deal)
                  : risk.deal_name ?? "--"}
              </td>
              <td className="py-3 pr-4 text-muted-foreground capitalize">
                {risk.risk_type?.replace(/_/g, " ") ?? "--"}
              </td>
              <td className="py-3 pr-4 max-w-xs text-muted-foreground">
                {truncate(risk.description, 80)}
              </td>
              <td className="py-3 pr-4">
                <SeverityBadge severity={risk.severity} />
              </td>
              <td className="py-3 pr-4 text-muted-foreground capitalize">
                {risk.probability ?? "--"}
              </td>
              <td className="py-3 pr-4">
                <StatusBadge status={risk.status} />
              </td>
              <td className="py-3 max-w-xs text-muted-foreground">
                {truncate(risk.mitigation_strategy, 60)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------- FAR Clauses Tab ----------

function FARClausesTab({
  clauses,
  loading,
}: {
  clauses: FARClause[];
  loading: boolean;
}) {
  const [search, setSearch] = useState("");

  const filtered = clauses.filter((c) => {
    const q = search.toLowerCase();
    return (
      c.clause_number?.toLowerCase().includes(q) ||
      c.title?.toLowerCase().includes(q) ||
      c.applicability?.toLowerCase().includes(q) ||
      c.source?.toLowerCase().includes(q)
    );
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading FAR clauses...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search clauses..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mb-3" />
          <p className="text-muted-foreground">
            {search ? "No clauses match your search." : "No FAR clauses found."}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="pb-3 pr-4 font-medium text-muted-foreground">
                  Clause #
                </th>
                <th className="pb-3 pr-4 font-medium text-muted-foreground">
                  Title
                </th>
                <th className="pb-3 pr-4 font-medium text-muted-foreground">
                  Source
                </th>
                <th className="pb-3 pr-4 font-medium text-muted-foreground">
                  Mandatory
                </th>
                <th className="pb-3 font-medium text-muted-foreground">
                  Applicability
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((clause) => (
                <tr
                  key={clause.id}
                  className="border-b transition-colors hover:bg-muted/50"
                >
                  <td className="py-3 pr-4 font-mono font-medium text-sm">
                    {clause.clause_number}
                  </td>
                  <td className="py-3 pr-4 max-w-sm">
                    {truncate(clause.title, 70)}
                  </td>
                  <td className="py-3 pr-4">
                    <SourceBadge source={clause.source ?? ""} />
                  </td>
                  <td className="py-3 pr-4">
                    {clause.is_mandatory ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        Mandatory
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                        Optional
                      </span>
                    )}
                  </td>
                  <td className="py-3">
                    {clause.applicability ? (
                      <div className="flex flex-wrap gap-1">
                        {clause.applicability.split(",").map((a, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-muted text-muted-foreground"
                          >
                            {a.trim()}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-xs">--</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ---------- Compliance Assessments Tab ----------

function ComplianceAssessmentsTab({
  assessments,
  loading,
}: {
  assessments: ComplianceAssessment[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading compliance assessments...
        </span>
      </div>
    );
  }

  if (assessments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <ShieldCheck className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No compliance assessments found.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {assessments.map((assessment) => {
        const riskLevel =
          assessment.risk_level || assessment.overall_risk_level || "low";
        const overallStatus = assessment.overall_status || assessment.status || "not_assessed";
        const dealName =
          assessment.deal_name ||
          getDealName(assessment.deal);
        const findingsCount =
          assessment.findings_count ??
          (Array.isArray(assessment.findings)
            ? assessment.findings.length
            : 0);

        return (
          <Card key={assessment.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">
                {truncate(dealName, 40)}
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                {formatDate(assessment.assessment_date || assessment.created_at)}
              </p>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <StatusBadge status={overallStatus} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Risk Level</span>
                <SeverityBadge severity={riskLevel} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Findings</span>
                <span className="text-sm font-medium">{findingsCount}</span>
              </div>
              {assessment.recommendations && (
                <div className="pt-1 border-t">
                  <p className="text-xs text-muted-foreground">
                    {truncate(
                      Array.isArray(assessment.recommendations)
                        ? assessment.recommendations.join("; ")
                        : String(assessment.recommendations),
                      100
                    )}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ---------- Contract Reviews Tab ----------

function ContractReviewsTab({
  notes,
  loading,
}: {
  notes: ContractReviewNote[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading contract review notes...
        </span>
      </div>
    );
  }

  if (notes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <FileText className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No contract review notes found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Section</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Type</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Concern</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Recommendation</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Severity</th>
            <th className="pb-3 font-medium text-muted-foreground">Resolved</th>
          </tr>
        </thead>
        <tbody>
          {notes.map((note) => (
            <tr
              key={note.id}
              className="border-b transition-colors hover:bg-muted/50"
            >
              <td className="py-3 pr-4 font-medium">
                {truncate(
                  note.section_reference || note.section,
                  40
                )}
              </td>
              <td className="py-3 pr-4">
                <NoteTypeBadge noteType={note.note_type} />
              </td>
              <td className="py-3 pr-4 max-w-xs text-muted-foreground">
                {truncate(note.concern || note.note_text, 80)}
              </td>
              <td className="py-3 pr-4 max-w-xs text-muted-foreground">
                {truncate(note.recommendation, 80)}
              </td>
              <td className="py-3 pr-4">
                <SeverityBadge severity={note.severity || note.priority || "low"} />
              </td>
              <td className="py-3">
                {note.resolved ||
                note.status === "addressed" ||
                note.status === "dismissed" ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Yes
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                    No
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------- Main Page ----------

export default function LegalPage() {
  const [activeTab, setActiveTab] = useState<TabId>("risks");
  const [risks, setRisks] = useState<LegalRisk[]>([]);
  const [farClauses, setFARClauses] = useState<FARClause[]>([]);
  const [assessments, setAssessments] = useState<ComplianceAssessment[]>([]);
  const [reviewNotes, setReviewNotes] = useState<ContractReviewNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [risksRes, clausesRes, assessmentsRes, notesRes] = await Promise.all([
        getLegalRisks(),
        getFARClauses(),
        getComplianceAssessments(),
        getContractReviewNotes(),
      ]);
      setRisks(risksRes.results || []);
      setFARClauses(clausesRes.results || []);
      setAssessments(assessmentsRes.results || []);
      setReviewNotes(notesRes.results || []);
    } catch (err) {
      setError("Failed to load legal data. Please try again.");
      console.error("Error fetching legal data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    {
      id: "risks",
      label: "Legal Risks",
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    {
      id: "far_clauses",
      label: "FAR Clauses",
      icon: <FileText className="h-4 w-4" />,
    },
    {
      id: "assessments",
      label: "Compliance Assessments",
      icon: <ShieldCheck className="h-4 w-4" />,
    },
    {
      id: "contract_reviews",
      label: "Contract Reviews",
      icon: <Scale className="h-4 w-4" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Legal &amp; Compliance
          </h1>
          <p className="text-muted-foreground">
            Monitor legal risks, FAR clauses, and compliance assessments
          </p>
        </div>
        <Button variant="outline" onClick={fetchAll} disabled={loading}>
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Refresh
        </Button>
      </div>

      {/* Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Risk KPIs */}
      <RiskKPIs risks={risks} />

      {/* Tabs */}
      <div className="border-b">
        <nav className="-mb-px flex space-x-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 whitespace-nowrap py-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {tabs.find((t) => t.id === activeTab)?.label}
            {!loading && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                (
                {activeTab === "risks" && `${risks.length} results`}
                {activeTab === "far_clauses" && `${farClauses.length} results`}
                {activeTab === "assessments" && `${assessments.length} results`}
                {activeTab === "contract_reviews" && `${reviewNotes.length} results`}
                )
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeTab === "risks" && (
            <LegalRisksTab risks={risks} loading={loading} />
          )}
          {activeTab === "far_clauses" && (
            <FARClausesTab clauses={farClauses} loading={loading} />
          )}
          {activeTab === "assessments" && (
            <ComplianceAssessmentsTab
              assessments={assessments}
              loading={loading}
            />
          )}
          {activeTab === "contract_reviews" && (
            <ContractReviewsTab notes={reviewNotes} loading={loading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
