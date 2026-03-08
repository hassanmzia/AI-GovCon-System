"use client";

import { useState } from "react";
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
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

interface PastPerformanceEntry {
  id: string;
  projectName: string;
  agency: string;
  summary: string;
}

interface ContactInfo {
  name: string;
  title: string;
  email: string;
  phone: string;
  website: string;
}

interface CompanyData {
  uei: string;
  cageCode: string;
  naicsCodes: string[];
  pscCodes: string[];
  certifications: string[];
  contractVehicles: string[];
}

interface CapabilityStatement {
  id: string;
  title: string;
  version: string;
  targetAgency: string;
  targetNaics: string;
  isPrimary: boolean;
  createdAt: string;
  companyOverview: string;
  coreCompetencies: string[];
  differentiators: string[];
  pastPerformance: PastPerformanceEntry[];
  companyData: CompanyData;
  contact: ContactInfo;
}

// ── Mock Data ──────────────────────────────────────────────────────────────

function createId(): string {
  return Math.random().toString(36).slice(2, 10);
}

const MOCK_STATEMENTS: CapabilityStatement[] = [
  {
    id: "cs-1",
    title: "IT Modernization Capability Statement",
    version: "2.1",
    targetAgency: "Department of Defense",
    targetNaics: "541512",
    isPrimary: true,
    createdAt: "2025-11-15",
    companyOverview:
      "Apex Federal Solutions is a Service-Disabled Veteran-Owned Small Business specializing in IT modernization, cloud migration, and cybersecurity services for federal agencies. With over 15 years of experience supporting DoD and civilian agencies, we deliver mission-critical technology solutions that improve operational efficiency and security posture.",
    coreCompetencies: [
      "Cloud Migration & Infrastructure (AWS GovCloud, Azure Government)",
      "Cybersecurity & Zero Trust Architecture",
      "Agile Software Development & DevSecOps",
      "IT Service Management & Help Desk Operations",
      "Data Analytics & Business Intelligence",
    ],
    differentiators: [
      "100% of projects delivered on time and within budget over the past 5 years",
      "FedRAMP-authorized managed services platform",
      "Proprietary AI-powered threat detection reducing incident response time by 60%",
      "CMMC Level 3 certified with dedicated compliance team",
    ],
    pastPerformance: [
      {
        id: "pp-1",
        projectName: "Enterprise Cloud Migration Program",
        agency: "U.S. Army CECOM",
        summary:
          "Migrated 200+ legacy applications to AWS GovCloud, achieving 40% cost reduction and 99.99% uptime. $45M contract value over 5 years.",
      },
      {
        id: "pp-2",
        projectName: "Cybersecurity Operations Center",
        agency: "Defense Information Systems Agency (DISA)",
        summary:
          "Designed and operated 24/7 SOC supporting 50,000 endpoints. Reduced mean time to detect threats from 72 hours to under 15 minutes.",
      },
      {
        id: "pp-3",
        projectName: "DevSecOps Platform Modernization",
        agency: "Department of the Air Force",
        summary:
          "Implemented CI/CD pipeline with automated security scanning, accelerating software delivery from quarterly releases to bi-weekly deployments.",
      },
    ],
    companyData: {
      uei: "JKML9876ABCDE",
      cageCode: "7X4K2",
      naicsCodes: ["541512", "541511", "541519", "541513", "518210"],
      pscCodes: ["D302", "D306", "D310", "D399"],
      certifications: [
        "SDVOSB",
        "8(a)",
        "ISO 27001",
        "ISO 9001",
        "CMMC Level 3",
      ],
      contractVehicles: [
        "GSA MAS IT (47QTCA)",
        "SEWP V",
        "CIO-SP3",
        "OASIS SB Pool 1",
      ],
    },
    contact: {
      name: "James Richardson",
      title: "Chief Executive Officer",
      email: "jrichardson@apexfederalsolutions.com",
      phone: "(703) 555-0142",
      website: "www.apexfederalsolutions.com",
    },
  },
  {
    id: "cs-2",
    title: "Healthcare IT Solutions",
    version: "1.0",
    targetAgency: "Department of Veterans Affairs",
    targetNaics: "541511",
    isPrimary: false,
    createdAt: "2026-01-22",
    companyOverview:
      "Apex Federal Solutions provides specialized healthcare IT services including electronic health record modernization, telehealth platform development, and clinical data interoperability solutions for federal health agencies.",
    coreCompetencies: [
      "EHR Modernization & Integration",
      "Telehealth Platform Development",
      "HL7 FHIR & Healthcare Data Interoperability",
      "Clinical Decision Support Systems",
    ],
    differentiators: [
      "Deep VA-specific domain expertise with 8+ years of continuous service",
      "Proven EHR migration methodology reducing clinician downtime by 75%",
      "Staff includes 12 certified health IT specialists",
    ],
    pastPerformance: [
      {
        id: "pp-4",
        projectName: "Telehealth Expansion Initiative",
        agency: "Veterans Health Administration",
        summary:
          "Deployed telehealth capabilities across 35 VA medical centers, enabling 2M+ virtual visits annually.",
      },
    ],
    companyData: {
      uei: "JKML9876ABCDE",
      cageCode: "7X4K2",
      naicsCodes: ["541511", "541512", "621999"],
      pscCodes: ["D302", "D306", "AJ13"],
      certifications: ["SDVOSB", "8(a)", "ISO 27001", "HITRUST CSF"],
      contractVehicles: ["GSA MAS IT (47QTCA)", "T4NG", "VA MHIS"],
    },
    contact: {
      name: "James Richardson",
      title: "Chief Executive Officer",
      email: "jrichardson@apexfederalsolutions.com",
      phone: "(703) 555-0142",
      website: "www.apexfederalsolutions.com",
    },
  },
  {
    id: "cs-3",
    title: "Data Analytics & AI Services",
    version: "1.2",
    targetAgency: "Department of Homeland Security",
    targetNaics: "541519",
    isPrimary: false,
    createdAt: "2026-02-10",
    companyOverview:
      "Apex Federal Solutions delivers advanced data analytics, artificial intelligence, and machine learning solutions that enable federal agencies to transform raw data into actionable intelligence for improved decision-making and mission outcomes.",
    coreCompetencies: [
      "Machine Learning & AI Model Development",
      "Big Data Architecture & Engineering",
      "Predictive Analytics & Statistical Modeling",
      "Natural Language Processing",
      "Data Visualization & Dashboards",
    ],
    differentiators: [
      "Responsible AI framework aligned with NIST AI RMF",
      "Proprietary data pipeline reducing time-to-insight by 80%",
      "Team includes 20+ data scientists with active TS/SCI clearances",
    ],
    pastPerformance: [
      {
        id: "pp-5",
        projectName: "Border Threat Analytics Platform",
        agency: "CBP Office of Information Technology",
        summary:
          "Built ML-based threat scoring model processing 10M+ records daily with 94% accuracy, supporting frontline decision-making.",
      },
      {
        id: "pp-6",
        projectName: "Fraud Detection & Prevention System",
        agency: "DHS Office of Inspector General",
        summary:
          "Developed anomaly detection system identifying $120M in potential fraud across grant programs using advanced graph analytics.",
      },
    ],
    companyData: {
      uei: "JKML9876ABCDE",
      cageCode: "7X4K2",
      naicsCodes: ["541519", "541512", "541511", "518210"],
      pscCodes: ["D302", "D311", "D317", "D399"],
      certifications: ["SDVOSB", "8(a)", "ISO 27001", "ISO 9001"],
      contractVehicles: ["GSA MAS IT (47QTCA)", "SEWP V", "Alliant 2 SB"],
    },
    contact: {
      name: "James Richardson",
      title: "Chief Executive Officer",
      email: "jrichardson@apexfederalsolutions.com",
      phone: "(703) 555-0142",
      website: "www.apexfederalsolutions.com",
    },
  },
];

