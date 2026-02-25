"use client";

import {
  AlertTriangle,
  Plus,
  Minus,
  Edit3,
  Square,
  FileEdit,
} from "lucide-react";

interface DiffSection {
  type: "added" | "removed" | "changed" | "unchanged";
  section_ref: string;
  content: string;
  impact: string;
}

interface AmendmentImpactPanelProps {
  amendmentId?: string;
  dealTitle?: string;
  diffSections: DiffSection[];
  affectedProposalSections: string[];
  requiresReapproval: boolean;
  changeSummary?: string;
}

// --- Helpers ---
function truncate(text: string, maxLen = 160): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + "...";
}

function sectionTypeConfig(type: DiffSection["type"]) {
  switch (type) {
    case "added":
      return {
        border: "border-green-300",
        bg: "bg-green-50",
        badgeBg: "bg-green-100 text-green-700",
        impactText: "text-green-700",
        icon: <Plus className="h-3.5 w-3.5 text-green-600" />,
      };
    case "removed":
      return {
        border: "border-red-300",
        bg: "bg-red-50",
        badgeBg: "bg-red-100 text-red-700",
        impactText: "text-red-700",
        icon: <Minus className="h-3.5 w-3.5 text-red-600" />,
      };
    case "changed":
      return {
        border: "border-amber-300",
        bg: "bg-amber-50",
        badgeBg: "bg-amber-100 text-amber-700",
        impactText: "text-amber-700",
        icon: <Edit3 className="h-3.5 w-3.5 text-amber-600" />,
      };
    case "unchanged":
    default:
      return {
        border: "border-gray-200",
        bg: "bg-gray-50",
        badgeBg: "bg-gray-100 text-gray-500",
        impactText: "text-gray-500",
        icon: <Square className="h-3.5 w-3.5 text-gray-400" />,
      };
  }
}

// --- Section Group ---
function DiffSectionGroup({
  title,
  sections,
  emptyMessage,
}: {
  title: string;
  sections: DiffSection[];
  emptyMessage: string;
}) {
  if (sections.length === 0) {
    return (
      <div>
        <h4 className="text-sm font-semibold text-gray-600 mb-2">{title}</h4>
        <p className="text-xs text-gray-400 italic">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
        {title}
        <span className="text-xs font-bold bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
          {sections.length}
        </span>
      </h4>
      <div className="space-y-2">
        {sections.map((section, i) => {
          const config = sectionTypeConfig(section.type);
          return (
            <div
              key={i}
              className={`rounded-lg border ${config.border} ${config.bg} p-3`}
            >
              <div className="flex items-start gap-2">
                <div className="mt-0.5 flex-shrink-0">{config.icon}</div>
                <div className="flex-1 min-w-0">
                  {/* Section ref badge */}
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded font-mono ${config.badgeBg}`}
                    >
                      {section.section_ref}
                    </span>
                  </div>
                  {/* Content snippet */}
                  {section.content && (
                    <p className="text-xs text-gray-700 leading-relaxed mb-1">
                      {truncate(section.content)}
                    </p>
                  )}
                  {/* Impact */}
                  {section.impact && (
                    <p className={`text-xs font-medium ${config.impactText}`}>
                      Impact: {section.impact}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Main Component ---
export function AmendmentImpactPanel({
  amendmentId,
  dealTitle,
  diffSections,
  affectedProposalSections,
  requiresReapproval,
  changeSummary,
}: AmendmentImpactPanelProps) {
  const addedSections = diffSections.filter((s) => s.type === "added");
  const removedOrChangedSections = diffSections.filter(
    (s) => s.type === "removed" || s.type === "changed"
  );
  const unchangedSections = diffSections.filter((s) => s.type === "unchanged");

  const addedCount = addedSections.length;
  const changedCount = diffSections.filter((s) => s.type === "changed").length;
  const removedCount = diffSections.filter((s) => s.type === "removed").length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-50 rounded-lg">
            <FileEdit className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900">
              Amendment Impact Analysis
            </h3>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
              {amendmentId && (
                <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                  {amendmentId}
                </span>
              )}
              {dealTitle && <span>{dealTitle}</span>}
            </div>
          </div>
        </div>

        {/* Count badges */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {addedCount > 0 && (
            <span className="text-xs font-bold bg-green-100 text-green-700 px-2.5 py-1 rounded-full flex items-center gap-1">
              <Plus className="h-3 w-3" />
              {addedCount} Added
            </span>
          )}
          {changedCount > 0 && (
            <span className="text-xs font-bold bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full flex items-center gap-1">
              <Edit3 className="h-3 w-3" />
              {changedCount} Changed
            </span>
          )}
          {removedCount > 0 && (
            <span className="text-xs font-bold bg-red-100 text-red-700 px-2.5 py-1 rounded-full flex items-center gap-1">
              <Minus className="h-3 w-3" />
              {removedCount} Removed
            </span>
          )}
        </div>
      </div>

      {/* Re-approval banner */}
      {requiresReapproval && (
        <div className="rounded-lg border-2 border-red-300 bg-red-50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-red-800">
              This amendment requires proposal re-approval
            </p>
            <p className="text-sm text-red-700 mt-0.5">
              Material changes were detected that invalidate previous approvals.
              All stakeholders must re-review and re-approve before submission.
            </p>
          </div>
        </div>
      )}

      {/* Change summary */}
      {changeSummary && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
            Change Summary
          </p>
          <p className="text-sm text-gray-700">{changeSummary}</p>
        </div>
      )}

      {/* Empty state */}
      {diffSections.length === 0 && (
        <div className="flex flex-col items-center justify-center py-10 text-gray-400">
          <FileEdit className="h-10 w-10 mb-2 opacity-30" />
          <p className="text-sm">No diff sections to display</p>
          <p className="text-xs mt-1">
            Amendment analysis will appear here once processed
          </p>
        </div>
      )}

      {/* Diff sections by group */}
      {diffSections.length > 0 && (
        <div className="space-y-5">
          <DiffSectionGroup
            title="Added Requirements"
            sections={addedSections}
            emptyMessage="No new requirements added."
          />
          <DiffSectionGroup
            title="Removed / Changed Requirements"
            sections={removedOrChangedSections}
            emptyMessage="No requirements removed or changed."
          />
          {unchangedSections.length > 0 && (
            <DiffSectionGroup
              title="Unchanged Sections"
              sections={unchangedSections}
              emptyMessage=""
            />
          )}
        </div>
      )}

      {/* Affected Proposal Sections */}
      {affectedProposalSections.length > 0 && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
            <FileEdit className="h-4 w-4" />
            Affected Proposal Sections
          </p>
          <ul className="space-y-1.5">
            {affectedProposalSections.map((section, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-blue-700">
                <Edit3 className="h-3.5 w-3.5 text-blue-400 flex-shrink-0" />
                <span>{section}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer stats */}
      <div className="flex items-center gap-4 pt-2 border-t border-gray-100 text-xs text-gray-500">
        <span>
          {diffSections.length} total section
          {diffSections.length !== 1 ? "s" : ""} analyzed
        </span>
        <span>•</span>
        <span>
          {affectedProposalSections.length} proposal section
          {affectedProposalSections.length !== 1 ? "s" : ""} affected
        </span>
        {requiresReapproval && (
          <>
            <span>•</span>
            <span className="text-red-600 font-semibold">
              Re-approval required
            </span>
          </>
        )}
      </div>
    </div>
  );
}
