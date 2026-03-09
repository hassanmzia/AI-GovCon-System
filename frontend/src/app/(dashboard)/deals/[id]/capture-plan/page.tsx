"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getDeal } from "@/services/deals";
import { Deal } from "@/types/deal";
import api from "@/lib/api";
import {
  Loader2,
  ArrowLeft,
  Target,
  Lightbulb,
  Flag,
  Shield,
  Users,
  TrendingUp,
  FileText,
  CheckCircle,
  Clock,
  AlertTriangle,
  Zap,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

interface CapturePlan {
  id: string;
  deal: string;
  win_strategy: string;
  value_proposition: string;
  competitive_positioning: string;
  key_risks: Array<{ risk: string; mitigation: string; severity: "low" | "medium" | "high" }>;
  action_items: Array<{ action: string; owner: string; due_date: string | null; status: string }>;
  customer_hot_buttons: string[];
  incumbent_info: string;
  teaming_strategy: string;
  price_to_win_notes: string;
  created_at: string;
  updated_at: string;
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const SEVERITY_COLORS: Record<string, string> = {
  low: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  high: "bg-red-100 text-red-700 border-red-200",
};

const ACTION_STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  in_progress: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  blocked: "bg-red-100 text-red-700",
};

function RiskRow({ risk }: { risk: CapturePlan["key_risks"][0] }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`border rounded-lg overflow-hidden ${SEVERITY_COLORS[risk.severity]}`}>
      <div
        className="flex items-center gap-3 p-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <button className="flex-shrink-0">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </button>
        <AlertTriangle className="h-4 w-4 flex-shrink-0" />
        <span className="flex-1 text-sm font-medium">{risk.risk}</span>
        <span className="text-xs px-2 py-0.5 rounded-full border capitalize">{risk.severity}</span>
      </div>
      {expanded && (
        <div className="border-t bg-white px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-1">Mitigation</p>
          <p className="text-sm">{risk.mitigation || "No mitigation defined."}</p>
        </div>
      )}
    </div>
  );
}

function CapturePlanDisplay({ plan }: { plan: CapturePlan }) {
  const completedActions = plan.action_items?.filter((a) => a.status === "completed").length || 0;
  const totalActions = plan.action_items?.length || 0;

  return (
    <div className="space-y-6">
      {/* Win Strategy & Value Proposition */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-500" /> Win Strategy
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.win_strategy ? (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{plan.win_strategy}</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">No win strategy defined.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-yellow-500" /> Value Proposition
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.value_proposition ? (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{plan.value_proposition}</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">No value proposition defined.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Competitive Positioning & Customer Hot Buttons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-purple-500" /> Competitive Positioning
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.competitive_positioning ? (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{plan.competitive_positioning}</p>
            ) : (
              <p className="text-sm text-muted-foreground italic">No competitive positioning defined.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="h-4 w-4 text-orange-500" /> Customer Hot Buttons
            </CardTitle>
          </CardHeader>
          <CardContent>
            {plan.customer_hot_buttons?.length > 0 ? (
              <ul className="space-y-2">
                {plan.customer_hot_buttons.map((hb, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-5 h-5 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    {hb}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground italic">No hot buttons identified.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Risks */}
      {plan.key_risks?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="h-4 w-4 text-red-500" /> Key Risks & Mitigations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {plan.key_risks.map((risk, i) => (
              <RiskRow key={i} risk={risk} />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Action Items */}
      {plan.action_items?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" /> Action Items
              <span className="text-xs text-muted-foreground font-normal ml-1">
                ({completedActions}/{totalActions} completed)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs text-muted-foreground pb-2 border-b">
                <span className="sm:col-span-2">Action</span>
                <span className="hidden sm:block">Owner</span>
                <span className="hidden sm:block">Due</span>
              </div>
              {plan.action_items.map((a, i) => (
                <div key={i} className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-sm py-2 border-b last:border-0 items-center">
                  <div className="sm:col-span-2 flex items-start gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-xs flex-shrink-0 ${ACTION_STATUS_COLORS[a.status] || "bg-gray-100 text-gray-600"}`}>
                      {a.status}
                    </span>
                    <span className="text-sm">{a.action}</span>
                  </div>
                  <span className="hidden sm:block text-muted-foreground">{a.owner || "--"}</span>
                  <span className="hidden sm:block text-muted-foreground">{formatDate(a.due_date)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Teaming & PTW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {plan.teaming_strategy && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="h-4 w-4" /> Teaming Strategy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{plan.teaming_strategy}</p>
            </CardContent>
          </Card>
        )}
        {plan.price_to_win_notes && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Flag className="h-4 w-4" /> Price-to-Win Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{plan.price_to_win_notes}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {plan.incumbent_info && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4" /> Incumbent Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{plan.incumbent_info}</p>
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-muted-foreground text-right">
        Last updated: {formatDate(plan.updated_at)}
      </p>
    </div>
  );
}

export default function DealCapturePlanPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [deal, setDeal] = useState<Deal | null>(null);
  const [plan, setPlan] = useState<CapturePlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await getDeal(id);
      setDeal(d);
      // Try to fetch the capture plan
      try {
        const res = await api.get("/deals/capture-plans/", { params: { deal: id } });
        const plans = res.data.results || res.data;
        if (plans.length > 0) setPlan(plans[0]);
      } catch {
        // capture plan not yet created
      }
    } catch {
      setError("Failed to load capture plan.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-red-600">{error}</p>
        <Button variant="outline" onClick={() => router.back()} className="mt-4">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/deals">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" /> Deals
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Capture Plan</h1>
          {deal && (
            <p className="text-muted-foreground mt-0.5">{deal.title}</p>
          )}
        </div>
      </div>

      {plan ? (
        <CapturePlanDisplay plan={plan} />
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
            <Target className="h-12 w-12 text-muted-foreground" />
            <div className="text-center">
              <h3 className="font-semibold text-lg">No Capture Plan Yet</h3>
              <p className="text-muted-foreground text-sm mt-1">
                A capture plan will be auto-generated when the AI orchestrator processes this deal,
                or you can trigger generation from the deal pipeline.
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => router.back()}>
                <ArrowLeft className="h-4 w-4 mr-2" /> Back to Deal
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
