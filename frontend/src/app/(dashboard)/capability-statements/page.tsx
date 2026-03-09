"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileText,
  Plus,
  Trash2,
  Eye,
  Edit3,
  Star,
  Building2,
  Phone,
  Mail,
  Globe,
  User,
  Hash,
  Award,
  ChevronRight,
  X,
  ArrowLeft,
  Copy,
  Download,
  Loader2,
  AlertTriangle,
  Sparkles,
} from "lucide-react";
import {
  CapabilityStatementListItem,
  CapabilityStatement,
  CapabilityStatementPayload,
  PastPerformanceEntry,
  AIImprovementResult,
  getCapabilityStatements,
  getCapabilityStatement,
  createCapabilityStatement,
  updateCapabilityStatement,
  deleteCapabilityStatement,
  setPrimary,
  unsetPrimary,
  duplicateStatement,
  aiImprove,
} from "@/services/capability-statements";

// ── Types ──────────────────────────────────────────────────────────────────

type ViewMode = "list" | "editor" | "preview";

interface FormState {
  id: string;
  title: string;
  version: string;
  targetAgency: string;
  targetNaics: string;
  isPrimary: boolean;
  companyOverview: string;
  coreCompetencies: string[];
  differentiators: string[];
  pastPerformance: PastPerformanceEntry[];
  companyData: {
    uei: string;
    cageCode: string;
    naicsCodes: string[];
    pscCodes: string[];
    certifications: string[];
    contractVehicles: string[];
  };
  contact: {
    name: string;
    title: string;
    email: string;
    phone: string;
    website: string;
  };
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function emptyForm(): FormState {
  return {
    id: "",
    title: "",
    version: "1",
    targetAgency: "",
    targetNaics: "",
    isPrimary: false,
    companyOverview: "",
    coreCompetencies: [],
    differentiators: [],
    pastPerformance: [],
    companyData: {
      uei: "",
      cageCode: "",
      naicsCodes: [],
      pscCodes: [],
      certifications: [],
      contractVehicles: [],
    },
    contact: { name: "", title: "", email: "", phone: "", website: "" },
  };
}

function apiToForm(stmt: CapabilityStatement): FormState {
  return {
    id: stmt.id,
    title: stmt.title,
    version: String(stmt.version),
    targetAgency: stmt.target_agency || "",
    targetNaics: stmt.target_naics || "",
    isPrimary: stmt.is_primary,
    companyOverview: stmt.company_overview || "",
    coreCompetencies: stmt.core_competencies || [],
    differentiators: stmt.differentiators || [],
    pastPerformance: (stmt.past_performance_highlights || []).map(
      (pp: PastPerformanceEntry, i: number) => ({
        id: pp.id || `pp-${i}`,
        projectName: pp.projectName || "",
        agency: pp.agency || "",
        summary: pp.summary || "",
      })
    ),
    companyData: {
      uei: stmt.uei_number || "",
      cageCode: stmt.cage_code || "",
      naicsCodes: stmt.naics_codes || [],
      pscCodes: stmt.psc_codes || [],
      certifications: stmt.certifications || [],
      contractVehicles: stmt.contract_vehicles || [],
    },
    contact: {
      name: stmt.contact_name || "",
      title: stmt.contact_title || "",
      email: stmt.contact_email || "",
      phone: stmt.contact_phone || "",
      website: stmt.website || "",
    },
  };
}

function formToPayload(form: FormState): CapabilityStatementPayload {
  return {
    title: form.title || "Untitled Statement",
    version: parseInt(form.version) || 1,
    is_primary: form.isPrimary,
    target_agency: form.targetAgency,
    target_naics: form.targetNaics,
    company_overview: form.companyOverview,
    core_competencies: form.coreCompetencies,
    differentiators: form.differentiators,
    past_performance_highlights: form.pastPerformance,
    uei_number: form.companyData.uei,
    cage_code: form.companyData.cageCode,
    naics_codes: form.companyData.naicsCodes,
    psc_codes: form.companyData.pscCodes,
    certifications: form.companyData.certifications,
    contract_vehicles: form.companyData.contractVehicles,
    contact_name: form.contact.name,
    contact_title: form.contact.title,
    contact_email: form.contact.email,
    contact_phone: form.contact.phone,
    website: form.contact.website,
  };
}

// ── ListBuilder Component ─────────────────────────────────────────────────

function ListBuilder({
  label,
  items,
  onAdd,
  onRemove,
  placeholder,
}: {
  label: string;
  items: string[];
  onAdd: (v: string) => void;
  onRemove: (i: number) => void;
  placeholder: string;
}) {
  const [draft, setDraft] = useState("");
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      {items.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {items.map((item, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-sm"
            >
              {item}
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="text-slate-400 hover:text-red-600"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.key === "Enter" && draft.trim()) {
              e.preventDefault();
              onAdd(draft.trim());
              setDraft("");
            }
          }}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            if (draft.trim()) {
              onAdd(draft.trim());
              setDraft("");
            }
          }}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ── Preview Panel ─────────────────────────────────────────────────────────

function PreviewPanel({ stmt }: { stmt: FormState }) {
  return (
    <div className="border rounded-lg bg-white text-sm shadow-sm overflow-hidden">
      <div className="bg-slate-800 text-white px-6 py-4">
        <h2 className="text-lg font-bold tracking-wide">
          {stmt.title || "Capability Statement"}
        </h2>
        {stmt.targetAgency && (
          <p className="text-slate-300 text-xs mt-1">
            Prepared for: {stmt.targetAgency}
          </p>
        )}
      </div>
      <div className="px-6 py-4 space-y-4">
        {stmt.companyOverview && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
              Company Overview
            </h3>
            <p className="text-slate-700 leading-relaxed">
              {stmt.companyOverview}
            </p>
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {stmt.coreCompetencies.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Core Competencies
              </h3>
              <ul className="space-y-1">
                {stmt.coreCompetencies.map((c, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-slate-700">
                    <ChevronRight className="h-3.5 w-3.5 mt-0.5 text-blue-500 shrink-0" />
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {stmt.differentiators.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Differentiators
              </h3>
              <ul className="space-y-1">
                {stmt.differentiators.map((d, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-slate-700">
                    <Star className="h-3.5 w-3.5 mt-0.5 text-amber-500 shrink-0" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        {stmt.pastPerformance.length > 0 && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Past Performance Highlights
            </h3>
            <div className="space-y-2">
              {stmt.pastPerformance.map((pp, i) => (
                <div key={pp.id || i} className="border-l-2 border-blue-500 pl-3 py-1">
                  <p className="font-medium text-slate-800">{pp.projectName}</p>
                  <p className="text-xs text-slate-500">{pp.agency}</p>
                  <p className="text-slate-600 mt-0.5">{pp.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="border-t pt-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            Company Data
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            {stmt.companyData.uei && (
              <div>
                <span className="text-slate-400">UEI:</span>{" "}
                <span className="font-mono font-medium">{stmt.companyData.uei}</span>
              </div>
            )}
            {stmt.companyData.cageCode && (
              <div>
                <span className="text-slate-400">CAGE:</span>{" "}
                <span className="font-mono font-medium">{stmt.companyData.cageCode}</span>
              </div>
            )}
            {stmt.companyData.naicsCodes.length > 0 && (
              <div className="col-span-2 sm:col-span-1">
                <span className="text-slate-400">NAICS:</span>{" "}
                <span className="font-mono">{stmt.companyData.naicsCodes.join(", ")}</span>
              </div>
            )}
          </div>
          {stmt.companyData.certifications.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {stmt.companyData.certifications.map((c, i) => (
                <span key={i} className="rounded-full bg-green-100 text-green-800 px-2 py-0.5 text-xs font-medium">
                  {c}
                </span>
              ))}
            </div>
          )}
          {stmt.companyData.contractVehicles.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {stmt.companyData.contractVehicles.map((v, i) => (
                <span key={i} className="rounded-full bg-blue-100 text-blue-800 px-2 py-0.5 text-xs font-medium">
                  {v}
                </span>
              ))}
            </div>
          )}
        </div>
        {stmt.contact.name && (
          <div className="border-t pt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-600">
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {stmt.contact.name}
              {stmt.contact.title && `, ${stmt.contact.title}`}
            </span>
            {stmt.contact.email && (
              <span className="flex items-center gap-1">
                <Mail className="h-3 w-3" />
                {stmt.contact.email}
              </span>
            )}
            {stmt.contact.phone && (
              <span className="flex items-center gap-1">
                <Phone className="h-3 w-3" />
                {stmt.contact.phone}
              </span>
            )}
            {stmt.contact.website && (
              <span className="flex items-center gap-1">
                <Globe className="h-3 w-3" />
                {stmt.contact.website}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────

export default function CapabilityStatementsPage() {
  const [statements, setStatements] = useState<CapabilityStatementListItem[]>([]);
  const [view, setView] = useState<ViewMode>("list");
  const [form, setForm] = useState<FormState>(emptyForm());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState<AIImprovementResult | null>(null);
  const [ppDraft, setPpDraft] = useState({ projectName: "", agency: "", summary: "" });

  const loadStatements = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const resp = await getCapabilityStatements();
      setStatements(resp.results || []);
    } catch {
      setError("Failed to load capability statements.");
      setStatements([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadStatements(); }, [loadStatements]);

  // ── Handlers ──────────────────────────────────────────────────

  function handleNew() { setForm(emptyForm()); setAiResult(null); setView("editor"); }

  async function handleEdit(item: CapabilityStatementListItem) {
    try {
      setSaving(true);
      const full = await getCapabilityStatement(item.id);
      setForm(apiToForm(full));
      setAiResult(null);
      setView("editor");
    } catch { setError("Failed to load statement."); } finally { setSaving(false); }
  }

  async function handlePreview(item: CapabilityStatementListItem) {
    try {
      setSaving(true);
      const full = await getCapabilityStatement(item.id);
      setForm(apiToForm(full));
      setView("preview");
    } catch { setError("Failed to load statement."); } finally { setSaving(false); }
  }

  async function handleSave() {
    try {
      setSaving(true);
      const payload = formToPayload(form);
      if (form.id) {
        await updateCapabilityStatement(form.id, payload);
      } else {
        const created = await createCapabilityStatement(payload);
        setForm((prev) => ({ ...prev, id: created.id }));
      }
      await loadStatements();
      setView("list");
    } catch { setError("Failed to save statement."); } finally { setSaving(false); }
  }

  async function handleDelete(id: string) {
    try { setSaving(true); await deleteCapabilityStatement(id); await loadStatements(); }
    catch { setError("Failed to delete."); } finally { setSaving(false); }
  }

  async function handleTogglePrimary(item: CapabilityStatementListItem) {
    try {
      setSaving(true);
      if (item.is_primary) { await unsetPrimary(item.id); } else { await setPrimary(item.id); }
      await loadStatements();
    } catch { setError("Failed to update."); } finally { setSaving(false); }
  }

  async function handleDuplicate(id: string) {
    try { setSaving(true); await duplicateStatement(id); await loadStatements(); }
    catch { setError("Failed to duplicate."); } finally { setSaving(false); }
  }

  async function handleAiImprove() {
    if (!form.id) { setError("Save the statement first before using AI Review."); return; }
    try {
      setAiLoading(true); setAiResult(null);
      const result = await aiImprove(form.id);
      setAiResult(result);
    } catch {
      setAiResult({
        error: "AI service unavailable",
        fallback_tips: [
          "Ensure your company overview is 2-3 concise sentences highlighting your unique value proposition",
          "List 4-6 core competencies that directly align with the target agency's mission",
          "Include at least 3 quantifiable differentiators (percentages, dollar values, time savings)",
          "Past performance entries should include contract values, timelines, and measurable outcomes",
        ],
      });
    } finally { setAiLoading(false); }
  }

  // ── Form helpers ──────────────────────────────────────────────

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }
  function updateContact(key: keyof FormState["contact"], value: string) {
    setForm((prev) => ({ ...prev, contact: { ...prev.contact, [key]: value } }));
  }
  function updateCompanyData(key: "uei" | "cageCode", value: string) {
    setForm((prev) => ({ ...prev, companyData: { ...prev.companyData, [key]: value } }));
  }
  function addToList(key: "coreCompetencies" | "differentiators", value: string) {
    setForm((prev) => ({ ...prev, [key]: [...prev[key], value] }));
  }
  function removeFromList(key: "coreCompetencies" | "differentiators", index: number) {
    setForm((prev) => ({ ...prev, [key]: prev[key].filter((_, i) => i !== index) }));
  }
  function addToCompanyDataList(key: "naicsCodes" | "pscCodes" | "certifications" | "contractVehicles", value: string) {
    setForm((prev) => ({ ...prev, companyData: { ...prev.companyData, [key]: [...prev.companyData[key], value] } }));
  }
  function removeFromCompanyDataList(key: "naicsCodes" | "pscCodes" | "certifications" | "contractVehicles", index: number) {
    setForm((prev) => ({ ...prev, companyData: { ...prev.companyData, [key]: prev.companyData[key].filter((_, i) => i !== index) } }));
  }
  function addPastPerformance() {
    if (!ppDraft.projectName.trim()) return;
    setForm((prev) => ({ ...prev, pastPerformance: [...prev.pastPerformance, { id: `pp-${Date.now()}`, ...ppDraft }] }));
    setPpDraft({ projectName: "", agency: "", summary: "" });
  }
  function removePastPerformance(id: string) {
    setForm((prev) => ({ ...prev, pastPerformance: prev.pastPerformance.filter((pp) => pp.id !== id) }));
  }

  // ── Loading ───────────────────────────────────────────────────

  if (loading && view === "list") {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading statements...</span>
      </div>
    );
  }

  // ── List View ─────────────────────────────────────────────────

  if (view === "list") {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Capability Statements</h1>
            <p className="text-muted-foreground">Build and manage one-page capability statements per Bidvantage Guide</p>
          </div>
          <Button onClick={handleNew} className="gap-2"><Plus className="h-4 w-4" />New Statement</Button>
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex items-center justify-between">
            <span><AlertTriangle className="mr-2 inline h-4 w-4" />{error}</span>
            <Button variant="ghost" size="sm" onClick={() => setError(null)}>Dismiss</Button>
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card><CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100"><FileText className="h-5 w-5 text-blue-600" /></div>
            <div><p className="text-sm text-muted-foreground">Total Statements</p><p className="text-2xl font-bold">{statements.length}</p></div>
          </CardContent></Card>
          <Card><CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100"><Building2 className="h-5 w-5 text-green-600" /></div>
            <div><p className="text-sm text-muted-foreground">Agencies Targeted</p><p className="text-2xl font-bold">{new Set(statements.map((s) => s.target_agency).filter(Boolean)).size}</p></div>
          </CardContent></Card>
          <Card><CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100"><Award className="h-5 w-5 text-amber-600" /></div>
            <div><p className="text-sm text-muted-foreground">Primary Active</p><p className="text-2xl font-bold">{statements.filter((s) => s.is_primary).length > 0 ? "Yes" : "None"}</p></div>
          </CardContent></Card>
        </div>

        <div className="space-y-3">
          {statements.length === 0 ? (
            <Card><CardContent className="flex flex-col items-center justify-center py-16">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground text-lg font-medium mb-1">No capability statements yet</p>
              <p className="text-muted-foreground text-sm mb-4">Create your first one-page capability statement to get started.</p>
              <Button onClick={handleNew} className="gap-2"><Plus className="h-4 w-4" />Create Statement</Button>
            </CardContent></Card>
          ) : (
            statements.map((stmt) => (
              <Card key={stmt.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-5">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <h3 className="font-semibold text-base">{stmt.title || "Untitled Statement"}</h3>
                        <span className="inline-flex items-center rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 text-xs font-medium">v{stmt.version}</span>
                        {stmt.is_primary && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 text-amber-800 px-2 py-0.5 text-xs font-medium"><Star className="h-3 w-3" />Primary</span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                        {stmt.target_agency && (<span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{stmt.target_agency}</span>)}
                        {stmt.target_naics && (<span className="flex items-center gap-1"><Hash className="h-3.5 w-3.5" />NAICS {stmt.target_naics}</span>)}
                        <span>Created {formatDate(stmt.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button variant="outline" size="sm" onClick={() => handleTogglePrimary(stmt)} className="gap-1" disabled={saving}>
                        <Star className={`h-3.5 w-3.5 ${stmt.is_primary ? "fill-amber-400 text-amber-500" : ""}`} />
                        {stmt.is_primary ? "Unset" : "Primary"}
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handlePreview(stmt)} className="gap-1"><Eye className="h-3.5 w-3.5" />Preview</Button>
                      <Button variant="outline" size="sm" onClick={() => handleEdit(stmt)} className="gap-1"><Edit3 className="h-3.5 w-3.5" />Edit</Button>
                      <Button variant="outline" size="sm" onClick={() => handleDuplicate(stmt.id)} disabled={saving}><Copy className="h-3.5 w-3.5" /></Button>
                      <Button variant="outline" size="sm" onClick={() => handleDelete(stmt.id)} className="text-red-600 hover:text-red-700 hover:bg-red-50" disabled={saving}><Trash2 className="h-3.5 w-3.5" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    );
  }

  // ── Preview View ──────────────────────────────────────────────

  if (view === "preview") {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={() => setView("list")} className="gap-1"><ArrowLeft className="h-4 w-4" />Back</Button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Preview</h1>
              <p className="text-muted-foreground text-sm">{form.title || "Untitled Statement"}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setView("editor")} className="gap-1"><Edit3 className="h-4 w-4" />Edit</Button>
            {form.id && (<Button variant="outline" size="sm" onClick={() => handleDuplicate(form.id)} className="gap-1" disabled={saving}><Copy className="h-4 w-4" />Duplicate</Button>)}
            <Button variant="outline" size="sm" className="gap-1"><Download className="h-4 w-4" />Export PDF</Button>
          </div>
        </div>
        <div className="max-w-4xl mx-auto"><PreviewPanel stmt={form} /></div>
      </div>
    );
  }

  // ── Editor View ───────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => { setView("list"); setAiResult(null); }} className="gap-1"><ArrowLeft className="h-4 w-4" />Back</Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{form.id ? "Edit Statement" : "New Statement"}</h1>
            <p className="text-muted-foreground text-sm">Fill in each section per the Bidvantage one-page format</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {form.id && (
            <Button variant="outline" size="sm" onClick={handleAiImprove} disabled={aiLoading} className="gap-1">
              {aiLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              AI Review
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => setView("preview")} className="gap-1"><Eye className="h-4 w-4" />Preview</Button>
          <Button onClick={handleSave} className="gap-1" disabled={saving}>
            {saving && <Loader2 className="mr-1 h-4 w-4 animate-spin" />}
            Save Statement
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex items-center justify-between">
          <span><AlertTriangle className="mr-2 inline h-4 w-4" />{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>Dismiss</Button>
        </div>
      )}

      {/* AI Result Panel */}
      {aiResult && (
        <Card className="border-purple-200 bg-purple-50/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2"><Sparkles className="h-4 w-4 text-purple-600" />AI Review Results</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setAiResult(null)}><X className="h-4 w-4" /></Button>
            </div>
          </CardHeader>
          <CardContent>
            {aiResult.error ? (
              <div className="space-y-3">
                <p className="text-sm text-purple-800">{aiResult.error}. Here are some manual review tips:</p>
                {aiResult.fallback_tips && (
                  <ul className="space-y-1.5">
                    {aiResult.fallback_tips.map((tip, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-purple-700">
                        <ChevronRight className="h-3.5 w-3.5 mt-0.5 shrink-0 text-purple-500" />{tip}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {aiResult.summary && <p className="text-sm text-purple-800">{aiResult.summary}</p>}
                {aiResult.quality_score !== undefined && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-purple-600">Quality Score:</span>
                    <span className="font-bold text-purple-800">{Math.round(aiResult.quality_score * 100)}%</span>
                  </div>
                )}
                {aiResult.suggestions && aiResult.suggestions.length > 0 && (
                  <ul className="space-y-1.5">
                    {aiResult.suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-purple-700">
                        <ChevronRight className="h-3.5 w-3.5 mt-0.5 shrink-0 text-purple-500" />
                        <span><strong>{s.section}:</strong> {s.suggestion}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <div className="xl:col-span-3 space-y-6">
          {/* Statement Meta */}
          <Card><CardHeader><CardTitle className="text-base">Statement Details</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5"><label className="text-sm font-medium">Title</label>
                  <Input value={form.title} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateForm("title", e.target.value)} placeholder="e.g., IT Modernization Capability Statement" /></div>
                <div className="space-y-1.5"><label className="text-sm font-medium">Version</label>
                  <Input value={form.version} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateForm("version", e.target.value)} placeholder="1" /></div>
              </div>
            </CardContent>
          </Card>

          {/* Target Customization */}
          <Card><CardHeader><CardTitle className="text-base">Target Customization</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5"><label className="text-sm font-medium">Target Agency</label>
                  <Input value={form.targetAgency} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateForm("targetAgency", e.target.value)} placeholder="e.g., Department of Defense" /></div>
                <div className="space-y-1.5"><label className="text-sm font-medium">Target NAICS</label>
                  <Input value={form.targetNaics} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateForm("targetNaics", e.target.value)} placeholder="e.g., 541512" /></div>
              </div>
            </CardContent>
          </Card>

          {/* Company Overview */}
          <Card><CardHeader><CardTitle className="text-base">Company Overview</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Brief Company Description</label>
                <textarea className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y"
                  value={form.companyOverview} onChange={(e) => updateForm("companyOverview", e.target.value)}
                  placeholder="Describe your company, its mission, years of experience, and primary focus areas for federal contracting..." />
                <p className="text-xs text-muted-foreground">2-3 sentences recommended. Highlight your unique value proposition and relevant experience.</p>
              </div>
            </CardContent>
          </Card>

          {/* Core Competencies */}
          <Card><CardHeader><CardTitle className="text-base">Core Competencies</CardTitle></CardHeader>
            <CardContent>
              <ListBuilder label="Competencies" items={form.coreCompetencies} onAdd={(v) => addToList("coreCompetencies", v)} onRemove={(i) => removeFromList("coreCompetencies", i)} placeholder="e.g., Cloud Migration & Infrastructure" />
            </CardContent>
          </Card>

          {/* Differentiators */}
          <Card><CardHeader><CardTitle className="text-base">Differentiators</CardTitle></CardHeader>
            <CardContent>
              <ListBuilder label="What sets you apart" items={form.differentiators} onAdd={(v) => addToList("differentiators", v)} onRemove={(i) => removeFromList("differentiators", i)} placeholder="e.g., 100% on-time delivery record over 5 years" />
            </CardContent>
          </Card>

          {/* Past Performance */}
          <Card><CardHeader><CardTitle className="text-base">Past Performance Highlights</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {form.pastPerformance.length > 0 && (
                <div className="space-y-3">
                  {form.pastPerformance.map((pp) => (
                    <div key={pp.id} className="relative border rounded-md p-3 pr-10">
                      <button type="button" onClick={() => removePastPerformance(pp.id!)} className="absolute top-2 right-2 text-muted-foreground hover:text-red-600"><X className="h-4 w-4" /></button>
                      <p className="font-medium text-sm">{pp.projectName}</p>
                      <p className="text-xs text-muted-foreground">{pp.agency}</p>
                      <p className="text-sm text-muted-foreground mt-1">{pp.summary}</p>
                    </div>
                  ))}
                </div>
              )}
              <div className="border rounded-md p-4 bg-slate-50 space-y-3">
                <p className="text-sm font-medium text-muted-foreground">Add Past Performance Entry</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1.5"><label className="text-xs font-medium">Project Name</label>
                    <Input value={ppDraft.projectName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPpDraft((prev) => ({ ...prev, projectName: e.target.value }))} placeholder="e.g., Cloud Migration Program" /></div>
                  <div className="space-y-1.5"><label className="text-xs font-medium">Agency</label>
                    <Input value={ppDraft.agency} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPpDraft((prev) => ({ ...prev, agency: e.target.value }))} placeholder="e.g., U.S. Army CECOM" /></div>
                </div>
                <div className="space-y-1.5"><label className="text-xs font-medium">Summary</label>
                  <textarea className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y"
                    value={ppDraft.summary} onChange={(e) => setPpDraft((prev) => ({ ...prev, summary: e.target.value }))} placeholder="Brief description of the project, outcomes, and contract value..." /></div>
                <Button type="button" variant="outline" size="sm" onClick={addPastPerformance} className="gap-1"><Plus className="h-4 w-4" />Add Entry</Button>
              </div>
            </CardContent>
          </Card>

          {/* Company Data */}
          <Card><CardHeader><CardTitle className="text-base">Company Data</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5"><label className="text-sm font-medium">UEI (Unique Entity Identifier)</label>
                  <Input value={form.companyData.uei} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateCompanyData("uei", e.target.value)} placeholder="e.g., JKML9876ABCDE" /></div>
                <div className="space-y-1.5"><label className="text-sm font-medium">CAGE Code</label>
                  <Input value={form.companyData.cageCode} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateCompanyData("cageCode", e.target.value)} placeholder="e.g., 7X4K2" /></div>
              </div>
              <ListBuilder label="NAICS Codes" items={form.companyData.naicsCodes} onAdd={(v) => addToCompanyDataList("naicsCodes", v)} onRemove={(i) => removeFromCompanyDataList("naicsCodes", i)} placeholder="e.g., 541512" />
              <ListBuilder label="PSC Codes" items={form.companyData.pscCodes} onAdd={(v) => addToCompanyDataList("pscCodes", v)} onRemove={(i) => removeFromCompanyDataList("pscCodes", i)} placeholder="e.g., D302" />
              <ListBuilder label="Certifications" items={form.companyData.certifications} onAdd={(v) => addToCompanyDataList("certifications", v)} onRemove={(i) => removeFromCompanyDataList("certifications", i)} placeholder="e.g., SDVOSB, ISO 27001" />
              <ListBuilder label="Contract Vehicles" items={form.companyData.contractVehicles} onAdd={(v) => addToCompanyDataList("contractVehicles", v)} onRemove={(i) => removeFromCompanyDataList("contractVehicles", i)} placeholder="e.g., GSA MAS IT, SEWP V" />
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card><CardHeader><CardTitle className="text-base">Contact Information</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5"><label className="text-sm font-medium">Contact Name</label>
                  <Input value={form.contact.name} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateContact("name", e.target.value)} placeholder="e.g., Jane Smith" /></div>
                <div className="space-y-1.5"><label className="text-sm font-medium">Title</label>
                  <Input value={form.contact.title} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateContact("title", e.target.value)} placeholder="e.g., CEO" /></div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5"><label className="text-sm font-medium">Email</label>
                  <Input value={form.contact.email} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateContact("email", e.target.value)} placeholder="e.g., jane@company.com" /></div>
                <div className="space-y-1.5"><label className="text-sm font-medium">Phone</label>
                  <Input value={form.contact.phone} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateContact("phone", e.target.value)} placeholder="e.g., (703) 555-0100" /></div>
              </div>
              <div className="space-y-1.5"><label className="text-sm font-medium">Website</label>
                <Input value={form.contact.website} onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateContact("website", e.target.value)} placeholder="e.g., www.company.com" /></div>
            </CardContent>
          </Card>
        </div>

        {/* Live Preview */}
        <div className="xl:col-span-2">
          <div className="sticky top-6 space-y-3">
            <div className="flex items-center gap-2">
              <Eye className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Live Preview</h2>
            </div>
            <PreviewPanel stmt={form} />
          </div>
        </div>
      </div>
    </div>
  );
}
