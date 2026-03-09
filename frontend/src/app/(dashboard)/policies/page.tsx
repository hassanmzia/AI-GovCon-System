"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getPolicies,
  getEvaluations,
  getExceptions,
  approveException,
  rejectException,
} from "@/services/policies";
import {
  BusinessPolicy,
  PolicyEvaluation,
  PolicyException,
  PolicyType,
  EvaluationOutcome,
} from "@/types/policy";
import {
  Loader2,
  ShieldCheck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  FileWarning,
  ScrollText,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

type ActiveTab = "policies" | "evaluations" | "exceptions";

const POLICY_TYPE_LABELS: Record<PolicyType, string> = {
  bid_threshold: "Bid Threshold",
  approval_gate: "Approval Gate",
  risk_limit: "Risk Limit",
  compliance_requirement: "Compliance",
  teaming_rule: "Teaming Rule",
  pricing_constraint: "Pricing",
};

const POLICY_TYPE_COLORS: Record<PolicyType, string> = {
  bid_threshold: "bg-blue-100 text-blue-700",
  approval_gate: "bg-purple-100 text-purple-700",
  risk_limit: "bg-red-100 text-red-700",
  compliance_requirement: "bg-orange-100 text-orange-700",
  teaming_rule: "bg-teal-100 text-teal-700",
  pricing_constraint: "bg-yellow-100 text-yellow-700",
};

const SCOPE_LABELS: Record<string, string> = {
  global: "Global",
  deal_type: "Deal Type",
  naics_code: "NAICS Code",
  agency: "Agency",
};

const OUTCOME_COLORS: Record<EvaluationOutcome, string> = {
  pass: "bg-green-100 text-green-700",
  warn: "bg-yellow-100 text-yellow-700",
  fail: "bg-red-100 text-red-700",
  skip: "bg-gray-100 text-gray-500",
};

const OUTCOME_ICONS: Record<EvaluationOutcome, React.ComponentType<{ className?: string }>> = {
  pass: CheckCircle,
  warn: AlertTriangle,
  fail: XCircle,
  skip: Clock,
};

const EXCEPTION_STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function PoliciesPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("policies");

  const [policies, setPolicies] = useState<BusinessPolicy[]>([]);
  const [evaluations, setEvaluations] = useState<PolicyEvaluation[]>([]);
  const [exceptions, setExceptions] = useState<PolicyException[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPolicy, setExpandedPolicy] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState("");

  const fetchPolicies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (typeFilter) params.policy_type = typeFilter;
      if (activeFilter) params.is_active = activeFilter;
      const data = await getPolicies(params);
      setPolicies(data.results || []);
    } catch {
      setError("Failed to load policies.");
    } finally {
      setLoading(false);
    }
  }, [typeFilter, activeFilter]);

  const fetchEvaluations = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getEvaluations();
      setEvaluations(data.results || []);
    } catch {
      setError("Failed to load evaluations.");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchExceptions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getExceptions();
      setExceptions(data.results || []);
    } catch {
      setError("Failed to load exceptions.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "policies") fetchPolicies();
    else if (activeTab === "evaluations") fetchEvaluations();
    else if (activeTab === "exceptions") fetchExceptions();
  }, [activeTab, fetchPolicies, fetchEvaluations, fetchExceptions]);

  const handleExceptionAction = async (id: string, action: "approve" | "reject") => {
    try {
      const updated = action === "approve"
        ? await approveException(id)
        : await rejectException(id);
      setExceptions((prev) =>
        prev.map((e) => (e.id === id ? updated : e))
      );
    } catch {
      setError(`Failed to ${action} exception.`);
    }
  };

  // Summary stats
  const activePolicies = policies.filter((p) => p.is_active).length;
  const pendingExceptions = exceptions.filter((e) => e.status === "pending").length;
  const recentFailures = evaluations.filter((e) => e.outcome === "fail").length;

  const tabs: { key: ActiveTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { key: "policies", label: "Policies", icon: ScrollText },
    { key: "evaluations", label: "Evaluations", icon: ShieldCheck },
    { key: "exceptions", label: "Exceptions", icon: FileWarning },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Policy & Autonomy Engine
        </h1>
        <p className="text-muted-foreground">
          Business rules, automated policy evaluation, and exception management
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Policies</p>
                <p className="text-2xl font-bold">{activePolicies}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {policies.length} total
                </p>
              </div>
              <ShieldCheck className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Recent Failures</p>
                <p className={`text-2xl font-bold ${recentFailures > 0 ? "text-red-600" : ""}`}>
                  {recentFailures}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  From {evaluations.length} evaluations
                </p>
              </div>
              <XCircle className={`h-8 w-8 ${recentFailures > 0 ? "text-red-500" : "text-muted-foreground"}`} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending Exceptions</p>
                <p className={`text-2xl font-bold ${pendingExceptions > 0 ? "text-yellow-600" : ""}`}>
                  {pendingExceptions}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Awaiting approval
                </p>
              </div>
              <AlertTriangle className={`h-8 w-8 ${pendingExceptions > 0 ? "text-yellow-500" : "text-muted-foreground"}`} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="-mb-px flex space-x-4 sm:space-x-8 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:border-muted-foreground hover:text-foreground"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
              {tab.key === "exceptions" && pendingExceptions > 0 && (
                <span className="ml-1 rounded-full bg-yellow-100 px-1.5 py-0.5 text-xs font-semibold text-yellow-700">
                  {pendingExceptions}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Policies Tab */}
      {activeTab === "policies" && (
        <>
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-center gap-3">
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">All Types</option>
                  {Object.entries(POLICY_TYPE_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
                <select
                  value={activeFilter}
                  onChange={(e) => setActiveFilter(e.target.value)}
                  className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">All Status</option>
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Business Policies
                {!loading && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({policies.length} results)
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <p className="text-red-600 mb-4">{error}</p>
                  <Button variant="outline" onClick={fetchPolicies}>Retry</Button>
                </div>
              ) : policies.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <ScrollText className="h-10 w-10 text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">No policies found.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {policies.map((policy) => {
                    const isExpanded = expandedPolicy === policy.id;
                    return (
                      <div
                        key={policy.id}
                        className="rounded-lg border transition-colors hover:bg-muted/30"
                      >
                        <button
                          onClick={() => setExpandedPolicy(isExpanded ? null : policy.id)}
                          className="w-full flex items-center gap-3 p-4 text-left"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                          )}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-sm">{policy.name}</span>
                              <span className="text-xs text-muted-foreground">v{policy.version}</span>
                            </div>
                            {policy.description && (
                              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                                {policy.description}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${POLICY_TYPE_COLORS[policy.policy_type] || "bg-gray-100 text-gray-600"}`}>
                              {POLICY_TYPE_LABELS[policy.policy_type] || policy.policy_type}
                            </span>
                            <span className="hidden sm:inline text-xs text-muted-foreground">
                              {SCOPE_LABELS[policy.scope] || policy.scope}
                            </span>
                            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${policy.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                              {policy.is_active ? "Active" : "Inactive"}
                            </span>
                            <span className="hidden sm:inline text-xs text-muted-foreground">P{policy.priority}</span>
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="border-t px-4 pb-4 pt-3 space-y-3">
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                              <div>
                                <span className="font-medium text-foreground">Effective:</span>{" "}
                                <span className="text-muted-foreground">{formatDate(policy.effective_date)}</span>
                              </div>
                              <div>
                                <span className="font-medium text-foreground">Expires:</span>{" "}
                                <span className="text-muted-foreground">{formatDate(policy.expiry_date)}</span>
                              </div>
                              <div>
                                <span className="font-medium text-foreground">Created by:</span>{" "}
                                <span className="text-muted-foreground">{policy.created_by_username || "--"}</span>
                              </div>
                              <div>
                                <span className="font-medium text-foreground">Updated:</span>{" "}
                                <span className="text-muted-foreground">{formatDate(policy.updated_at)}</span>
                              </div>
                            </div>

                            {/* Rules */}
                            {policy.rules && policy.rules.length > 0 && (
                              <div>
                                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                                  Rules ({policy.rules.length})
                                </p>
                                <div className="space-y-2">
                                  {policy.rules.map((rule) => (
                                    <div
                                      key={rule.id}
                                      className="rounded border px-3 py-2 text-xs space-y-1"
                                    >
                                      <div className="flex items-center justify-between">
                                        <span className="font-medium">{rule.rule_name}</span>
                                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${rule.is_blocking ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
                                          {rule.is_blocking ? "Blocking" : "Warning"}
                                        </span>
                                      </div>
                                      <p className="text-muted-foreground">
                                        <span className="font-mono">{rule.field_path}</span>{" "}
                                        <span className="font-semibold">{rule.operator}</span>{" "}
                                        <span className="font-mono">{rule.threshold_value || JSON.stringify(rule.threshold_json)}</span>
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Evaluations Tab */}
      {activeTab === "evaluations" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Policy Evaluations
              {!loading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({evaluations.length} results)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : evaluations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <ShieldCheck className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No evaluations recorded yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Policy</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Deal</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Outcome</th>
                      <th className="hidden sm:table-cell pb-3 pr-4 font-medium text-muted-foreground">Rules Triggered</th>
                      <th className="hidden md:table-cell pb-3 font-medium text-muted-foreground">Evaluated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evaluations.map((ev) => {
                      const OutcomeIcon = OUTCOME_ICONS[ev.outcome] || Clock;
                      const failedRules = (ev.triggered_rules || []).filter(
                        (r: Record<string, unknown>) => !r.passed
                      ).length;
                      return (
                        <tr key={ev.id} className="border-b transition-colors hover:bg-muted/50">
                          <td className="py-3 pr-4 font-medium">{ev.policy_name || "--"}</td>
                          <td className="py-3 pr-4 text-muted-foreground">{ev.deal_title || "--"}</td>
                          <td className="py-3 pr-4">
                            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${OUTCOME_COLORS[ev.outcome] || "bg-gray-100 text-gray-600"}`}>
                              <OutcomeIcon className="h-3 w-3" />
                              {ev.outcome.charAt(0).toUpperCase() + ev.outcome.slice(1)}
                            </span>
                          </td>
                          <td className="hidden sm:table-cell py-3 pr-4">
                            {failedRules > 0 ? (
                              <span className="text-xs text-red-600 font-medium">{failedRules} failed</span>
                            ) : (
                              <span className="text-xs text-green-600">All passed</span>
                            )}
                          </td>
                          <td className="hidden md:table-cell py-3 text-xs text-muted-foreground">
                            {formatDateTime(ev.evaluated_at)}
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
      )}

      {/* Exceptions Tab */}
      {activeTab === "exceptions" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Policy Exceptions
              {!loading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({exceptions.length} total)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : exceptions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <FileWarning className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No policy exceptions.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {exceptions.map((exc) => (
                  <div key={exc.id} className="rounded-lg border p-4 space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{exc.policy_name || "Policy"}</p>
                        <p className="text-xs text-muted-foreground">{exc.deal_title || "Deal"}</p>
                      </div>
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium shrink-0 ${EXCEPTION_STATUS_COLORS[exc.status] || "bg-gray-100 text-gray-600"}`}>
                        {exc.status.charAt(0).toUpperCase() + exc.status.slice(1)}
                      </span>
                    </div>

                    <p className="text-xs text-muted-foreground">{exc.reason}</p>

                    <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 text-xs text-muted-foreground">
                      <span>Requested by: {exc.requested_by_username || "--"}</span>
                      <span>Created: {formatDate(exc.created_at)}</span>
                      {exc.expires_at && <span>Expires: {formatDate(exc.expires_at)}</span>}
                      {exc.approved_by_username && (
                        <span>
                          {exc.status === "approved" ? "Approved" : "Rejected"} by: {exc.approved_by_username}
                        </span>
                      )}
                    </div>

                    {exc.status === "pending" && (
                      <div className="flex gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs border-green-300 text-green-700 hover:bg-green-50"
                          onClick={() => handleExceptionAction(exc.id, "approve")}
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs border-red-300 text-red-700 hover:bg-red-50"
                          onClick={() => handleExceptionAction(exc.id, "reject")}
                        >
                          Reject
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
