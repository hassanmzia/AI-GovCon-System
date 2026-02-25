"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getSecurityFrameworks,
  getControlMappings,
  getComplianceReports,
  getComplianceRequirements,
} from "@/services/security";
import {
  SecurityFramework,
  SecurityControlMapping,
  SecurityComplianceReport,
  ComplianceRequirement,
  ImplementationStatus,
  ReportType,
} from "@/types/security";
import {
  Shield,
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  BookOpen,
} from "lucide-react";

type TabId = "reports" | "mappings" | "frameworks" | "requirements";

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
  deal:
    | string
    | { id: string; name: string; title?: string }
    | undefined
): string {
  if (!deal) return "--";
  if (typeof deal === "string") return deal;
  return deal.name || deal.title || "--";
}

function getFrameworkName(
  framework:
    | string
    | { id: string; name: string; version: string }
    | undefined
): string {
  if (!framework) return "--";
  if (typeof framework === "string") return framework;
  return framework.version
    ? `${framework.name} v${framework.version}`
    : framework.name;
}

// ---------- Implementation Status Badge ----------

const implStatusConfig: Record<string, { label: string; cls: string }> = {
  implemented: { label: "Implemented", cls: "bg-green-100 text-green-800" },
  partially_implemented: {
    label: "Partial",
    cls: "bg-yellow-100 text-yellow-800",
  },
  partial: { label: "Partial", cls: "bg-yellow-100 text-yellow-800" },
  not_implemented: {
    label: "Not Implemented",
    cls: "bg-red-100 text-red-800",
  },
  not_applicable: { label: "N/A", cls: "bg-gray-100 text-gray-600" },
  planned: { label: "Planned", cls: "bg-blue-100 text-blue-800" },
};

function ImplStatusBadge({ status }: { status: string }) {
  const cfg = implStatusConfig[status] ?? {
    label: status,
    cls: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cfg.cls}`}
    >
      {cfg.label}
    </span>
  );
}

// ---------- Report Type Badge ----------

const reportTypeConfig: Record<string, { label: string; cls: string }> = {
  gap_analysis: { label: "Gap Analysis", cls: "bg-orange-100 text-orange-800" },
  ssp_draft: { label: "SSP Draft", cls: "bg-blue-100 text-blue-800" },
  assessment_report: {
    label: "Assessment",
    cls: "bg-purple-100 text-purple-800",
  },
  cmmc_readiness: {
    label: "CMMC Readiness",
    cls: "bg-green-100 text-green-800",
  },
  readiness_assessment: {
    label: "Readiness",
    cls: "bg-green-100 text-green-800",
  },
  poam: { label: "POA&M", cls: "bg-red-100 text-red-800" },
  ssp_section: { label: "SSP Section", cls: "bg-blue-100 text-blue-800" },
  authorization_package: {
    label: "Auth Package",
    cls: "bg-indigo-100 text-indigo-800",
  },
};

function ReportTypeBadge({ type }: { type: string }) {
  const cfg = reportTypeConfig[type] ?? {
    label: type?.replace(/_/g, " ") ?? "--",
    cls: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cfg.cls}`}
    >
      {cfg.label}
    </span>
  );
}

