"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import {
  runSolutionArchitect,
  getTechnicalSolution,
  getArchitectureDiagrams,
  getValidationReport,
} from "@/services/architecture";
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

// ── Markdown renderer ─────────────────────────────────────────────────────

/**
 * Preprocess markdown to fix common LLM table formatting issues:
 * - Convert dash-separated tables to proper markdown pipe tables
 * - Ensure pipe tables have proper header separator rows
 */
function preprocessMarkdown(text: string): string {
  const lines = text.split("\n");
  const result: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Skip pure dash separator lines (------- or ---- | ---- | ----)
    if (/^[-\s|]+$/.test(trimmed) && trimmed.includes("-")) {
      // Check if this is a table separator: if previous line has pipes, keep it as markdown separator
      if (i > 0 && result.length > 0 && result[result.length - 1].includes("|")) {
        // Convert to proper markdown separator
        const prevCols = result[result.length - 1].split("|").filter(c => c.trim()).length;
        result.push("| " + Array(prevCols).fill("---").join(" | ") + " |");
      }
      // Otherwise skip the dashes line entirely
      continue;
    }

    // If line contains pipe characters, ensure it's properly formatted
    if (trimmed.includes("|") && !trimmed.startsWith("```")) {
      let cols = trimmed.split("|").map(c => c.trim()).filter(c => c.length > 0);
      if (cols.length >= 2) {
        const formatted = "| " + cols.join(" | ") + " |";
        result.push(formatted);

        // If this looks like a header row (next line is dashes or this is the first pipe line)
        // and we don't already have a separator after it
        const nextLine = i + 1 < lines.length ? lines[i + 1]?.trim() : "";
        const isHeaderRow = i === 0 ||
          (i > 0 && !lines[i - 1]?.trim().includes("|")) ||
          /^[-\s|]+$/.test(nextLine);

        const alreadyHasSep = result.length >= 1 && /^\|[\s-|]+\|$/.test(result[result.length - 1]);

        if (isHeaderRow && !alreadyHasSep && /^[-\s|]+$/.test(nextLine)) {
          // The next line is the separator, it will be handled in the next iteration
        } else if (isHeaderRow && !alreadyHasSep && !nextLine.includes("|") ) {
          // No separator follows — add one
        }
        continue;
      }
    }

    result.push(line);
  }

  // Second pass: ensure every pipe table block has a separator after the first row
  const final: string[] = [];
  let inTable = false;
  let tableRowCount = 0;

  for (let i = 0; i < result.length; i++) {
    const line = result[i];
    const isPipeLine = line.trim().startsWith("|") && line.trim().endsWith("|");
    const isSepLine = /^\|[\s-:|]+\|$/.test(line.trim());

    if (isPipeLine) {
      if (!inTable) {
        inTable = true;
        tableRowCount = 0;
      }
      tableRowCount++;
      final.push(line);

      // After first row, if next line is NOT a separator, insert one
      if (tableRowCount === 1 && !isSepLine) {
        const nextLine = result[i + 1]?.trim() || "";
        const nextIsSep = /^\|[\s-:|]+\|$/.test(nextLine);
        if (!nextIsSep) {
          const colCount = line.split("|").filter(c => c.trim()).length;
          final.push("| " + Array(colCount).fill("---").join(" | ") + " |");
        }
      }
    } else {
      inTable = false;
      tableRowCount = 0;
      final.push(line);
    }
  }

  return final.join("\n");
}

