"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Shield,
  ShieldCheck,
  Award,
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
  CalendarDays,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

type CertStatus =
  | "not_applicable"
  | "eligible"
  | "applied"
  | "certified"
  | "expired";

interface Certification {
  id: string;
  name: string;
  abbreviation: string;
  status: CertStatus;
  certificationDate: string | null;
  expirationDate: string | null;
  certificationNumber: string | null;
  eligibilityNotes: string;
}

type SizeStandardType = "revenue" | "employees";

interface NaicsCode {
  code: string;
  title: string;
  sizeStandard: string;
  sizeStandardType: SizeStandardType;
  selected: boolean;
}

// ── Constants ──────────────────────────────────────────────────────────────

const STATUS_OPTIONS: { value: CertStatus; label: string }[] = [
  { value: "not_applicable", label: "Not Applicable" },
  { value: "eligible", label: "Eligible" },
  { value: "applied", label: "Applied" },
  { value: "certified", label: "Certified" },
  { value: "expired", label: "Expired" },
];

const STATUS_STYLES: Record<CertStatus, string> = {
  not_applicable: "bg-gray-100 text-gray-600",
  eligible: "bg-blue-100 text-blue-700",
  applied: "bg-yellow-100 text-yellow-700",
  certified: "bg-green-100 text-green-700",
  expired: "bg-red-100 text-red-700",
};

const STATUS_LABELS: Record<CertStatus, string> = {
  not_applicable: "Not Applicable",
  eligible: "Eligible",
  applied: "Applied",
  certified: "Certified",
  expired: "Expired",
};

// ── Mock Data ──────────────────────────────────────────────────────────────

const INITIAL_CERTIFICATIONS: Certification[] = [
  {
    id: "sb",
    name: "Small Business",
    abbreviation: "SB",
    status: "certified",
    certificationDate: "2024-01-15",
    expirationDate: "2027-01-15",
    certificationNumber: "SB-2024-00487",
    eligibilityNotes:
      "Meets revenue threshold under primary NAICS 541512. Annual re-certification required via SAM.gov.",
  },
  {
    id: "sdb",
    name: "Small Disadvantaged Business",
    abbreviation: "SDB",
    status: "eligible",
    certificationDate: null,
    expirationDate: null,
    certificationNumber: null,
    eligibilityNotes:
      "Owner qualifies under socially and economically disadvantaged criteria. Documentation prepared for application.",
  },
  {
    id: "8a",
    name: "8(a) Business Development",
    abbreviation: "8(a)",
    status: "applied",
    certificationDate: null,
    expirationDate: null,
    certificationNumber: null,
    eligibilityNotes:
      "Application submitted to SBA on 2025-11-20. 9-year program eligibility. Awaiting review (est. 90 days).",
  },
  {
    id: "wosb",
    name: "Woman-Owned Small Business",
    abbreviation: "WOSB",
    status: "certified",
    certificationDate: "2024-06-01",
    expirationDate: "2027-06-01",
    certificationNumber: "WOSB-2024-01293",
    eligibilityNotes:
      "Certified through SBA WOSB Federal Contracting Program. 51% owned/controlled by women.",
  },
  {
    id: "edwosb",
    name: "Economically Disadvantaged WOSB",
    abbreviation: "EDWOSB",
    status: "certified",
    certificationDate: "2024-06-01",
    expirationDate: "2027-06-01",
    certificationNumber: "EDWOSB-2024-01294",
    eligibilityNotes:
      "Qualifies under EDWOSB economic thresholds. Linked to WOSB certification. Personal net worth under $750K.",
  },
  {
    id: "vosb",
    name: "Veteran-Owned Small Business",
    abbreviation: "VOSB",
    status: "not_applicable",
    certificationDate: null,
    expirationDate: null,
    certificationNumber: null,
    eligibilityNotes:
      "Not applicable — no veteran ownership stake in current organizational structure.",
  },
  {
    id: "sdvosb",
    name: "Service-Disabled Veteran-Owned",
    abbreviation: "SDVOSB",
    status: "not_applicable",
    certificationDate: null,
    expirationDate: null,
    certificationNumber: null,
    eligibilityNotes:
      "Not applicable — requires 51% ownership by service-disabled veteran.",
  },
  {
    id: "hubzone",
    name: "HUBZone",
    abbreviation: "HUBZone",
    status: "expired",
    certificationDate: "2021-03-10",
    expirationDate: "2024-03-10",
    certificationNumber: "HZ-2021-05582",
    eligibilityNotes:
      "Previously certified. Expired due to principal office relocation outside designated HUBZone. Re-evaluation pending.",
  },
];

