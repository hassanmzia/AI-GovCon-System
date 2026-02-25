"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getDeals,
  createDeal,
  transitionDealStage,
  getDealStageHistory,
} from "@/services/deals";
import { Deal, DealStage, DealStageHistory, CreateDealPayload } from "@/types/deal";
import { Search, Plus, Loader2, X, ChevronRight, AlertCircle } from "lucide-react";

// ---------------------------------------------------------------------------
// Stage configuration
// ---------------------------------------------------------------------------

const ACTIVE_STAGES: DealStage[] = [
  "intake",
  "qualify",
  "bid_no_bid",
  "capture_plan",
  "proposal_dev",
  "red_team",
  "final_review",
  "submit",
  "post_submit",
  "award_pending",
  "contract_setup",
  "delivery",
];

const CLOSED_STAGES: DealStage[] = ["closed_won", "closed_lost", "no_bid"];

const STAGE_LABELS: Record<DealStage, string> = {
  intake: "Intake",
  qualify: "Qualify",
  bid_no_bid: "Bid / No-Bid",
  capture_plan: "Capture Plan",
  proposal_dev: "Proposal Dev",
  red_team: "Red Team",
  final_review: "Final Review",
  submit: "Submit",
  post_submit: "Post Submit",
  award_pending: "Award Pending",
  contract_setup: "Contract Setup",
  delivery: "Delivery",
  closed_won: "Closed Won",
  closed_lost: "Closed Lost",
  no_bid: "No Bid",
};

// Color tokens for each stage header strip
const STAGE_COLORS: Record<DealStage, string> = {
  intake: "bg-gray-500",
  qualify: "bg-blue-500",
  bid_no_bid: "bg-yellow-500",
  capture_plan: "bg-orange-500",
  proposal_dev: "bg-purple-500",
  red_team: "bg-red-500",
  final_review: "bg-orange-600",
  submit: "bg-green-500",
  post_submit: "bg-teal-500",
  award_pending: "bg-yellow-600",
  contract_setup: "bg-blue-600",
  delivery: "bg-green-600",
  closed_won: "bg-emerald-600",
  closed_lost: "bg-gray-600",
  no_bid: "bg-slate-500",
};

// Text color for stage badges on cards
const STAGE_TEXT_COLORS: Record<DealStage, string> = {
  intake: "text-gray-600 bg-gray-100",
  qualify: "text-blue-700 bg-blue-100",
  bid_no_bid: "text-yellow-700 bg-yellow-100",
  capture_plan: "text-orange-700 bg-orange-100",
  proposal_dev: "text-purple-700 bg-purple-100",
  red_team: "text-red-700 bg-red-100",
  final_review: "text-orange-700 bg-orange-100",
  submit: "text-green-700 bg-green-100",
  post_submit: "text-teal-700 bg-teal-100",
  award_pending: "text-yellow-700 bg-yellow-100",
  contract_setup: "text-blue-700 bg-blue-100",
  delivery: "text-green-700 bg-green-100",
  closed_won: "text-emerald-700 bg-emerald-100",
  closed_lost: "text-gray-600 bg-gray-100",
  no_bid: "text-slate-600 bg-slate-100",
};

const PRIORITY_LABELS: Record<number, string> = {
  1: "Critical",
  2: "High",
  3: "Medium",
  4: "Low",
};

const PRIORITY_COLORS: Record<number, string> = {
  1: "text-red-700 bg-red-100",
  2: "text-orange-700 bg-orange-100",
  3: "text-blue-700 bg-blue-100",
  4: "text-gray-600 bg-gray-100",
};