function MarkdownContent({ content }: { content: string }) {
  const processed = preprocessMarkdown(content);

  return (
    <div className="prose prose-sm max-w-none text-muted-foreground prose-headings:text-foreground prose-strong:text-foreground">
      <ReactMarkdown
        components={{
          h1: ({ children }) => <h3 className="text-base font-bold mt-4 mb-2 text-foreground">{children}</h3>,
          h2: ({ children }) => <h4 className="text-sm font-bold mt-3 mb-1.5 text-foreground">{children}</h4>,
          h3: ({ children }) => <h5 className="text-sm font-semibold mt-2 mb-1 text-foreground">{children}</h5>,
          p: ({ children }) => <p className="text-sm leading-relaxed mb-2">{children}</p>,
          ul: ({ children }) => <ul className="text-sm space-y-1 mb-3 ml-1">{children}</ul>,
          ol: ({ children }) => <ol className="text-sm space-y-1 mb-3 ml-1 list-decimal list-inside">{children}</ol>,
          li: ({ children }) => (
            <li className="text-sm leading-relaxed flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary/60 shrink-0" />
              <span>{children}</span>
            </li>
          ),
          strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
          table: ({ children }) => (
            <div className="overflow-x-auto my-4 rounded-xl border border-border shadow-sm">
              <table className="w-full text-sm border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-primary/10">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2.5 text-left text-xs font-bold text-primary uppercase tracking-wider border-b-2 border-primary/20">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2.5 text-sm text-foreground border-b border-border">
              {children}
            </td>
          ),
          tr: ({ children }) => (
            <tr className="even:bg-secondary/40 hover:bg-primary/5 transition-colors">{children}</tr>
          ),
          code: ({ children }) => (
            <code className="rounded bg-secondary px-1.5 py-0.5 text-xs font-mono">{children}</code>
          ),
          hr: () => <hr className="my-4 border-secondary" />,
        }}
      >
        {processed}
      </ReactMarkdown>
    </div>
  );
}

// ── Mermaid diagram viewer ─────────────────────────────────────────────────

/**
 * Convert unsupported C4 diagram syntax to standard flowchart.
 * C4Context/C4Container use actor(), container(), component(), boundary()
 * which aren't supported by standard Mermaid. Convert to graph TD.
 */
function convertC4ToFlowchart(code: string): string {
  const trimmed = code.trim();
  // Only convert if it starts with a C4 keyword
  if (!/^C4(Context|Container|Deployment|Component)/m.test(trimmed)) {
    return code;
  }

  const nodes: string[] = [];
  const edges: string[] = [];
  const styles: string[] = [];
  let nodeCounter = 0;
  const idMap: Record<string, string> = {};

  function getNodeId(alias: string): string {
    if (!idMap[alias]) {
      idMap[alias] = `n${nodeCounter++}`;
    }
    return idMap[alias];
  }

  for (const line of trimmed.split("\n")) {
    const stripped = line.trim();

    // actor(alias, "Label") or Person(alias, "Label", "Desc")
    const actorMatch = stripped.match(/^(?:actor|Person|Person_Ext)\s*\(\s*(\w+)\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]*)")?\)/);
    if (actorMatch) {
      const id = getNodeId(actorMatch[1]);
      nodes.push(`    ${id}[/"${actorMatch[2]}"\\]`);
      styles.push(`    style ${id} fill:#08427B,color:#fff`);
      continue;
    }

    // container(alias, "Label", "Tech") or System(alias, ...)
    const containerMatch = stripped.match(/^(?:container|container_system|System|System_Ext|Container|Container_Ext|component|Component)\s*\(\s*(\w+)\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]*)")?/);
    if (containerMatch) {
      const id = getNodeId(containerMatch[1]);
      const label = containerMatch[3]
        ? `${containerMatch[2]}<br/><i>${containerMatch[3]}</i>`
        : containerMatch[2];
      nodes.push(`    ${id}[${label}]`);
      styles.push(`    style ${id} fill:#1168BD,color:#fff`);
      continue;
    }

    // Rel(from, to, "label") or Rel_D, Rel_R, etc.
    const relMatch = stripped.match(/^Rel(?:_[A-Z])?\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*"([^"]+)"/);
    if (relMatch) {
      edges.push(`    ${getNodeId(relMatch[1])} -->|${relMatch[3]}| ${getNodeId(relMatch[2])}`);
      continue;
    }

    // Simple arrow: Alias --> Alias : Label
    const arrowMatch = stripped.match(/^(\w+)\s*-->\s*(\w+)\s*:\s*(.+)/);
    if (arrowMatch) {
      edges.push(`    ${getNodeId(arrowMatch[1])} -->|${arrowMatch[3].trim()}| ${getNodeId(arrowMatch[2])}`);
      continue;
    }
  }

  if (nodes.length === 0) return code; // Conversion failed, return original

  return ["graph TD", ...nodes, "", ...edges, "", ...styles].join("\n");
}

