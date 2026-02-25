"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { runSolutionArchitect } from "@/services/architecture";
import { getDeals } from "@/services/deals";
import { Deal } from "@/types/deal";
import {
  ArchitectureResult,
  ArchitectureDiagram,
  RequirementAnalysis,
  TechnicalSolution,
  TechnicalVolume,
  ValidationReport,
} from "@/types/architecture";
import {
  Cpu,
  Loader2,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  Layers,
  FileText,
  ShieldCheck,
  BarChart2,
  Wand2,
  Info,
} from "lucide-react";

// ── Helpers ────────────────────────────────────────────────────────────────

function formatKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

// ── Mermaid diagram viewer ─────────────────────────────────────────────────

function DiagramCard({ diagram }: { diagram: ArchitectureDiagram }) {
  const [showCode, setShowCode] = useState(false);
  const [copied, setCopied] = useState(false);

  // Build mermaid.ink URL for rendered preview (base64 encode the mermaid code)
  const mermaidB64 =
    typeof window !== "undefined"
      ? btoa(unescape(encodeURIComponent(diagram.mermaid)))
      : "";
  const previewUrl = mermaidB64
    ? `https://mermaid.ink/img/${mermaidB64}?theme=neutral`
    : "";

  const handleCopy = () => {
    copyToClipboard(diagram.mermaid);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-sm font-semibold">{diagram.title}</CardTitle>
            {diagram.type && (
              <span className="mt-0.5 inline-block rounded bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground">
                {diagram.type}
              </span>
            )}
          </div>
          <div className="flex gap-2 shrink-0">
            <Button size="sm" variant="ghost" onClick={handleCopy}>
              <Copy className="h-3.5 w-3.5" />
              {copied ? " Copied!" : ""}
            </Button>
            {previewUrl && (
              <a
                href={previewUrl}
                target="_blank"
                rel="noreferrer"
                className={buttonVariants({ size: "sm", variant: "ghost" })}
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowCode((v) => !v)}
            >
              {showCode ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {diagram.description && (
          <p className="text-sm text-muted-foreground">{diagram.description}</p>
        )}

        {/* Rendered preview via mermaid.ink */}
        {previewUrl && (
          <div className="rounded-lg border bg-white p-2 overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt={diagram.title}
              className="max-w-full mx-auto"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
        )}

        {/* Mermaid source code */}
        {showCode && (
          <pre className="overflow-x-auto rounded-lg bg-secondary p-4 text-xs leading-relaxed text-foreground">
            <code>{diagram.mermaid}</code>
          </pre>
        )}
      </CardContent>
    </Card>
  );
}

// ── Tab content components ─────────────────────────────────────────────────

function RequirementsTab({ analysis }: { analysis: RequirementAnalysis }) {
  const entries = Object.entries(analysis).filter(([, v]) => v && v.trim());
  if (!entries.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No requirement analysis available.
      </p>
    );
  }
  return (
    <div className="space-y-4">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded-lg border p-4">
          <h4 className="mb-2 text-sm font-semibold text-foreground">
            {formatKey(key)}
          </h4>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {value}
          </p>
        </div>
      ))}
    </div>
  );
}

function SolutionTab({ solution }: { solution: TechnicalSolution }) {
  const entries = Object.entries(solution).filter(([, v]) => v && v.trim());
  if (!entries.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No solution data available.
      </p>
    );
  }
  return (
    <div className="space-y-4">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded-lg border p-4">
          <h4 className="mb-2 text-sm font-semibold text-foreground flex items-center gap-2">
            <Cpu className="h-4 w-4 text-primary" />
            {formatKey(key)}
          </h4>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {value}
          </p>
        </div>
      ))}
    </div>
  );
}

function DiagramsTab({ diagrams }: { diagrams: ArchitectureDiagram[] }) {
  if (!diagrams.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No diagrams generated.
      </p>
    );
  }
  return (
    <div className="space-y-4">
      {diagrams.map((d, i) => (
        <DiagramCard key={i} diagram={d} />
      ))}
    </div>
  );
}