// ---------- Score Bar ----------

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(Math.max(score, 0), 100);
  const color =
    pct >= 80
      ? "bg-green-500"
      : pct >= 60
      ? "bg-yellow-500"
      : "bg-red-500";
  const textColor =
    pct >= 80
      ? "text-green-700"
      : pct >= 60
      ? "text-yellow-700"
      : "text-red-700";

  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-xs font-semibold w-9 text-right ${textColor}`}>
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

// ---------- Priority Badge ----------

function PriorityBadge({ priority }: { priority: string }) {
  const config: Record<string, string> = {
    critical: "bg-red-100 text-red-800",
    high: "bg-orange-100 text-orange-800",
    medium: "bg-yellow-100 text-yellow-800",
    low: "bg-blue-100 text-blue-800",
    P1: "bg-red-100 text-red-800",
    P2: "bg-yellow-100 text-yellow-800",
    P3: "bg-blue-100 text-blue-800",
  };
  const cls = config[priority] ?? "bg-gray-100 text-gray-700";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}
    >
      {priority}
    </span>
  );
}

// ---------- KPI Summary ----------

function SecurityKPIs({
  mappings,
  reports,
}: {
  mappings: SecurityControlMapping[];
  reports: SecurityComplianceReport[];
}) {
  const totalMapped = mappings.length;
  const implemented = mappings.filter((m) => {
    const s = m.mapping_status || m.implementation_status || "";
    return s === "implemented";
  }).length;
  const implementedPct =
    totalMapped > 0 ? Math.round((implemented / totalMapped) * 100) : 0;
  const gapsIdentified = reports.reduce((acc, r) => {
    const gaps =
      r.gaps_identified ??
      (Array.isArray(r.gaps) ? r.gaps.length : 0);
    return acc + gaps;
  }, 0);

  const kpis = [
    {
      label: "Controls Mapped",
      value: totalMapped.toString(),
      icon: <Shield className="h-5 w-5 text-muted-foreground" />,
    },
    {
      label: "Implemented",
      value: `${implementedPct}%`,
      icon: <CheckCircle className="h-5 w-5 text-green-600" />,
    },
    {
      label: "Gaps Identified",
      value: gapsIdentified.toString(),
      icon: <AlertTriangle className="h-5 w-5 text-orange-500" />,
      highlight: gapsIdentified > 0,
    },
    {
      label: "Reports",
      value: reports.length.toString(),
      icon: <BarChart3 className="h-5 w-5 text-blue-500" />,
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
                    kpi.highlight ? "text-orange-600" : ""
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

// ---------- Compliance Reports Tab ----------

function ComplianceReportsTab({
  reports,
  loading,
}: {
  reports: SecurityComplianceReport[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading compliance reports...
        </span>
      </div>
    );
  }

  if (reports.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <BarChart3 className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No compliance reports found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Deal</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Framework
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Type</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Score</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Controls
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Gaps</th>
            <th className="pb-3 font-medium text-muted-foreground">Created</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => {
            const score =
              report.overall_score ?? report.overall_compliance_pct ?? 0;
            const compliantControls =
              report.compliant_controls ?? report.controls_implemented ?? 0;
            const totalControls =
              report.total_controls ??
              (report.controls_implemented ?? 0) +
                (report.controls_partial ?? 0) +
                (report.controls_planned ?? 0);
            const gaps =
              report.gaps_identified ??
              (Array.isArray(report.gaps) ? report.gaps.length : 0);
            const dealName =
              getDealName(report.deal) !== "--"
                ? getDealName(report.deal)
                : report.deal_name ?? "--";
            const frameworkName =
              getFrameworkName(report.framework) !== "--"
                ? getFrameworkName(report.framework)
                : report.framework_name ?? "--";

            return (
              <tr
                key={report.id}
                className="border-b transition-colors hover:bg-muted/50"
              >
                <td className="py-3 pr-4 font-medium">
                  {truncate(dealName, 35)}
                </td>
                <td className="py-3 pr-4 text-muted-foreground">
                  {truncate(frameworkName, 30)}
                </td>
                <td className="py-3 pr-4">
                  <ReportTypeBadge type={report.report_type} />
                </td>
                <td className="py-3 pr-4">
                  <ScoreBar score={score} />
                </td>
                <td className="py-3 pr-4 text-muted-foreground">
                  {compliantControls} / {totalControls || "--"}
                </td>
                <td className="py-3 pr-4">
                  {gaps > 0 ? (
                    <span className="text-red-600 font-medium">{gaps}</span>
                  ) : (
                    <span className="text-muted-foreground">{gaps}</span>
                  )}
                </td>
                <td className="py-3 text-muted-foreground">
                  {formatDate(report.created_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------- Frameworks Tab ----------

function FrameworksTab({
  frameworks,
  loading,
}: {
  frameworks: SecurityFramework[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading frameworks...
        </span>
      </div>
    );
  }

  if (frameworks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <BookOpen className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No security frameworks found.</p>
      </div>
    );
  }

  const frameworkTypeColors: Record<string, string> = {
    nist: "bg-blue-100 text-blue-800",
    fedramp: "bg-purple-100 text-purple-800",
    cmmc: "bg-green-100 text-green-800",
    iso: "bg-orange-100 text-orange-800",
    soc2: "bg-indigo-100 text-indigo-800",
    fisma: "bg-red-100 text-red-800",
  };

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {frameworks.map((fw) => {
        const typeKey = fw.framework_type?.toLowerCase() ?? "";
        const typeCls =
          frameworkTypeColors[typeKey] ?? "bg-gray-100 text-gray-700";
        return (
          <Card key={fw.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base font-semibold leading-tight">
                  {fw.name}
                </CardTitle>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium shrink-0 ${typeCls}`}
                >
                  {fw.framework_type ?? "Framework"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">v{fw.version}</p>
            </CardHeader>
            <CardContent className="space-y-3">
              {fw.description && (
                <p className="text-sm text-muted-foreground">
                  {truncate(fw.description, 100)}
                </p>
              )}
              <div className="flex items-center justify-between pt-1 border-t">
                <span className="text-sm text-muted-foreground">Controls</span>
                <span className="text-sm font-bold">
                  {fw.controls_count ?? 0}
                </span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ---------- Control Mappings Tab ----------

function ControlMappingsTab({
  mappings,
  loading,
}: {
  mappings: SecurityControlMapping[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading control mappings...
        </span>
      </div>
    );
  }

  if (mappings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Shield className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No control mappings found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Control ID
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Title
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Framework
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Status
            </th>
            <th className="pb-3 font-medium text-muted-foreground">Deal</th>
          </tr>
        </thead>
        <tbody>
          {mappings.map((mapping) => {
            const status =
              mapping.mapping_status || mapping.implementation_status || "planned";
            const dealName =
              getDealName(mapping.deal) !== "--"
                ? getDealName(mapping.deal)
                : mapping.deal_name ?? "--";

            let controlId = mapping.control_id ?? "--";
            let controlTitle = mapping.control_title ?? "--";
            let frameworkName = mapping.framework_name ?? "--";

            if (mapping.control && typeof mapping.control === "object") {
              controlId = mapping.control.control_id ?? controlId;
              controlTitle = mapping.control.title ?? controlTitle;
              if (mapping.control.framework) {
                frameworkName = getFrameworkName(mapping.control.framework);
              }
            }

            return (
              <tr
                key={mapping.id}
                className="border-b transition-colors hover:bg-muted/50"
              >
                <td className="py-3 pr-4 font-mono font-medium text-sm">
                  {controlId}
                </td>
                <td className="py-3 pr-4 max-w-xs">
                  {truncate(controlTitle, 50)}
                </td>
                <td className="py-3 pr-4 text-muted-foreground">
                  {truncate(frameworkName, 30)}
                </td>
                <td className="py-3 pr-4">
                  <ImplStatusBadge status={status as ImplementationStatus} />
                </td>
                <td className="py-3 text-muted-foreground">
                  {truncate(dealName, 35)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------- Requirements Tab ----------

function RequirementsTab({
  requirements,
  loading,
}: {
  requirements: ComplianceRequirement[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading requirements...
        </span>
      </div>
    );
  }

  if (requirements.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <CheckCircle className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No compliance requirements found.</p>
      </div>
    );
  }

  const reqStatusConfig: Record<string, string> = {
    compliant: "bg-green-100 text-green-800",
    gap: "bg-red-100 text-red-800",
    in_progress: "bg-blue-100 text-blue-800",
    not_assessed: "bg-gray-100 text-gray-700",
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Deal</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Requirement
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Framework Ref
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Priority
            </th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">
              Status
            </th>
            <th className="pb-3 font-medium text-muted-foreground">
              Assigned To
            </th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((req) => {
            const status = req.status || req.current_status || "not_assessed";
            const statusCls =
              reqStatusConfig[status] ?? "bg-gray-100 text-gray-700";
            const statusLabel = status.replace(/_/g, " ");
            const dealName =
              getDealName(req.deal) !== "--"
                ? getDealName(req.deal)
                : req.deal_name ?? "--";

            return (
              <tr
                key={req.id}
                className="border-b transition-colors hover:bg-muted/50"
              >
                <td className="py-3 pr-4 font-medium">
                  {truncate(dealName, 30)}
                </td>
                <td className="py-3 pr-4 max-w-xs text-muted-foreground">
                  {truncate(req.requirement_text, 80)}
                </td>
                <td className="py-3 pr-4 font-mono text-xs text-muted-foreground">
                  {req.framework_reference || "--"}
                </td>
                <td className="py-3 pr-4">
                  <PriorityBadge priority={req.priority ?? "medium"} />
                </td>
                <td className="py-3 pr-4">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${statusCls}`}
                  >
                    {statusLabel}
                  </span>
                </td>
                <td className="py-3 text-muted-foreground">
                  {truncate(
                    typeof req.assigned_to === "string"
                      ? req.assigned_to
                      : null,
                    25
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------- Main Page ----------

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<TabId>("reports");
  const [frameworks, setFrameworks] = useState<SecurityFramework[]>([]);
  const [mappings, setMappings] = useState<SecurityControlMapping[]>([]);
  const [reports, setReports] = useState<SecurityComplianceReport[]>([]);
  const [requirements, setRequirements] = useState<ComplianceRequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fwRes, mapRes, repRes, reqRes] = await Promise.all([
        getSecurityFrameworks(),
        getControlMappings(),
        getComplianceReports(),
        getComplianceRequirements(),
      ]);
      setFrameworks(fwRes.results || []);
      setMappings(mapRes.results || []);
      setReports(repRes.results || []);
      setRequirements(reqRes.results || []);
    } catch (err) {
      setError("Failed to load security compliance data. Please try again.");
      console.error("Error fetching security data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const tabs: { id: TabId; label: string; icon: React.ReactNode; count?: number }[] = [
    {
      id: "reports",
      label: "Compliance Reports",
      icon: <BarChart3 className="h-4 w-4" />,
      count: reports.length,
    },
    {
      id: "mappings",
      label: "Control Mappings",
      icon: <Shield className="h-4 w-4" />,
      count: mappings.length,
    },
    {
      id: "frameworks",
      label: "Frameworks",
      icon: <BookOpen className="h-4 w-4" />,
      count: frameworks.length,
    },
    {
      id: "requirements",
      label: "Requirements",
      icon: <CheckCircle className="h-4 w-4" />,
      count: requirements.length,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Security &amp; Compliance
          </h1>
          <p className="text-muted-foreground">
            Track security frameworks, control mappings, and compliance reports
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
          <CardContent className="pt-6 flex items-center justify-between">
            <p className="text-red-700">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchAll}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* KPI Summary */}
      <SecurityKPIs mappings={mappings} reports={reports} />

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
              {!loading && tab.count !== undefined && (
                <span className="ml-1 text-xs text-muted-foreground">
                  ({tab.count})
                </span>
              )}
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
                {activeTab === "reports" && `${reports.length} results`}
                {activeTab === "mappings" && `${mappings.length} results`}
                {activeTab === "frameworks" && `${frameworks.length} results`}
                {activeTab === "requirements" && `${requirements.length} results`}
                )
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeTab === "reports" && (
            <ComplianceReportsTab reports={reports} loading={loading} />
          )}
          {activeTab === "mappings" && (
            <ControlMappingsTab mappings={mappings} loading={loading} />
          )}
          {activeTab === "frameworks" && (
            <FrameworksTab frameworks={frameworks} loading={loading} />
          )}
          {activeTab === "requirements" && (
            <RequirementsTab requirements={requirements} loading={loading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