/**
 * Fix common Mermaid syntax errors produced by LLMs (especially smaller models like DeepSeek).
 */
function sanitizeMermaid(code: string): string {
  // First, try converting C4 syntax to standard flowchart
  let fixed = convertC4ToFlowchart(code);

  // Fix classDef class references: "class A, B, C styleName" → "class A,B,C styleName"
  fixed = fixed.replace(
    /^(\s*class\s+)([A-Za-z0-9_]+(?:\s*,\s*[A-Za-z0-9_]+)*)(\s+\w+)\s*;?\s*$/gm,
    (_match, prefix, nodeList, styleName) => {
      const nodes = nodeList.split(",").map((n: string) => n.trim()).join(",");
      return `${prefix}${nodes}${styleName}`;
    }
  );

  // Remove markdown bold/italic markers **text** or *text*
  fixed = fixed.replace(/\*\*([^*]+)\*\*/g, "$1");
  fixed = fixed.replace(/\*([^*]+)\*/g, "$1");

  // Remove trailing semicolons (safe for most diagram types)
  fixed = fixed.replace(/;\s*$/gm, "");

  // Remove `title` lines (not valid in graph/flowchart)
  fixed = fixed.replace(/^\s*title\s+.+$/gm, "");

  // Replace / in node IDs (e.g. CI/CDPipeline → CICDPipeline)
  // Only replace when NOT inside brackets [...] or pipes |...|
  fixed = fixed.split("\n").map(line => {
    // Process each part of the line that's outside brackets and pipes
    return line.replace(/^([^[\]|]*?)([A-Za-z]+)\/([A-Za-z]+)/g, "$1$2$3");
  }).join("\n");

  // Fix "pods, containers" style node references — split into separate lines
  fixed = fixed.replace(
    /^(\s*)(\w+)\s*-->\|([^|]*)\|\s*(\w+)\s*,\s*(\w+)/gm,
    "$1$2 -->|$3| $4\n$1$2 -->|$3| $5"
  );

  // Remove lines where a node definition contains "subgraph" inside brackets
  // e.g. DB -->|Interacts with| API[subgraph APIs Integration ...]
  fixed = fixed.replace(/^.*\[subgraph\b.*$/gm, "");

  // Fix "Subgraph" (capitalized) → "subgraph"
  fixed = fixed.replace(/^\s*Subgraph\b/gm, (m) => m.replace("Subgraph", "subgraph"));

  // Fix node IDs that contain spaces or parens: "Application Execution (Lambda)" → AppExecLambda
  // Match: word spaces word --> or word spaces word[ or start-of-arrow-line patterns
  fixed = fixed.split("\n").map(line => {
    // Don't touch graph/subgraph/end/style/class lines
    if (/^\s*(graph|flowchart|subgraph|end|style|classDef|class)\b/i.test(line)) return line;

    // Replace bare multi-word node refs (not inside brackets) with camelCase IDs
    // Match sequences like "Some Node Name" that appear as source or target of arrows
    line = line.replace(
      /([A-Z][a-z]+(?:\s+[A-Za-z()]+)+)(\s*(?:-->|---|\[))/g,
      (_, words, suffix) => {
        const id = words.replace(/[^A-Za-z0-9]/g, "");
        return id + suffix;
      }
    );
    line = line.replace(
      /(-->(?:\|[^|]*\|)?\s*)([A-Z][a-z]+(?:\s+[A-Za-z()]+)+)(\s*$|\s*\[)/gm,
      (_, prefix, words, suffix) => {
        const id = words.replace(/[^A-Za-z0-9]/g, "");
        return prefix + id + suffix;
      }
    );

    // Fix remaining node IDs with parens: NodeName(stuff) → NodeNameStuff
    line = line.replace(/\b([A-Za-z]\w*)\(([^)]*)\)(?!\s*-->)/g, (_, id, inner) => {
      return id + inner.replace(/[^A-Za-z0-9]/g, "");
    });

    // Fix pipe chars inside node labels (not edge labels): [Build | Deploy] → [Build, Deploy]
    line = line.replace(/\[([^\]]*\|[^\]]*)\]/g, (_, content) => {
      return "[" + content.replace(/\|/g, ",") + "]";
    });

    return line;
  }).join("\n");

  // Ensure the diagram starts with a valid declaration (graph/flowchart)
  // Strip any leading text/whitespace before the declaration
  const declMatch = fixed.match(/^(.*?)((?:graph|flowchart)\s+(?:TD|TB|LR|RL|BT))/m);
  if (declMatch && declMatch.index !== undefined && declMatch.index > 0) {
    fixed = fixed.substring(declMatch.index);
  }

  // If no declaration at all, prepend graph TD
  if (!/^(graph|flowchart)\s+(TD|TB|LR|RL|BT)/m.test(fixed.trim())) {
    fixed = "graph TD\n" + fixed;
  }

  // Remove nested subgraph declarations inside other subgraph blocks
  // (Mermaid supports nested subgraphs but LLMs often produce broken nesting)
  const lines = fixed.split("\n");
  const cleanedLines: string[] = [];
  let subgraphDepth = 0;

  for (const line of lines) {
    const trimmed = line.trim();

    if (/^subgraph\b/i.test(trimmed)) {
      subgraphDepth++;
      // Only allow top-level subgraphs (depth <= 1)
      if (subgraphDepth <= 1) {
        cleanedLines.push(line);
      }
      continue;
    }

    if (trimmed === "end" && subgraphDepth > 0) {
      if (subgraphDepth <= 1) {
        cleanedLines.push(line);
      }
      subgraphDepth--;
      continue;
    }

    // Skip lines inside deeply nested subgraphs
    if (subgraphDepth <= 1) {
      cleanedLines.push(line);
    }
  }

  fixed = cleanedLines.join("\n");

  // Remove empty subgraph blocks (subgraph ... end with nothing between)
  fixed = fixed.replace(/^\s*subgraph\b[^\n]*\n\s*end\s*$/gm, "");

  // Remove lines with broken bracket nesting (unmatched [ or ])
  fixed = fixed.split("\n").filter(line => {
    const open = (line.match(/\[/g) || []).length;
    const close = (line.match(/\]/g) || []).length;
    // Allow lines with no brackets or balanced brackets
    return open === close || (!line.includes("[") && !line.includes("]"));
  }).join("\n");

  return fixed;
}