// Valid next-stage transitions (simplified linear + key branches)
const NEXT_STAGES: Partial<Record<DealStage, DealStage[]>> = {
  intake: ["qualify", "no_bid"],
  qualify: ["bid_no_bid", "no_bid"],
  bid_no_bid: ["capture_plan", "no_bid"],
  capture_plan: ["proposal_dev", "no_bid"],
  proposal_dev: ["red_team", "no_bid"],
  red_team: ["final_review", "proposal_dev"],
  final_review: ["submit", "proposal_dev"],
  submit: ["post_submit"],
  post_submit: ["award_pending"],
  award_pending: ["contract_setup", "closed_lost"],
  contract_setup: ["delivery"],
  delivery: ["closed_won", "closed_lost"],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatCurrency(value: string | null): string {
  if (!value) return "--";
  const num = parseFloat(value);
  if (isNaN(num)) return "--";
  if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `$${(num / 1_000).toFixed(0)}K`;
  return `$${num.toFixed(0)}`;
}

function getDaysUntilDue(dueDateStr: string | null): number | null {
  if (!dueDateStr) return null;
  const due = new Date(dueDateStr);
  const now = new Date();
  const diff = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return diff;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function DueBadge({ dueDate }: { dueDate: string | null }) {
  const days = getDaysUntilDue(dueDate);
  if (days === null) return <span className="text-muted-foreground text-xs">No due date</span>;
  if (days < 0) return <span className="text-xs text-red-600 font-medium">Overdue</span>;
  if (days <= 7) return <span className="text-xs text-red-600 font-medium">{days}d left</span>;
  if (days <= 30) return <span className="text-xs text-yellow-600 font-medium">{days}d left</span>;
  return <span className="text-xs text-green-600 font-medium">{days}d left</span>;
}

// ---------------------------------------------------------------------------
// Deal Card
// ---------------------------------------------------------------------------

interface DealCardProps {
  deal: Deal;
  onClick: (deal: Deal) => void;
}

function DealCard({ deal, onClick }: DealCardProps) {
  return (
    <div
      onClick={() => onClick(deal)}
      className="bg-card border border-border rounded-lg p-3 cursor-pointer hover:border-primary/50 hover:shadow-md transition-all space-y-2"
    >
      {/* Title */}
      <p className="text-sm font-medium leading-tight line-clamp-2">
        {deal.title}
      </p>

      {/* Opportunity */}
      {deal.opportunity_title && (
        <p className="text-xs text-muted-foreground truncate">
          {deal.opportunity_title}
        </p>
      )}

      {/* Value + Win Probability row */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">
          {formatCurrency(deal.estimated_value)}
        </span>
        <span className="text-xs text-muted-foreground">
          {deal.win_probability}% win
        </span>
      </div>

      {/* Priority + Due date */}
      <div className="flex items-center justify-between">
        <span
          className={`text-xs font-medium px-1.5 py-0.5 rounded ${PRIORITY_COLORS[deal.priority]}`}
        >
          {PRIORITY_LABELS[deal.priority] || deal.priority_display}
        </span>
        <DueBadge dueDate={deal.due_date} />
      </div>

      {/* Owner */}
      <p className="text-xs text-muted-foreground truncate">
        Owner: {deal.owner_name || "--"}
      </p>

      {/* Badges row: tasks + approvals */}
      <div className="flex items-center gap-2">
        {deal.task_count > 0 && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">
            {deal.task_count} task{deal.task_count !== 1 ? "s" : ""}
          </span>
        )}
        {deal.pending_approval_count > 0 && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700 font-medium">
            {deal.pending_approval_count} approval{deal.pending_approval_count !== 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pipeline Column
// ---------------------------------------------------------------------------

interface PipelineColumnProps {
  stage: DealStage;
  deals: Deal[];
  onCardClick: (deal: Deal) => void;
}

function PipelineColumn({ stage, deals, onCardClick }: PipelineColumnProps) {
  const totalValue = deals.reduce((sum, d) => {
    if (!d.estimated_value) return sum;
    const num = parseFloat(d.estimated_value);
    return isNaN(num) ? sum : sum + num;
  }, 0);

  return (
    <div className="flex flex-col w-64 flex-shrink-0">
      {/* Column header */}
      <div className={`${STAGE_COLORS[stage]} rounded-t-lg px-3 py-2`}>
        <div className="flex items-center justify-between">
          <span className="text-white text-sm font-semibold truncate">
            {STAGE_LABELS[stage]}
          </span>
          <span className="text-white/80 text-xs font-medium ml-1 flex-shrink-0">
            {deals.length}
          </span>
        </div>
      </div>

      {/* Summary row */}
      <div className="bg-muted/50 border-x border-border px-3 py-1.5">
        <p className="text-xs text-muted-foreground">
          {totalValue > 0 ? formatCurrency(totalValue.toString()) : "No value"} pipeline
        </p>
      </div>

      {/* Cards */}
      <div className="flex-1 border border-t-0 border-border rounded-b-lg bg-background/50 p-2 space-y-2 overflow-y-auto min-h-[120px] max-h-[calc(100vh-280px)]">
        {deals.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center pt-4 pb-2">
            No deals
          </p>
        ) : (
          deals.map((deal) => (
            <DealCard key={deal.id} deal={deal} onClick={onCardClick} />
          ))
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Deal Detail / Transition Modal
// ---------------------------------------------------------------------------

interface DealModalProps {
  deal: Deal;
  onClose: () => void;
  onTransition: (deal: Deal, targetStage: DealStage, reason: string) => Promise<void>;
}

function DealModal({ deal, onClose, onTransition }: DealModalProps) {
  const [transitioning, setTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [stageHistory, setStageHistory] = useState<DealStageHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  const nextStages = NEXT_STAGES[deal.stage] || [];

  useEffect(() => {
    const loadHistory = async () => {
      setHistoryLoading(true);
      try {
        const history = await getDealStageHistory(deal.id);
        setStageHistory(Array.isArray(history) ? history : []);
      } catch {
        setStageHistory([]);
      } finally {
        setHistoryLoading(false);
      }
    };
    loadHistory();
  }, [deal.id]);

  const handleTransition = async (targetStage: DealStage) => {
    setTransitioning(true);
    setTransitionError(null);
    try {
      await onTransition(deal, targetStage, reason);
      onClose();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to transition stage.";
      setTransitionError(message);
    } finally {
      setTransitioning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative z-10 bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-border">
          <div className="flex-1 min-w-0 pr-3">
            <h2 className="text-lg font-semibold leading-tight">{deal.title}</h2>
            <p className="text-sm text-muted-foreground mt-0.5 truncate">
              {deal.opportunity_title}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="flex-shrink-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Details grid */}
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Current Stage</p>
              <span
                className={`text-xs font-medium px-2 py-1 rounded ${STAGE_TEXT_COLORS[deal.stage]}`}
              >
                {deal.stage_display || STAGE_LABELS[deal.stage]}
              </span>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Priority</p>
              <span
                className={`text-xs font-medium px-2 py-1 rounded ${PRIORITY_COLORS[deal.priority]}`}
              >
                {deal.priority_display}
              </span>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Est. Value</p>
              <p className="font-medium">{formatCurrency(deal.estimated_value)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Win Probability</p>
              <p className="font-medium">{deal.win_probability}%</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Owner</p>
              <p className="font-medium truncate">{deal.owner_name || "--"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Due Date</p>
              <div>
                <p className="font-medium">{formatDate(deal.due_date)}</p>
                <DueBadge dueDate={deal.due_date} />
              </div>
            </div>
            {deal.task_count > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Tasks</p>
                <p className="font-medium">{deal.task_count} open</p>
              </div>
            )}
            {deal.pending_approval_count > 0 && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Approvals</p>
                <p className="font-medium text-yellow-600">
                  {deal.pending_approval_count} pending
                </p>
              </div>
            )}
          </div>

          {/* Stage Transition */}
          {nextStages.length > 0 && (
            <div className="border-t border-border pt-4 space-y-3">
              <h3 className="text-sm font-semibold">Move Stage</h3>

              <div>
                <label className="text-xs text-muted-foreground mb-1 block">
                  Reason (optional)
                </label>
                <Input
                  placeholder="Reason for stage transition..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="text-sm"
                />
              </div>

              {transitionError && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{transitionError}</span>
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                {nextStages.map((targetStage) => (
                  <Button
                    key={targetStage}
                    variant="outline"
                    size="sm"
                    disabled={transitioning}
                    onClick={() => handleTransition(targetStage)}
                    className="flex items-center gap-1"
                  >
                    {transitioning ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                    {STAGE_LABELS[targetStage]}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Stage History */}
          <div className="border-t border-border pt-4 space-y-2">
            <h3 className="text-sm font-semibold">Stage History</h3>
            {historyLoading ? (
              <div className="flex items-center gap-2 text-muted-foreground text-sm py-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                Loading history...
              </div>
            ) : stageHistory.length === 0 ? (
              <p className="text-sm text-muted-foreground">No history yet.</p>
            ) : (
              <div className="space-y-1.5">
                {stageHistory.map((entry) => (
                  <div
                    key={entry.id}
                    className="text-xs text-muted-foreground flex items-start gap-2"
                  >
                    <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-muted-foreground flex-shrink-0" />
                    <div>
                      <span className="font-medium text-foreground">
                        {entry.from_stage
                          ? `${STAGE_LABELS[entry.from_stage]} → `
                          : "Created → "}
                        {STAGE_LABELS[entry.to_stage]}
                      </span>
                      {entry.reason && (
                        <span className="ml-1 italic">&ldquo;{entry.reason}&rdquo;</span>
                      )}
                      <div className="text-muted-foreground">
                        {entry.transitioned_by_name} &middot;{" "}
                        {formatDate(entry.transitioned_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Create Deal Modal
// ---------------------------------------------------------------------------

interface CreateDealModalProps {
  onClose: () => void;
  onCreated: (deal: Deal) => void;
}

function CreateDealModal({ onClose, onCreated }: CreateDealModalProps) {
  const [title, setTitle] = useState("");
  const [opportunityId, setOpportunityId] = useState("");
  const [estimatedValue, setEstimatedValue] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState<string>("3");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !opportunityId.trim()) {
      setError("Title and Opportunity ID are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload: CreateDealPayload = {
        title: title.trim(),
        opportunity: opportunityId.trim(),
        priority: parseInt(priority, 10) as 1 | 2 | 3 | 4,
      };
      if (estimatedValue) payload.estimated_value = estimatedValue;
      if (dueDate) payload.due_date = dueDate;

      const deal = await createDeal(payload);
      onCreated(deal);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create deal.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-10 bg-card border border-border rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 className="text-lg font-semibold">New Deal</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="text-sm font-medium mb-1.5 block">
              Title <span className="text-red-500">*</span>
            </label>
            <Input
              placeholder="Deal title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-1.5 block">
              Opportunity ID <span className="text-red-500">*</span>
            </label>
            <Input
              placeholder="UUID of the linked opportunity..."
              value={opportunityId}
              onChange={(e) => setOpportunityId(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground mt-1">
              Paste the UUID from the Opportunities page.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                Estimated Value
              </label>
              <Input
                type="number"
                placeholder="e.g. 1500000"
                value={estimatedValue}
                onChange={(e) => setEstimatedValue(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                Due Date
              </label>
              <Input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-1.5 block">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="1">Critical</option>
              <option value="2">High</option>
              <option value="3">Medium</option>
              <option value="4">Low</option>
            </select>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Deal
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Closed Deals Table
// ---------------------------------------------------------------------------

interface ClosedDealsTableProps {
  deals: Deal[];
  onCardClick: (deal: Deal) => void;
}

function ClosedDealsTable({ deals, onCardClick }: ClosedDealsTableProps) {
  if (deals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-muted-foreground">No closed deals found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Title</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Stage</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Owner</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Value</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Win %</th>
            <th className="pb-3 pr-4 font-medium text-muted-foreground">Priority</th>
            <th className="pb-3 font-medium text-muted-foreground">Updated</th>
          </tr>
        </thead>
        <tbody>
          {deals.map((deal) => (
            <tr
              key={deal.id}
              onClick={() => onCardClick(deal)}
              className="border-b cursor-pointer transition-colors hover:bg-muted/50"
            >
              <td className="py-3 pr-4 font-medium">
                <span className="line-clamp-1">{deal.title}</span>
              </td>
              <td className="py-3 pr-4">
                <span
                  className={`text-xs font-medium px-1.5 py-0.5 rounded ${STAGE_TEXT_COLORS[deal.stage]}`}
                >
                  {deal.stage_display || STAGE_LABELS[deal.stage]}
                </span>
              </td>
              <td className="py-3 pr-4 text-muted-foreground">
                {deal.owner_name || "--"}
              </td>
              <td className="py-3 pr-4 font-medium">
                {formatCurrency(deal.estimated_value)}
              </td>
              <td className="py-3 pr-4 text-muted-foreground">
                {deal.win_probability}%
              </td>
              <td className="py-3 pr-4">
                <span
                  className={`text-xs font-medium px-1.5 py-0.5 rounded ${PRIORITY_COLORS[deal.priority]}`}
                >
                  {deal.priority_display}
                </span>
              </td>
              <td className="py-3 text-muted-foreground">
                {formatDate(deal.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

type Tab = "pipeline" | "closed";

export default function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");

  // UI state
  const [activeTab, setActiveTab] = useState<Tab>("pipeline");
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchDeals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (priorityFilter) params.priority = priorityFilter;

      const data = await getDeals(params);
      setDeals(data.results || []);
    } catch (err) {
      setError("Failed to load deals. Please try again.");
      console.error("Error fetching deals:", err);
    } finally {
      setLoading(false);
    }
  }, [search, priorityFilter]);

  useEffect(() => {
    fetchDeals();
  }, [fetchDeals]);

  const handleCardClick = (deal: Deal) => {
    setSelectedDeal(deal);
  };

  const handleTransition = async (
    deal: Deal,
    targetStage: DealStage,
    reason: string
  ) => {
    const updated = await transitionDealStage(deal.id, {
      target_stage: targetStage,
      reason: reason || undefined,
    });
    setDeals((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
  };

  const handleDealCreated = (deal: Deal) => {
    setDeals((prev) => [deal, ...prev]);
    setShowCreateModal(false);
  };

  // Partition deals
  const activeDeals = deals.filter((d) => ACTIVE_STAGES.includes(d.stage));
  const closedDeals = deals.filter((d) => CLOSED_STAGES.includes(d.stage));

  const dealsByStage = (stage: DealStage) =>
    activeDeals.filter((d) => d.stage === stage);

  // Pipeline summary
  const totalPipelineValue = activeDeals.reduce((sum, d) => {
    if (!d.estimated_value) return sum;
    const num = parseFloat(d.estimated_value);
    return isNaN(num) ? sum : sum + num;
  }, 0);

  return (
    <div className="space-y-6">
      {/* Modals */}
      {selectedDeal && (
        <DealModal
          deal={selectedDeal}
          onClose={() => setSelectedDeal(null)}
          onTransition={handleTransition}
        />
      )}
      {showCreateModal && (
        <CreateDealModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleDealCreated}
        />
      )}

      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Deals Pipeline</h1>
          <p className="text-muted-foreground">
            Track and manage your active deal pursuits
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Deal
        </Button>
      </div>

      {/* Summary cards */}
      {!loading && !error && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Active Deals</p>
              <p className="text-2xl font-bold">{activeDeals.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Pipeline Value</p>
              <p className="text-2xl font-bold">
                {formatCurrency(totalPipelineValue.toString())}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Closed Won</p>
              <p className="text-2xl font-bold text-emerald-600">
                {closedDeals.filter((d) => d.stage === "closed_won").length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-xs text-muted-foreground">Closed Lost / No-Bid</p>
              <p className="text-2xl font-bold text-muted-foreground">
                {closedDeals.filter(
                  (d) => d.stage === "closed_lost" || d.stage === "no_bid"
                ).length}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-4 pb-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search deals..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Priorities</option>
              <option value="1">Critical</option>
              <option value="2">High</option>
              <option value="3">Medium</option>
              <option value="4">Low</option>
            </select>

            {/* Tab switcher */}
            <div className="flex rounded-md border border-input overflow-hidden ml-auto">
              <button
                onClick={() => setActiveTab("pipeline")}
                className={`px-3 py-1.5 text-sm transition-colors ${
                  activeTab === "pipeline"
                    ? "bg-primary text-primary-foreground"
                    : "bg-background hover:bg-muted"
                }`}
              >
                Pipeline Board
              </button>
              <button
                onClick={() => setActiveTab("closed")}
                className={`px-3 py-1.5 text-sm transition-colors border-l border-input ${
                  activeTab === "closed"
                    ? "bg-primary text-primary-foreground"
                    : "bg-background hover:bg-muted"
                }`}
              >
                Closed ({closedDeals.length})
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading deals...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="outline" onClick={fetchDeals}>
            Retry
          </Button>
        </div>
      ) : activeTab === "pipeline" ? (
        /* Kanban Board */
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-3 min-w-max">
            {ACTIVE_STAGES.map((stage) => (
              <PipelineColumn
                key={stage}
                stage={stage}
                deals={dealsByStage(stage)}
                onCardClick={handleCardClick}
              />
            ))}
          </div>
        </div>
      ) : (
        /* Closed Deals Tab */
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Closed Deals
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({closedDeals.length} results)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ClosedDealsTable deals={closedDeals} onCardClick={handleCardClick} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