const INITIAL_NAICS_CODES: NaicsCode[] = [
  { code: "541511", title: "Custom Computer Programming Services", sizeStandard: "$34M", sizeStandardType: "revenue", selected: true },
  { code: "541512", title: "Computer Systems Design Services", sizeStandard: "$34M", sizeStandardType: "revenue", selected: true },
  { code: "541513", title: "Computer Facilities Management Services", sizeStandard: "$34M", sizeStandardType: "revenue", selected: true },
  { code: "541519", title: "Other Computer Related Services", sizeStandard: "$34M", sizeStandardType: "revenue", selected: true },
  { code: "541611", title: "Administrative Management Consulting Services", sizeStandard: "$24.5M", sizeStandardType: "revenue", selected: false },
  { code: "541612", title: "Human Resources Consulting Services", sizeStandard: "$24.5M", sizeStandardType: "revenue", selected: false },
  { code: "541613", title: "Marketing Consulting Services", sizeStandard: "$19M", sizeStandardType: "revenue", selected: false },
  { code: "541614", title: "Process, Physical Distribution, & Logistics Consulting", sizeStandard: "$19M", sizeStandardType: "revenue", selected: false },
  { code: "541618", title: "Other Management Consulting Services", sizeStandard: "$19M", sizeStandardType: "revenue", selected: false },
  { code: "541690", title: "Other Scientific & Technical Consulting Services", sizeStandard: "$19M", sizeStandardType: "revenue", selected: false },
  { code: "541715", title: "Research & Development in the Physical, Engineering, & Life Sciences", sizeStandard: "1,000 employees", sizeStandardType: "employees", selected: true },
  { code: "541990", title: "All Other Professional, Scientific, & Technical Services", sizeStandard: "$19M", sizeStandardType: "revenue", selected: false },
  { code: "518210", title: "Data Processing, Hosting, & Related Services", sizeStandard: "$40M", sizeStandardType: "revenue", selected: true },
  { code: "511210", title: "Software Publishers", sizeStandard: "$47M", sizeStandardType: "revenue", selected: false },
  { code: "561110", title: "Office Administrative Services", sizeStandard: "$12.5M", sizeStandardType: "revenue", selected: false },
  { code: "611420", title: "Computer Training", sizeStandard: "$15M", sizeStandardType: "revenue", selected: false },
  { code: "561210", title: "Facilities Support Services", sizeStandard: "$47M", sizeStandardType: "revenue", selected: false },
  { code: "334111", title: "Electronic Computer Manufacturing", sizeStandard: "1,250 employees", sizeStandardType: "employees", selected: false },
  { code: "423430", title: "Computer & Peripheral Equipment Merchant Wholesalers", sizeStandard: "250 employees", sizeStandardType: "employees", selected: false },
  { code: "541330", title: "Engineering Services", sizeStandard: "$25.5M", sizeStandardType: "revenue", selected: false },
];

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
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status]}`}
    >
      {status === "certified" && <ShieldCheck className="h-3 w-3" />}
      {status === "applied" && <Clock className="h-3 w-3" />}
      {status === "eligible" && <Star className="h-3 w-3" />}
      {status === "expired" && <AlertTriangle className="h-3 w-3" />}
      {STATUS_LABELS[status]}
    </span>
  );
}

// ── Certification Card ─────────────────────────────────────────────────────

function CertificationCard({
  cert,
  onUpdate,
}: {
  cert: Certification;
  onUpdate: (id: string, updates: Partial<Certification>) => void;
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const borderColor =
    cert.status === "certified"
      ? "border-l-green-500"
      : cert.status === "applied"
        ? "border-l-yellow-500"
        : cert.status === "eligible"
          ? "border-l-blue-500"
          : cert.status === "expired"
            ? "border-l-red-500"
            : "border-l-gray-300";

  return (
    <Card className={`border-l-4 ${borderColor} relative`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="text-base font-semibold leading-tight">
              {cert.name}
            </CardTitle>
            <p className="mt-0.5 text-xs font-medium text-muted-foreground">
              {cert.abbreviation}
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
            {STATUS_LABELS[cert.status]}
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
                    cert.status === opt.value
                      ? "bg-accent font-medium"
                      : ""
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Details grid */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Cert Date</p>
            <p className="font-medium">{formatDate(cert.certificationDate)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Expiration</p>
            <p
              className={`font-medium ${
                cert.expirationDate && isExpiringSoon(cert.expirationDate)
                  ? "text-amber-600"
                  : ""
              }`}
            >
              {formatDate(cert.expirationDate)}
              {cert.expirationDate && isExpiringSoon(cert.expirationDate) && (
                <AlertTriangle className="ml-1 inline h-3 w-3 text-amber-500" />
              )}
            </p>
          </div>
          <div className="col-span-2">
            <p className="text-xs text-muted-foreground">Cert Number</p>
            <p className="font-mono text-xs font-medium">
              {cert.certificationNumber ?? "--"}
            </p>
          </div>
        </div>

        {/* Notes */}
        <div>
          <p className="mb-1 text-xs text-muted-foreground">
            Eligibility Notes
          </p>
          <p className="text-xs leading-relaxed text-muted-foreground">
            {cert.eligibilityNotes || "--"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function SBACertificationsPage() {
  const [certifications, setCertifications] = useState<Certification[]>(
    INITIAL_CERTIFICATIONS
  );
  const [naicsCodes, setNaicsCodes] = useState<NaicsCode[]>(
    INITIAL_NAICS_CODES
  );
  const [naicsSearch, setNaicsSearch] = useState("");

  // ── Derived stats ──────────────────────────────────────────────────────

  const stats = useMemo(() => {
    const total = certifications.filter(
      (c) => c.status !== "not_applicable"
    ).length;
    const active = certifications.filter(
      (c) => c.status === "certified"
    ).length;
    const expiringSoon = certifications.filter(
      (c) => c.status === "certified" && isExpiringSoon(c.expirationDate)
    ).length;
    const selectedNaics = naicsCodes.filter((n) => n.selected).length;
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
        n.sizeStandard.toLowerCase().includes(q)
    );
  }, [naicsCodes, naicsSearch]);

  // ── Handlers ──────────────────────────────────────────────────────────

  function updateCertification(id: string, updates: Partial<Certification>) {
    setCertifications((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  }

  function toggleNaicsSelection(code: string) {
    setNaicsCodes((prev) =>
      prev.map((n) =>
        n.code === code ? { ...n, selected: !n.selected } : n
      )
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
              <p className="text-sm text-muted-foreground">
                Total Certifications
              </p>
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
              <p className="text-sm text-muted-foreground">
                Active Certifications
              </p>
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
              onUpdate={updateCertification}
            />
          ))}
        </div>
      </div>

      {/* NAICS Code Manager Section */}
      <div>
        <div className="mb-4 flex items-center gap-2">
          <Building2 className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold">NAICS Code Manager</h2>
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
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Selected
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      NAICS Code
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Title
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Size Standard
                    </th>
                    <th className="pb-3 font-medium text-muted-foreground">
                      Type
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredNaics.map((naics) => (
                    <tr
                      key={naics.code}
                      className={`border-b border-border/50 transition-colors hover:bg-accent/50 ${
                        naics.selected ? "bg-primary/5" : ""
                      }`}
                    >
                      <td className="py-3 pr-4">
                        <button
                          onClick={() => toggleNaicsSelection(naics.code)}
                          className={`flex h-5 w-5 items-center justify-center rounded border transition-colors ${
                            naics.selected
                              ? "border-primary bg-primary text-primary-foreground"
                              : "border-border hover:border-primary"
                          }`}
                        >
                          {naics.selected && (
                            <CheckCircle className="h-3.5 w-3.5" />
                          )}
                        </button>
                      </td>
                      <td className="py-3 pr-4">
                        <span className="rounded bg-muted px-2 py-0.5 font-mono text-xs font-semibold">
                          {naics.code}
                        </span>
                      </td>
                      <td className="py-3 pr-4 font-medium">{naics.title}</td>
                      <td className="py-3 pr-4">
                        <span className="font-medium">
                          {naics.sizeStandard}
                        </span>
                      </td>
                      <td className="py-3">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            naics.sizeStandardType === "revenue"
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-indigo-100 text-indigo-700"
                          }`}
                        >
                          {naics.sizeStandardType === "revenue" ? (
                            <DollarSign className="h-3 w-3" />
                          ) : (
                            <Users className="h-3 w-3" />
                          )}
                          {naics.sizeStandardType === "revenue"
                            ? "Revenue"
                            : "Employees"}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {filteredNaics.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="py-8 text-center text-muted-foreground"
                      >
                        No NAICS codes match your search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex items-center justify-between border-t border-border pt-4 text-sm text-muted-foreground">
              <p>
                Showing {filteredNaics.length} of {naicsCodes.length} codes
                {" | "}
                <span className="font-medium text-foreground">
                  {naicsCodes.filter((n) => n.selected).length}
                </span>{" "}
                selected
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