/**
 * Last-resort rebuild: extract nodes and edges from broken Mermaid code and
 * build a minimal valid graph TD diagram.
 */
function rebuildMermaid(code: string): string | null {
  const nodes = new Set<string>();
  const edges: string[] = [];

  // Sanitize node ID: replace non-alphanumeric chars with nothing
  const cleanId = (id: string) => id.replace(/[^A-Za-z0-9_]/g, "");

  for (const line of code.split("\n")) {
    const trimmed = line.trim();

    // Skip graph/subgraph/end/style/class lines
    if (/^(graph|flowchart|subgraph|end|style|classDef|class)\b/i.test(trimmed)) continue;
    // Skip lines with broken subgraph-inside-brackets
    if (trimmed.includes("[subgraph")) continue;

    // Match arrows with various patterns:
    // A -->|label| B, A --> B, A -->|label| B[Label], A[Label] --> B[Label]
    const arrowMatch = trimmed.match(
      /^\s*([A-Za-z0-9_/.:-]+)(?:\[[^\]]*\])?\s*--+>(?:\|([^|]*)\|)?\s*([A-Za-z0-9_/.:-]+)/
    );
    if (arrowMatch) {
      const from = cleanId(arrowMatch[1]);
      const label = arrowMatch[2]?.trim();
      const to = cleanId(arrowMatch[3]);
      if (from && to && from !== to) {
        nodes.add(from);
        nodes.add(to);
        edges.push(
          label ? `    ${from} -->|${label}| ${to}` : `    ${from} --> ${to}`
        );
      }
    }
  }

  if (nodes.size < 2 || edges.length === 0) return null;

  return ["graph TD", ...edges].join("\n");
}

