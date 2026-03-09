"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Shield,
  ShieldCheck,
  Search,
  Plus,
  CheckCircle,
  Clock,
  AlertTriangle,
  Hash,
  ChevronDown,
  Building2,
  Users,
  DollarSign,
  Star,
  X,
  FileText,
  Loader2,
  Trash2,
} from "lucide-react";
import {
  type SBACertification,
  type CertStatus,
  type NAICSCode,
  getCertifications,
  initializeCertifications,
  updateCertification as apiUpdateCert,
  getNAICSCodes,
  createNAICSCode,
  deleteNAICSCode,
  setNAICSPrimary,
} from "@/services/sba-certifications";

// ── Constants ──────────────────────────────────────────────────────────────

const STATUS_OPTIONS: { value: CertStatus; label: string }[] = [
  { value: "not_applicable", label: "Not Applicable" },
  { value: "eligible", label: "Eligible" },
  { value: "in_progress", label: "In Progress" },
  { value: "applied", label: "Applied" },
  { value: "under_review", label: "Under Review" },
  { value: "certified", label: "Certified" },
  { value: "expired", label: "Expired" },
  { value: "denied", label: "Denied" },
];

const STATUS_STYLES: Record<CertStatus, string> = {
  not_applicable: "bg-gray-100 text-gray-600",
  eligible: "bg-blue-100 text-blue-700",
  in_progress: "bg-cyan-100 text-cyan-700",
  applied: "bg-yellow-100 text-yellow-700",
  under_review: "bg-orange-100 text-orange-700",
  certified: "bg-green-100 text-green-700",
  expired: "bg-red-100 text-red-700",
  denied: "bg-red-100 text-red-600",
};

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function isExpiringSoon(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const exp = new Date(dateStr);
  const now = new Date();
  const diffDays = (exp.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays > 0 && diffDays <= 180;
}

// ── Status Badge ───────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: CertStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status] || "bg-gray-100 text-gray-600"}`}
    >
      {status === "certified" && <ShieldCheck className="h-3 w-3" />}
      {(status === "applied" || status === "under_review" || status === "in_progress") && (
        <Clock className="h-3 w-3" />
      )}
      {status === "eligible" && <Star className="h-3 w-3" />}
      {(status === "expired" || status === "denied") && (
        <AlertTriangle className="h-3 w-3" />
      )}
      {STATUS_OPTIONS.find((o) => o.value === status)?.label || status}
    </span>
  );
}

// ── Certification Card ─────────────────────────────────────────────────────

