"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Copy,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";
import { ArchitectureDiagram } from "@/types/architecture";

// ── Helpers ──────────────────────────────────────────────────────────────────

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

// ── Markdown ─────────────────────────────────────────────────────────────────

function preprocessMarkdown(text: string): string {
  const lines = text.split("\n");
  const result: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (/^[-\s|]+$/.test(trimmed) && trimmed.includes("-")) {
      if (i > 0 && result.length > 0 && result[result.length - 1].includes("|")) {
        const prevCols = result[result.length - 1].split("|").filter((c) => c.trim()).length;
        result.push("| " + Array(prevCols).fill("---").join(" | ") + " |");
      }
      continue;
    }

    if (trimmed.includes("|") && !trimmed.startsWith("```")) {
      const cols = trimmed
        .split("|")
        .map((c) => c.trim())
        .filter((c) => c.length > 0);
      if (cols.length >= 2) {
        result.push("| " + cols.join(" | ") + " |");
        continue;
      }
    }

    result.push(line);
  }

  // Ensure every pipe table block has a separator after the first row
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

      if (tableRowCount === 1 && !isSepLine) {
        const nextLine = result[i + 1]?.trim() || "";
        const nextIsSep = /^\|[\s-:|]+\|$/.test(nextLine);
        if (!nextIsSep) {
          const colCount = line.split("|").filter((c) => c.trim()).length;
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

export function MarkdownContent({ content }: { content: string }) {
  const processed = preprocessMarkdown(content);

  return (
    <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground/90 prose-strong:text-foreground prose-li:text-foreground/90">
      <ReactMarkdown
        components={{
          h1: ({ children }) => (
            <h3 className="text-base font-bold mt-4 mb-2 text-foreground">{children}</h3>
          ),
          h2: ({ children }) => (
            <h4 className="text-sm font-bold mt-3 mb-1.5 text-foreground">{children}</h4>
          ),
          h3: ({ children }) => (
            <h5 className="text-sm font-semibold mt-2 mb-1 text-foreground">{children}</h5>
          ),
          p: ({ children }) => (
            <p className="text-sm leading-relaxed mb-2 text-foreground/90">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="text-sm space-y-1 mb-3 ml-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="text-sm space-y-1 mb-3 ml-1 list-decimal list-inside">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-sm leading-relaxed text-foreground/90 flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-blue-500/60 shrink-0" />
              <span>{children}</span>
            </li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-4 rounded-lg border border-border shadow-sm">
              <table className="w-full text-sm border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
          th: ({ children }) => (
            <th className="px-4 py-2.5 text-left text-xs font-bold text-foreground/80 uppercase tracking-wider border-b-2 border-border">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2.5 text-sm text-foreground/80 border-b border-border/50">
              {children}
            </td>
          ),
          tr: ({ children }) => (
            <tr className="even:bg-muted/50 hover:bg-accent/30 transition-colors">
              {children}
            </tr>
          ),
          code: ({ children }) => (
            <code className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-foreground/90">
              {children}
            </code>
          ),
          hr: () => <hr className="my-4 border-border" />,
        }}
      >
        {processed}
      </ReactMarkdown>
    </div>
  );
}

// ── Mermaid ──────────────────────────────────────────────────────────────────

function convertC4ToFlowchart(code: string): string {
  const trimmed = code.trim();
  if (!/^C4(Context|Container|Deployment|Component)/m.test(trimmed)) return code;

  const nodes: string[] = [];
  const edges: string[] = [];
  const styles: string[] = [];
  let nodeCounter = 0;
  const idMap: Record<string, string> = {};

  function getNodeId(alias: string): string {
    if (!idMap[alias]) idMap[alias] = `n${nodeCounter++}`;
    return idMap[alias];
  }

  for (const line of trimmed.split("\n")) {
    const stripped = line.trim();
    const actorMatch = stripped.match(
      /^(?:actor|Person|Person_Ext)\s*\(\s*(\w+)\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]*)")?\)/
    );
    if (actorMatch) {
      const id = getNodeId(actorMatch[1]);
      nodes.push(`    ${id}[/"${actorMatch[2]}"\\]`);
      styles.push(`    style ${id} fill:#08427B,color:#fff`);
      continue;
    }
    const containerMatch = stripped.match(
      /^(?:container|container_system|System|System_Ext|Container|Container_Ext|component|Component)\s*\(\s*(\w+)\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]*)")?/
    );
    if (containerMatch) {
      const id = getNodeId(containerMatch[1]);
      const label = containerMatch[3]
        ? `${containerMatch[2]}<br/><i>${containerMatch[3]}</i>`
        : containerMatch[2];
      nodes.push(`    ${id}[${label}]`);
      styles.push(`    style ${id} fill:#1168BD,color:#fff`);
      continue;
    }
    const relMatch = stripped.match(/^Rel(?:_[A-Z])?\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*"([^"]+)"/);
    if (relMatch) {
      edges.push(`    ${getNodeId(relMatch[1])} -->|${relMatch[3]}| ${getNodeId(relMatch[2])}`);
      continue;
    }
    const arrowMatch = stripped.match(/^(\w+)\s*-->\s*(\w+)\s*:\s*(.+)/);
    if (arrowMatch) {
      edges.push(`    ${getNodeId(arrowMatch[1])} -->|${arrowMatch[3].trim()}| ${getNodeId(arrowMatch[2])}`);
    }
  }

  if (nodes.length === 0) return code;
  return ["graph TD", ...nodes, "", ...edges, "", ...styles].join("\n");
}

