"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getContracts,
  getContractClauses,
  createContract,
} from "@/services/contracts";
import { Contract, ContractClause, ContractType, ContractStatus } from "@/types/contract";
import { fetchAllDeals } from "@/services/analytics";
import { Deal } from "@/types/deal";
import {
  Loader2,
  Plus,
  Search,
  FileText,
  DollarSign,
  CheckCircle,
  AlertTriangle,
  X,
} from "lucide-react";

type ActiveTab = "contracts" | "clauses";

const CONTRACT_TYPE_LABELS: Record<ContractType, string> = {
  FFP: "Firm Fixed Price",
  "T&M": "Time & Materials",
  CPFF: "Cost Plus Fixed Fee",
  CPAF: "Cost Plus Award Fee",
  CPIF: "Cost Plus Incentive Fee",
  IDIQ: "IDIQ",
  BPA: "BPA",
};

const CONTRACT_TYPE_COLORS: Record<ContractType, string> = {
  FFP: "bg-blue-100 text-blue-700",
  "T&M": "bg-purple-100 text-purple-700",
  CPFF: "bg-orange-100 text-orange-700",
  CPAF: "bg-amber-100 text-amber-700",
  CPIF: "bg-yellow-100 text-yellow-700",
  IDIQ: "bg-cyan-100 text-cyan-700",
  BPA: "bg-teal-100 text-teal-700",
};

