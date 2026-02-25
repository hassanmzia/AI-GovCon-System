"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, CheckCircle, AlertTriangle, Clock, XCircle } from "lucide-react";

interface Deliverable {
  id: string;
  title: string;
  due_date: string;        // ISO date string
  status: "not_started" | "in_progress" | "submitted" | "accepted" | "overdue" | "waived";
  deliverable_type?: string;
  clin?: string;
  responsible_party?: string;
  description?: string;
}

interface DeliverablesTimelineProps {
  deliverables: Deliverable[];
  contractTitle?: string;
}

const STATUS_CONFIG = {
  not_started: { icon: Clock, color: "text-slate-500", bg: "bg-slate-100", label: "Not Started" },
  in_progress: { icon: Clock, color: "text-blue-600", bg: "bg-blue-100", label: "In Progress" },
  submitted: { icon: CheckCircle, color: "text-yellow-600", bg: "bg-yellow-100", label: "Submitted" },
  accepted: { icon: CheckCircle, color: "text-emerald-600", bg: "bg-emerald-100", label: "Accepted" },
  overdue: { icon: AlertTriangle, color: "text-red-600", bg: "bg-red-100", label: "Overdue" },
  waived: { icon: XCircle, color: "text-gray-400", bg: "bg-gray-100", label: "Waived" },
} as const;

function isOverdue(dueDate: string, status: Deliverable["status"]): boolean {
  if (status === "accepted" || status === "waived") return false;
  return new Date(dueDate) < new Date();
}

function daysUntil(dueDate: string): number {
  const diff = new Date(dueDate).getTime() - new Date().getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function urgencyClass(days: number, status: Deliverable["status"]): string {
  if (status === "accepted" || status === "waived") return "border-l-gray-300";
  if (days < 0) return "border-l-red-500";
  if (days <= 7) return "border-l-orange-400";
  if (days <= 30) return "border-l-yellow-400";
  return "border-l-emerald-400";
}

export function DeliverablesTimeline({ deliverables, contractTitle }: DeliverablesTimelineProps) {
  if (!deliverables || deliverables.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4 text-blue-500" /> Deliverables Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-20 text-muted-foreground text-sm">
            No deliverables defined
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sort by due date
  const sorted = [...deliverables].sort(
    (a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
  );

  const overdue = sorted.filter((d) => isOverdue(d.due_date, d.status));
  const upcoming = sorted.filter(
    (d) => !isOverdue(d.due_date, d.status) && d.status !== "accepted" && d.status !== "waived"
  );
  const done = sorted.filter((d) => d.status === "accepted" || d.status === "waived");

  const groups: Array<{ label: string; items: Deliverable[]; accent: string }> = [
    { label: "Overdue", items: overdue, accent: "text-red-600" },
    { label: "Upcoming", items: upcoming, accent: "text-blue-600" },
    { label: "Completed / Waived", items: done, accent: "text-emerald-600" },
  ].filter((g) => g.items.length > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Calendar className="h-4 w-4 text-blue-500" /> Deliverables Timeline
          {contractTitle && (
            <span className="text-xs font-normal text-muted-foreground ml-1">— {contractTitle}</span>
          )}
          <div className="ml-auto flex items-center gap-2 text-xs font-normal text-muted-foreground">
            {overdue.length > 0 && (
              <span className="flex items-center gap-1 text-red-600 font-medium">
                <AlertTriangle className="h-3 w-3" /> {overdue.length} overdue
              </span>
            )}
            <span>{upcoming.length} upcoming · {done.length} done</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {groups.map((group) => (
            <div key={group.label}>
              <h4 className={`text-xs font-semibold uppercase tracking-wide mb-2 ${group.accent}`}>
                {group.label} ({group.items.length})
              </h4>
              <div className="space-y-2">
                {group.items.map((d) => {
                  const effectiveStatus: Deliverable["status"] =
                    isOverdue(d.due_date, d.status) ? "overdue" : d.status;
                  const cfg = STATUS_CONFIG[effectiveStatus] || STATUS_CONFIG.not_started;
                  const Icon = cfg.icon;
                  const days = daysUntil(d.due_date);
                  const urg = urgencyClass(days, effectiveStatus);

                  return (
                    <div
                      key={d.id}
                      className={`border-l-4 ${urg} pl-3 py-2 bg-muted/30 rounded-r`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2 min-w-0">
                          <Icon className={`h-4 w-4 mt-0.5 flex-shrink-0 ${cfg.color}`} />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-foreground truncate">{d.title}</p>
                            {d.description && (
                              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{d.description}</p>
                            )}
                            <div className="flex items-center gap-2 mt-1 flex-wrap">
                              {d.clin && (
                                <span className="text-[10px] bg-blue-100 text-blue-700 px-1 rounded">
                                  CLIN {d.clin}
                                </span>
                              )}
                              {d.deliverable_type && (
                                <span className="text-[10px] bg-gray-100 text-gray-600 px-1 rounded">
                                  {d.deliverable_type}
                                </span>
                              )}
                              {d.responsible_party && (
                                <span className="text-xs text-muted-foreground">{d.responsible_party}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex-shrink-0 text-right">
                          <p className="text-xs font-medium text-foreground">{formatDate(d.due_date)}</p>
                          {effectiveStatus !== "accepted" && effectiveStatus !== "waived" && (
                            <p className={`text-[10px] font-semibold ${days < 0 ? "text-red-600" : days <= 7 ? "text-orange-600" : "text-muted-foreground"}`}>
                              {days < 0 ? `${Math.abs(days)}d overdue` : days === 0 ? "Due today" : `${days}d left`}
                            </p>
                          )}
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${cfg.bg} ${cfg.color}`}>
                            {cfg.label}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
