"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AutonomyLevelControl } from "@/components/governance/autonomy-level-control";
import { RiskScoreDisplay } from "@/components/governance/risk-score-display";
import {
  Shield,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  FileText,
  Activity,
  Bug,
} from "lucide-react";

// --- Types ---
interface AutonomyPolicy {
  id: string;
  level: 0 | 1 | 2 | 3;
  kill_switch_active: boolean;
  version: string;
  updated_at: string;
  pricing_floor_margin?: number;
  risk_thresholds?: Record<string, number>;
  hitl_gates?: string[];
  agency_allowlist?: string[];
  agency_blocklist?: string[];
  [key: string]: unknown;
}

interface RiskScoreData {
  legal: number;
  compliance: number;
  deadline: number;
  financial: number;
  security: number;
  reputation: number;
  composite: number;
}

interface EnforcementLog {
  id: string;
  timestamp: string;
  action: string;
  deal: string;
  decision: "allowed" | "blocked" | "hitl_required";
  reason: string;
}

interface AIIncident {
  id: string;
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "investigating" | "resolved";
  created_at: string;
  description: string;
}

// --- Helpers ---
function decisionColor(decision: string): string {
  switch (decision) {
    case "allowed":
      return "text-green-700 bg-green-100";
    case "blocked":
      return "text-red-700 bg-red-100";
    case "hitl_required":
      return "text-amber-700 bg-amber-100";
    default:
      return "text-gray-600 bg-gray-100";
  }
}

function severityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-red-700 bg-red-100 border-red-200";
    case "high":
      return "text-orange-700 bg-orange-100 border-orange-200";
    case "medium":
      return "text-amber-700 bg-amber-100 border-amber-200";
    case "low":
      return "text-blue-700 bg-blue-100 border-blue-200";
    default:
      return "text-gray-600 bg-gray-100 border-gray-200";
  }
}

function statusColor(status: string): string {
  switch (status) {
    case "open":
      return "text-red-600";
    case "investigating":
      return "text-amber-600";
    case "resolved":
      return "text-green-600";
    default:
      return "text-gray-500";
  }
}

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