function emptyStatement(): CapabilityStatement {
  return {
    id: createId(),
    title: "",
    version: "1.0",
    targetAgency: "",
    targetNaics: "",
    isPrimary: false,
    createdAt: new Date().toISOString().split("T")[0],
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
    contact: {
      name: "",
      title: "",
      email: "",
      phone: "",
      website: "",
    },
  };
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── List Item Builder ──────────────────────────────────────────────────────

function ListBuilder({
  label,
  items,
  onAdd,
  onRemove,
  placeholder,
}: {
  label: string;
  items: string[];
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
  placeholder?: string;
}) {
  const [draft, setDraft] = useState("");

  function handleAdd() {
    const trimmed = draft.trim();
    if (trimmed) {
      onAdd(trimmed);
      setDraft("");
    }
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground">{label}</label>
      <div className="flex gap-2">
        <Input
          value={draft}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setDraft(e.target.value)
          }
          placeholder={placeholder || `Add ${label.toLowerCase()}...`}
          onKeyDown={(e: React.KeyboardEvent) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
        />
        <Button type="button" variant="outline" size="sm" onClick={handleAdd}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {items.length > 0 && (
        <ul className="space-y-1">
          {items.map((item, i) => (
            <li
              key={i}
              className="flex items-center justify-between rounded-md border px-3 py-1.5 text-sm"
            >
              <span className="flex-1 mr-2">{item}</span>
              <button
                type="button"
                onClick={() => onRemove(i)}
                className="text-muted-foreground hover:text-red-600 shrink-0"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ── Preview Panel ──────────────────────────────────────────────────────────

function PreviewPanel({ stmt }: { stmt: CapabilityStatement }) {
  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Preview Header Bar */}
      <div className="bg-slate-800 text-white px-6 py-4">
        <h2 className="text-lg font-bold tracking-tight">
          {stmt.title || "Capability Statement"}
        </h2>
        {stmt.targetAgency && (
          <p className="text-slate-300 text-xs mt-0.5">
            Prepared for: {stmt.targetAgency}
          </p>
        )}
      </div>

      <div className="p-6 space-y-5 text-sm">
        {/* Company Overview */}
        {stmt.companyOverview && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              Company Overview
            </h3>
            <p className="text-slate-700 leading-relaxed">
              {stmt.companyOverview}
            </p>
          </div>
        )}

        {/* Two-column: Core Competencies + Differentiators */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {stmt.coreCompetencies.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Core Competencies
              </h3>
              <ul className="space-y-1">
                {stmt.coreCompetencies.map((c, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-slate-700">
                    <ChevronRight className="h-3.5 w-3.5 mt-0.5 text-blue-600 shrink-0" />
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

        {/* Past Performance */}
        {stmt.pastPerformance.length > 0 && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Past Performance Highlights
            </h3>
            <div className="space-y-2">
              {stmt.pastPerformance.map((pp) => (
                <div
                  key={pp.id}
                  className="border-l-2 border-blue-500 pl-3 py-1"
                >
                  <p className="font-medium text-slate-800">
                    {pp.projectName}
                  </p>
                  <p className="text-xs text-slate-500">{pp.agency}</p>
                  <p className="text-slate-600 mt-0.5">{pp.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Company Data Grid */}
        {(stmt.companyData.uei ||
          stmt.companyData.cageCode ||
          stmt.companyData.naicsCodes.length > 0 ||
          stmt.companyData.certifications.length > 0) && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Company Data
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-2 text-xs">
              {stmt.companyData.uei && (
                <div>
                  <span className="font-semibold text-slate-500">UEI:</span>{" "}
                  <span className="text-slate-700">{stmt.companyData.uei}</span>
                </div>
              )}
              {stmt.companyData.cageCode && (
                <div>
                  <span className="font-semibold text-slate-500">CAGE:</span>{" "}
                  <span className="text-slate-700">
                    {stmt.companyData.cageCode}
                  </span>
                </div>
              )}
              {stmt.companyData.naicsCodes.length > 0 && (
                <div className="col-span-2 md:col-span-1">
                  <span className="font-semibold text-slate-500">NAICS:</span>{" "}
                  <span className="text-slate-700">
                    {stmt.companyData.naicsCodes.join(", ")}
                  </span>
                </div>
              )}
              {stmt.companyData.pscCodes.length > 0 && (
                <div className="col-span-2 md:col-span-1">
                  <span className="font-semibold text-slate-500">PSC:</span>{" "}
                  <span className="text-slate-700">
                    {stmt.companyData.pscCodes.join(", ")}
                  </span>
                </div>
              )}
            </div>
            {stmt.companyData.certifications.length > 0 && (
              <div className="mt-2">
                <span className="font-semibold text-xs text-slate-500">
                  Certifications:{" "}
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {stmt.companyData.certifications.map((cert, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full bg-green-100 text-green-800 px-2 py-0.5 text-xs font-medium"
                    >
                      {cert}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {stmt.companyData.contractVehicles.length > 0 && (
              <div className="mt-2">
                <span className="font-semibold text-xs text-slate-500">
                  Contract Vehicles:{" "}
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {stmt.companyData.contractVehicles.map((cv, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full bg-blue-100 text-blue-800 px-2 py-0.5 text-xs font-medium"
                    >
                      {cv}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Contact Footer */}
        {(stmt.contact.name || stmt.contact.email) && (
          <div className="border-t pt-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
              Contact Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-1 text-xs text-slate-700">
              {stmt.contact.name && (
                <div className="flex items-center gap-1.5">
                  <User className="h-3 w-3 text-slate-400" />
                  <span>
                    {stmt.contact.name}
                    {stmt.contact.title ? `, ${stmt.contact.title}` : ""}
                  </span>
                </div>
              )}
              {stmt.contact.email && (
                <div className="flex items-center gap-1.5">
                  <Mail className="h-3 w-3 text-slate-400" />
                  <span>{stmt.contact.email}</span>
                </div>
              )}
              {stmt.contact.phone && (
                <div className="flex items-center gap-1.5">
                  <Phone className="h-3 w-3 text-slate-400" />
                  <span>{stmt.contact.phone}</span>
                </div>
              )}
              {stmt.contact.website && (
                <div className="flex items-center gap-1.5">
                  <Globe className="h-3 w-3 text-slate-400" />
                  <span>{stmt.contact.website}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Preview Footer */}
      <div className="bg-slate-50 border-t px-6 py-2 text-center">
        <p className="text-[10px] text-slate-400">
          v{stmt.version}
          {stmt.targetNaics ? ` | Primary NAICS: ${stmt.targetNaics}` : ""}
        </p>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

type View = "list" | "editor" | "preview";

export default function CapabilityStatementsPage() {
  const [statements, setStatements] =
    useState<CapabilityStatement[]>(MOCK_STATEMENTS);
  const [view, setView] = useState<View>("list");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [form, setForm] = useState<CapabilityStatement>(emptyStatement());

  // ── Past performance draft state ─────────────────────────────────────
  const [ppDraft, setPpDraft] = useState({
    projectName: "",
    agency: "",
    summary: "",
  });

  const activeStatement = activeId
    ? statements.find((s) => s.id === activeId) ?? null
    : null;

  // ── Handlers ─────────────────────────────────────────────────────────

  function handleNew() {
    const fresh = emptyStatement();
    setForm(fresh);
    setActiveId(fresh.id);
    setView("editor");
  }

  function handleEdit(stmt: CapabilityStatement) {
    setForm(JSON.parse(JSON.stringify(stmt)));
    setActiveId(stmt.id);
    setView("editor");
  }

  function handlePreview(stmt: CapabilityStatement) {
    setActiveId(stmt.id);
    setForm(JSON.parse(JSON.stringify(stmt)));
    setView("preview");
  }

  function handleSave() {
    setStatements((prev) => {
      const idx = prev.findIndex((s) => s.id === form.id);
      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = { ...form };
        return updated;
      }
      return [...prev, { ...form }];
    });
    setView("list");
    setActiveId(null);
  }

  function handleDelete(id: string) {
    setStatements((prev) => prev.filter((s) => s.id !== id));
    if (activeId === id) {
      setView("list");
      setActiveId(null);
    }
  }

  function handleTogglePrimary(id: string) {
    setStatements((prev) =>
      prev.map((s) => ({
        ...s,
        isPrimary: s.id === id ? !s.isPrimary : false,
      }))
    );
  }

  function updateForm<K extends keyof CapabilityStatement>(
    key: K,
    value: CapabilityStatement[K]
  ) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateCompanyData<K extends keyof CompanyData>(
    key: K,
    value: CompanyData[K]
  ) {
    setForm((prev) => ({
      ...prev,
      companyData: { ...prev.companyData, [key]: value },
    }));
  }

  function updateContact<K extends keyof ContactInfo>(
    key: K,
    value: ContactInfo[K]
  ) {
    setForm((prev) => ({
      ...prev,
      contact: { ...prev.contact, [key]: value },
    }));
  }

  function addPastPerformance() {
    if (!ppDraft.projectName.trim()) return;
    const entry: PastPerformanceEntry = {
      id: createId(),
      projectName: ppDraft.projectName.trim(),
      agency: ppDraft.agency.trim(),
      summary: ppDraft.summary.trim(),
    };
    setForm((prev) => ({
      ...prev,
      pastPerformance: [...prev.pastPerformance, entry],
    }));
    setPpDraft({ projectName: "", agency: "", summary: "" });
  }

  function removePastPerformance(id: string) {
    setForm((prev) => ({
      ...prev,
      pastPerformance: prev.pastPerformance.filter((pp) => pp.id !== id),
    }));
  }

  function addToList(
    key: "coreCompetencies" | "differentiators",
    value: string
  ) {
    setForm((prev) => ({ ...prev, [key]: [...prev[key], value] }));
  }

  function removeFromList(
    key: "coreCompetencies" | "differentiators",
    index: number
  ) {
    setForm((prev) => ({
      ...prev,
      [key]: prev[key].filter((_, i) => i !== index),
    }));
  }

  function addToCompanyDataList(
    key: "naicsCodes" | "pscCodes" | "certifications" | "contractVehicles",
    value: string
  ) {
    setForm((prev) => ({
      ...prev,
      companyData: {
        ...prev.companyData,
        [key]: [...prev.companyData[key], value],
      },
    }));
  }

  function removeFromCompanyDataList(
    key: "naicsCodes" | "pscCodes" | "certifications" | "contractVehicles",
    index: number
  ) {
    setForm((prev) => ({
      ...prev,
      companyData: {
        ...prev.companyData,
        [key]: prev.companyData[key].filter((_, i) => i !== index),
      },
    }));
  }

  // ── Render: List View ────────────────────────────────────────────────

  if (view === "list") {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              Capability Statements
            </h1>
            <p className="text-muted-foreground">
              Build and manage one-page capability statements per Bidvantage
              Guide
            </p>
          </div>
          <Button onClick={handleNew} className="gap-2">
            <Plus className="h-4 w-4" />
            New Statement
          </Button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="flex items-center gap-4 pt-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">
                  Total Statements
                </p>
                <p className="text-2xl font-bold">{statements.length}</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 pt-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                <Building2 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">
                  Agencies Targeted
                </p>
                <p className="text-2xl font-bold">
                  {new Set(statements.map((s) => s.targetAgency).filter(Boolean))
                    .size}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 pt-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100">
                <Award className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Primary Active</p>
                <p className="text-2xl font-bold">
                  {statements.filter((s) => s.isPrimary).length > 0
                    ? "Yes"
                    : "None"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Statement List */}
        <div className="space-y-3">
          {statements.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground text-lg font-medium mb-1">
                  No capability statements yet
                </p>
                <p className="text-muted-foreground text-sm mb-4">
                  Create your first one-page capability statement to get
                  started.
                </p>
                <Button onClick={handleNew} className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Statement
                </Button>
              </CardContent>
            </Card>
          ) : (
            statements.map((stmt) => (
              <Card key={stmt.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-5">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <h3 className="font-semibold text-base">
                          {stmt.title || "Untitled Statement"}
                        </h3>
                        <span className="inline-flex items-center rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 text-xs font-medium">
                          v{stmt.version}
                        </span>
                        {stmt.isPrimary && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 text-amber-800 px-2 py-0.5 text-xs font-medium">
                            <Star className="h-3 w-3" />
                            Primary
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                        {stmt.targetAgency && (
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3.5 w-3.5" />
                            {stmt.targetAgency}
                          </span>
                        )}
                        {stmt.targetNaics && (
                          <span className="flex items-center gap-1">
                            <Hash className="h-3.5 w-3.5" />
                            NAICS {stmt.targetNaics}
                          </span>
                        )}
                        <span>Created {formatDate(stmt.createdAt)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTogglePrimary(stmt.id)}
                        className="gap-1"
                      >
                        <Star
                          className={`h-3.5 w-3.5 ${
                            stmt.isPrimary
                              ? "fill-amber-400 text-amber-500"
                              : ""
                          }`}
                        />
                        {stmt.isPrimary ? "Unset Primary" : "Set Primary"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePreview(stmt)}
                        className="gap-1"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        Preview
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(stmt)}
                        className="gap-1"
                      >
                        <Edit3 className="h-3.5 w-3.5" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(stmt.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
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

  // ── Render: Preview View ─────────────────────────────────────────────

  if (view === "preview") {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setView("list")}
              className="gap-1"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Preview</h1>
              <p className="text-muted-foreground text-sm">
                {form.title || "Untitled Statement"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setView("editor")}
              className="gap-1"
            >
              <Edit3 className="h-4 w-4" />
              Edit
            </Button>
            <Button variant="outline" size="sm" className="gap-1">
              <Copy className="h-4 w-4" />
              Duplicate
            </Button>
            <Button variant="outline" size="sm" className="gap-1">
              <Download className="h-4 w-4" />
              Export PDF
            </Button>
          </div>
        </div>

        {/* Preview */}
        <div className="max-w-4xl mx-auto">
          <PreviewPanel stmt={form} />
        </div>
      </div>
    );
  }

  // ── Render: Editor View ──────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setView("list");
              setActiveId(null);
            }}
            className="gap-1"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {statements.find((s) => s.id === form.id)
                ? "Edit Statement"
                : "New Statement"}
            </h1>
            <p className="text-muted-foreground text-sm">
              Fill in each section per the Bidvantage one-page format
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setView("preview");
            }}
            className="gap-1"
          >
            <Eye className="h-4 w-4" />
            Preview
          </Button>
          <Button onClick={handleSave} className="gap-1">
            Save Statement
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Editor (left 3 columns) */}
        <div className="xl:col-span-3 space-y-6">
          {/* Statement Meta */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Statement Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Title</label>
                  <Input
                    value={form.title}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateForm("title", e.target.value)
                    }
                    placeholder="e.g., IT Modernization Capability Statement"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Version</label>
                  <Input
                    value={form.version}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateForm("version", e.target.value)
                    }
                    placeholder="1.0"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Target Customization */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Target Customization</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Target Agency</label>
                  <Input
                    value={form.targetAgency}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateForm("targetAgency", e.target.value)
                    }
                    placeholder="e.g., Department of Defense"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Target NAICS</label>
                  <Input
                    value={form.targetNaics}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateForm("targetNaics", e.target.value)
                    }
                    placeholder="e.g., 541512"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Company Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Company Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">
                  Brief Company Description
                </label>
                <textarea
                  className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                  value={form.companyOverview}
                  onChange={(e) =>
                    updateForm("companyOverview", e.target.value)
                  }
                  placeholder="Describe your company, its mission, years of experience, and primary focus areas for federal contracting..."
                />
                <p className="text-xs text-muted-foreground">
                  2-3 sentences recommended. Highlight your unique value
                  proposition and relevant experience.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Core Competencies */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Core Competencies</CardTitle>
            </CardHeader>
            <CardContent>
              <ListBuilder
                label="Competencies"
                items={form.coreCompetencies}
                onAdd={(v) => addToList("coreCompetencies", v)}
                onRemove={(i) => removeFromList("coreCompetencies", i)}
                placeholder="e.g., Cloud Migration & Infrastructure"
              />
            </CardContent>
          </Card>

          {/* Differentiators */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Differentiators</CardTitle>
            </CardHeader>
            <CardContent>
              <ListBuilder
                label="What sets you apart"
                items={form.differentiators}
                onAdd={(v) => addToList("differentiators", v)}
                onRemove={(i) => removeFromList("differentiators", i)}
                placeholder="e.g., 100% on-time delivery record over 5 years"
              />
            </CardContent>
          </Card>

          {/* Past Performance */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Past Performance Highlights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Existing entries */}
              {form.pastPerformance.length > 0 && (
                <div className="space-y-3">
                  {form.pastPerformance.map((pp) => (
                    <div
                      key={pp.id}
                      className="relative border rounded-md p-3 pr-10"
                    >
                      <button
                        type="button"
                        onClick={() => removePastPerformance(pp.id)}
                        className="absolute top-2 right-2 text-muted-foreground hover:text-red-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                      <p className="font-medium text-sm">{pp.projectName}</p>
                      <p className="text-xs text-muted-foreground">
                        {pp.agency}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {pp.summary}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Add new entry */}
              <div className="border rounded-md p-4 bg-slate-50 space-y-3">
                <p className="text-sm font-medium text-muted-foreground">
                  Add Past Performance Entry
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium">Project Name</label>
                    <Input
                      value={ppDraft.projectName}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setPpDraft((prev) => ({
                          ...prev,
                          projectName: e.target.value,
                        }))
                      }
                      placeholder="e.g., Cloud Migration Program"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium">Agency</label>
                    <Input
                      value={ppDraft.agency}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setPpDraft((prev) => ({
                          ...prev,
                          agency: e.target.value,
                        }))
                      }
                      placeholder="e.g., U.S. Army CECOM"
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium">Summary</label>
                  <textarea
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y"
                    value={ppDraft.summary}
                    onChange={(e) =>
                      setPpDraft((prev) => ({
                        ...prev,
                        summary: e.target.value,
                      }))
                    }
                    placeholder="Brief description of the project, outcomes, and contract value..."
                  />
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addPastPerformance}
                  className="gap-1"
                >
                  <Plus className="h-4 w-4" />
                  Add Entry
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Company Data */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Company Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">
                    UEI (Unique Entity Identifier)
                  </label>
                  <Input
                    value={form.companyData.uei}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateCompanyData("uei", e.target.value)
                    }
                    placeholder="e.g., JKML9876ABCDE"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">CAGE Code</label>
                  <Input
                    value={form.companyData.cageCode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateCompanyData("cageCode", e.target.value)
                    }
                    placeholder="e.g., 7X4K2"
                  />
                </div>
              </div>

              <ListBuilder
                label="NAICS Codes"
                items={form.companyData.naicsCodes}
                onAdd={(v) => addToCompanyDataList("naicsCodes", v)}
                onRemove={(i) => removeFromCompanyDataList("naicsCodes", i)}
                placeholder="e.g., 541512"
              />

              <ListBuilder
                label="PSC Codes"
                items={form.companyData.pscCodes}
                onAdd={(v) => addToCompanyDataList("pscCodes", v)}
                onRemove={(i) => removeFromCompanyDataList("pscCodes", i)}
                placeholder="e.g., D302"
              />

              <ListBuilder
                label="Certifications"
                items={form.companyData.certifications}
                onAdd={(v) => addToCompanyDataList("certifications", v)}
                onRemove={(i) => removeFromCompanyDataList("certifications", i)}
                placeholder="e.g., SDVOSB, ISO 27001"
              />

              <ListBuilder
                label="Contract Vehicles"
                items={form.companyData.contractVehicles}
                onAdd={(v) => addToCompanyDataList("contractVehicles", v)}
                onRemove={(i) =>
                  removeFromCompanyDataList("contractVehicles", i)
                }
                placeholder="e.g., GSA MAS IT, SEWP V"
              />
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Contact Name</label>
                  <Input
                    value={form.contact.name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateContact("name", e.target.value)
                    }
                    placeholder="e.g., Jane Smith"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Title</label>
                  <Input
                    value={form.contact.title}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateContact("title", e.target.value)
                    }
                    placeholder="e.g., CEO"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Email</label>
                  <Input
                    value={form.contact.email}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateContact("email", e.target.value)
                    }
                    placeholder="e.g., jane@company.com"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Phone</label>
                  <Input
                    value={form.contact.phone}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      updateContact("phone", e.target.value)
                    }
                    placeholder="e.g., (703) 555-0100"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Website</label>
                <Input
                  value={form.contact.website}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    updateContact("website", e.target.value)
                  }
                  placeholder="e.g., www.company.com"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Preview (right 2 columns) */}
        <div className="xl:col-span-2">
          <div className="sticky top-6 space-y-3">
            <div className="flex items-center gap-2">
              <Eye className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Live Preview
              </h2>
            </div>
            <PreviewPanel stmt={form} />
          </div>
        </div>
      </div>
    </div>
  );
}