function TechnicalVolumeTab({ volume }: { volume: TechnicalVolume }) {
  const sections = Object.entries(volume.sections || {});
  if (!sections.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No technical volume sections generated.
      </p>
    );
  }
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>{sections.length} sections</span>
        <span>·</span>
        <span>{volume.diagram_count} diagrams referenced</span>
        {volume.word_count && (
          <>
            <span>·</span>
            <span>~{volume.word_count.toLocaleString()} words</span>
          </>
        )}
      </div>
      {sections.map(([title, content]) => (
        <div key={title} className="rounded-lg border">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h4 className="font-semibold text-foreground">{title}</h4>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => copyToClipboard(content)}
            >
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              Copy
            </Button>
          </div>
          <div className="p-4">
            <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
              {content}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function ValidationTab({ report }: { report: ValidationReport }) {
  const pass = report.pass ?? (report.overall_quality === "excellent" || report.overall_quality === "good");
  const score = report.score;

  return (
    <div className="space-y-4">
      {/* Overall score */}
      <div className={`rounded-lg border p-4 ${pass ? "border-green-200 bg-green-50" : "border-orange-200 bg-orange-50"}`}>
        <div className="flex items-center gap-3">
          {pass ? (
            <CheckCircle className="h-6 w-6 text-green-600" />
          ) : (
            <AlertTriangle className="h-6 w-6 text-orange-600" />
          )}
          <div>
            <p className={`font-semibold ${pass ? "text-green-800" : "text-orange-800"}`}>
              {report.overall_quality
                ? formatKey(report.overall_quality)
                : pass
                ? "Passed Validation"
                : "Needs Revision"}
            </p>
            {score != null && (
              <p className={`text-sm ${pass ? "text-green-600" : "text-orange-600"}`}>
                Quality score: {score}/100
              </p>
            )}
          </div>
        </div>
      </div>

      {report.issues?.length > 0 && (
        <div className="rounded-lg border p-4">
          <h4 className="mb-3 text-sm font-semibold text-foreground">Issues Found</h4>
          <ul className="space-y-2">
            {report.issues.map((issue, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-orange-500" />
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.compliance_gaps?.length > 0 && (
        <div className="rounded-lg border border-red-100 p-4">
          <h4 className="mb-3 text-sm font-semibold text-red-700">Compliance Gaps</h4>
          <ul className="space-y-2">
            {report.compliance_gaps.map((gap, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-red-600">
                <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.suggestions?.length > 0 && (
        <div className="rounded-lg border border-blue-100 p-4">
          <h4 className="mb-3 text-sm font-semibold text-blue-700">Suggestions</h4>
          <ul className="space-y-2">
            {report.suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-blue-700">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── Tab bar ────────────────────────────────────────────────────────────────

type Tab = "requirements" | "solution" | "diagrams" | "volume" | "validation";

const TABS: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "requirements", label: "Requirements", icon: FileText },
  { id: "solution", label: "Solution", icon: Cpu },
  { id: "diagrams", label: "Diagrams", icon: Layers },
  { id: "volume", label: "Technical Volume", icon: BarChart2 },
  { id: "validation", label: "Validation", icon: ShieldCheck },
];

// ── Main page ──────────────────────────────────────────────────────────────

export default function SolutionsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [dealsLoading, setDealsLoading] = useState(true);
  const [selectedDealId, setSelectedDealId] = useState<string>("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ArchitectureResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("requirements");

  const loadDeals = useCallback(async () => {
    setDealsLoading(true);
    try {
      const data = await getDeals({ ordering: "-updated_at", page_size: "100" });
      const active = (data.results ?? []).filter(
        (d: Deal) => !["closed_won", "closed_lost", "no_bid"].includes(d.stage)
      );
      setDeals(active);
    } catch {
      // Non-fatal – show empty list
    } finally {
      setDealsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  const handleRun = async () => {
    if (!selectedDealId) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const data = await runSolutionArchitect(selectedDealId);
      setResult(data);
      setActiveTab("requirements");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Agent failed. Check that the AI Orchestrator is running and ANTHROPIC_API_KEY is configured.";
      setError(msg);
    } finally {
      setRunning(false);
    }
  };

  const selectedDeal = deals.find((d) => d.id === selectedDealId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Solution Architect</h1>
        <p className="text-muted-foreground">
          AI-generated technical architecture, diagrams, and proposal-ready volume
        </p>
      </div>

      {/* Agent info banner */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="pt-5">
          <div className="flex items-start gap-3">
            <Wand2 className="h-5 w-5 text-primary mt-0.5 shrink-0" />
            <div className="text-sm text-foreground">
              <p className="font-medium">9-node LangGraph Pipeline</p>
              <p className="mt-0.5 text-muted-foreground">
                Analyzes RFP requirements across 10 categories → selects architecture frameworks
                (C4, TOGAF, FedRAMP, NIST) → retrieves knowledge vault docs → synthesizes 17 architecture
                areas → generates Mermaid.js diagrams → writes proposal-ready Technical Volume sections →
                self-validates with up to 2 refinement iterations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Deal selector + run */}
      <Card>
        <CardContent className="pt-5">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[260px]">
              <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                Select Deal
              </label>
              {dealsLoading ? (
                <div className="flex items-center gap-2 h-9 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading deals...
                </div>
              ) : (
                <select
                  value={selectedDealId}
                  onChange={(e) => {
                    setSelectedDealId(e.target.value);
                    setResult(null);
                    setError(null);
                  }}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="">-- Choose an active deal --</option>
                  {deals.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title} ({d.stage_display})
                    </option>
                  ))}
                </select>
              )}
            </div>

            <Button
              onClick={handleRun}
              disabled={!selectedDealId || running}
              className="flex items-center gap-2"
            >
              {running ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Running Agent...
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4" />
                  Run Solution Architect
                </>
              )}
            </Button>

            {result && (
              <Button variant="outline" onClick={handleRun} disabled={running}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Re-run
              </Button>
            )}
          </div>

          {/* Selected deal summary */}
          {selectedDeal && (
            <div className="mt-4 flex flex-wrap gap-4 rounded-lg bg-secondary/40 px-4 py-3 text-xs text-muted-foreground">
              <span>
                <strong className="text-foreground">Stage:</strong>{" "}
                {selectedDeal.stage_display}
              </span>
              <span>
                <strong className="text-foreground">Priority:</strong>{" "}
                {selectedDeal.priority_display}
              </span>
              {selectedDeal.estimated_value && (
                <span>
                  <strong className="text-foreground">Value:</strong> $
                  {parseFloat(selectedDeal.estimated_value).toLocaleString()}
                </span>
              )}
              <span>
                <strong className="text-foreground">Win Prob:</strong>{" "}
                {selectedDeal.win_probability}%
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Running indicator */}
      {running && (
        <Card className="border-primary/20">
          <CardContent className="pt-5">
            <div className="flex items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div>
                <p className="font-medium text-foreground">
                  Solution Architect Agent is running...
                </p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Analyzing RFP requirements · Selecting frameworks · Synthesizing solution ·
                  Generating diagrams · Writing technical volume
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  This typically takes 30–120 seconds depending on complexity.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Card className="border-red-200">
          <CardContent className="pt-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-red-700">Agent Failed</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="flex flex-wrap items-center gap-4 rounded-lg border bg-card px-5 py-3 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="font-medium text-foreground">Architecture Complete</span>
            </div>
            <span className="text-muted-foreground">
              {result.selected_frameworks.join(" · ")}
            </span>
            <span className="text-muted-foreground">
              {result.diagrams.length} diagram{result.diagrams.length !== 1 ? "s" : ""}
            </span>
            <span className="text-muted-foreground">
              {Object.keys(result.technical_volume?.sections ?? {}).length} volume sections
            </span>
            {result.iteration_count > 0 && (
              <span className="text-muted-foreground">
                {result.iteration_count} refinement{result.iteration_count !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {/* Tab navigation */}
          <div className="flex gap-1 border-b">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                  activeTab === id
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {activeTab === "requirements" && (
              <RequirementsTab analysis={result.requirement_analysis ?? {}} />
            )}
            {activeTab === "solution" && (
              <SolutionTab solution={result.technical_solution ?? {}} />
            )}
            {activeTab === "diagrams" && (
              <DiagramsTab diagrams={result.diagrams ?? []} />
            )}
            {activeTab === "volume" && (
              <TechnicalVolumeTab volume={result.technical_volume ?? { sections: {}, diagram_count: 0 }} />
            )}
            {activeTab === "validation" && (
              <ValidationTab report={result.validation_report ?? { overall_quality: "", issues: [], suggestions: [], compliance_gaps: [] }} />
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !running && !error && (
        <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
          <Cpu className="h-12 w-12 text-muted-foreground" />
          <div>
            <p className="text-lg font-medium text-foreground">
              No architecture generated yet
            </p>
            <p className="mt-1 text-sm text-muted-foreground max-w-sm">
              Select an active deal and click "Run Solution Architect" to generate a
              complete technical architecture and proposal-ready content.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
