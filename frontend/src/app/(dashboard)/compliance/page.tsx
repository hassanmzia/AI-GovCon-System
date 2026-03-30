"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getSecurityFrameworks,
  getSecurityControls,
  getComplianceRequirements,
  getComplianceReports,
} from "@/services/security";
import {
  SecurityFramework,
  SecurityControl,
  ComplianceRequirement,
  SecurityComplianceReport,
} from "@/types/security";
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ClipboardCheck,
  ShieldCheck,
  Shield,
  BarChart3,
  BookOpen,
  FileText,
  Loader2,
  RefreshCw,
  AlertOctagon,
  ListChecks,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getFrameworkDisplayName(
  framework: string | { id: string; name: string; version: string } | undefined
): string {
  if (!framework) return "--";
  if (typeof framework === "string") return framework;
  return framework.version
    ? `${framework.name} v${framework.version}`
    : framework.name;
}

function getDealDisplayName(
  deal: string | { id: string; name: string; title?: string } | undefined
): string {
  if (!deal) return "--";
  if (typeof deal === "string") return deal;
  return deal.name || deal.title || "--";
}

function truncate(str: string | null | undefined, max: number): string {
  if (!str) return "--";
  return str.length > max ? str.slice(0, max) + "…" : str;
}

// ---------------------------------------------------------------------------
// Badge sub-components
// ---------------------------------------------------------------------------

const IMPL_STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  implemented: { label: "Implemented", cls: "bg-green-100 text-green-800 border-green-200" },
  partially_implemented: { label: "Partial", cls: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  partial: { label: "Partial", cls: "bg-yellow-100 text-yellow-800 border-yellow-200" },
  not_implemented: { label: "Not Implemented", cls: "bg-red-100 text-red-800 border-red-200" },
  not_applicable: { label: "N/A", cls: "bg-gray-100 text-gray-600 border-gray-200" },
  planned: { label: "Planned", cls: "bg-blue-100 text-blue-800 border-blue-200" },
};

function ImplStatusBadge({ status }: { status: string }) {
  const cfg = IMPL_STATUS_CONFIG[status] ?? {
    label: status?.replace(/_/g, " ") ?? "--",
    cls: "bg-gray-100 text-gray-700 border-gray-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

const PRIORITY_CONFIG: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-blue-100 text-blue-800 border-blue-200",
  P1: "bg-red-100 text-red-800 border-red-200",
  P2: "bg-yellow-100 text-yellow-800 border-yellow-200",
  P3: "bg-blue-100 text-blue-800 border-blue-200",
};

function PriorityBadge({ priority }: { priority: string }) {
  const cls = PRIORITY_CONFIG[priority] ?? "bg-gray-100 text-gray-700 border-gray-200";
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {priority}
    </span>
  );
}

const REPORT_TYPE_CONFIG: Record<string, { label: string; cls: string }> = {
  gap_analysis: { label: "Gap Analysis", cls: "bg-orange-100 text-orange-800 border-orange-200" },
  ssp_draft: { label: "SSP Draft", cls: "bg-blue-100 text-blue-800 border-blue-200" },
  assessment_report: { label: "Assessment", cls: "bg-purple-100 text-purple-800 border-purple-200" },
  cmmc_readiness: { label: "CMMC Readiness", cls: "bg-green-100 text-green-800 border-green-200" },
  readiness_assessment: { label: "Readiness", cls: "bg-green-100 text-green-800 border-green-200" },
  poam: { label: "POA&M", cls: "bg-red-100 text-red-800 border-red-200" },
  ssp_section: { label: "SSP Section", cls: "bg-blue-100 text-blue-800 border-blue-200" },
  authorization_package: { label: "Auth Package", cls: "bg-indigo-100 text-indigo-800 border-indigo-200" },
};