const STATUS_COLORS: Record<ContractStatus, string> = {
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

const STATUS_LABELS: Record<ContractStatus, string> = {
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

const CLAUSE_TYPE_LABELS: Record<string, string> = {
  standard: "Standard",
  special: "Special",
  custom: "Custom",
  far_reference: "FAR",
  dfars_reference: "DFARS",
};

const CLAUSE_SOURCE_COLORS: Record<string, string> = {
  FAR: "bg-blue-100 text-blue-700",
  DFARS: "bg-purple-100 text-purple-700",
  far_reference: "bg-blue-100 text-blue-700",
  dfars_reference: "bg-purple-100 text-purple-700",
  standard: "bg-gray-100 text-gray-700",
  special: "bg-yellow-100 text-yellow-700",
  custom: "bg-green-100 text-green-700",
};

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function isExpiringSoon(endDate: string | null): boolean {
  if (!endDate) return false;
  const end = new Date(endDate);
  const now = new Date();
  const diffMs = end.getTime() - now.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= 90;
}

// ── New Contract Modal ────────────────────────────────────────────────────

interface NewContractModalProps {
  onClose: () => void;
  onCreated: (contract: Contract) => void;
}

function NewContractModal({ onClose, onCreated }: NewContractModalProps) {
  const [title, setTitle] = useState("");
  const [contractNumber, setContractNumber] = useState("");
  const [contractType, setContractType] = useState<ContractType>("FFP");
  const [dealId, setDealId] = useState("");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allTypes: ContractType[] = ["FFP", "T&M", "CPFF", "CPAF", "CPIF", "IDIQ", "BPA"];

  useEffect(() => {
    fetchAllDeals()
      .then((d) => setDeals(d))
      .catch(() => {})
      .finally(() => setDealsLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: Partial<Contract> = {
        title: title.trim(),
        contract_type: contractType,
      };
      if (contractNumber.trim()) payload.contract_number = contractNumber.trim();
      if (dealId) payload.deal = dealId;
      const contract = await createContract(payload);
      onCreated(contract);
    } catch {
      setError("Failed to create contract. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background shadow-lg">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">New Contract</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Title <span className="text-red-500">*</span></label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. CIO-SP4 Task Order 001" autoFocus />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Contract Number</label>
            <Input value={contractNumber} onChange={(e) => setContractNumber(e.target.value)} placeholder="e.g. GS-00T-24-001" />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Contract Type</label>
            <select value={contractType} onChange={(e) => setContractType(e.target.value as ContractType)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
              {allTypes.map((t) => <option key={t} value={t}>{CONTRACT_TYPE_LABELS[t]}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Deal (optional)</label>
            {dealsLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2"><Loader2 className="h-4 w-4 animate-spin" />Loading deals...</div>
            ) : (
              <select value={dealId} onChange={(e) => setDealId(e.target.value)} className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                <option value="">No deal selected</option>
                {deals.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
              </select>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : "Create Contract"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function ContractsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("contracts");
  const [showNewModal, setShowNewModal] = useState(false);

  // Data state
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [clauses, setClauses] = useState<ContractClause[]>([]);

  // UI state
  const [loading, setLoading] = useState(true);
  const [clausesLoading, setClausesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<ContractType | "">("");
  const [statusFilter, setStatusFilter] = useState<ContractStatus | "">("");

  const fetchContracts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (typeFilter) params.contract_type = typeFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await getContracts(params);
      setContracts(data.results || []);
    } catch (err) {
      setError("Failed to load contracts. Please try again.");
      console.error("Error fetching contracts:", err);
    } finally {
      setLoading(false);
    }
  }, [search, typeFilter, statusFilter]);

  const fetchClauses = useCallback(async () => {
    setClausesLoading(true);
    try {
      const data = await getContractClauses();
      setClauses(data.results || []);
    } catch (err) {
      console.error("Error fetching clauses:", err);
    } finally {
      setClausesLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContracts();
  }, [fetchContracts]);

  useEffect(() => {
    if (activeTab === "clauses") {
      fetchClauses();
    }
  }, [activeTab, fetchClauses]);

  // Summary statistics
  const activeContracts = contracts.filter((c) => c.status === "active");
  const totalValue = contracts.reduce(
    (sum, c) => sum + (c.total_value || 0),
    0
  );
  const expiringSoonCount = contracts.filter((c) =>
    isExpiringSoon(c.period_of_performance_end)
  ).length;

  const uniqueTypes = Array.from(
    new Set(contracts.map((c) => c.contract_type).filter(Boolean))
  ).sort() as ContractType[];

  const uniqueStatuses = Array.from(
    new Set(contracts.map((c) => c.status).filter(Boolean))
  ).sort() as ContractStatus[];

  const tabs: { key: ActiveTab; label: string }[] = [
    { key: "contracts", label: "Contracts" },
    { key: "clauses", label: "Clause Library" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Contract Management
          </h1>
          <p className="text-muted-foreground">
            Track contracts, templates, and clause library
          </p>
        </div>
        <Button onClick={() => setShowNewModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Contract
        </Button>
      </div>

      {showNewModal && (
        <NewContractModal
          onClose={() => setShowNewModal(false)}
          onCreated={(contract) => {
            setContracts((prev) => [contract, ...prev]);
            setShowNewModal(false);
          }}
        />
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Total Contracts Value
                </p>
                <p className="text-2xl font-bold">
                  {formatCurrency(totalValue)}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {contracts.length} total contracts
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Active Contracts
                </p>
                <p className="text-2xl font-bold">{activeContracts.length}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Currently performing
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Expiring Soon</p>
                <p
                  className={`text-2xl font-bold ${expiringSoonCount > 0 ? "text-yellow-600" : ""}`}
                >
                  {expiringSoonCount}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Within 90 days
                </p>
              </div>
              <AlertTriangle
                className={`h-8 w-8 ${expiringSoonCount > 0 ? "text-yellow-500" : "text-muted-foreground"}`}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:border-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Contracts Tab */}
      {activeTab === "contracts" && (
        <>
          {/* Filter Bar */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by contract number or title..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <select
                  value={typeFilter}
                  onChange={(e) =>
                    setTypeFilter(e.target.value as ContractType | "")
                  }
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
                >
                  <option value="">All Types</option>
                  {uniqueTypes.map((type) => (
                    <option key={type} value={type}>
                      {CONTRACT_TYPE_LABELS[type] || type}
                    </option>
                  ))}
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) =>
                    setStatusFilter(e.target.value as ContractStatus | "")
                  }
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
                >
                  <option value="">All Statuses</option>
                  {uniqueStatuses.map((status) => (
                    <option key={status} value={status}>
                      {STATUS_LABELS[status] || status}
                    </option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Contracts Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Contracts
                {!loading && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({contracts.length} results)
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="ml-3 text-muted-foreground">
                    Loading contracts...
                  </span>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <p className="text-red-600 mb-4">{error}</p>
                  <Button variant="outline" onClick={fetchContracts}>
                    Retry
                  </Button>
                </div>
              ) : contracts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <FileText className="h-10 w-10 text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">
                    No contracts found matching your filters.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">
                          Contract #
                        </th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">
                          Title
                        </th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">
                          Type
                        </th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">
                          Status
                        </th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">
                          Total Value
                        </th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">
                          Period of Performance
                        </th>
                        <th className="pb-3 font-medium text-muted-foreground">
                          Contracting Officer
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {contracts.map((contract) => {
                        const expiring = isExpiringSoon(
                          contract.period_of_performance_end
                        );
                        return (
                          <tr
                            key={contract.id}
                            className="border-b cursor-pointer transition-colors hover:bg-muted/50"
                          >
                            <td className="py-3 pr-4">
                              <span className="font-mono text-xs font-medium">
                                {contract.contract_number || "--"}
                              </span>
                            </td>
                            <td className="py-3 pr-4">
                              <div className="max-w-[200px]">
                                <span className="font-medium line-clamp-2">
                                  {contract.title || "--"}
                                </span>
                                {contract.deal_name && (
                                  <span className="text-xs text-muted-foreground block">
                                    {contract.deal_name}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 pr-4">
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                  CONTRACT_TYPE_COLORS[contract.contract_type] ||
                                  "bg-gray-100 text-gray-700"
                                }`}
                              >
                                {contract.contract_type || "--"}
                              </span>
                            </td>
                            <td className="py-3 pr-4">
                              <span
                                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                  STATUS_COLORS[contract.status] ||
                                  "bg-gray-100 text-gray-700"
                                }`}
                              >
                                {STATUS_LABELS[contract.status] ||
                                  contract.status}
                              </span>
                            </td>
                            <td className="py-3 pr-4 font-medium">
                              {formatCurrency(contract.total_value)}
                            </td>
                            <td className="py-3 pr-4">
                              <div className="text-xs">
                                <span className="text-muted-foreground">
                                  {formatDate(
                                    contract.period_of_performance_start
                                  )}
                                </span>
                                <span className="text-muted-foreground mx-1">
                                  –
                                </span>
                                <span
                                  className={
                                    expiring
                                      ? "text-yellow-600 font-medium"
                                      : "text-muted-foreground"
                                  }
                                >
                                  {formatDate(
                                    contract.period_of_performance_end
                                  )}
                                </span>
                                {expiring && (
                                  <span className="ml-1 inline-flex items-center rounded-full bg-yellow-100 px-1.5 py-0.5 text-xs font-medium text-yellow-700">
                                    Expiring
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 text-muted-foreground text-xs">
                              {contract.contracting_officer || "--"}
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
        </>
      )}

      {/* Clause Library Tab */}
      {activeTab === "clauses" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Clause Library
              {!clausesLoading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({clauses.length} clauses)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {clausesLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-3 text-muted-foreground">
                  Loading clauses...
                </span>
              </div>
            ) : clauses.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <FileText className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">
                  No clauses found in the library.
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
                        Source / Type
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Risk
                      </th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">
                        Mandatory
                      </th>
                      <th className="pb-3 font-medium text-muted-foreground">
                        Negotiable
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {clauses.map((clause) => {
                      const sourceKey =
                        clause.source || clause.clause_type || "";
                      const isMandatory =
                        clause.is_mandatory !== undefined
                          ? clause.is_mandatory
                          : !clause.is_negotiable;
                      return (
                        <tr
                          key={clause.id}
                          className="border-b transition-colors hover:bg-muted/50"
                        >
                          <td className="py-3 pr-4">
                            <span className="font-mono text-xs font-medium">
                              {clause.clause_number || "--"}
                            </span>
                          </td>
                          <td className="py-3 pr-4">
                            <div className="max-w-[300px]">
                              <span className="font-medium line-clamp-2">
                                {clause.title || "--"}
                              </span>
                              {clause.category && (
                                <span className="text-xs text-muted-foreground block">
                                  {clause.category}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 pr-4">
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                CLAUSE_SOURCE_COLORS[sourceKey] ||
                                "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {clause.source ||
                                CLAUSE_TYPE_LABELS[clause.clause_type] ||
                                clause.clause_type}
                            </span>
                          </td>
                          <td className="py-3 pr-4">
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                RISK_COLORS[clause.risk_level] ||
                                "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {clause.risk_level
                                ? clause.risk_level.charAt(0).toUpperCase() +
                                  clause.risk_level.slice(1)
                                : "--"}
                            </span>
                          </td>
                          <td className="py-3 pr-4">
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                isMandatory
                                  ? "bg-red-100 text-red-700"
                                  : "bg-gray-100 text-gray-500"
                              }`}
                            >
                              {isMandatory ? "Mandatory" : "Optional"}
                            </span>
                          </td>
                          <td className="py-3">
                            <span
                              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                clause.is_negotiable
                                  ? "bg-green-100 text-green-700"
                                  : "bg-gray-100 text-gray-500"
                              }`}
                            >
                              {clause.is_negotiable ? "Yes" : "No"}
                            </span>
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
    </div>
  );
}
