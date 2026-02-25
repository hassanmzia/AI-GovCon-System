"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScoreBadge, RecommendationBadge } from "@/components/opportunities/score-badge";
import { getOpportunities, triggerScan } from "@/services/opportunities";
import { Opportunity } from "@/types/opportunity";
import { Search, RefreshCw, Loader2 } from "lucide-react";

export default function OpportunitiesPage() {
  const router = useRouter();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");
  const [naicsFilter, setNaicsFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [recommendationFilter, setRecommendationFilter] = useState("");

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (agencyFilter) params.agency = agencyFilter;
      if (naicsFilter) params.naics_code = naicsFilter;
      if (statusFilter) params.status = statusFilter;
      if (recommendationFilter) params.recommendation = recommendationFilter;

      const data = await getOpportunities(params);
      setOpportunities(data.results || []);
    } catch (err) {
      setError("Failed to load opportunities. Please try again.");
      console.error("Error fetching opportunities:", err);
    } finally {
      setLoading(false);
    }
  }, [search, agencyFilter, naicsFilter, statusFilter, recommendationFilter]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const handleTriggerScan = async () => {
    setScanning(true);
    try {
      await triggerScan();
      await fetchOpportunities();
    } catch (err) {
      console.error("Error triggering scan:", err);
    } finally {
      setScanning(false);
    }
  };

  const handleRowClick = (id: string) => {
    router.push(`/opportunities/${id}`);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const truncate = (str: string, maxLen: number) => {
    if (!str) return "--";
    return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
  };

  const getDaysRemainingBadge = (days: number | null) => {
    if (days === null || days === undefined) {
      return <span className="text-muted-foreground text-xs">--</span>;
    }
    if (days < 0) {
      return (
        <span className="text-xs text-red-600 font-medium">Expired</span>
      );
    }
    if (days <= 7) {
      return (
        <span className="text-xs text-red-600 font-medium">{days}d left</span>
      );
    }
    if (days <= 30) {
      return (
        <span className="text-xs text-yellow-600 font-medium">
          {days}d left
        </span>
      );
    }
    return (
      <span className="text-xs text-green-600 font-medium">{days}d left</span>
    );
  };

  // Extract unique values for filter dropdowns
  const uniqueAgencies = Array.from(
    new Set(opportunities.map((o) => o.agency).filter(Boolean))
  ).sort();
  const uniqueNaics = Array.from(
    new Set(opportunities.map((o) => o.naics_code).filter(Boolean))
  ).sort();
  const uniqueStatuses = Array.from(
    new Set(opportunities.map((o) => o.status).filter(Boolean))
  ).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Opportunity Intelligence
          </h1>
          <p className="text-muted-foreground">
            Discover and evaluate government contract opportunities
          </p>
        </div>
        <Button onClick={handleTriggerScan} disabled={scanning}>
          {scanning ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Trigger Scan
        </Button>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search opportunities..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={agencyFilter}
              onChange={(e) => setAgencyFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Agencies</option>
              {uniqueAgencies.map((agency) => (
                <option key={agency} value={agency}>
                  {agency}
                </option>
              ))}
            </select>
            <select
              value={naicsFilter}
              onChange={(e) => setNaicsFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All NAICS</option>
              {uniqueNaics.map((naics) => (
                <option key={naics} value={naics}>
                  {naics}
                </option>
              ))}
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Statuses</option>
              {uniqueStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
            <select
              value={recommendationFilter}
              onChange={(e) => setRecommendationFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Recommendations</option>
              <option value="strong_bid">Strong Bid</option>
              <option value="bid">Bid</option>
              <option value="consider">Consider</option>
              <option value="no_bid">No Bid</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Opportunities
            {!loading && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({opportunities.length} results)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-3 text-muted-foreground">
                Loading opportunities...
              </span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button variant="outline" onClick={fetchOpportunities}>
                Retry
              </Button>
            </div>
          ) : opportunities.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground">
                No opportunities found matching your filters.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Title
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Agency
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      NAICS
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Set-Aside
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Deadline
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Score
                    </th>
                    <th className="pb-3 pr-4 font-medium text-muted-foreground">
                      Recommendation
                    </th>
                    <th className="pb-3 font-medium text-muted-foreground">
                      Posted
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {opportunities.map((opp) => (
                    <tr
                      key={opp.id}
                      onClick={() => handleRowClick(opp.id)}
                      className="border-b cursor-pointer transition-colors hover:bg-muted/50"
                    >
                      <td className="py-3 pr-4 font-medium">
                        {truncate(opp.title, 50)}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {truncate(opp.agency, 30)}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {opp.naics_code || "--"}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {opp.set_aside || "--"}
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex flex-col">
                          <span className="text-muted-foreground">
                            {formatDate(opp.response_deadline)}
                          </span>
                          {getDaysRemainingBadge(opp.days_until_deadline)}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        {opp.score ? (
                          <ScoreBadge
                            score={opp.score.total_score}
                            recommendation={opp.score.recommendation}
                            size="sm"
                          />
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            --
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-4">
                        {opp.score ? (
                          <RecommendationBadge
                            recommendation={opp.score.recommendation}
                            size="sm"
                          />
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            --
                          </span>
                        )}
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {formatDate(opp.posted_date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
