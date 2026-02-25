"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getPastPerformanceRecords,
  createPastPerformanceRecord,
  deletePastPerformanceRecord,
} from "@/services/past-performance";
import {
  PastPerformance,
  ContractType,
  PerformanceRating,
  CreatePastPerformancePayload,
} from "@/types/past-performance";
import {
  Search,
  PlusCircle,
  Loader2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Star,
  Trash2,
  ChevronDown,
  ChevronUp,
  Building2,
  Calendar,
  DollarSign,
  Tag,
} from "lucide-react";

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

function formatCurrency(value: string | null): string {
  if (!value) return "--";
  const n = parseFloat(value);
  if (isNaN(n)) return "--";
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

const RATING_COLORS: Record<string, string> = {
  Exceptional: "text-green-700 bg-green-100",
  "Very Good": "text-blue-700 bg-blue-100",
  Satisfactory: "text-yellow-700 bg-yellow-100",
  Marginal: "text-orange-700 bg-orange-100",
  Unsatisfactory: "text-red-700 bg-red-100",
};

function RatingBadge({ rating }: { rating: string }) {
  if (!rating) return <span className="text-xs text-muted-foreground">--</span>;
  const cls = RATING_COLORS[rating] ?? "text-muted-foreground bg-secondary";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      <Star className="h-3 w-3" />
      {rating}
    </span>
  );
}

// ── Record card ─────────────────────────────────────────────────────────────

