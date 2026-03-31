"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getPartners,
  createPartner,
  updatePartner,
  deletePartner,
  getPartnerRiskAssessment,
} from "@/services/teaming";
import {
  TeamingPartner,
  CLEARANCE_LABELS,
  RISK_COLORS,
} from "@/types/teaming";
import {
  Building2,
  Loader2,
  RefreshCw,
  PlusCircle,
  Search,
  X,
  Trash2,
  Pencil,
  Eye,
  Shield,
  ShieldAlert,
  Users,
  Handshake,
  Star,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
} from "lucide-react";

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(d: string | null | undefined): string {
  if (!d) return "--";
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function formatRevenue(v: number): string {
  if (!v) return "--";
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
  return `$${v}`;
}

const clearanceColors: Record<string, string> = {
  none: "bg-gray-100 text-gray-600",
  public_trust: "bg-blue-100 text-blue-700",
  secret: "bg-yellow-100 text-yellow-800",
  top_secret: "bg-orange-100 text-orange-800",
  ts_sci: "bg-red-100 text-red-800",
};

const sbColors: Record<string, string> = {
  SBA: "bg-blue-100 text-blue-800",
  "8A": "bg-purple-100 text-purple-800",
  WOSB: "bg-pink-100 text-pink-800",
  SDVOSB: "bg-green-100 text-green-800",
  HUBZone: "bg-orange-100 text-orange-800",
};

// ── KPI Cards ───────────────────────────────────────────────────────────────

function KpiCards({ partners }: { partners: TeamingPartner[] }) {
  const total = partners.length;
  const sb = partners.filter((p) => p.is_small_business).length;
  const channel = partners.filter((p) => p.is_channel_partner).length;
  const scores = partners.map((p) => p.reliability_score).filter((s) => s > 0);
  const avgScore = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : "--";

  const kpis = [
    { label: "Total Partners", value: total, icon: <Building2 className="h-5 w-5 text-muted-foreground" /> },
    { label: "Small Business", value: sb, icon: <Shield className="h-5 w-5 text-blue-600" /> },
    { label: "Channel / Co-Sell", value: channel, icon: <Handshake className="h-5 w-5 text-green-600" /> },
    { label: "Avg Reliability", value: avgScore, icon: <Star className="h-5 w-5 text-yellow-500" /> },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {kpis.map((k) => (
        <Card key={k.label}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{k.label}</p>
                <p className="text-2xl font-bold mt-1">{k.value}</p>
              </div>
              {k.icon}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ── Risk Assessment Modal ───────────────────────────────────────────────────

function RiskModal({ partner, onClose }: { partner: TeamingPartner; onClose: () => void }) {
  const [risk, setRisk] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPartnerRiskAssessment(partner.id)
      .then((r) => setRisk(r))
      .catch(() => setRisk({ error: "Failed to load risk assessment" }))
      .finally(() => setLoading(false));
  }, [partner.id]);

  const factors = (risk?.risk_factors as Array<Record<string, string>>) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-lg border bg-background shadow-lg max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Risk Assessment — {partner.name}</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-6 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : risk?.error ? (
            <p className="text-red-600">{String(risk.error)}</p>
          ) : (
            <>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-3xl font-bold">{String(risk?.risk_score ?? "--")}</p>
                  <p className="text-xs text-muted-foreground">/ 10</p>
                </div>
                <span className={`px-3 py-1 rounded text-sm font-medium ${RISK_COLORS[String(risk?.risk_level)] || "bg-gray-100 text-gray-700"}`}>
                  {String(risk?.risk_level || "unknown").toUpperCase()}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">{String(risk?.recommendation || "")}</p>
              {factors.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-medium text-sm">Risk Factors</h3>
                  {factors.map((f, i) => (
                    <div key={i} className="border rounded p-3 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{f.category}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${f.severity === "critical" ? "bg-red-100 text-red-800" : f.severity === "high" ? "bg-orange-100 text-orange-800" : "bg-yellow-100 text-yellow-800"}`}>
                          {f.severity}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">{f.description}</p>
                      <p className="text-xs text-green-700">Mitigation: {f.mitigation}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Partner Detail Modal ────────────────────────────────────────────────────

function DetailModal({ partner, onClose, onRisk }: { partner: TeamingPartner; onClose: () => void; onRisk: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-lg border bg-background shadow-lg max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">{partner.name}</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-6 space-y-5">
          {/* Identity */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-muted-foreground">UEI:</span> <span className="font-mono">{partner.uei}</span></div>
            <div><span className="text-muted-foreground">CAGE:</span> {partner.cage_code || "--"}</div>
            <div><span className="text-muted-foreground">HQ:</span> {partner.headquarters || "--"}</div>
            <div><span className="text-muted-foreground">Employees:</span> {partner.employee_count || "--"}</div>
            <div><span className="text-muted-foreground">Revenue:</span> {formatRevenue(partner.past_revenue)}</div>
            <div><span className="text-muted-foreground">Website:</span> {partner.website ? <a href={partner.website} target="_blank" rel="noreferrer" className="text-blue-600 underline">{partner.website}</a> : "--"}</div>
          </div>

          {/* Clearance & Risk */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${clearanceColors[partner.clearance_level] || "bg-gray-100 text-gray-600"}`}>
              {CLEARANCE_LABELS[partner.clearance_level] || partner.clearance_level}
            </span>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_COLORS[partner.risk_level] || "bg-gray-100 text-gray-700"}`}>
              Risk: {partner.risk_level}
            </span>
            <span className="text-xs">Reliability: <strong>{partner.reliability_score}/10</strong></span>
            <span className="text-xs">Performance: {partner.performance_history}</span>
            {partner.has_cpars_issues && <span className="text-xs text-red-600 flex items-center gap-1"><AlertTriangle className="h-3 w-3" />CPARS Issues</span>}
          </div>

          {/* SB Certs */}
          {partner.sb_certifications.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">SB Certifications</p>
              <div className="flex flex-wrap gap-1">
                {partner.sb_certifications.map((c) => (
                  <span key={c} className={`px-2 py-0.5 rounded text-xs font-medium ${sbColors[c] || "bg-gray-100 text-gray-700"}`}>{c}</span>
                ))}
              </div>
            </div>
          )}

          {/* Capabilities */}
          {partner.capabilities.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Capabilities</p>
              <div className="flex flex-wrap gap-1">
                {partner.capabilities.map((c) => (
                  <span key={c} className="px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700">{c}</span>
                ))}
              </div>
            </div>
          )}

          {/* NAICS & Vehicles */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">NAICS Codes</p>
              <p className="font-mono text-xs">{partner.naics_codes.join(", ") || "--"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Contract Vehicles</p>
              <p className="text-xs">{partner.contract_vehicles.join(", ") || "--"}</p>
            </div>
          </div>

          {/* Agencies */}
          {partner.primary_agencies.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Primary Agencies</p>
              <p className="text-xs">{partner.primary_agencies.join(", ")}</p>
            </div>
          )}

          {/* Contact */}
          {(partner.primary_contact_name || partner.primary_contact_email) && (
            <div className="text-sm">
              <p className="text-xs text-muted-foreground mb-1">Primary Contact</p>
              <p>{partner.primary_contact_name || "--"}</p>
              {partner.primary_contact_email && <p className="text-muted-foreground">{partner.primary_contact_email}</p>}
              {partner.primary_contact_phone && <p className="text-muted-foreground">{partner.primary_contact_phone}</p>}
            </div>
          )}

          {/* Co-sell */}
          {partner.is_channel_partner && (
            <div className="text-sm border rounded p-3 bg-green-50">
              <p className="font-medium text-green-800 mb-1">Channel / Co-Sell Partner</p>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>Referral Fee: {partner.referral_fee_pct != null ? `${partner.referral_fee_pct}%` : "--"}</div>
                <div>Opportunities: {partner.co_sell_opportunities}</div>
                <div>Wins: {partner.co_sell_wins}</div>
              </div>
            </div>
          )}

          {/* Mentor-Protege */}
          {partner.mentor_protege_role && (
            <div className="text-sm border rounded p-3 bg-orange-50">
              <p className="font-medium text-orange-800 mb-1">Mentor-Protege: {partner.mentor_protege_role}</p>
              <p className="text-xs">{partner.mentor_protege_program || "--"}</p>
              {partner.mentor_protege_start && <p className="text-xs text-muted-foreground">{formatDate(partner.mentor_protege_start)} — {formatDate(partner.mentor_protege_end)}</p>}
            </div>
          )}

          {/* Notes */}
          {partner.notes && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Notes</p>
              <p className="text-sm">{partner.notes}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end pt-2">
            <Button variant="outline" onClick={onRisk}>
              <ShieldAlert className="mr-2 h-4 w-4" />
              Run Risk Assessment
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Add / Edit Partner Modal ────────────────────────────────────────────────

interface PartnerFormProps {
  initial?: TeamingPartner | null;
  onClose: () => void;
  onSaved: (p: TeamingPartner) => void;
}

function PartnerFormModal({ initial, onClose, onSaved }: PartnerFormProps) {
  const isEdit = !!initial;
  const [form, setForm] = useState({
    name: initial?.name || "",
    uei: initial?.uei || "",
    cage_code: initial?.cage_code || "",
    headquarters: initial?.headquarters || "",
    website: initial?.website || "",
    primary_contact_name: initial?.primary_contact_name || "",
    primary_contact_email: initial?.primary_contact_email || "",
    primary_contact_phone: initial?.primary_contact_phone || "",
    naics_codes: (initial?.naics_codes || []).join(", "),
    capabilities: (initial?.capabilities || []).join(", "),
    contract_vehicles: (initial?.contract_vehicles || []).join(", "),
    sb_certifications: (initial?.sb_certifications || []).join(", "),
    is_small_business: initial?.is_small_business || false,
    clearance_level: initial?.clearance_level || "none",
    reliability_score: initial?.reliability_score ?? 5,
    performance_history: initial?.performance_history || "unknown",
    risk_level: initial?.risk_level || "low",
    has_cpars_issues: initial?.has_cpars_issues || false,
    past_revenue: initial?.past_revenue || 0,
    employee_count: initial?.employee_count || 0,
    is_channel_partner: initial?.is_channel_partner || false,
    referral_fee_pct: initial?.referral_fee_pct ?? "",
    co_sell_opportunities: initial?.co_sell_opportunities || 0,
    co_sell_wins: initial?.co_sell_wins || 0,
    mentor_protege_role: initial?.mentor_protege_role || "",
    mentor_protege_program: initial?.mentor_protege_program || "",
    notes: initial?.notes || "",
    primary_agencies: (initial?.primary_agencies || []).join(", "),
    tags: (initial?.tags || []).join(", "),
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (field: string, value: unknown) => setForm((f) => ({ ...f, [field]: value }));

  const splitCsv = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.uei.trim()) { setError("Name and UEI are required."); return; }
    setSubmitting(true);
    setError(null);
    const payload: Partial<TeamingPartner> = {
      name: form.name.trim(),
      uei: form.uei.trim(),
      cage_code: form.cage_code,
      headquarters: form.headquarters,
      website: form.website,
      primary_contact_name: form.primary_contact_name,
      primary_contact_email: form.primary_contact_email,
      primary_contact_phone: form.primary_contact_phone,
      naics_codes: splitCsv(form.naics_codes),
      capabilities: splitCsv(form.capabilities),
      contract_vehicles: splitCsv(form.contract_vehicles),
      sb_certifications: splitCsv(form.sb_certifications),
      is_small_business: form.is_small_business,
      clearance_level: form.clearance_level,
      reliability_score: Number(form.reliability_score),
      performance_history: form.performance_history,
      risk_level: form.risk_level,
      has_cpars_issues: form.has_cpars_issues,
      past_revenue: Number(form.past_revenue),
      employee_count: Number(form.employee_count),
      is_channel_partner: form.is_channel_partner,
      referral_fee_pct: form.referral_fee_pct !== "" ? Number(form.referral_fee_pct) : null,
      co_sell_opportunities: Number(form.co_sell_opportunities),
      co_sell_wins: Number(form.co_sell_wins),
      mentor_protege_role: form.mentor_protege_role,
      mentor_protege_program: form.mentor_protege_program,
      notes: form.notes,
      primary_agencies: splitCsv(form.primary_agencies),
      tags: splitCsv(form.tags),
    };
    try {
      const saved = isEdit ? await updatePartner(initial!.id, payload) : await createPartner(payload);
      onSaved(saved);
    } catch {
      setError("Failed to save partner.");
    } finally {
      setSubmitting(false);
    }
  };

  const fieldCls = "w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-2xl rounded-lg border bg-background shadow-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">{isEdit ? "Edit Partner" : "Add Partner"}</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted"><X className="h-4 w-4" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Identity */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Identity</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><label className="text-xs font-medium">Company Name *</label><Input value={form.name} onChange={(e) => set("name", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">UEI *</label><Input value={form.uei} onChange={(e) => set("uei", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">CAGE Code</label><Input value={form.cage_code} onChange={(e) => set("cage_code", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Headquarters</label><Input value={form.headquarters} onChange={(e) => set("headquarters", e.target.value)} /></div>
            </div>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Contact</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><label className="text-xs font-medium">Contact Name</label><Input value={form.primary_contact_name} onChange={(e) => set("primary_contact_name", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Email</label><Input type="email" value={form.primary_contact_email} onChange={(e) => set("primary_contact_email", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Phone</label><Input value={form.primary_contact_phone} onChange={(e) => set("primary_contact_phone", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Website</label><Input value={form.website} onChange={(e) => set("website", e.target.value)} /></div>
            </div>
          </div>

          {/* Capabilities */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Capabilities</h3>
            <div className="space-y-3">
              <div className="space-y-1"><label className="text-xs font-medium">NAICS Codes (comma-separated)</label><Input value={form.naics_codes} onChange={(e) => set("naics_codes", e.target.value)} placeholder="541511, 541512" /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Capabilities (comma-separated)</label><Input value={form.capabilities} onChange={(e) => set("capabilities", e.target.value)} placeholder="software development, cloud migration" /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Contract Vehicles (comma-separated)</label><Input value={form.contract_vehicles} onChange={(e) => set("contract_vehicles", e.target.value)} placeholder="GSA MAS, SEWP V" /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Primary Agencies (comma-separated)</label><Input value={form.primary_agencies} onChange={(e) => set("primary_agencies", e.target.value)} placeholder="DoD, VA, HHS" /></div>
            </div>
          </div>

          {/* SB & Clearance */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Small Business & Clearance</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center gap-2"><input type="checkbox" checked={form.is_small_business} onChange={(e) => set("is_small_business", e.target.checked)} className="rounded" /><label className="text-xs font-medium">Small Business</label></div>
              <div className="space-y-1"><label className="text-xs font-medium">SB Certifications (comma-separated)</label><Input value={form.sb_certifications} onChange={(e) => set("sb_certifications", e.target.value)} placeholder="SBA, WOSB, SDVOSB" /></div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Clearance Level</label>
                <select value={form.clearance_level} onChange={(e) => set("clearance_level", e.target.value)} className={fieldCls}>
                  {Object.entries(CLEARANCE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Performance */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Performance & Risk</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium">Reliability Score ({form.reliability_score})</label>
                <input type="range" min="0" max="10" step="0.5" value={form.reliability_score} onChange={(e) => set("reliability_score", e.target.value)} className="w-full" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Performance History</label>
                <select value={form.performance_history} onChange={(e) => set("performance_history", e.target.value)} className={fieldCls}>
                  {["excellent", "very_good", "good", "satisfactory", "marginal", "unsatisfactory", "unknown"].map((v) => <option key={v} value={v}>{v.replace("_", " ")}</option>)}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Risk Level</label>
                <select value={form.risk_level} onChange={(e) => set("risk_level", e.target.value)} className={fieldCls}>
                  {["low", "medium", "high", "critical"].map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2 pt-4"><input type="checkbox" checked={form.has_cpars_issues} onChange={(e) => set("has_cpars_issues", e.target.checked)} className="rounded" /><label className="text-xs font-medium">CPARS Issues</label></div>
            </div>
          </div>

          {/* Financials */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Financials</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><label className="text-xs font-medium">Annual Revenue ($)</label><Input type="number" value={form.past_revenue} onChange={(e) => set("past_revenue", e.target.value)} /></div>
              <div className="space-y-1"><label className="text-xs font-medium">Employee Count</label><Input type="number" value={form.employee_count} onChange={(e) => set("employee_count", e.target.value)} /></div>
            </div>
          </div>

          {/* Co-sell */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Co-Sell / Channel</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center gap-2"><input type="checkbox" checked={form.is_channel_partner} onChange={(e) => set("is_channel_partner", e.target.checked)} className="rounded" /><label className="text-xs font-medium">Channel / Co-Sell Partner</label></div>
              <div className="space-y-1"><label className="text-xs font-medium">Referral Fee %</label><Input type="number" step="0.1" value={form.referral_fee_pct} onChange={(e) => set("referral_fee_pct", e.target.value)} /></div>
            </div>
          </div>

          {/* Mentor-Protege */}
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">Mentor-Protege</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium">Role</label>
                <select value={form.mentor_protege_role} onChange={(e) => set("mentor_protege_role", e.target.value)} className={fieldCls}>
                  <option value="">None</option>
                  <option value="mentor">Mentor</option>
                  <option value="protege">Protege</option>
                </select>
              </div>
              <div className="space-y-1"><label className="text-xs font-medium">Program</label><Input value={form.mentor_protege_program} onChange={(e) => set("mentor_protege_program", e.target.value)} placeholder="SBA All Small Mentor-Protege" /></div>
            </div>
          </div>

          {/* Notes & Tags */}
          <div className="space-y-3">
            <div className="space-y-1"><label className="text-xs font-medium">Tags (comma-separated)</label><Input value={form.tags} onChange={(e) => set("tags", e.target.value)} /></div>
            <div className="space-y-1"><label className="text-xs font-medium">Notes</label><textarea value={form.notes} onChange={(e) => set("notes", e.target.value)} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" /></div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : isEdit ? "Update Partner" : "Add Partner"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function PartnerDirectoryPage() {
  const [partners, setPartners] = useState<TeamingPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [clearanceFilter, setClearanceFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [sbOnly, setSbOnly] = useState(false);
  const [channelOnly, setChannelOnly] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editPartner, setEditPartner] = useState<TeamingPartner | null>(null);
  const [viewPartner, setViewPartner] = useState<TeamingPartner | null>(null);
  const [riskPartner, setRiskPartner] = useState<TeamingPartner | null>(null);

  const fetchPartners = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (clearanceFilter) params.clearance_level = clearanceFilter;
      if (riskFilter) params.risk_level = riskFilter;
      if (sbOnly) params.is_small_business = "true";
      if (channelOnly) params.is_channel_partner = "true";
      const data = await getPartners(params);
      setPartners(data.results || []);
    } catch {
      setError("Failed to load partners.");
    } finally {
      setLoading(false);
    }
  }, [search, clearanceFilter, riskFilter, sbOnly, channelOnly]);

  useEffect(() => { fetchPartners(); }, [fetchPartners]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this partner?")) return;
    try {
      await deletePartner(id);
      setPartners((p) => p.filter((x) => x.id !== id));
    } catch { /* ignore */ }
  };

  const fieldCls = "h-8 rounded-md border border-input bg-background px-2 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Partner Directory</h1>
          <p className="text-muted-foreground">Manage your reusable partner company database</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchPartners} disabled={loading}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
            Refresh
          </Button>
          <Button onClick={() => { setEditPartner(null); setShowForm(true); }}>
            <PlusCircle className="mr-2 h-4 w-4" />Add Partner
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name, UEI, capabilities..." className="pl-8 h-8 text-xs" />
        </div>
        <select value={clearanceFilter} onChange={(e) => setClearanceFilter(e.target.value)} className={fieldCls}>
          <option value="">All Clearances</option>
          {Object.entries(CLEARANCE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} className={fieldCls}>
          <option value="">All Risk Levels</option>
          {["low", "medium", "high", "critical"].map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
        <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={sbOnly} onChange={(e) => setSbOnly(e.target.checked)} className="rounded" />Small Business</label>
        <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={channelOnly} onChange={(e) => setChannelOnly(e.target.checked)} className="rounded" />Channel Partners</label>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6 flex items-center justify-between">
            <p className="text-red-700">{error}</p>
            <Button variant="outline" size="sm" onClick={fetchPartners}>Retry</Button>
          </CardContent>
        </Card>
      )}

      <KpiCards partners={partners} />

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Partners{!loading && <span className="ml-2 text-sm font-normal text-muted-foreground">({partners.length})</span>}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-3 text-muted-foreground">Loading partners...</span></div>
          ) : partners.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Building2 className="h-12 w-12 text-muted-foreground mb-3" />
              <p className="text-muted-foreground font-medium mb-2">No partners yet</p>
              <p className="text-sm text-muted-foreground text-center max-w-sm">Build your teaming network by adding partner companies.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Company</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">HQ</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Clearance</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">SB Certs</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Reliability</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Risk</th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">Status</th>
                    <th className="pb-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {partners.map((p) => (
                    <tr key={p.id} className="border-b transition-colors hover:bg-muted/50">
                      <td className="py-3 pr-4">
                        <p className="font-medium">{p.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">{p.uei}</p>
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground text-xs">{p.headquarters || "--"}</td>
                      <td className="py-3 pr-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${clearanceColors[p.clearance_level] || "bg-gray-100 text-gray-600"}`}>
                          {CLEARANCE_LABELS[p.clearance_level] || p.clearance_level}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex flex-wrap gap-1">
                          {p.sb_certifications.length > 0 ? p.sb_certifications.slice(0, 3).map((c) => (
                            <span key={c} className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${sbColors[c] || "bg-gray-100 text-gray-700"}`}>{c}</span>
                          )) : <span className="text-xs text-muted-foreground">--</span>}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`text-xs font-medium ${p.reliability_score >= 8 ? "text-green-600" : p.reliability_score >= 5 ? "text-yellow-600" : "text-red-600"}`}>
                          {p.reliability_score}/10
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_COLORS[p.risk_level] || "bg-gray-100 text-gray-700"}`}>
                          {p.risk_level}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className={`inline-flex items-center gap-1 text-xs ${p.is_active ? "text-green-600" : "text-gray-400"}`}>
                          <span className={`h-2 w-2 rounded-full ${p.is_active ? "bg-green-500" : "bg-gray-300"}`} />
                          {p.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="py-3">
                        <div className="flex items-center gap-1">
                          <button onClick={() => setViewPartner(p)} className="p-1 rounded hover:bg-muted" title="View"><Eye className="h-3.5 w-3.5 text-muted-foreground" /></button>
                          <button onClick={() => { setEditPartner(p); setShowForm(true); }} className="p-1 rounded hover:bg-muted" title="Edit"><Pencil className="h-3.5 w-3.5 text-muted-foreground" /></button>
                          <button onClick={() => setRiskPartner(p)} className="p-1 rounded hover:bg-muted" title="Risk Assessment"><ShieldAlert className="h-3.5 w-3.5 text-muted-foreground" /></button>
                          <button onClick={() => handleDelete(p.id)} className="p-1 rounded hover:bg-muted" title="Delete"><Trash2 className="h-3.5 w-3.5 text-red-400" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      {showForm && (
        <PartnerFormModal
          initial={editPartner}
          onClose={() => { setShowForm(false); setEditPartner(null); }}
          onSaved={(p) => {
            if (editPartner) {
              setPartners((prev) => prev.map((x) => (x.id === p.id ? p : x)));
            } else {
              setPartners((prev) => [p, ...prev]);
            }
            setShowForm(false);
            setEditPartner(null);
          }}
        />
      )}
      {viewPartner && (
        <DetailModal
          partner={viewPartner}
          onClose={() => setViewPartner(null)}
          onRisk={() => { setRiskPartner(viewPartner); setViewPartner(null); }}
        />
      )}
      {riskPartner && <RiskModal partner={riskPartner} onClose={() => setRiskPartner(null)} />}
    </div>
  );
}