function ReportTypeBadge({ type }: { type: string }) {
  const cfg = REPORT_TYPE_CONFIG[type] ?? {
    label: type?.replace(/_/g, " ") ?? "--",
    cls: "bg-gray-100 text-gray-700 border-gray-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Reusable UI pieces
// ---------------------------------------------------------------------------

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
    (pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500");
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
  value: number | string;
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

function LoadingSpinner({ message }: { message?: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      {message && (
        <span className="ml-3 text-sm text-gray-500">{message}</span>
      )}
    </div>
  );
}

function EmptyState({
  icon: Icon,
  message,
}: {
  icon: typeof Shield;
  message: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-400">
      <Icon className="mb-3 h-12 w-12" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Frameworks
// ---------------------------------------------------------------------------

function FrameworksTab({
  frameworks,
  loading,
  error,
}: {
  frameworks: SecurityFramework[];
  loading: boolean;
  error: string | null;
}) {
  if (loading) return <LoadingSpinner message="Loading frameworks..." />;
  if (error)
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  if (frameworks.length === 0)
    return <EmptyState icon={Shield} message="No compliance frameworks found." />;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {frameworks.map((fw) => {
        const controlCount = fw.control_count ?? fw.controls_count ?? fw.control_families?.length ?? 0;
        const isActive = fw.is_active !== false;
        return (
          <Card key={fw.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-100">
                    <Shield className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle className="text-base leading-tight">
                      {fw.name}
                    </CardTitle>
                    {fw.version && (
                      <p className="text-xs text-gray-400">v{fw.version}</p>
                    )}
                  </div>
                </div>
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${
                    isActive
                      ? "border-green-200 bg-green-100 text-green-700"
                      : "border-gray-200 bg-gray-100 text-gray-500"
                  }`}
                >
                  {isActive ? "Active" : "Inactive"}
                </span>
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              {fw.description && (
                <p className="text-sm text-gray-600 line-clamp-2">
                  {fw.description}
                </p>
              )}
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Controls</span>
                <span className="font-semibold text-gray-900">
                  {controlCount}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Families</span>
                <span className="font-semibold text-gray-900">
                  {fw.control_families?.length ?? 0}
                </span>
              </div>
              {fw.control_families && fw.control_families.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {fw.control_families.slice(0, 6).map((fam) => (
                    <span key={fam} className="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600">
                      {fam.split(" - ")[0]}
                    </span>
                  ))}
                  {fw.control_families.length > 6 && (
                    <span className="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
                      +{fw.control_families.length - 6} more
                    </span>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Controls
// ---------------------------------------------------------------------------

function ControlsTab({
  controls,
  loading,
  error,
}: {
  controls: SecurityControl[];
  loading: boolean;
  error: string | null;
}) {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = controls.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      c.control_id.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      (c.framework_name ?? "").toLowerCase().includes(q) ||
      (c.control_family ?? c.family ?? "").toLowerCase().includes(q)
    );
  });

  if (loading) return <LoadingSpinner message="Loading security controls..." />;
  if (error)
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <Input
          placeholder="Search controls..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          className="pl-9"
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={ListChecks}
          message={
            search
              ? "No controls match your search."
              : "No security controls found."
          }
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-3">Control ID</th>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Framework</th>
                    <th className="px-4 py-3">Family</th>
                    <th className="px-4 py-3">Priority</th>
                    <th className="px-4 py-3">Baseline</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filtered.map((ctrl) => {
                    const family = ctrl.control_family ?? ctrl.family ?? "--";
                    const frameworkName =
                      ctrl.framework_name ??
                      getFrameworkDisplayName(
                        typeof ctrl.framework === "object"
                          ? ctrl.framework
                          : undefined
                      );
                    const isExpanded = expandedId === ctrl.id;
                    return (
                      <>
                        <tr
                          key={ctrl.id}
                          className="hover:bg-gray-50 transition-colors"
                        >
                          <td className="whitespace-nowrap px-4 py-3 font-mono font-medium text-gray-900">
                            {ctrl.control_id}
                          </td>
                          <td className="px-4 py-3 text-gray-700 max-w-xs">
                            {truncate(ctrl.title, 60)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                            {frameworkName}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                            {family}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3">
                            {ctrl.priority ? (
                              <PriorityBadge priority={ctrl.priority} />
                            ) : (
                              "--"
                            )}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-gray-600 capitalize">
                            {ctrl.baseline_impact?.replace(/_/g, " ") ?? "--"}
                          </td>
                          <td className="px-4 py-3">
                            {ctrl.description && (
                              <button
                                onClick={() =>
                                  setExpandedId(isExpanded ? null : ctrl.id)
                                }
                                className="text-blue-600 hover:text-blue-800"
                                aria-label={isExpanded ? "Collapse" : "Expand"}
                              >
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                              </button>
                            )}
                          </td>
                        </tr>
                        {isExpanded && ctrl.description && (
                          <tr key={`${ctrl.id}-detail`} className="bg-blue-50">
                            <td colSpan={7} className="px-6 py-3">
                              <p className="text-sm text-gray-700">
                                {ctrl.description}
                              </p>
                              {ctrl.implementation_guidance && (
                                <div className="mt-2">
                                  <p className="text-xs font-medium uppercase tracking-wider text-gray-500 mb-1">
                                    Implementation Guidance
                                  </p>
                                  <p className="text-sm text-gray-600">
                                    {ctrl.implementation_guidance}
                                  </p>
                                </div>
                              )}
                            </td>
                          </tr>
                        )}
                      </>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Requirements
// ---------------------------------------------------------------------------

function RequirementsTab({
  requirements,
  loading,
  error,
}: {
  requirements: ComplianceRequirement[];
  loading: boolean;
  error: string | null;
}) {
  const [search, setSearch] = useState("");

  const filtered = requirements.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.requirement_text.toLowerCase().includes(q) ||
      (r.framework_reference ?? "").toLowerCase().includes(q) ||
      (r.category ?? "").toLowerCase().includes(q) ||
      (r.source_document ?? "").toLowerCase().includes(q)
    );
  });

  // Summary stats from the full (unfiltered) list
  const total = requirements.length;
  const statusCounts = requirements.reduce<Record<string, number>>((acc, r) => {
    const s = r.current_status ?? r.status ?? "unknown";
    acc[s] = (acc[s] ?? 0) + 1;
    return acc;
  }, {});

  if (loading) return <LoadingSpinner message="Loading requirements..." />;
  if (error)
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      {total > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Total Requirements"
            value={total}
            icon={BarChart3}
            colorClass="bg-blue-100 text-blue-600"
          />
          {Object.entries(statusCounts)
            .slice(0, 3)
            .map(([status, count]) => (
              <div
                key={status}
                className="flex items-center gap-3 rounded-lg border bg-white p-4"
              >
                <div className="rounded-lg bg-gray-100 p-2 text-gray-600">
                  <ClipboardCheck className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm capitalize text-gray-500">
                    {status.replace(/_/g, " ")}
                  </p>
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Search */}
      <div className="relative">
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

      {filtered.length === 0 ? (
        <EmptyState
          icon={ClipboardCheck}
          message={
            search
              ? "No requirements match your search."
              : "No compliance requirements found."
          }
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-3">Requirement</th>
                    <th className="px-4 py-3">Framework Ref</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Priority</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Source</th>
                    <th className="px-4 py-3">Deal</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filtered.map((req) => {
                    const status = req.current_status ?? req.status ?? "--";
                    const category = req.category ?? "--";
                    return (
                      <tr
                        key={req.id}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-4 py-3 text-gray-700 max-w-sm">
                          <p className="line-clamp-2">
                            {truncate(req.requirement_text, 120)}
                          </p>
                          {req.gap_description && (
                            <p className="mt-1 text-xs text-orange-600">
                              Gap: {truncate(req.gap_description, 80)}
                            </p>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-600">
                          {req.framework_reference || "--"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 capitalize text-gray-600">
                          {category.replace(/_/g, " ")}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          {req.priority ? (
                            <PriorityBadge priority={req.priority} />
                          ) : (
                            "--"
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <ImplStatusBadge status={status} />
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-xs text-gray-500">
                          {truncate(req.source_document, 30)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                          {getDealDisplayName(req.deal)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tab: Reports
// ---------------------------------------------------------------------------

function ReportsTab({
  reports,
  loading,
  error,
}: {
  reports: SecurityComplianceReport[];
  loading: boolean;
  error: string | null;
}) {
  if (loading) return <LoadingSpinner message="Loading compliance reports..." />;
  if (error)
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );

  // Aggregate stats
  const avgScore =
    reports.length > 0
      ? Math.round(
          reports.reduce((sum, r) => {
            const s = r.overall_score ?? r.overall_compliance_pct ?? 0;
            return sum + s;
          }, 0) / reports.length
        )
      : 0;
  const totalGaps = reports.reduce((sum, r) => {
    const g =
      r.gaps_identified ?? (Array.isArray(r.gaps) ? r.gaps.length : 0);
    return sum + g;
  }, 0);

  return (
    <div className="space-y-6">
      {/* Summary */}
      {reports.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-5">
          <Card className="lg:col-span-2">
            <CardContent className="flex flex-col items-center justify-center gap-4 py-8">
              <CircularProgress value={avgScore} />
              <p className="text-sm font-medium text-gray-600">
                Average Compliance Score
              </p>
              <ProgressBar value={avgScore} className="max-w-xs" />
            </CardContent>
          </Card>
          <div className="grid gap-4 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-2">
            <StatCard
              label="Total Reports"
              value={reports.length}
              icon={FileText}
              colorClass="bg-blue-100 text-blue-600"
            />
            <StatCard
              label="Avg Compliance"
              value={`${avgScore}%`}
              icon={CheckCircle2}
              colorClass="bg-green-100 text-green-600"
            />
            <StatCard
              label="Gaps Identified"
              value={totalGaps}
              icon={AlertTriangle}
              colorClass="bg-orange-100 text-orange-600"
            />
            <StatCard
              label="Frameworks Covered"
              value={
                new Set(
                  reports.map((r) => getFrameworkDisplayName(r.framework))
                ).size
              }
              icon={Shield}
              colorClass="bg-purple-100 text-purple-600"
            />
          </div>
        </div>
      )}

      {reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          message="No compliance reports found."
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileText className="h-5 w-5 text-blue-600" />
              Compliance Reports
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-3">Deal</th>
                    <th className="px-4 py-3">Framework</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Controls</th>
                    <th className="px-4 py-3">Gaps</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {reports.map((report) => {
                    const score =
                      report.overall_score ?? report.overall_compliance_pct ?? 0;
                    const compliantControls =
                      report.compliant_controls ??
                      report.controls_implemented ??
                      0;
                    const totalControls =
                      report.total_controls ??
                      (report.controls_implemented ?? 0) +
                        (report.controls_partial ?? 0) +
                        (report.controls_planned ?? 0) +
                        (report.controls_na ?? 0);
                    const gaps =
                      report.gaps_identified ??
                      (Array.isArray(report.gaps) ? report.gaps.length : 0);
                    const pct = Math.min(Math.max(score, 0), 100);
                    const barColor =
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
                      <tr
                        key={report.id}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-4 py-3 text-gray-700">
                          {getDealDisplayName(report.deal)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                          {report.framework_name ??
                            getFrameworkDisplayName(report.framework)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <ReportTypeBadge type={report.report_type} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 min-w-[120px]">
                            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${barColor}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span
                              className={`text-xs font-semibold w-9 text-right ${textColor}`}
                            >
                              {pct.toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                          {totalControls > 0
                            ? `${compliantControls}/${totalControls}`
                            : "--"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          {gaps > 0 ? (
                            <span className="font-medium text-orange-600">
                              {gaps}
                            </span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          {report.status ? (
                            <ImplStatusBadge status={report.status} />
                          ) : (
                            "--"
                          )}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-gray-500">
                          {formatDate(report.created_at)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type TabKey = "frameworks" | "controls" | "requirements" | "reports";

const TABS: { key: TabKey; label: string; icon: typeof Shield }[] = [
  { key: "frameworks", label: "Frameworks", icon: Shield },
  { key: "controls", label: "Security Controls", icon: ListChecks },
  { key: "requirements", label: "Requirements", icon: ClipboardCheck },
  { key: "reports", label: "Reports", icon: FileText },
];

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<TabKey>("frameworks");

  const [frameworks, setFrameworks] = useState<SecurityFramework[]>([]);
  const [controls, setControls] = useState<SecurityControl[]>([]);
  const [requirements, setRequirements] = useState<ComplianceRequirement[]>([]);
  const [reports, setReports] = useState<SecurityComplianceReport[]>([]);

  const [loadingFrameworks, setLoadingFrameworks] = useState(false);
  const [loadingControls, setLoadingControls] = useState(false);
  const [loadingRequirements, setLoadingRequirements] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);

  const [errorFrameworks, setErrorFrameworks] = useState<string | null>(null);
  const [errorControls, setErrorControls] = useState<string | null>(null);
  const [errorRequirements, setErrorRequirements] = useState<string | null>(null);
  const [errorReports, setErrorReports] = useState<string | null>(null);

  const fetchFrameworks = useCallback(async () => {
    setLoadingFrameworks(true);
    setErrorFrameworks(null);
    try {
      const data = await getSecurityFrameworks();
      setFrameworks(data.results ?? []);
    } catch {
      setErrorFrameworks("Failed to load frameworks. Please try again.");
    } finally {
      setLoadingFrameworks(false);
    }
  }, []);

  const fetchControls = useCallback(async () => {
    setLoadingControls(true);
    setErrorControls(null);
    try {
      const data = await getSecurityControls();
      setControls(data.results ?? []);
    } catch {
      setErrorControls("Failed to load security controls. Please try again.");
    } finally {
      setLoadingControls(false);
    }
  }, []);

  const fetchRequirements = useCallback(async () => {
    setLoadingRequirements(true);
    setErrorRequirements(null);
    try {
      const data = await getComplianceRequirements();
      setRequirements(data.results ?? []);
    } catch {
      setErrorRequirements("Failed to load requirements. Please try again.");
    } finally {
      setLoadingRequirements(false);
    }
  }, []);

  const fetchReports = useCallback(async () => {
    setLoadingReports(true);
    setErrorReports(null);
    try {
      const data = await getComplianceReports();
      setReports(data.results ?? []);
    } catch {
      setErrorReports("Failed to load compliance reports. Please try again.");
    } finally {
      setLoadingReports(false);
    }
  }, []);

  // Fetch all data on mount
  useEffect(() => {
    fetchFrameworks();
    fetchControls();
    fetchRequirements();
    fetchReports();
  }, [fetchFrameworks, fetchControls, fetchRequirements, fetchReports]);

  const handleRefresh = () => {
    fetchFrameworks();
    fetchControls();
    fetchRequirements();
    fetchReports();
  };

  const isAnyLoading =
    loadingFrameworks || loadingControls || loadingRequirements || loadingReports;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Compliance &amp; Security
          </h1>
          <p className="text-sm text-gray-500">
            Manage security frameworks, controls, requirements, and compliance reports
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isAnyLoading}
            className="flex items-center gap-2"
          >
            <RefreshCw
              className={`h-4 w-4 ${isAnyLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <ShieldCheck className="h-8 w-8 text-blue-600" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border bg-gray-50 p-1 flex-wrap">
        {TABS.map((tab) => {
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

      {/* Tab content */}
      {activeTab === "frameworks" && (
        <FrameworksTab
          frameworks={frameworks}
          loading={loadingFrameworks}
          error={errorFrameworks}
        />
      )}

      {activeTab === "controls" && (
        <ControlsTab
          controls={controls}
          loading={loadingControls}
          error={errorControls}
        />
      )}

      {activeTab === "requirements" && (
        <RequirementsTab
          requirements={requirements}
          loading={loadingRequirements}
          error={errorRequirements}
        />
      )}

      {activeTab === "reports" && (
        <ReportsTab
          reports={reports}
          loading={loadingReports}
          error={errorReports}
        />
      )}
    </div>
  );
}