function RecordCard({
  record,
  onDelete,
}: {
  record: PastPerformance;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Delete "${record.project_name}"?`)) return;
    setDeleting(true);
    try {
      await deletePastPerformanceRecord(record.id);
      onDelete(record.id);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="pt-5">
        {/* Top row */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-semibold text-foreground">
                {record.project_name}
              </h3>
              {record.contract_type && (
                <span className="rounded bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground">
                  {record.contract_type}
                </span>
              )}
              {!record.is_active && (
                <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-600">
                  Inactive
                </span>
              )}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                {record.client_agency}
              </span>
              {(record.start_date || record.end_date) && (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(record.start_date)} – {formatDate(record.end_date)}
                </span>
              )}
              {record.contract_value && (
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatCurrency(record.contract_value)}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <RatingBadge rating={record.performance_rating} />
            <Button
              size="sm"
              variant="ghost"
              onClick={handleDelete}
              disabled={deleting}
              className="text-destructive hover:bg-destructive/10"
            >
              {deleting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="h-3.5 w-3.5" />
              )}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setExpanded((v) => !v)}
            >
              {expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Description */}
        <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
          {record.description}
        </p>

        {/* Badges row */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className="flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs text-muted-foreground">
            {record.on_time_delivery ? (
              <CheckCircle className="h-3 w-3 text-green-500" />
            ) : (
              <XCircle className="h-3 w-3 text-red-500" />
            )}
            On Time
          </span>
          <span className="flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs text-muted-foreground">
            {record.within_budget ? (
              <CheckCircle className="h-3 w-3 text-green-500" />
            ) : (
              <XCircle className="h-3 w-3 text-red-500" />
            )}
            On Budget
          </span>
          {record.domains.slice(0, 3).map((d) => (
            <span
              key={d}
              className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
            >
              {d}
            </span>
          ))}
          {record.technologies.slice(0, 2).map((t) => (
            <span
              key={t}
              className="rounded-full bg-secondary px-2 py-0.5 text-xs text-muted-foreground"
            >
              {t}
            </span>
          ))}
        </div>

        {/* Expanded detail */}
        {expanded && (
          <div className="mt-4 space-y-4 border-t pt-4">
            {record.key_achievements.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Key Achievements
                </p>
                <ul className="space-y-1">
                  {record.key_achievements.map((a, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-green-500" />
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {record.narrative && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Narrative
                </p>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {record.narrative}
                </p>
              </div>
            )}

            {Object.keys(record.metrics).length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Metrics
                </p>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(record.metrics).map(([k, v]) => (
                    <div key={k} className="rounded-lg border bg-secondary/30 px-3 py-2 text-center">
                      <p className="text-sm font-bold text-foreground">{String(v)}</p>
                      <p className="text-xs text-muted-foreground">{k}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {record.cpars_rating && (
              <p className="text-xs text-muted-foreground">
                CPARS Rating: <strong>{record.cpars_rating}</strong>
              </p>
            )}

            {record.client_name && (
              <p className="text-xs text-muted-foreground">
                Contact: {record.client_name}
                {record.client_email && ` · ${record.client_email}`}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Add record form ────────────────────────────────────────────────────────

const EMPTY_FORM: CreatePastPerformancePayload = {
  project_name: "",
  contract_number: "",
  client_agency: "",
  client_name: "",
  description: "",
  contract_type: "",
  performance_rating: "",
  contract_value: "",
  start_date: "",
  end_date: "",
  on_time_delivery: true,
  within_budget: true,
  narrative: "",
  domains: [],
  technologies: [],
  key_achievements: [],
};

function AddRecordForm({
  onAdd,
  onCancel,
}: {
  onAdd: (r: PastPerformance) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<CreatePastPerformancePayload>(EMPTY_FORM);
  const [achievementInput, setAchievementInput] = useState("");
  const [domainInput, setDomainInput] = useState("");
  const [techInput, setTechInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const set = (k: keyof CreatePastPerformancePayload, v: unknown) =>
    setForm((prev) => ({ ...prev, [k]: v }));

  const addListItem = (
    field: "key_achievements" | "domains" | "technologies",
    value: string,
    clear: () => void
  ) => {
    if (!value.trim()) return;
    setForm((prev) => ({
      ...prev,
      [field]: [...(prev[field] as string[]), value.trim()],
    }));
    clear();
  };

  const removeListItem = (
    field: "key_achievements" | "domains" | "technologies",
    idx: number
  ) =>
    setForm((prev) => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((_, i) => i !== idx),
    }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.project_name.trim() || !form.client_agency.trim() || !form.description.trim()) {
      setErr("Project name, client agency, and description are required.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      const record = await createPastPerformanceRecord(form);
      onAdd(record);
    } catch {
      setErr("Failed to create record. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const labelCls = "block text-xs font-medium text-muted-foreground mb-1";
  const inputCls =
    "w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Add Past Performance Record</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={labelCls}>Project Name *</label>
              <Input
                value={form.project_name}
                onChange={(e) => set("project_name", e.target.value)}
                placeholder="e.g. DoD ERP Modernization"
              />
            </div>
            <div>
              <label className={labelCls}>Contract Number</label>
              <Input
                value={form.contract_number}
                onChange={(e) => set("contract_number", e.target.value)}
                placeholder="e.g. W15P7T-22-C-0001"
              />
            </div>
            <div>
              <label className={labelCls}>Client Agency *</label>
              <Input
                value={form.client_agency}
                onChange={(e) => set("client_agency", e.target.value)}
                placeholder="e.g. U.S. Army"
              />
            </div>
            <div>
              <label className={labelCls}>Client Contact Name</label>
              <Input
                value={form.client_name}
                onChange={(e) => set("client_name", e.target.value)}
                placeholder="COR / COTR name"
              />
            </div>
            <div>
              <label className={labelCls}>Contract Value ($)</label>
              <Input
                type="number"
                value={form.contract_value}
                onChange={(e) => set("contract_value", e.target.value)}
                placeholder="e.g. 4500000"
              />
            </div>
            <div>
              <label className={labelCls}>Contract Type</label>
              <select
                className={inputCls}
                value={form.contract_type}
                onChange={(e) => set("contract_type", e.target.value as ContractType)}
              >
                <option value="">-- Select --</option>
                {["FFP", "T&M", "CPFF", "CPAF", "IDIQ", "BPA"].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Start Date</label>
              <input
                type="date"
                className={inputCls}
                value={form.start_date}
                onChange={(e) => set("start_date", e.target.value)}
              />
            </div>
            <div>
              <label className={labelCls}>End Date</label>
              <input
                type="date"
                className={inputCls}
                value={form.end_date}
                onChange={(e) => set("end_date", e.target.value)}
              />
            </div>
            <div>
              <label className={labelCls}>Performance Rating</label>
              <select
                className={inputCls}
                value={form.performance_rating}
                onChange={(e) => set("performance_rating", e.target.value as PerformanceRating)}
              >
                <option value="">-- Select --</option>
                {["Exceptional", "Very Good", "Satisfactory", "Marginal", "Unsatisfactory"].map(
                  (r) => <option key={r} value={r}>{r}</option>
                )}
              </select>
            </div>
            <div className="flex items-center gap-6 pt-5">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.on_time_delivery}
                  onChange={(e) => set("on_time_delivery", e.target.checked)}
                  className="h-4 w-4"
                />
                On-time delivery
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.within_budget}
                  onChange={(e) => set("within_budget", e.target.checked)}
                  className="h-4 w-4"
                />
                Within budget
              </label>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className={labelCls}>Description *</label>
            <textarea
              className={`${inputCls} min-h-[80px] resize-y`}
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="Describe the project scope, objectives, and your role..."
            />
          </div>

          {/* Narrative */}
          <div>
            <label className={labelCls}>Proposal Narrative (pre-written)</label>
            <textarea
              className={`${inputCls} min-h-[80px] resize-y`}
              value={form.narrative}
              onChange={(e) => set("narrative", e.target.value)}
              placeholder="Ready-to-use narrative for proposal past performance volumes..."
            />
          </div>

          {/* Domains */}
          <div>
            <label className={labelCls}>Domains</label>
            <div className="flex gap-2">
              <Input
                value={domainInput}
                onChange={(e) => setDomainInput(e.target.value)}
                placeholder="e.g. Cloud, AI/ML, Cyber"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addListItem("domains", domainInput, () => setDomainInput(""));
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => addListItem("domains", domainInput, () => setDomainInput(""))}
              >
                Add
              </Button>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(form.domains as string[]).map((d, i) => (
                <span
                  key={i}
                  className="flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                >
                  {d}
                  <button
                    type="button"
                    onClick={() => removeListItem("domains", i)}
                    className="hover:text-destructive"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Key achievements */}
          <div>
            <label className={labelCls}>Key Achievements</label>
            <div className="flex gap-2">
              <Input
                value={achievementInput}
                onChange={(e) => setAchievementInput(e.target.value)}
                placeholder="e.g. Delivered 20% under budget"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addListItem("key_achievements", achievementInput, () =>
                      setAchievementInput("")
                    );
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  addListItem("key_achievements", achievementInput, () =>
                    setAchievementInput("")
                  )
                }
              >
                Add
              </Button>
            </div>
            <ul className="mt-2 space-y-1">
              {(form.key_achievements as string[]).map((a, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CheckCircle className="h-3.5 w-3.5 text-green-500 shrink-0" />
                  <span className="flex-1">{a}</span>
                  <button
                    type="button"
                    onClick={() => removeListItem("key_achievements", i)}
                    className="text-destructive hover:opacity-80"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {err && <p className="text-sm text-red-600">{err}</p>}

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Record"
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function PastPerformancePage() {
  const [records, setRecords] = useState<PastPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");
  const [ratingFilter, setRatingFilter] = useState("");
  const [domainFilter, setDomainFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (agencyFilter) params.client_agency = agencyFilter;
      if (ratingFilter) params.performance_rating = ratingFilter;
      const data = await getPastPerformanceRecords(params);
      setRecords(data.results ?? []);
    } catch {
      setError("Failed to load past performance records.");
    } finally {
      setLoading(false);
    }
  }, [search, agencyFilter, ratingFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = (record: PastPerformance) => {
    setRecords((prev) => [record, ...prev]);
    setShowForm(false);
  };

  const handleDelete = (id: string) => {
    setRecords((prev) => prev.filter((r) => r.id !== id));
  };

  // Client-side domain filter (not a server param in this example)
  const filtered = domainFilter
    ? records.filter((r) => r.domains.some((d) => d.toLowerCase().includes(domainFilter.toLowerCase())))
    : records;

  const uniqueAgencies = Array.from(new Set(records.map((r) => r.client_agency).filter(Boolean))).sort();
  const allDomains = Array.from(new Set(records.flatMap((r) => r.domains))).sort();

  // Summary stats
  const totalValue = records.reduce((s, r) => {
    const v = parseFloat(r.contract_value ?? "0");
    return s + (isNaN(v) ? 0 : v);
  }, 0);
  const exceptional = records.filter((r) => r.performance_rating === "Exceptional").length;
  const onTime = records.filter((r) => r.on_time_delivery).length;

  function formatCurrencyNum(n: number) {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(0)}M`;
    if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Past Performance</h1>
          <p className="text-muted-foreground">
            Manage and search your contract history for proposals
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setShowForm(true)} disabled={showForm}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Record
          </Button>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Total Records", value: String(records.length) },
          {
            label: "Portfolio Value",
            value: records.length ? formatCurrencyNum(totalValue) : "--",
          },
          {
            label: "Exceptional",
            value: records.length ? `${exceptional} / ${records.length}` : "--",
          },
          {
            label: "On-Time Delivery",
            value: records.length
              ? `${Math.round((onTime / records.length) * 100)}%`
              : "--",
          },
        ].map(({ label, value }) => (
          <Card key={label}>
            <CardContent className="pt-5">
              <p className="text-2xl font-bold text-foreground">{value}</p>
              <p className="mt-1 text-xs text-muted-foreground">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Add form */}
      {showForm && (
        <AddRecordForm onAdd={handleAdd} onCancel={() => setShowForm(false)} />
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-5">
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[180px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search records..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={agencyFilter}
              onChange={(e) => setAgencyFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Agencies</option>
              {uniqueAgencies.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
            <select
              value={ratingFilter}
              onChange={(e) => setRatingFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Ratings</option>
              {["Exceptional", "Very Good", "Satisfactory", "Marginal", "Unsatisfactory"].map(
                (r) => <option key={r} value={r}>{r}</option>
              )}
            </select>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Domains</option>
              {allDomains.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Records list */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading records...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <p className="text-red-600">{error}</p>
          <Button variant="outline" onClick={load}>
            <RefreshCw className="mr-2 h-4 w-4" /> Retry
          </Button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <Tag className="h-10 w-10 text-muted-foreground" />
          <p className="text-muted-foreground">
            {records.length === 0
              ? "No past performance records yet. Add your first one!"
              : "No records match your filters."}
          </p>
          {records.length === 0 && (
            <Button onClick={() => setShowForm(true)}>
              <PlusCircle className="mr-2 h-4 w-4" />
              Add First Record
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-xs text-muted-foreground">
            {filtered.length} record{filtered.length !== 1 ? "s" : ""}
          </p>
          {filtered.map((record) => (
            <RecordCard key={record.id} record={record} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}