function sanitizeMermaid(code: string): string {
  let fixed = convertC4ToFlowchart(code);
  fixed = fixed.replace(/\*\*([^*]+)\*\*/g, "$1");
  fixed = fixed.replace(/\*([^*]+)\*/g, "$1");
  fixed = fixed.replace(/;\s*$/gm, "");
  fixed = fixed.replace(/^\s*title\s+.+$/gm, "");
  fixed = fixed.replace(/^.*\[subgraph\b.*$/gm, "");
  fixed = fixed.replace(/\bSubgraph\b/g, "subgraph");

  fixed = fixed
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      if (/^\s*(graph|flowchart|subgraph|end|style|classDef|class)\b/i.test(trimmed)) return line;
      line = line.replace(/\b([A-Za-z]\w*)\/([A-Za-z]\w*)/g, "$1$2");
      line = line.replace(/\b([A-Za-z]\w*)\(([^)]*)\)/g, (_, id, inner) => id + inner.replace(/[^A-Za-z0-9_]/g, ""));
      line = line.replace(/\[([^\]]*)\]/g, (_, content) =>
        content.includes("|") ? "[" + content.replace(/\|/g, " / ") + "]" : "[" + content + "]"
      );
      line = line.replace(/"([^"]+)"/g, (_, content) => content.replace(/[^A-Za-z0-9_]/g, ""));
      line = line.replace(/^(\s*)([A-Z][a-z]+(?:\s+[A-Za-z][a-z]*)+)(\s*(?:\[|-->))/g, (_, indent, words, suffix) => indent + words.replace(/\s+/g, "") + suffix);
      line = line.replace(/(-->(?:\|[^|]*\|)?\s*)([A-Z][a-z]+(?:\s+[A-Za-z][a-z]*)+)(\s*$|\s*\[)/g, (_, prefix, words, suffix) => prefix + words.replace(/\s+/g, "") + suffix);
      return line;
    })
    .join("\n");

  const declMatch = fixed.match(/((?:graph|flowchart)\s+(?:TD|TB|LR|RL|BT))/m);
  if (declMatch && declMatch.index !== undefined) {
    fixed = fixed.substring(declMatch.index);
  } else if (!/^(graph|flowchart)\s+(TD|TB|LR|RL|BT)/m.test(fixed.trim())) {
    fixed = "graph TD\n" + fixed;
  }

  const lines = fixed.split("\n");
  const cleanedLines: string[] = [];
  let subgraphDepth = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    if (/^subgraph\b/i.test(trimmed)) {
      subgraphDepth++;
      if (subgraphDepth <= 1) cleanedLines.push(line);
      continue;
    }
    if (trimmed === "end" && subgraphDepth > 0) {
      if (subgraphDepth <= 1) cleanedLines.push(line);
      subgraphDepth--;
      continue;
    }
    if (subgraphDepth <= 1) cleanedLines.push(line);
  }
  fixed = cleanedLines.join("\n");
  fixed = fixed.replace(/^\s*subgraph\b[^\n]*\n\s*end\s*$/gm, "");
  fixed = fixed
    .split("\n")
    .filter((line) => {
      const open = (line.match(/\[/g) || []).length;
      const close = (line.match(/\]/g) || []).length;
      return open === close;
    })
    .join("\n");
  fixed = fixed
    .split("\n")
    .filter((line) => {
      const open = (line.match(/\(/g) || []).length;
      const close = (line.match(/\)/g) || []).length;
      return open === close;
    })
    .join("\n");
  fixed = fixed
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (!trimmed) return true;
      if (/^(graph|flowchart|subgraph|end|style|classDef|class)\b/i.test(trimmed)) return true;
      if (/\w+.*-->/.test(trimmed) || /-->\s*\w+/.test(trimmed)) return true;
      if (/^\s+\w+\s*$/.test(trimmed)) return true;
      return false;
    })
    .join("\n");
  return fixed;
}

