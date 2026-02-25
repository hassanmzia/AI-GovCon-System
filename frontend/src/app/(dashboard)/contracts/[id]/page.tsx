"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getContract,
  getContractVersions,
} from "@/services/contracts";
import { Contract, ContractVersion } from "@/types/contract";
import {
  Loader2,
  ArrowLeft,
  FileText,
  DollarSign,
  Calendar,
  User,
  CheckCircle,
  Clock,
  AlertTriangle,
  GitBranch,
  Info,
} from "lucide-react";

function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const STATUS_COLORS: Record<string, string> = {
  drafting: "bg-gray-100 text-gray-700",
  review: "bg-blue-100 text-blue-700",
  negotiation: "bg-yellow-100 text-yellow-700",
  pending_execution: "bg-orange-100 text-orange-700",
  executed: "bg-indigo-100 text-indigo-700",
  active: "bg-green-100 text-green-700",
  modification: "bg-purple-100 text-purple-700",
  closeout: "bg-gray-100 text-gray-600",
  terminated: "bg-red-100 text-red-700",
  expired: "bg-gray-100 text-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
  drafting: "Drafting",
  review: "Review",
  negotiation: "Negotiation",
  pending_execution: "Pending Execution",
  executed: "Executed",
  active: "Active",
  modification: "Modification",
  closeout: "Closeout",
  terminated: "Terminated",
  expired: "Expired",
};

const CONTRACT_TYPE_LABELS: Record<string, string> = {
  FFP: "Firm Fixed Price",
  "T&M": "Time & Materials",
  CPFF: "Cost Plus Fixed Fee",
  CPAF: "Cost Plus Award Fee",
  CPIF: "Cost Plus Incentive Fee",
  IDIQ: "IDIQ",
  BPA: "BPA",
};

const CHANGE_TYPE_LABELS: Record<string, string> = {
  initial: "Initial Award",
  modification: "Modification",
  amendment: "Amendment",
  option_exercise: "Option Exercise",
  administrative: "Administrative",
};

