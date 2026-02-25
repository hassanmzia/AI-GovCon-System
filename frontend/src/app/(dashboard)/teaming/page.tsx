"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getPartnerships, createPartnership } from "@/services/teaming";
import { TeamingPartnership, AgreementStatus, PartnershipType } from "@/types/teaming";
import { fetchAllDeals } from "@/services/analytics";
import { Deal } from "@/types/deal";
import {
  Users,
  Loader2,
  RefreshCw,
  FileSignature,
  Briefcase,
  BarChart3,
  PlusCircle,
  LayoutList,
  LayoutGrid,
  X,
} from "lucide-react";

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

function getPartnerName(p: TeamingPartnership): string {
  return p.partner_name || p.partner_company || "--";
}

function getAgreementStatus(p: TeamingPartnership): AgreementStatus {
  return (p.agreement_status || p.status || "identifying") as AgreementStatus;
}

function getPartnershipType(p: TeamingPartnership): PartnershipType {
  return (p.partnership_type || p.relationship_type || "teaming_agreement") as PartnershipType;
}

function getWorkShare(p: TeamingPartnership): number | null {
  return p.work_share_percentage ?? p.revenue_share_percentage ?? null;
}

// ---------- Agreement Status Badge ----------

const agreementStatusConfig: Record<
  string,
  { label: string; cls: string }
> = {
  identifying: { label: "Identifying", cls: "bg-gray-100 text-gray-700" },
  evaluating: { label: "Evaluating", cls: "bg-blue-100 text-blue-700" },
  negotiating: { label: "Negotiating", cls: "bg-yellow-100 text-yellow-800" },
  signed: { label: "Signed", cls: "bg-teal-100 text-teal-800" },
  active: { label: "Active", cls: "bg-green-100 text-green-800" },
  inactive: { label: "Inactive", cls: "bg-gray-100 text-gray-500" },
  prospect: { label: "Prospect", cls: "bg-blue-100 text-blue-700" },
  completed: { label: "Completed", cls: "bg-green-100 text-green-800" },
  terminated: { label: "Terminated", cls: "bg-red-100 text-red-800" },
};