// --- Main Page ---
export default function GovernancePage() {
  // Policy state
  const [policy, setPolicy] = useState<AutonomyPolicy | null>(null);
  const [policyLoading, setPolicyLoading] = useState(true);
  const [policyError, setPolicyError] = useState<string | null>(null);

  // Risk state
  const [riskScore, setRiskScore] = useState<RiskScoreData | null>(null);
  const [riskLoading, setRiskLoading] = useState(false);
  const [riskError, setRiskError] = useState<string | null>(null);

  // Enforcement log state
  const [enforcementLog, setEnforcementLog] = useState<EnforcementLog[]>([]);
  const [logLoading, setLogLoading] = useState(true);
  const [logError, setLogError] = useState<string | null>(null);

  // Incidents state
  const [incidents, setIncidents] = useState<AIIncident[]>([]);
  const [incidentsLoading, setIncidentsLoading] = useState(true);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);

  // Policy JSON expanded
  const [policyExpanded, setPolicyExpanded] = useState(false);

  // Kill switch + level update loading
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch active autonomy policy
  const fetchPolicy = useCallback(async () => {
    setPolicyLoading(true);
    setPolicyError(null);
    try {
      const res = await api.get("/policies/autonomy-policies/active/");
      const data = res.data;
      setPolicy(data);
    } catch (e) {
      setPolicyError(e instanceof Error ? e.message : "Failed to load policy");
    } finally {
      setPolicyLoading(false);
    }
  }, []);

  // Fetch enforcement log
  const fetchLog = useCallback(async () => {
    setLogLoading(true);
    setLogError(null);
    try {
      const res = await api.get("/policies/enforcement-log/?limit=20");
      const data = res.data;
      setEnforcementLog(Array.isArray(data) ? data : data.results ?? []);
    } catch (e) {
      setLogError(e instanceof Error ? e.message : "Failed to load log");
    } finally {
      setLogLoading(false);
    }
  }, []);

  // Fetch incidents
  const fetchIncidents = useCallback(async () => {
    setIncidentsLoading(true);
    setIncidentsError(null);
    try {
      const res = await api.get("/policies/incidents/");
      const data = res.data;
      setIncidents(Array.isArray(data) ? data : data.results ?? []);
    } catch (e) {
      setIncidentsError(
        e instanceof Error ? e.message : "Failed to load incidents"
      );
    } finally {
      setIncidentsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicy();
    fetchLog();
    fetchIncidents();
  }, [fetchPolicy, fetchLog, fetchIncidents]);

  // Run risk assessment
  const handleRunRiskAssessment = async () => {
    setRiskLoading(true);
    setRiskError(null);
    try {
      const res = await api.post("/policies/assess-risk/", {
        context: "current_pipeline",
        deal_value: 5000000,
        agency: "DoD",
        classification: "unclassified",
      });
      const data = res.data;
      setRiskScore(data.risk_score ?? data);
    } catch (e) {
      setRiskError(
        e instanceof Error ? e.message : "Risk assessment failed"
      );
    } finally {
      setRiskLoading(false);
    }
  };

  // Handle level change
  const handleLevelChange = async (level: number) => {
    if (!policy) return;
    setActionLoading(true);
    try {
      await api.post(`/policies/autonomy-policies/${policy.id}/set-level/`, { level });
      await fetchPolicy();
    } catch {
      // silently refresh
      await fetchPolicy();
    } finally {
      setActionLoading(false);
    }
  };

  // Handle kill switch toggle
  const handleKillSwitch = async () => {
    if (!policy) return;
    setActionLoading(true);
    try {
      const endpoint = policy.kill_switch_active
        ? `/policies/autonomy-policies/${policy.id}/restore/`
        : `/policies/autonomy-policies/${policy.id}/kill-switch/`;
      await api.post(endpoint);
      await fetchPolicy();
    } catch {
      await fetchPolicy();
    } finally {
      setActionLoading(false);
    }
  };

  // Policy detail sections
  const policyKeys = policy
    ? {
        "Pricing Floor Margin": policy.pricing_floor_margin
          ? `${(policy.pricing_floor_margin * 100).toFixed(1)}%`
          : "N/A",
        "Risk Thresholds": policy.risk_thresholds
          ? JSON.stringify(policy.risk_thresholds, null, 2)
          : "N/A",
        "HITL Gates": policy.hitl_gates?.join(", ") ?? "N/A",
        "Agency Allowlist": policy.agency_allowlist?.join(", ") || "All agencies",
        "Agency Blocklist": policy.agency_blocklist?.join(", ") || "None",
      }
    : null;

  const openIncidents = incidents.filter(
    (i) => i.status === "open" || i.status === "investigating"
  );

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-100 rounded-lg">
            <Shield className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              AI Governance & Autonomy Control
            </h1>
            <p className="text-sm text-gray-500">
              {policy
                ? `Policy v${policy.version} — last updated ${formatTs(policy.updated_at)}`
                : "Loading policy..."}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            fetchPolicy();
            fetchLog();
            fetchIncidents();
          }}
          disabled={policyLoading || logLoading}
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Refresh
        </Button>
      </div>

      {/* 1. Autonomy Level Control */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-500" />
            Autonomy Level Control
          </CardTitle>
          <CardDescription>
            Set the AI autonomy level for all pipeline operations. The kill
            switch immediately freezes all autonomous AI actions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {policyLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading policy...</span>
            </div>
          ) : policyError ? (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4">
              <div className="flex items-center gap-2 text-red-700 text-sm">
                <AlertTriangle className="h-4 w-4" />
                <span>Failed to load policy: {policyError}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={fetchPolicy}
              >
                Retry
              </Button>
            </div>
          ) : policy ? (
            <div className={actionLoading ? "opacity-60 pointer-events-none" : ""}>
              <AutonomyLevelControl
                currentLevel={policy.level}
                killSwitchActive={policy.kill_switch_active}
                onLevelChange={handleLevelChange}
                onKillSwitch={handleKillSwitch}
              />
            </div>
          ) : (
            <p className="text-sm text-gray-500">No active policy found.</p>
          )}
        </CardContent>
      </Card>

      {/* 2. Risk Assessment Panel */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Risk Assessment Panel
              </CardTitle>
              <CardDescription>
                Real-time risk scoring for the current pipeline context.
              </CardDescription>
            </div>
            <Button
              onClick={handleRunRiskAssessment}
              disabled={riskLoading}
              size="sm"
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              {riskLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                  Assessing...
                </>
              ) : (
                "Run Risk Assessment"
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {riskError && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              {riskError}
            </div>
          )}
          <RiskScoreDisplay
            riskScore={riskScore}
            threshold={
              policy?.risk_thresholds?.composite ??
              policy?.risk_thresholds?.default ??
              0.35
            }
            showDetails={true}
          />
        </CardContent>
      </Card>

      {/* 3. Active Policy Details */}
      <Card>
        <CardHeader
          className="pb-3 cursor-pointer select-none"
          onClick={() => setPolicyExpanded((v) => !v)}
        >
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4 text-gray-500" />
              Active Policy Details
            </CardTitle>
            {policyExpanded ? (
              <ChevronDown className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-400" />
            )}
          </div>
        </CardHeader>
        {policyExpanded && (
          <CardContent className="space-y-4">
            {policy ? (
              <>
                {/* Key settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {policyKeys &&
                    Object.entries(policyKeys).map(([label, value]) => (
                      <div
                        key={label}
                        className="rounded-lg bg-gray-50 border border-gray-200 p-3"
                      >
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                          {label}
                        </p>
                        <p className="text-sm text-gray-800 font-mono break-words whitespace-pre-wrap">
                          {value}
                        </p>
                      </div>
                    ))}
                </div>

                {/* Full JSON */}
                <div className="rounded-lg bg-gray-900 p-4 overflow-auto max-h-64">
                  <pre className="text-xs text-green-400 font-mono">
                    {JSON.stringify(policy, null, 2)}
                  </pre>
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500">No policy loaded.</p>
            )}
          </CardContent>
        )}
      </Card>

      {/* 4. Recent Policy Enforcement Log */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Shield className="h-4 w-4 text-purple-500" />
            Recent Policy Enforcement Log
          </CardTitle>
          <CardDescription>Last 20 enforcement decisions</CardDescription>
        </CardHeader>
        <CardContent>
          {logLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading enforcement log...</span>
            </div>
          ) : logError ? (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {logError}
            </div>
          ) : enforcementLog.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Shield className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No enforcement events recorded</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Timestamp
                    </th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Action
                    </th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Deal
                    </th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Decision
                    </th>
                    <th className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Reason
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {enforcementLog.map((entry, i) => (
                    <tr
                      key={entry.id ?? i}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-2 px-3 text-xs text-gray-500 whitespace-nowrap">
                        {formatTs(entry.timestamp)}
                      </td>
                      <td className="py-2 px-3 text-xs font-medium text-gray-700">
                        {entry.action}
                      </td>
                      <td className="py-2 px-3 text-xs text-gray-600 max-w-[140px] truncate">
                        {entry.deal}
                      </td>
                      <td className="py-2 px-3">
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded ${decisionColor(entry.decision)}`}
                        >
                          {entry.decision?.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-xs text-gray-500 max-w-[200px] truncate">
                        {entry.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 5. AI Incidents */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Bug className="h-4 w-4 text-red-500" />
              AI Incidents
              {openIncidents.length > 0 && (
                <span className="ml-1 text-xs font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                  {openIncidents.length} open
                </span>
              )}
            </CardTitle>
            <CardDescription>
              Open & investigating AI incidents
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {incidentsLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading incidents...</span>
            </div>
          ) : incidentsError ? (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {incidentsError}
            </div>
          ) : incidents.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Bug className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-medium">No AI incidents reported</p>
              <p className="text-xs mt-1">
                The system is operating within normal parameters.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {incidents.map((incident, i) => (
                <div
                  key={incident.id ?? i}
                  className={`rounded-lg border p-3 ${severityColor(incident.severity)}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-xs font-bold uppercase tracking-wide">
                          {incident.severity}
                        </span>
                        <span
                          className={`text-xs font-medium ${statusColor(incident.status)}`}
                        >
                          {incident.status}
                        </span>
                        <span className="text-xs text-gray-400 ml-auto">
                          {formatTs(incident.created_at)}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-gray-800 truncate">
                        {incident.title}
                      </p>
                      {incident.description && (
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                          {incident.description}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
