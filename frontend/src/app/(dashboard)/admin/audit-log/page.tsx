"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";
import {
  Loader2,
  RefreshCw,
  Search,
  Activity,
  User,
  Bot,
  Clock,
  Filter,
  ChevronLeft,
  ChevronRight,
  FileText,
  GitBranch,
  CheckSquare,
  MessageCircle,
  Shield,
  Zap,
} from "lucide-react";

interface ActivityEntry {
  id: string;
  deal: string;
  deal_title?: string;
  actor: string | null;
  actor_name?: string;
  action: string;
  description: string;
  metadata: Record<string, unknown>;
  is_ai_action: boolean;
  created_at: string;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function timeAgo(dateStr: string): string {
  const now = new Date();
  const d = new Date(dateStr);
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}d ago`;
}

const ACTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  stage_changed: GitBranch,
  task_completed: CheckSquare,
  comment_added: MessageCircle,
  approval_requested: Shield,
  approval_decided: Shield,
  agent_action: Bot,
  document_uploaded: FileText,
  deal_created: Activity,
  deal_updated: Activity,
};

const ACTION_COLORS: Record<string, string> = {
  stage_changed: "bg-blue-100 text-blue-700",
  task_completed: "bg-green-100 text-green-700",
  comment_added: "bg-gray-100 text-gray-700",
  approval_requested: "bg-yellow-100 text-yellow-700",
  approval_decided: "bg-purple-100 text-purple-700",
  agent_action: "bg-indigo-100 text-indigo-700",
  document_uploaded: "bg-orange-100 text-orange-700",
  deal_created: "bg-teal-100 text-teal-700",
  deal_updated: "bg-cyan-100 text-cyan-700",
};

function ActivityRow({ entry }: { entry: ActivityEntry }) {
  const ActionIcon = ACTION_ICONS[entry.action] || Activity;
  const actionColor = ACTION_COLORS[entry.action] || "bg-gray-100 text-gray-600";

  return (
    <div className="flex items-start gap-4 py-3 border-b last:border-0 hover:bg-gray-50 rounded px-2 group">
      <div className={`mt-0.5 p-1.5 rounded-lg flex-shrink-0 ${actionColor}`}>
        <ActionIcon className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2 flex-wrap">
          <span className="text-sm font-medium">{entry.description}</span>
          {entry.is_ai_action && (
            <span className="px-1.5 py-0.5 text-xs rounded-full bg-indigo-100 text-indigo-700 flex items-center gap-1 flex-shrink-0">
              <Zap className="h-2.5 w-2.5" /> AI
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground flex-wrap">
          {entry.deal_title && (
            <span className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {entry.deal_title}
            </span>
          )}
          <span className="flex items-center gap-1">
            {entry.is_ai_action ? (
              <Bot className="h-3 w-3" />
            ) : (
              <User className="h-3 w-3" />
            )}
            {entry.is_ai_action ? "AI Agent" : entry.actor_name || "System"}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-xs ${actionColor}`}>
            {entry.action.replace(/_/g, " ")}
          </span>
        </div>
      </div>
      <div className="flex-shrink-0 text-xs text-muted-foreground flex items-center gap-1" title={formatDate(entry.created_at)}>
        <Clock className="h-3 w-3" />
        {timeAgo(entry.created_at)}
      </div>
    </div>
  );
}

const PAGE_SIZE = 30;

export default function AuditLogPage() {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterAction, setFilterAction] = useState("");
  const [filterActor, setFilterActor] = useState<"all" | "human" | "ai">("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {
        page: String(page),
        page_size: String(PAGE_SIZE),
        ordering: "-created_at",
      };
      if (search) params.search = search;
      if (filterAction) params.action = filterAction;
      if (filterActor === "ai") params.is_ai_action = "true";
      if (filterActor === "human") params.is_ai_action = "false";

      const res = await api.get("/deals/activities/", { params });
      const data = res.data;
      setEntries(data.results || data || []);
      setTotal(data.count || (data.results || data).length);
    } catch {
      setError("Failed to load activity log.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [page, search, filterAction, filterActor]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const actionTypes = [
    { value: "", label: "All Actions" },
    { value: "stage_changed", label: "Stage Changed" },
    { value: "task_completed", label: "Task Completed" },
    { value: "comment_added", label: "Comment Added" },
    { value: "approval_requested", label: "Approval Requested" },
    { value: "approval_decided", label: "Approval Decided" },
    { value: "agent_action", label: "AI Agent Action" },
    { value: "document_uploaded", label: "Document Uploaded" },
  ];

  const aiCount = entries.filter((e) => e.is_ai_action).length;
  const humanCount = entries.filter((e) => !e.is_ai_action).length;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" /> Audit Log
          </h1>
          <p className="text-muted-foreground mt-0.5">
            Full activity trail — human and AI actions
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => load(true)}
          disabled={refreshing}
        >
          {refreshing ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4 flex items-center gap-3">
            <Activity className="h-8 w-8 text-muted-foreground" />
            <div>
              <div className="text-2xl font-bold">{total.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">Total Events</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 flex items-center gap-3">
            <User className="h-8 w-8 text-blue-500" />
            <div>
              <div className="text-2xl font-bold">{humanCount}</div>
              <div className="text-xs text-muted-foreground">Human Actions</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 flex items-center gap-3">
            <Bot className="h-8 w-8 text-indigo-500" />
            <div>
              <div className="text-2xl font-bold">{aiCount}</div>
              <div className="text-xs text-muted-foreground">AI Agent Actions</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:flex-wrap">
            <div className="relative w-full sm:flex-1 sm:min-w-48">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search activities..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <select
                value={filterAction}
                onChange={(e) => {
                  setFilterAction(e.target.value);
                  setPage(1);
                }}
                className="text-sm border rounded px-2 py-1.5 bg-background text-foreground"
              >
                {actionTypes.map((t) => (
                  <option key={t.value} value={t.value} className="bg-background text-foreground">
                    {t.label}
                  </option>
                ))}
              </select>
              <div className="flex items-center border rounded overflow-hidden text-sm">
                {(["all", "human", "ai"] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => {
                      setFilterActor(v);
                      setPage(1);
                    }}
                    className={`px-3 py-1.5 capitalize ${
                      filterActor === v
                        ? "bg-blue-600 text-white"
                        : "text-muted-foreground hover:bg-accent"
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Activity List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Activity Feed
            {total > 0 && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                {total.toLocaleString()} events
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">{error}</div>
          ) : entries.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Activity className="h-12 w-12 mx-auto mb-3 opacity-40" />
              <p className="font-medium">No activities found</p>
              <p className="text-sm mt-1">Activities are recorded automatically as deals progress</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {entries.map((entry) => (
                <ActivityRow key={entry.id} entry={entry} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mt-4 pt-4 border-t">
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages} ({total.toLocaleString()} total)
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