function MermaidRenderer({ code, id }: { code: string; id: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [renderError, setRenderError] = useState(false);

  useEffect(() => {
    if (!code) return;
    let cancelled = false;

    (async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "neutral",
          securityLevel: "loose",
          fontFamily: "ui-sans-serif, system-ui, sans-serif",
        });

        // Attempt 1: original code
        // Attempt 2: sanitized code
        // Attempt 3: rebuilt minimal graph from extracted nodes/edges
        const candidates = [
          code,
          sanitizeMermaid(code),
          rebuildMermaid(code),
        ];

        // Deduplicate while preserving order, skip nulls
        const seen = new Set<string>();
        const unique = candidates.filter((c): c is string => {
          if (c === null) return false;
          if (seen.has(c)) return false;
          seen.add(c);
          return true;
        });

        let rendered: string | null = null;
        for (let i = 0; i < unique.length; i++) {
          try {
            const result = await mermaid.render(`mermaid-${id}-${i}`, unique[i]);
            rendered = result.svg;
            break;
          } catch {
            // Try next attempt
          }
        }

        if (!cancelled) {
          if (rendered) {
            setSvg(rendered);
            setRenderError(false);
          } else {
            setRenderError(true);
          }
        }
      } catch {
        if (!cancelled) setRenderError(true);
      }
    })();

    return () => { cancelled = true; };
  }, [code, id]);

  if (renderError) {
    return (
      <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 text-sm text-orange-700">
        <p className="font-medium mb-1">Diagram render failed — showing Mermaid source code:</p>
        <pre className="overflow-x-auto rounded bg-white p-3 text-xs leading-relaxed text-foreground border">
          <code>{code}</code>
        </pre>
        <p className="mt-2 text-xs">
          You can copy this code and paste it into{" "}
          <a href="https://mermaid.live" target="_blank" rel="noreferrer" className="underline font-medium">
            mermaid.live
          </a>{" "}
          to view and edit the diagram.
        </p>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin mr-2" /> Rendering diagram...
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="rounded-lg border bg-white p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

function DiagramCard({ diagram, index }: { diagram: ArchitectureDiagram; index: number }) {
  const [showCode, setShowCode] = useState(false);
  const [copied, setCopied] = useState(false);

  const mermaidCode = diagram.mermaid || diagram.mermaid_code || "";

  const handleCopy = () => {
    copyToClipboard(mermaidCode);
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
          <div className="rounded-md bg-secondary/30 px-3 py-2">
            <MarkdownContent
              content={diagram.description
                .replace(/^\*?\*?Description\*?\*?:?\s*/i, "")
                .replace(/^---+\s*/, "")
                .trim()}
            />
          </div>
        )}

        {/* Client-side rendered Mermaid diagram */}
        {mermaidCode && (
          <MermaidRenderer code={mermaidCode} id={`diagram-${index}`} />
        )}

        {/* Mermaid source code toggle */}
        {showCode && mermaidCode && (
          <pre className="overflow-x-auto rounded-lg bg-secondary p-4 text-xs leading-relaxed text-foreground">
            <code>{mermaidCode}</code>
          </pre>
        )}
      </CardContent>
    </Card>
  );
}

// ── Tab content components ─────────────────────────────────────────────────

function RequirementsTab({ analysis }: { analysis: RequirementAnalysis }) {
  const entries = Object.entries(analysis).filter(([, v]) => typeof v === "string" && v.trim());
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
          <MarkdownContent content={value as string} />
        </div>
      ))}
    </div>
  );
}