function AgreementStatusBadge({ status }: { status: string }) {
  const cfg = agreementStatusConfig[status] ?? {
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

// ---------- Partnership Type Badge ----------

const partnershipTypeConfig: Record<string, { label: string; cls: string }> = {
  prime: { label: "Prime", cls: "bg-purple-100 text-purple-800" },
  prime_contractor: { label: "Prime Contractor", cls: "bg-purple-100 text-purple-800" },
  subcontractor: { label: "Subcontractor", cls: "bg-blue-100 text-blue-800" },
  joint_venture: { label: "Joint Venture", cls: "bg-green-100 text-green-800" },
  mentor_protege: { label: "Mentor-Protege", cls: "bg-orange-100 text-orange-800" },
  mentor: { label: "Mentor", cls: "bg-orange-100 text-orange-800" },
  protege: { label: "Protege", cls: "bg-amber-100 text-amber-800" },
  teaming_agreement: {
    label: "Teaming Agreement",
    cls: "bg-indigo-100 text-indigo-800",
  },
  strategic_partner: {
    label: "Strategic Partner",
    cls: "bg-cyan-100 text-cyan-800",
  },
};

function PartnershipTypeBadge({ type }: { type: string }) {
  const cfg = partnershipTypeConfig[type] ?? {
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

// ---------- Work Share Progress Bar ----------

function WorkShareBar({ percentage }: { percentage: number | null }) {
  if (percentage === null || percentage === undefined) {
    return <span className="text-muted-foreground text-xs">--</span>;
  }
  const pct = Math.min(Math.max(percentage, 0), 100);
  return (
    <div className="flex items-center gap-2 min-w-[100px]">
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium w-10 text-right">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

// ---------- Summary KPI Cards ----------

function SummaryCards({ partnerships }: { partnerships: TeamingPartnership[] }) {
  const total = partnerships.length;
  const signed = partnerships.filter((p) => {
    const s = getAgreementStatus(p);
    return s === "signed" || s === "active" || p.signed_agreement === true;
  }).length;
  const active = partnerships.filter((p) => getAgreementStatus(p) === "active").length;

  const workShares = partnerships
    .map((p) => getWorkShare(p))
    .filter((v): v is number => v !== null && v !== undefined);
  const avgWorkShare =
    workShares.length > 0
      ? workShares.reduce((a, b) => a + b, 0) / workShares.length
      : null;

  const kpis = [
    {
      label: "Total Partners",
      value: total.toString(),
      icon: <Users className="h-5 w-5 text-muted-foreground" />,
    },
    {
      label: "Signed Agreements",
      value: signed.toString(),
      icon: <FileSignature className="h-5 w-5 text-teal-600" />,
    },
    {
      label: "Active Partnerships",
      value: active.toString(),
      icon: <Briefcase className="h-5 w-5 text-green-600" />,
    },
    {
      label: "Avg Work Share",
      value: avgWorkShare !== null ? `${avgWorkShare.toFixed(1)}%` : "--",
      icon: <BarChart3 className="h-5 w-5 text-blue-600" />,
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
                <p className="text-2xl font-bold mt-1">{kpi.value}</p>
              </div>
              {kpi.icon}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ---------- Partnerships Table ----------

function PartnershipsTable({
  partnerships,
  loading,
}: {
  partnerships: TeamingPartnership[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading partnerships...</span>
      </div>
    );
  }

  if (partnerships.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Users className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground font-medium mb-2">
          No partnerships yet
        </p>
        <p className="text-sm text-muted-foreground text-center max-w-sm">
          Start building your teaming network by adding partners to your deals.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Partner</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Deal</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Role</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Type</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Status</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Work Share</th>
            <th className="pb-3 font-medium text-muted-foreground">Agreement Date</th>
          </tr>
        </thead>
        <tbody>
          {partnerships.map((p) => (
            <tr
              key={p.id}
              className="border-b transition-colors hover:bg-muted/50"
            >
              <td className="py-3 pr-4 font-medium">
                {truncate(getPartnerName(p), 35)}
                {p.partner_uei && (
                  <div className="text-xs text-muted-foreground font-mono">
                    {p.partner_uei}
                  </div>
                )}
              </td>
              <td className="py-3 pr-4 text-muted-foreground">
                {truncate(getDealName(p.deal) !== "--" ? getDealName(p.deal) : p.deal_name, 35)}
              </td>
              <td className="py-3 pr-4 text-muted-foreground">
                {truncate(p.role || p.description, 30)}
              </td>
              <td className="py-3 pr-4">
                <PartnershipTypeBadge type={getPartnershipType(p)} />
              </td>
              <td className="py-3 pr-4">
                <AgreementStatusBadge status={getAgreementStatus(p)} />
              </td>
              <td className="py-3 pr-4">
                <WorkShareBar percentage={getWorkShare(p)} />
              </td>
              <td className="py-3 text-muted-foreground">
                {formatDate(p.agreement_date)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------- Group By Deal View ----------

function GroupedByDeal({
  partnerships,
  loading,
}: {
  partnerships: TeamingPartnership[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading partnerships...</span>
      </div>
    );
  }

  if (partnerships.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Users className="h-12 w-12 text-muted-foreground mb-3" />
        <p className="text-muted-foreground">No partnerships found.</p>
      </div>
    );
  }

  // Group by deal
  const groups: Record<string, TeamingPartnership[]> = {};
  partnerships.forEach((p) => {
    const dealName = getDealName(p.deal) !== "--" ? getDealName(p.deal) : (p.deal_name ?? "Unknown Deal");
    if (!groups[dealName]) groups[dealName] = [];
    groups[dealName].push(p);
  });

  return (
    <div className="space-y-6">
      {Object.entries(groups).map(([dealName, partners]) => (
        <div key={dealName}>
          <h3 className="font-semibold text-base mb-3 flex items-center gap-2">
            <Briefcase className="h-4 w-4 text-muted-foreground" />
            {dealName}
            <span className="text-sm font-normal text-muted-foreground">
              ({partners.length} partner{partners.length !== 1 ? "s" : ""})
            </span>
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {partners.map((p) => (
              <Card key={p.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-4">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-sm leading-tight">
                        {truncate(getPartnerName(p), 30)}
                      </p>
                      <PartnershipTypeBadge type={getPartnershipType(p)} />
                    </div>
                    {p.role && (
                      <p className="text-xs text-muted-foreground">
                        {truncate(p.role, 50)}
                      </p>
                    )}
                    <div className="flex items-center justify-between">
                      <AgreementStatusBadge status={getAgreementStatus(p)} />
                      {getWorkShare(p) !== null && (
                        <span className="text-xs text-muted-foreground">
                          {getWorkShare(p)!.toFixed(0)}% share
                        </span>
                      )}
                    </div>
                    {getWorkShare(p) !== null && (
                      <WorkShareBar percentage={getWorkShare(p)} />
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------- Add Partner Modal ----------

interface AddPartnerModalProps {
  onClose: () => void;
  onCreated: (partnership: TeamingPartnership) => void;
}

function AddPartnerModal({ onClose, onCreated }: AddPartnerModalProps) {
  const [partnerCompany, setPartnerCompany] = useState("");
  const [relationshipType, setRelationshipType] = useState("subcontractor");
  const [dealId, setDealId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const relationshipTypes = [
    { value: "prime_contractor", label: "Prime Contractor" },
    { value: "subcontractor", label: "Subcontractor" },
    { value: "joint_venture", label: "Joint Venture" },
    { value: "mentor", label: "Mentor" },
    { value: "protege", label: "Protege" },
    { value: "strategic_partner", label: "Strategic Partner" },
  ];

  useEffect(() => {
    fetchAllDeals()
      .then((d) => setDeals(d))
      .catch(() => {})
      .finally(() => setDealsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!partnerCompany.trim() || !dealId) {
      setError("Partner company and deal are required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const partnership = await createPartnership({
        partner_company: partnerCompany.trim(),
        relationship_type: relationshipType as TeamingPartnership["relationship_type"],
        deal: dealId,
      });
      onCreated(partnership);
    } catch {
      setError("Failed to add partner. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Add Teaming Partner</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Partner Company <span className="text-red-500">*</span></label>
            <Input value={partnerCompany} onChange={(e) => setPartnerCompany(e.target.value)} placeholder="e.g. Acme Defense Solutions" autoFocus />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Relationship Type</label>
            <select value={relationshipType} onChange={(e) => setRelationshipType(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              {relationshipTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Deal <span className="text-red-500">*</span></label>
            {dealsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2"><Loader2 className="h-4 w-4 animate-spin" />Loading deals...</div>
            ) : (
              <select value={dealId} onChange={(e) => setDealId(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                <option value="">Select a deal...</option>
                {deals.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
              </select>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
            <Button type="submit" disabled={submitting || dealsLoading}>
              {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Adding...</> : "Add Partner"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------- Main Page ----------

export default function TeamingPage() {
  const [partnerships, setPartnerships] = useState<TeamingPartnership[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [groupByDeal, setGroupByDeal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  const fetchPartnerships = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPartnerships();
      setPartnerships(data.results || []);
    } catch (err) {
      setError("Failed to load partnerships. Please try again.");
      console.error("Error fetching partnerships:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPartnerships();
  }, [fetchPartnerships]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Teaming &amp; Partnerships
          </h1>
          <p className="text-muted-foreground">
            Manage teaming partners and track agreement status
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchPartnerships} disabled={loading}>
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
          <Button onClick={() => setShowAddModal(true)}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Partner
          </Button>
        </div>
      </div>

      {showAddModal && (
        <AddPartnerModal
          onClose={() => setShowAddModal(false)}
          onCreated={(partnership) => {
            setPartnerships((prev) => [partnership, ...prev]);
            setShowAddModal(false);
          }}
        />
      )}

      {/* Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6 flex items-center justify-between">
            <p className="text-red-700">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchPartnerships}>
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <SummaryCards partnerships={partnerships} />

      {/* Partnerships Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">
              Partnerships
              {!loading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({partnerships.length} results)
                </span>
              )}
            </CardTitle>
            <div className="flex items-center gap-1 rounded-md border p-1">
              <button
                onClick={() => setGroupByDeal(false)}
                className={`p-1.5 rounded transition-colors ${
                  !groupByDeal
                    ? "bg-background shadow text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Table view"
              >
                <LayoutList className="h-4 w-4" />
              </button>
              <button
                onClick={() => setGroupByDeal(true)}
                className={`p-1.5 rounded transition-colors ${
                  groupByDeal
                    ? "bg-background shadow text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                title="Group by deal"
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {groupByDeal ? (
            <GroupedByDeal partnerships={partnerships} loading={loading} />
          ) : (
            <PartnershipsTable partnerships={partnerships} loading={loading} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
