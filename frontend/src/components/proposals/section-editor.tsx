"use client";

import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ChevronDown,
  ChevronRight,
  Wand2,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  RotateCcw,
  Save,
} from "lucide-react";

interface ProposalSection {
  id: string;
  section_number: string;  // e.g. "L.1", "M.2"
  title: string;
  content: string;
  word_count?: number;
  page_limit?: number;
  status: "draft" | "ai_draft" | "in_review" | "approved" | "needs_revision";
  compliance_status?: "compliant" | "non_compliant" | "not_checked";
  rfp_reference?: string;
  ai_suggestions?: string;
  is_required: boolean;
}

interface SectionEditorProps {
  sections: ProposalSection[];
  onSave?: (sectionId: string, content: string) => Promise<void>;
  onGenerateAI?: (sectionId: string) => Promise<void>;
  readOnly?: boolean;
}

const STATUS_CONFIG = {
  draft: { icon: FileText, color: "bg-gray-100 text-gray-700", label: "Draft" },
  ai_draft: { icon: Wand2, color: "bg-purple-100 text-purple-700", label: "AI Draft" },
  in_review: { icon: Clock, color: "bg-yellow-100 text-yellow-700", label: "In Review" },
  approved: { icon: CheckCircle, color: "bg-emerald-100 text-emerald-700", label: "Approved" },
  needs_revision: { icon: AlertCircle, color: "bg-red-100 text-red-700", label: "Needs Revision" },
} as const;

const COMPLIANCE_CONFIG = {
  compliant: { color: "text-emerald-600", label: "Compliant" },
  non_compliant: { color: "text-red-600", label: "Non-Compliant" },
  not_checked: { color: "text-gray-400", label: "Not Checked" },
} as const;

function SectionRow({
  section,
  onSave,
  onGenerateAI,
  readOnly,
}: {
  section: ProposalSection;
  onSave?: (id: string, content: string) => Promise<void>;
  onGenerateAI?: (id: string) => Promise<void>;
  readOnly?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [localContent, setLocalContent] = useState(section.content);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  const statusCfg = STATUS_CONFIG[section.status] || STATUS_CONFIG.draft;
  const StatusIcon = statusCfg.icon;
  const complianceCfg = COMPLIANCE_CONFIG[section.compliance_status || "not_checked"];
  const wordCount = localContent.trim() ? localContent.trim().split(/\s+/).length : 0;
  const overLimit = section.page_limit && wordCount > section.page_limit * 300; // ~300 words/page

  const handleSave = useCallback(async () => {
    if (!onSave) return;
    setSaving(true);
    try {
      await onSave(section.id, localContent);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }, [onSave, section.id, localContent]);

  const handleGenerateAI = useCallback(async () => {
    if (!onGenerateAI) return;
    setGenerating(true);
    try {
      await onGenerateAI(section.id);
    } finally {
      setGenerating(false);
    }
  }, [onGenerateAI, section.id]);

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header row */}
      <div
        className="flex items-center gap-2 p-3 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-muted-foreground">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </span>

        <span className="text-xs font-mono font-semibold text-blue-700 w-10 flex-shrink-0">
          {section.section_number}
        </span>

        <span className="text-sm font-medium text-foreground flex-1 truncate">{section.title}</span>

        {section.is_required && (
          <span className="text-[10px] font-semibold text-red-600 flex-shrink-0">REQ</span>
        )}

        {section.rfp_reference && (
          <span className="text-[10px] text-muted-foreground flex-shrink-0">{section.rfp_reference}</span>
        )}

        <span className={`text-[10px] font-medium ${complianceCfg.color} flex-shrink-0`}>
          {complianceCfg.label}
        </span>

        <span className={`text-[10px] px-1.5 py-0.5 rounded flex items-center gap-1 flex-shrink-0 ${statusCfg.color}`}>
          <StatusIcon className="h-2.5 w-2.5" />
          {statusCfg.label}
        </span>

        <span className={`text-[10px] text-muted-foreground flex-shrink-0 ${overLimit ? "text-red-600 font-semibold" : ""}`}>
          {wordCount}w
          {section.page_limit ? ` / ${section.page_limit}p` : ""}
        </span>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="p-4 space-y-3 bg-white">
          {/* AI suggestions */}
          {section.ai_suggestions && (
            <div className="bg-purple-50 border border-purple-200 rounded p-3 text-xs text-purple-800">
              <p className="font-semibold mb-1 flex items-center gap-1">
                <Wand2 className="h-3 w-3" /> AI Suggestion
              </p>
              <p className="whitespace-pre-wrap">{section.ai_suggestions}</p>
            </div>
          )}

          {/* Content area */}
          {editing && !readOnly ? (
            <textarea
              className="w-full min-h-[200px] text-sm border rounded p-3 font-mono resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localContent}
              onChange={(e) => setLocalContent(e.target.value)}
              placeholder="Enter section content..."
            />
          ) : (
            <div className="min-h-[80px] text-sm whitespace-pre-wrap text-foreground bg-muted/20 rounded p-3">
              {localContent || (
                <span className="text-muted-foreground italic">No content yet.</span>
              )}
            </div>
          )}

          {/* Actions */}
          {!readOnly && (
            <div className="flex items-center gap-2 pt-1">
              {editing ? (
                <>
                  <Button size="sm" onClick={handleSave} disabled={saving} className="gap-1">
                    <Save className="h-3 w-3" />
                    {saving ? "Saving…" : "Save"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setLocalContent(section.content);
                      setEditing(false);
                    }}
                    className="gap-1"
                  >
                    <RotateCcw className="h-3 w-3" /> Cancel
                  </Button>
                </>
              ) : (
                <Button size="sm" variant="outline" onClick={() => setEditing(true)} className="gap-1">
                  <FileText className="h-3 w-3" /> Edit
                </Button>
              )}

              {onGenerateAI && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleGenerateAI}
                  disabled={generating}
                  className="gap-1 text-purple-700 border-purple-300 hover:bg-purple-50"
                >
                  <Wand2 className="h-3 w-3" />
                  {generating ? "Generating…" : "AI Draft"}
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function SectionEditor({ sections, onSave, onGenerateAI, readOnly = false }: SectionEditorProps) {
  const total = sections.length;
  const approved = sections.filter((s) => s.status === "approved").length;
  const compliant = sections.filter((s) => s.compliance_status === "compliant").length;
  const required = sections.filter((s) => s.is_required).length;
  const requiredDone = sections.filter((s) => s.is_required && s.status === "approved").length;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-500" /> Proposal Section Editor
          <div className="ml-auto flex items-center gap-2 text-xs font-normal">
            <span className="border rounded px-1.5 py-0.5">{approved}/{total} approved</span>
            <span className="border border-emerald-300 text-emerald-700 rounded px-1.5 py-0.5">
              {compliant}/{total} compliant
            </span>
            {required > 0 && (
              <span className="border border-red-300 text-red-700 rounded px-1.5 py-0.5">
                {requiredDone}/{required} required done
              </span>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {sections.length === 0 ? (
          <div className="flex items-center justify-center h-20 text-muted-foreground text-sm">
            No sections defined
          </div>
        ) : (
          <div className="space-y-2">
            {sections.map((section) => (
              <SectionRow
                key={section.id}
                section={section}
                onSave={onSave}
                onGenerateAI={onGenerateAI}
                readOnly={readOnly}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
