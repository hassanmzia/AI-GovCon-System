"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createDeal } from "@/services/deals";
import { getOpportunity } from "@/services/opportunities";
import { CreateDealPayload, DealPriority } from "@/types/deal";
import { Opportunity } from "@/types/opportunity";
import { ArrowLeft, Loader2, AlertCircle } from "lucide-react";

export default function NewDealPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const opportunityId = searchParams.get("opportunity_id") || "";

  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [loadingOpportunity, setLoadingOpportunity] = useState(false);

  const [title, setTitle] = useState("");
  const [estimatedValue, setEstimatedValue] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState<string>("3");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch opportunity details to pre-fill the form
  useEffect(() => {
    if (!opportunityId) return;

    const fetchOpportunity = async () => {
      setLoadingOpportunity(true);
      try {
        const opp = await getOpportunity(opportunityId);
        setOpportunity(opp);
        // Pre-fill form fields from opportunity
        if (!title) setTitle(opp.title || "");
        if (!estimatedValue && opp.estimated_value) {
          setEstimatedValue(String(opp.estimated_value));
        }
        if (!dueDate && opp.response_deadline) {
          setDueDate(opp.response_deadline.split("T")[0]);
        }
      } catch {
        // Opportunity fetch failed — user can still fill in manually
      } finally {
        setLoadingOpportunity(false);
      }
    };
    fetchOpportunity();
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opportunityId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    if (!opportunityId.trim()) {
      setError("Opportunity ID is required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const payload: CreateDealPayload = {
        title: title.trim(),
        opportunity: opportunityId.trim(),
        priority: parseInt(priority, 10) as DealPriority,
      };
      if (estimatedValue) payload.estimated_value = estimatedValue;
      if (dueDate) payload.due_date = dueDate;

      const deal = await createDeal(payload);
      router.push(`/deals`);
      // Could also navigate to deal detail: router.push(`/deals/${deal.id}`);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create deal.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">New Deal</h1>
          <p className="text-muted-foreground text-sm">
            Create a new deal{opportunity ? ` from "${opportunity.title}"` : ""}
          </p>
        </div>
      </div>

      {/* Opportunity Info */}
      {loadingOpportunity && (
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading opportunity details...
        </div>
      )}

      {opportunity && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Linked Opportunity
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p className="font-medium">{opportunity.title}</p>
            <p className="text-muted-foreground">
              {opportunity.agency}
              {opportunity.sol_number ? ` — ${opportunity.sol_number}` : ""}
            </p>
            {opportunity.estimated_value && (
              <p className="text-muted-foreground">
                Est. Value: ${opportunity.estimated_value.toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
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
                readOnly={!!searchParams.get("opportunity_id")}
                className={searchParams.get("opportunity_id") ? "bg-muted" : ""}
              />
              {searchParams.get("opportunity_id") && (
                <p className="text-xs text-muted-foreground mt-1">
                  Pre-filled from the linked opportunity.
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
              <label className="text-sm font-medium mb-1.5 block">
                Priority
              </label>
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

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Create Deal
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