function CertificationCard({
  cert,
  onUpdate,
}: {
  cert: SBACertification;
  onUpdate: (id: string, updates: Partial<SBACertification>) => void;
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [editingDates, setEditingDates] = useState(false);
  const [certNumber, setCertNumber] = useState(cert.certification_number);
  const [certDate, setCertDate] = useState(cert.certification_date || "");
  const [expDate, setExpDate] = useState(cert.expiration_date || "");
  const [notes, setNotes] = useState(cert.notes);

  const borderColor =
    cert.status === "certified"
      ? "border-l-green-500"
      : cert.status === "applied" || cert.status === "under_review" || cert.status === "in_progress"
        ? "border-l-yellow-500"
        : cert.status === "eligible"
          ? "border-l-blue-500"
          : cert.status === "expired" || cert.status === "denied"
            ? "border-l-red-500"
            : "border-l-gray-300";

  const saveDates = () => {
    onUpdate(cert.id, {
      certification_number: certNumber,
      certification_date: certDate || null,
      expiration_date: expDate || null,
      notes,
    });
    setEditingDates(false);
  };

  return (
    <Card className={`border-l-4 ${borderColor} relative`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="text-base font-semibold leading-tight">
              {cert.cert_type_display}
            </CardTitle>
            <p className="mt-0.5 text-xs font-medium text-muted-foreground">
              {cert.cert_type.toUpperCase()}
            </p>
          </div>
          <StatusBadge status={cert.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Status selector */}
        <div className="relative">
          <label className="mb-1 block text-xs font-medium text-muted-foreground">
            Status
          </label>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex w-full items-center justify-between rounded-md border border-border bg-background px-3 py-1.5 text-sm hover:bg-accent"
          >
            {STATUS_OPTIONS.find((o) => o.value === cert.status)?.label || cert.status}
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          {dropdownOpen && (
            <div className="absolute z-10 mt-1 w-full rounded-md border border-border bg-background shadow-lg">
              {STATUS_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    onUpdate(cert.id, { status: opt.value });
                    setDropdownOpen(false);
                  }}
                  className={`block w-full px-3 py-1.5 text-left text-sm hover:bg-accent ${
                    cert.status === opt.value ? "bg-accent font-medium" : ""
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details grid */}
        {!editingDates ? (
          <>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Cert Date</p>
                <p className="font-medium">{formatDate(cert.certification_date)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Expiration</p>
                <p
                  className={`font-medium ${
                    cert.expiration_date && isExpiringSoon(cert.expiration_date)
                      ? "text-amber-600"
                      : ""
                  }`}
                >
                  {formatDate(cert.expiration_date)}
                  {cert.expiration_date && isExpiringSoon(cert.expiration_date) && (
                    <AlertTriangle className="ml-1 inline h-3 w-3 text-amber-500" />
                  )}
                </p>
              </div>
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground">Cert Number</p>
                <p className="font-mono text-xs font-medium">
                  {cert.certification_number || "--"}
                </p>
              </div>
            </div>

            {cert.notes && (
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Notes</p>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {cert.notes}
                </p>
              </div>
            )}

            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs"
              onClick={() => setEditingDates(true)}
            >
              Edit Details
            </Button>
          </>
        ) : (
          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-foreground">Cert Number</label>
              <Input
                value={certNumber}
                onChange={(e) => setCertNumber(e.target.value)}
                placeholder="e.g. SB-2024-00487"
                className="h-8 text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-muted-foreground">Cert Date</label>
                <Input
                  type="date"
                  value={certDate}
                  onChange={(e) => setCertDate(e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Expiration</label>
                <Input
                  type="date"
                  value={expDate}
                  onChange={(e) => setExpDate(e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs min-h-[60px] resize-y"
                placeholder="Eligibility notes..."
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" className="flex-1 h-7 text-xs" onClick={saveDates}>
                Save
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="flex-1 h-7 text-xs"
                onClick={() => setEditingDates(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Add NAICS Modal ────────────────────────────────────────────────────────

function AddNAICSModal({
  onSave,
  onClose,
}: {
  onSave: (data: { code: string; title: string; size_standard: string; is_primary: boolean; qualifies_small: boolean }) => void;
  onClose: () => void;
}) {
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [sizeStandard, setSizeStandard] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [qualifiesSmall, setQualifiesSmall] = useState(true);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Add NAICS Code</CardTitle>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 p-4 sm:p-6">
          <div>
            <label className="text-xs font-medium text-muted-foreground">NAICS Code *</label>
            <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="e.g. 541512" />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">Title *</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Computer Systems Design Services" />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground">Size Standard</label>
            <Input value={sizeStandard} onChange={(e) => setSizeStandard(e.target.value)} placeholder="e.g. $34M or 1,000 employees" />
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={isPrimary} onChange={(e) => setIsPrimary(e.target.checked)} className="rounded" />
              Primary NAICS
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={qualifiesSmall} onChange={(e) => setQualifiesSmall(e.target.checked)} className="rounded" />
              Qualifies as Small
            </label>
          </div>
          <div className="flex gap-2 pt-2">
            <Button
              className="flex-1"
              disabled={!code.trim() || !title.trim()}
              onClick={() => onSave({ code, title, size_standard: sizeStandard, is_primary: isPrimary, qualifies_small: qualifiesSmall })}
            >
              Add Code
            </Button>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function SBACertificationsPage() {
  const [certifications, setCertifications] = useState<SBACertification[]>([]);
  const [naicsCodes, setNaicsCodes] = useState<NAICSCode[]>([]);
  const [naicsSearch, setNaicsSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddNaics, setShowAddNaics] = useState(false);

  // ── Load data ──────────────────────────────────────────────────────────

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const [certs, codes] = await Promise.all([getCertifications(), getNAICSCodes()]);

      if (certs.length === 0) {
        const result = await initializeCertifications();
        setCertifications(result.certifications);
      } else {
        setCertifications(certs);
      }
      setNaicsCodes(codes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ── Derived stats ──────────────────────────────────────────────────────

  const stats = useMemo(() => {
    const total = certifications.filter((c) => c.status !== "not_applicable").length;
    const active = certifications.filter((c) => c.status === "certified").length;
    const expiringSoon = certifications.filter(
      (c) => c.status === "certified" && isExpiringSoon(c.expiration_date)
    ).length;
    const selectedNaics = naicsCodes.length;
    return { total, active, expiringSoon, selectedNaics };
  }, [certifications, naicsCodes]);

  // ── Filtered NAICS ────────────────────────────────────────────────────

  const filteredNaics = useMemo(() => {
    if (!naicsSearch.trim()) return naicsCodes;
    const q = naicsSearch.toLowerCase();
    return naicsCodes.filter(
      (n) =>
        n.code.includes(q) ||
        n.title.toLowerCase().includes(q) ||
        n.size_standard.toLowerCase().includes(q)
    );
  }, [naicsCodes, naicsSearch]);

  // ── Handlers ──────────────────────────────────────────────────────────

  async function handleUpdateCert(id: string, updates: Partial<SBACertification>) {
    try {
      const updated = await apiUpdateCert(id, updates);
      setCertifications((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch {
      // keep simple
    }
  }

  async function handleAddNaics(data: {
    code: string;
    title: string;
    size_standard: string;
    is_primary: boolean;
    qualifies_small: boolean;
  }) {
    try {
      const created = await createNAICSCode(data);
      setNaicsCodes((prev) => [...prev, created]);
      setShowAddNaics(false);
    } catch {
      // handle error
    }
  }

  async function handleDeleteNaics(id: string) {
    if (!confirm("Delete this NAICS code?")) return;
    try {
      await deleteNAICSCode(id);
      setNaicsCodes((prev) => prev.filter((n) => n.id !== id));
    } catch {
      // handle error
    }
  }

  async function handleSetPrimary(id: string) {
    try {
      await setNAICSPrimary(id);
      setNaicsCodes((prev) =>
        prev.map((n) => ({ ...n, is_primary: n.id === id }))
      );
    } catch {
      // handle error
    }
  }

  // ── Loading / Error ───────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={loadData}>Retry</Button>
      </div>
    );
  }

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6 lg:p-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          SBA Certifications & NAICS
        </h1>
        <p className="mt-1 text-muted-foreground">
          Track certifications and size standards per The Vault Ch. II
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-4 p-4 md:p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Certifications</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 p-4 md:p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-700">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Active Certifications</p>
              <p className="text-2xl font-bold">{stats.active}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 p-4 md:p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Expiring Soon</p>
              <p className="text-2xl font-bold">{stats.expiringSoon}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 p-4 md:p-6">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-purple-100 text-purple-700">
              <Hash className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">NAICS Codes</p>
              <p className="text-2xl font-bold">{stats.selectedNaics}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SBA Certifications Section */}
      <div>
        <div className="mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">SBA Certifications</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {certifications.map((cert) => (
            <CertificationCard
              key={cert.id}
              cert={cert}
              onUpdate={handleUpdateCert}
            />
          ))}
        </div>
      </div>

      {/* NAICS Code Manager Section */}
      <div>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-muted-foreground" />
            <h2 className="text-xl font-semibold">NAICS Code Manager</h2>
          </div>
          <Button size="sm" className="w-full sm:w-auto" onClick={() => setShowAddNaics(true)}>
            <Plus className="mr-1 h-4 w-4" />
            Add NAICS Code
          </Button>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-base">
                Industry Classification Codes
              </CardTitle>
              <div className="relative w-full sm:w-72">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search codes or titles..."
                  className="pl-9"
                  value={naicsSearch}
                  onChange={(e) => setNaicsSearch(e.target.value)}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {naicsCodes.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <Hash className="h-10 w-10 text-muted-foreground" />
                <p className="text-muted-foreground">No NAICS codes yet. Add your first one.</p>
                <Button size="sm" onClick={() => setShowAddNaics(true)}>
                  <Plus className="mr-1 h-4 w-4" />
                  Add NAICS Code
                </Button>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left">
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">NAICS Code</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Title</th>
                        <th className="hidden md:table-cell pb-3 pr-4 font-medium text-muted-foreground">Size Standard</th>
                        <th className="hidden sm:table-cell pb-3 pr-4 font-medium text-muted-foreground">Primary</th>
                        <th className="hidden lg:table-cell pb-3 pr-4 font-medium text-muted-foreground">Small</th>
                        <th className="pb-3 font-medium text-muted-foreground">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredNaics.map((naics) => (
                        <tr
                          key={naics.id}
                          className={`border-b border-border/50 transition-colors hover:bg-accent/50 ${
                            naics.is_primary ? "bg-primary/5" : ""
                          }`}
                        >
                          <td className="py-3 pr-4">
                            <span className="rounded bg-muted px-2 py-0.5 font-mono text-xs font-semibold">
                              {naics.code}
                            </span>
                          </td>
                          <td className="py-3 pr-4 font-medium">{naics.title}</td>
                          <td className="hidden md:table-cell py-3 pr-4">
                            <span className="font-medium">{naics.size_standard || "--"}</span>
                          </td>
                          <td className="hidden sm:table-cell py-3 pr-4">
                            {naics.is_primary ? (
                              <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                                <Star className="h-3 w-3" />
                                Primary
                              </span>
                            ) : (
                              <button
                                onClick={() => handleSetPrimary(naics.id)}
                                className="text-xs text-muted-foreground hover:text-blue-600 hover:underline"
                              >
                                Set Primary
                              </button>
                            )}
                          </td>
                          <td className="hidden lg:table-cell py-3 pr-4">
                            {naics.qualifies_small ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <X className="h-4 w-4 text-red-500" />
                            )}
                          </td>
                          <td className="py-3">
                            <button
                              onClick={() => handleDeleteNaics(naics.id)}
                              className="text-muted-foreground hover:text-destructive"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                      {filteredNaics.length === 0 && (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-muted-foreground">
                            No NAICS codes match your search.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-t border-border pt-4 text-sm text-muted-foreground">
                  <p>
                    Showing {filteredNaics.length} of {naicsCodes.length} codes
                  </p>
                  {naicsSearch && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setNaicsSearch("")}
                      className="gap-1"
                    >
                      <X className="h-3.5 w-3.5" />
                      Clear filter
                    </Button>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Add NAICS Modal */}
      {showAddNaics && (
        <AddNAICSModal onSave={handleAddNaics} onClose={() => setShowAddNaics(false)} />
      )}
    </div>
  );
}