// ── Deliverables Timeline ────────────────────────────────────────────────────
function DeliverablesTimeline({ contract }: { contract: Contract }) {
  // Build a period-of-performance timeline
  const start = contract.period_of_performance_start
    ? new Date(contract.period_of_performance_start)
    : null;
  const end = contract.period_of_performance_end
    ? new Date(contract.period_of_performance_end)
    : null;

  if (!start || !end) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
        Period of performance not set
      </div>
    );
  }

  const now = new Date();
  const totalMs = end.getTime() - start.getTime();
  const elapsedMs = Math.max(0, Math.min(totalMs, now.getTime() - start.getTime()));
  const progressPct = totalMs > 0 ? (elapsedMs / totalMs) * 100 : 0;
  const daysRemaining = Math.max(0, Math.round((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
  const totalDays = Math.round(totalMs / (1000 * 60 * 60 * 24));

  // Option year milestones
  const optionYears = contract.option_years || 0;
  const baseYears = totalDays / 365;
  const milestones = [];
  for (let i = 1; i <= Math.min(optionYears, 5); i++) {
    const optionStart = new Date(start.getTime() + i * 365 * 24 * 60 * 60 * 1000);
    if (optionStart <= end) {
      milestones.push({ label: `Option Year ${i}`, date: optionStart });
    }
  }

  const isComplete = now >= end;
  const isActive = contract.status === "active";

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div>
        <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
          <span>{formatDate(contract.period_of_performance_start)}</span>
          <span>
            {isComplete ? "Completed" : `${daysRemaining} days remaining`}
          </span>
          <span>{formatDate(contract.period_of_performance_end)}</span>
        </div>
        <div className="h-4 bg-gray-100 rounded-full overflow-hidden relative">
          <div
            className={`h-full rounded-full transition-all ${
              isComplete ? "bg-gray-400" : isActive ? "bg-green-500" : "bg-blue-500"
            }`}
            style={{ width: `${Math.min(progressPct, 100)}%` }}
          />
          {/* Milestone markers */}
          {milestones.map((m) => {
            const msPct =
              ((m.date.getTime() - start.getTime()) / totalMs) * 100;
            return (
              <div
                key={m.label}
                className="absolute top-0 bottom-0 w-0.5 bg-yellow-500"
                style={{ left: `${msPct}%` }}
                title={`${m.label}: ${formatDate(m.date.toISOString())}`}
              />
            );
          })}
        </div>
        {milestones.length > 0 && (
          <div className="flex gap-2 mt-1.5 flex-wrap">
            {milestones.map((m) => (
              <span key={m.label} className="text-xs flex items-center gap-1">
                <span className="w-2 h-2 bg-yellow-500 rounded-full inline-block" />
                {m.label} ({formatDate(m.date.toISOString())})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-xs text-muted-foreground">Total Duration</p>
          <p className="font-semibold">{totalDays} days</p>
          <p className="text-xs text-muted-foreground">({baseYears.toFixed(1)} years)</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">Progress</p>
          <p className="font-semibold">{progressPct.toFixed(0)}%</p>
          <p className="text-xs text-muted-foreground">elapsed</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">Option Years</p>
          <p className="font-semibold">{optionYears}</p>
          <p className="text-xs text-muted-foreground">available</p>
        </div>
      </div>
    </div>
  );
}

// ── Contract Health Score ────────────────────────────────────────────────────
function ContractHealthScore({ contract }: { contract: Contract }) {
  let score = 100;
  const issues: string[] = [];

  if (!contract.contracting_officer) { score -= 10; issues.push("No CO assigned"); }
  if (!contract.period_of_performance_start) { score -= 15; issues.push("No PoP start date"); }
  if (!contract.period_of_performance_end) { score -= 15; issues.push("No PoP end date"); }
  if (!contract.total_value) { score -= 10; issues.push("No contract value"); }
  if (contract.status === "expired" || contract.status === "terminated") { score -= 20; }

  const clampedScore = Math.max(0, score);
  const color =
    clampedScore >= 80 ? "text-green-600" : clampedScore >= 60 ? "text-yellow-600" : "text-red-600";
  const bgColor =
    clampedScore >= 80 ? "bg-green-50" : clampedScore >= 60 ? "bg-yellow-50" : "bg-red-50";

  return (
    <div className={`rounded-lg p-4 ${bgColor} flex items-start gap-4`}>
      <div className="text-center">
        <div className={`text-4xl font-bold ${color}`}>{clampedScore}</div>
        <div className="text-xs text-muted-foreground">Health Score</div>
      </div>
      <div className="flex-1">
        {issues.length === 0 ? (
          <div className="flex items-center gap-2 text-green-600 text-sm">
            <CheckCircle className="h-4 w-4" /> All contract data complete
          </div>
        ) : (
          <div className="space-y-1">
            {issues.map((issue) => (
              <div key={issue} className="flex items-center gap-2 text-sm text-yellow-700">
                <AlertTriangle className="h-3 w-3 flex-shrink-0" />
                {issue}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [contract, setContract] = useState<Contract | null>(null);
  const [versions, setVersions] = useState<ContractVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const c = await getContract(id);
      setContract(c);
      const vRes = await getContractVersions(id);
      setVersions(vRes.results);
    } catch {
      setError("Failed to load contract.");
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

  if (error || !contract) {
    return (
      <div className="p-6">
        <p className="text-red-600">{error || "Contract not found."}</p>
        <Button variant="outline" onClick={() => router.back()} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/contracts">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" /> Contracts
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold">{contract.title}</h1>
            <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${STATUS_COLORS[contract.status]}`}>
              {STATUS_LABELS[contract.status]}
            </span>
            <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700 font-medium">
              {CONTRACT_TYPE_LABELS[contract.contract_type] || contract.contract_type}
            </span>
          </div>
          {contract.contract_number && (
            <p className="text-muted-foreground mt-0.5">
              Contract #{contract.contract_number}
            </p>
          )}
        </div>
      </div>

      {/* Health Score */}
      <ContractHealthScore contract={contract} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <DollarSign className="h-4 w-4" />
              <span className="text-xs">Contract Value</span>
            </div>
            <div className="text-xl font-bold">{formatCurrency(contract.total_value)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">Award Date</span>
            </div>
            <div className="text-xl font-bold">{formatDate(contract.awarded_date)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Clock className="h-4 w-4" />
              <span className="text-xs">Pop End</span>
            </div>
            <div className="text-xl font-bold">{formatDate(contract.period_of_performance_end)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <GitBranch className="h-4 w-4" />
              <span className="text-xs">Option Years</span>
            </div>
            <div className="text-xl font-bold">{contract.option_years}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Period of Performance Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-4 w-4" /> Performance Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DeliverablesTimeline contract={contract} />
          </CardContent>
        </Card>

        {/* Key Personnel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4" /> Key Personnel
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-muted-foreground">Contracting Officer</span>
              <span className="font-medium text-sm">{contract.contracting_officer || "--"}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-muted-foreground">CO Email</span>
              <span className="text-sm">
                {contract.contracting_officer_email ? (
                  <a
                    href={`mailto:${contract.contracting_officer_email}`}
                    className="text-blue-600 hover:underline"
                  >
                    {contract.contracting_officer_email}
                  </a>
                ) : (
                  "--"
                )}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-sm text-muted-foreground">COR</span>
              <span className="font-medium text-sm">{contract.cor_name || "--"}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-muted-foreground">Executed Date</span>
              <span className="text-sm">{formatDate(contract.executed_date)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Version History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <GitBranch className="h-4 w-4" /> Modification History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {versions.length === 0 ? (
            <div className="flex items-center justify-center h-16 text-muted-foreground text-sm">
              No modifications recorded
            </div>
          ) : (
            <div className="space-y-2">
              <div className="grid grid-cols-4 gap-2 text-xs text-muted-foreground pb-2 border-b">
                <span>Version</span>
                <span>Change Type</span>
                <span>Effective Date</span>
                <span>Description</span>
              </div>
              {versions.map((v) => (
                <div key={v.id} className="grid grid-cols-4 gap-2 text-sm py-2 border-b last:border-0">
                  <span className="font-mono font-medium">v{v.version_number}</span>
                  <span className="text-muted-foreground">
                    {CHANGE_TYPE_LABELS[v.change_type] || v.change_type}
                  </span>
                  <span>{formatDate(v.effective_date)}</span>
                  <span className="text-muted-foreground truncate">{v.description || "--"}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Notes */}
      {contract.notes && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Info className="h-4 w-4" /> Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{contract.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
