"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScoreBadge, RecommendationBadge } from "@/components/opportunities/score-badge";
import { getOpportunities, getOpportunityFilters, triggerScan } from "@/services/opportunities";
import { Opportunity } from "@/types/opportunity";
import { Search, RefreshCw, Loader2, ChevronLeft, ChevronRight } from "lucide-react";

const PAGE_SIZE = 50;

const NAICS_LABELS: Record<string, string> = {
  "513210": "513210 – Software Publishing",
  "541511": "541511 – Custom Computer Programming",
  "518210": "518210 – Computing Infrastructure / Web Hosting",
  "611420": "611420 – Computer Training",
  "541714": "541714 – R&D in Biotechnology",
};

interface FilterOptions {
  agencies: string[];
  sources: string[];
  statuses: string[];
  naics_codes: string[];
  states: string[];
}

export default function OpportunitiesPage() {
  const router = useRouter();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Filter options loaded from the API (all distinct values, not just current page)
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    agencies: [],
    sources: [],
    statuses: [],
    naics_codes: [],
    states: [],
  });

  // Filters
  const [search, setSearch] = useState("");
  const [agencyFilter, setAgencyFilter] = useState("");
  const [naicsFilter, setNaicsFilter] = useState("");   // selected from dropdown
  const [naicsCustom, setNaicsCustom] = useState("");  // typed manually
  const [statusFilter, setStatusFilter] = useState("");
  const [recommendationFilter, setRecommendationFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");

  // Load filter dropdown options once on mount
  useEffect(() => {
    getOpportunityFilters()
      .then(setFilterOptions)
      .catch((err) => console.error("Failed to load filter options:", err));
  }, []);

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {
        page: String(currentPage),
        page_size: String(PAGE_SIZE),
      };
      if (search) params.search = search;
      if (agencyFilter) params["agency__icontains"] = agencyFilter;
      const effectiveNaics = naicsCustom || naicsFilter;
      if (effectiveNaics) params["naics_code__icontains"] = effectiveNaics;
      if (statusFilter) params.status = statusFilter;
      if (recommendationFilter) params["score__recommendation"] = recommendationFilter;
      if (sourceFilter) params["source__name__icontains"] = sourceFilter;

      const data = await getOpportunities(params);
      setOpportunities(data.results || []);
      setTotalCount(data.count || 0);
    } catch (err) {
      setError("Failed to load opportunities. Please try again.");
      console.error("Error fetching opportunities:", err);
    } finally {
      setLoading(false);
    }
  }, [search, agencyFilter, naicsFilter, naicsCustom, statusFilter, recommendationFilter, sourceFilter, currentPage]);

  // Reset to page 1 when any filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [search, agencyFilter, naicsFilter, naicsCustom, statusFilter, recommendationFilter, sourceFilter]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const handleTriggerScan = async () => {
    setScanning(true);
    try {
      await triggerScan();
      getOpportunityFilters().then(setFilterOptions).catch(() => {});
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
      return <span className="text-xs text-red-600 font-medium">Expired</span>;
    }
    if (days <= 7) {
      return <span className="text-xs text-red-600 font-medium">{days}d left</span>;
    }
    if (days <= 30) {
      return <span className="text-xs text-yellow-600 font-medium">{days}d left</span>;
    }
    return <span className="text-xs text-green-600 font-medium">{days}d left</span>;
  };

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);
  const pageStart = totalCount === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const pageEnd = Math.min(currentPage * PAGE_SIZE, totalCount);

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
              {filterOptions.agencies.map((agency) => (
                <option key={agency} value={agency}>{agency}</option>
              ))}
            </select>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Sources</option>
              {filterOptions.sources.map((source) => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
            <select
              value={naicsFilter}
              onChange={(e) => { setNaicsFilter(e.target.value); setNaicsCustom(""); }}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All NAICS</option>
              {filterOptions.naics_codes.map((naics) => (
                <option key={naics} value={naics}>{NAICS_LABELS[naics] || naics}</option>
              ))}
            </select>
            <input
              type="text"
              value={naicsCustom}
              onChange={(e) => { setNaicsCustom(e.target.value); setNaicsFilter(""); }}
              placeholder="or type NAICS…"
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-32"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:h-9 sm:w-auto"
            >
              <option value="">All Statuses</option>
              {filterOptions.statuses.map((s) => (
                <option key={s} value={s}>{s}</option>
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
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">
            Opportunities
            {!loading && totalCount > 0 && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({pageStart}–{pageEnd} of {totalCount})
              </span>
            )}
          </CardTitle>
          {totalPages > 1 && (
            <div className="flex items-center gap-2 text-sm">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1 || loading}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-muted-foreground">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages || loading}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-3 text-muted-foreground">Loading opportunities...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button variant="outline" onClick={fetchOpportunities}>Retry</Button>
            </div>
          ) : opportunities.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground">
                No opportunities found matching your filters.
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Title</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Agency / State</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Source</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Sol #</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">NAICS</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Deadline</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Score</th>
                      <th className="pb-3 font-medium text-muted-foreground">Posted</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opportunities.map((opp) => (
                      <tr
                        key={opp.id}
                        onClick={() => handleRowClick(opp.id)}
                        className="border-b cursor-pointer transition-colors hover:bg-muted/50"
                      >
                        <td className="py-3 pr-4 font-medium">{truncate(opp.title, 50)}</td>
                        <td className="py-3 pr-4 text-muted-foreground">
                          <div>{truncate(opp.agency, 28)}</div>
                          {opp.place_state && (
                            <div className="text-xs text-muted-foreground/70">{opp.place_state}</div>
                          )}
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground text-xs">{opp.source_name || "--"}</td>
                        <td className="py-3 pr-4 text-muted-foreground font-mono text-xs">{opp.sol_number || "--"}</td>
                        <td className="py-3 pr-4 text-muted-foreground">{opp.naics_code || "--"}</td>
                        <td className="py-3 pr-4">
                          <div className="flex flex-col">
                            <span className="text-muted-foreground">{formatDate(opp.response_deadline)}</span>
                            {getDaysRemainingBadge(opp.days_until_deadline)}
                          </div>
                        </td>
                        <td className="py-3 pr-4">
                          {opp.score ? (
                            <div className="flex flex-col gap-1">
                              <ScoreBadge
                                score={opp.score.total_score}
                                recommendation={opp.score.recommendation}
                                size="sm"
                              />
                              <RecommendationBadge
                                recommendation={opp.score.recommendation}
                                size="sm"
                              />
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">--</span>
                          )}
                        </td>
                        <td className="py-3 text-muted-foreground">{formatDate(opp.posted_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Showing {pageStart}–{pageEnd} of {totalCount} opportunities
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1 || loading}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground px-2">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages || loading}
                    >
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