function rebuildMermaid(code: string): string | null {
  const nodeLabels = new Map<string, string>();
  const edges: string[] = [];
  const cleanId = (id: string) => id.replace(/[^A-Za-z0-9_]/g, "").replace(/\s+/g, "");

  for (const line of code.split("\n")) {
    const trimmed = line.trim();
    if (/^(graph|flowchart|subgraph|end|style|classDef|class)\b/i.test(trimmed)) continue;
    if (trimmed.includes("[subgraph") || !trimmed) continue;

    const nodeRe = /([A-Za-z][A-Za-z0-9_/.:\s-]*?)\[([^\]]+)\]/g;
    let nodeMatch: RegExpExecArray | null;
    while ((nodeMatch = nodeRe.exec(trimmed)) !== null) {
      const nid = cleanId(nodeMatch[1]);
      if (nid && nid.length >= 2) nodeLabels.set(nid, nodeMatch[2].replace(/\|/g, "/"));
    }

    const dbRe = /([A-Za-z]\w*)\[\(([^)]+)\)\]/g;
    let dbMatch: RegExpExecArray | null;
    while ((dbMatch = dbRe.exec(trimmed)) !== null) {
      const did = cleanId(dbMatch[1]);
      if (did) nodeLabels.set(did, dbMatch[2]);
    }

    const arrowMatch = trimmed.match(
      /([A-Za-z][A-Za-z0-9_/.:\s-]*?)(?:\[[^\]]*\])?\s*--+>(?:\|([^|]*)\|)?\s*([A-Za-z][A-Za-z0-9_/.:\s-]*?)(?:\s*\[|\s*$)/
    );
    if (arrowMatch) {
      const from = cleanId(arrowMatch[1]);
      const label = arrowMatch[2]?.trim();
      const to = cleanId(arrowMatch[3]);
      if (from && to && from !== to && from.length >= 2 && to.length >= 2) {
        if (!nodeLabels.has(from)) nodeLabels.set(from, from);
        if (!nodeLabels.has(to)) nodeLabels.set(to, to);
        edges.push(label ? `    ${from} -->|${label}| ${to}` : `    ${from} --> ${to}`);
      }
    }
  }

  if (nodeLabels.size < 2 || edges.length === 0) return null;
  const nodeDecls = Array.from(nodeLabels.entries()).map(([id, label]) => `    ${id}[${label}]`);
  return ["graph TD", ...nodeDecls, "", ...edges].join("\n");
}

export function MermaidRenderer({ code, id }: { code: string; id: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [renderError, setRenderError] = useState(false);

  useEffect(() => {
    if (!code) return;
    let cancelled = false;

    (async () => {
      try {
        const mermaidModule = await import("mermaid");
        const mermaid = mermaidModule.default;

        const candidates = [code, sanitizeMermaid(code), rebuildMermaid(code)];
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
            mermaid.initialize({
              startOnLoad: false,
              theme: "neutral",
              securityLevel: "loose",
              fontFamily: "ui-sans-serif, system-ui, sans-serif",
            });
            const staleEl = document.getElementById(`dmermaid-${id}-${i}`);
            if (staleEl) staleEl.remove();
            const result = await mermaid.render(`dmermaid-${id}-${i}`, unique[i]);
            rendered = result.svg;
            break;
          } catch {
            const failedEl = document.getElementById(`dmermaid-${id}-${i}`);
            if (failedEl) failedEl.remove();
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

    return () => {
      cancelled = true;
    };
  }, [code, id]);

  if (renderError) {
    return (
      <div className="rounded-lg border border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-950/30 p-4 text-sm text-orange-800 dark:text-orange-300">
        <p className="font-medium mb-1">Diagram render failed — showing source code:</p>
        <pre className="overflow-x-auto rounded bg-background p-3 text-xs leading-relaxed text-foreground/90 border border-border">
          <code>{code}</code>
        </pre>
        <p className="mt-2 text-xs text-orange-700 dark:text-orange-400">
          Copy this code and paste it into{" "}
          <a href="https://mermaid.live" target="_blank" rel="noreferrer" className="underline font-medium">
            mermaid.live
          </a>{" "}
          to view and edit.
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
      className="rounded-lg border bg-background p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}

export function DiagramCard({ diagram, index }: { diagram: ArchitectureDiagram; index: number }) {
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
            <CardTitle className="text-sm font-semibold text-foreground">{diagram.title}</CardTitle>
            {diagram.type && (
              <span className="mt-0.5 inline-block rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                {diagram.type}
              </span>
            )}
          </div>
          <div className="flex gap-1 shrink-0">
            <Button size="sm" variant="ghost" onClick={handleCopy} className="h-7 px-2">
              <Copy className="h-3.5 w-3.5" />
              {copied ? <span className="ml-1 text-xs">Copied!</span> : null}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowCode((v) => !v)} className="h-7 px-2">
              {showCode ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {diagram.description && (
          <div className="rounded-md bg-muted px-3 py-2">
            <p className="text-sm text-foreground/80 leading-relaxed">
              {diagram.description
                .replace(/^\*?\*?Description\*?\*?:?\s*/i, "")
                .replace(/^---+\s*/, "")
                .replace(/^\*{1,2}\s*/, "")
                .replace(/\s*\*{1,2}\s*$/, "")
                .replace(/\*\*([^*]+)\*\*/g, "$1")
                .replace(/\*([^*]+)\*/g, "$1")
                .trim()}
            </p>
          </div>
        )}
        {mermaidCode && <MermaidRenderer code={mermaidCode} id={`diagram-${index}`} />}
        {showCode && mermaidCode && (
          <pre className="overflow-x-auto rounded-lg bg-muted p-4 text-xs leading-relaxed text-foreground/90 border border-border">
            <code>{mermaidCode}</code>
          </pre>
        )}
      </CardContent>
    </Card>
  );
}