function SolutionTab({ solution }: { solution: TechnicalSolution }) {
  const entries = Object.entries(solution).filter(([, v]) => typeof v === "string" && v.trim());
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
          <MarkdownContent content={value as string} />
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
        <DiagramCard key={i} diagram={d} index={i} />
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
      {sections.map(([title, sectionContent]) => (
        <div key={title} className="rounded-lg border">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h4 className="font-semibold text-foreground">{title}</h4>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => copyToClipboard(sectionContent)}
            >
              <Copy className="mr-1.5 h-3.5 w-3.5" />
              Copy
            </Button>
          </div>
          <div className="p-4">
            <MarkdownContent content={sectionContent} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ValidationTab({ report }: { report: ValidationReport }) {
  const pass = report.pass != null
    ? report.pass
    : (report.verdict === "PASS" || report.overall_quality === "excellent" || report.overall_quality === "good");
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
              {pass ? "Passed Validation" : "Needs Revision"}
              {report.overall_quality && report.overall_quality !== "needs_revision" && report.overall_quality !== "good"
                ? ` — ${formatKey(report.overall_quality)}`
                : ""}
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

      {/* Full review text as expandable detail */}
      {report.review_text && (
        <details className="rounded-lg border p-4">
          <summary className="cursor-pointer text-sm font-semibold text-foreground">
            Full Validation Review
          </summary>
          <div className="mt-3">
            <MarkdownContent content={report.review_text} />
          </div>
        </details>
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
  const [fromCache, setFromCache] = useState(false);
  const [cacheLoading, setCacheLoading] = useState(false);

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

  // When the selected deal changes, try to load a previously persisted solution.
  useEffect(() => {
    if (!selectedDealId) return;

    let cancelled = false;
    setCacheLoading(true);

    (async () => {
      try {
        const solution = await getTechnicalSolution(selectedDealId);
        if (cancelled || !solution) return;

        // Enrich with persisted diagrams and validation report if available.
        const solutionId = solution.id as string | undefined;
        const [diagrams, validationReport] = await Promise.all([
          solutionId ? getArchitectureDiagrams(solutionId) : Promise.resolve([]),
          solutionId ? getValidationReport(solutionId) : Promise.resolve(null),
        ]);

        if (cancelled) return;

        // Merge persisted diagrams/validation into the result if they exist.
        const mappedDiagrams: ArchitectureDiagram[] = diagrams.length > 0
          ? diagrams.map((d) => ({
              title: d.title,
              type: d.diagram_type,
              mermaid: d.mermaid_code,
              mermaid_code: d.mermaid_code,
              description: d.description,
            }))
          : (solution.diagrams ?? []);

        const mappedValidation: ValidationReport = validationReport
          ? {
              overall_quality: validationReport.overall_quality,
              score: validationReport.score ?? undefined,
              issues: validationReport.issues,
              suggestions: validationReport.suggestions,
              compliance_gaps: validationReport.compliance_gaps,
              pass: validationReport.passed,
            }
          : (solution.validation_report ?? {} as ValidationReport);

        const merged: ArchitectureResult = {
          ...solution,
          diagrams: mappedDiagrams,
          validation_report: mappedValidation,
        };

        setResult(merged);
        setFromCache(true);
        setActiveTab("requirements");
      } catch {
        // Non-fatal — just don't pre-populate.
      } finally {
        if (!cancelled) setCacheLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [selectedDealId]);

  const handleRun = async () => {
    if (!selectedDealId) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setFromCache(false);
    try {
      const data = await runSolutionArchitect(selectedDealId);
      if (data.error) {
        throw new Error(data.error as string);
      }
      setResult(data);
      setActiveTab("requirements");
    } catch (err: unknown) {
      // Extract the error message from the API response if available
      let msg = "Agent failed. Check that the AI Orchestrator is running.";
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const axiosErr = err as any;
      if (axiosErr?.response?.data?.error) {
        msg = axiosErr.response.data.error;
        if (axiosErr.response.data.action) {
          msg += " " + axiosErr.response.data.action;
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
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
                    setFromCache(false);
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
              disabled={!selectedDealId || running || cacheLoading}
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

      {/* Cache loading indicator */}
      {cacheLoading && !running && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground px-1">
          <Loader2 className="h-4 w-4 animate-spin" />
          Checking for previous run...
        </div>
      )}

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
                {(error.toLowerCase().includes("credit") ||
                  error.toLowerCase().includes("api key") ||
                  error.toLowerCase().includes("billing") ||
                  error.toLowerCase().includes("settings")) && (
                  <a
                    href="/settings"
                    className="inline-block mt-2 text-sm font-medium text-blue-600 hover:underline"
                  >
                    Go to Settings to change LLM provider
                  </a>
                )}
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
            {fromCache && (
              <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                <RefreshCw className="h-3 w-3" />
                Loaded from previous run
              </span>
            )}
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
      {!result && !running && !error && !cacheLoading && (
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
