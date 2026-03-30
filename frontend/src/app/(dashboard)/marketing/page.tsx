"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  getCampaigns,
  getCompetitorProfiles,
  getMarketIntelligence,
} from "@/services/marketing";
import {
  MarketingCampaign,
  CompetitorProfile,
  MarketIntelligence,
} from "@/types/marketing";
import {
  Loader2,
  Target,
  Building2,
  BarChart3,
  Globe,
  Users,
  ExternalLink,
  Shield,
  Calendar,
} from "lucide-react";

type TabId = "campaigns" | "competitors" | "agencies";

const CAMPAIGN_STATUS_STYLES: Record<string, string> = {
  planning: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  completed: "bg-blue-100 text-blue-700",
  cancelled: "bg-red-100 text-red-700",
};

const CHANNEL_LABELS: Record<string, string> = {
  email: "Email",
  social_media: "Social Media",
  webinar: "Webinar",
  trade_show: "Trade Show",
  direct_outreach: "Direct Outreach",
  advertising: "Advertising",
  partnership: "Partnership",
  other: "Other",
};

const CATEGORY_STYLES: Record<string, string> = {
  budget_trends: "bg-green-100 text-green-700",
  policy_changes: "bg-purple-100 text-purple-700",
  technology_shifts: "bg-blue-100 text-blue-700",
  procurement_patterns: "bg-orange-100 text-orange-700",
  workforce_trends: "bg-rose-100 text-rose-700",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatBudget(budget: string | null): string {
  if (!budget) return "--";
  const num = parseFloat(budget);
  if (isNaN(num)) return "--";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(num);
}

function truncate(str: string, maxLen: number): string {
  if (!str) return "--";
  return str.length > maxLen ? str.slice(0, maxLen) + "..." : str;
}

function WinRateBar({ rate }: { rate: number | null }) {
  if (rate == null) return <span className="text-xs text-muted-foreground">N/A</span>;
  const pct = Math.round(rate * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 rounded-full bg-gray-100">
        <div
          className={`h-2 rounded-full ${pct >= 40 ? "bg-green-500" : pct >= 30 ? "bg-yellow-500" : "bg-red-400"}`}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <span className="text-xs font-medium">{pct}%</span>
    </div>
  );
}

export default function MarketingPage() {
  const [activeTab, setActiveTab] = useState<TabId>("campaigns");
  const [campaigns, setCampaigns] = useState<MarketingCampaign[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [intelligence, setIntelligence] = useState<MarketIntelligence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [campaignsData, competitorsData, intelData] = await Promise.all([
        getCampaigns().catch(() => ({ results: [], count: 0 })),
        getCompetitorProfiles().catch(() => ({ results: [], count: 0 })),
        getMarketIntelligence().catch(() => ({ results: [], count: 0 })),
      ]);
      setCampaigns(campaignsData.results || []);
      setCompetitors(competitorsData.results || []);
      setIntelligence(intelData.results || []);
    } catch (err) {
      setError("Failed to load marketing data. Please try again.");
      console.error("Error fetching marketing data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const activeCampaigns = campaigns.filter((c) => c.status === "active").length;

  const tabs: { id: TabId; label: string; count: number }[] = [
    { id: "campaigns", label: "Campaigns", count: campaigns.length },
    { id: "competitors", label: "Competitor Intelligence", count: competitors.length },
    { id: "agencies", label: "Market Intelligence", count: intelligence.length },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Marketing & Sales Intelligence
          </h1>
          <p className="text-muted-foreground">
            Manage campaigns, track competitors, and analyze market intelligence
          </p>
        </div>
      </div>

      {/* KPI Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100">
              <BarChart3 className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Competitors Tracked</p>
              <p className="text-2xl font-bold">{competitors.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
              <Building2 className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Market Intel Reports</p>
              <p className="text-2xl font-bold">{intelligence.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
              <Target className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Active Campaigns</p>
              <p className="text-2xl font-bold">{activeCampaigns}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground"
              }`}
            >
              {tab.label}
              <span className="ml-1.5 text-xs text-muted-foreground">({tab.count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading data...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16">
          <p className="text-red-600 mb-4">{error}</p>
          <Button variant="outline" onClick={fetchAll}>
            Retry
          </Button>
        </div>
      ) : (
        <>
          {/* Campaigns Tab */}
          {activeTab === "campaigns" && (
            <div className="space-y-4">
              {campaigns.length === 0 ? (
                <Card>
                  <CardContent className="flex items-center justify-center py-12">
                    <p className="text-muted-foreground">No campaigns found.</p>
                  </CardContent>
                </Card>
              ) : (
                campaigns.map((campaign) => (
                  <Card key={campaign.id}>
                    <CardContent className="pt-5">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h3 className="font-semibold text-base">
                              {campaign.name}
                            </h3>
                            <span
                              className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                CAMPAIGN_STATUS_STYLES[campaign.status] ||
                                "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {campaign.status.charAt(0).toUpperCase() +
                                campaign.status.slice(1)}
                            </span>
                            <span className="inline-flex items-center rounded-full bg-indigo-100 text-indigo-700 px-2 py-0.5 text-xs font-medium">
                              {CHANNEL_LABELS[campaign.channel] || campaign.channel}
                            </span>
                          </div>
                          {campaign.description && (
                            <p className="text-sm text-muted-foreground mb-2">
                              {truncate(campaign.description, 140)}
                            </p>
                          )}
                          {campaign.target_audience && (
                            <p className="text-xs text-muted-foreground">
                              <span className="font-medium">Target:</span>{" "}
                              {campaign.target_audience}
                            </p>
                          )}
                          {campaign.goals && campaign.goals.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Goals
                              </p>
                              <ul className="space-y-0.5">
                                {campaign.goals.map((goal, i) => (
                                  <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
                                    <span className="mt-0.5">&#8226;</span>
                                    <span>{goal}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {/* Campaign Metrics */}
                          {campaign.metrics && Object.keys(campaign.metrics).length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-3">
                              {Object.entries(campaign.metrics).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="text-muted-foreground">
                                    {key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}:
                                  </span>{" "}
                                  <span className="font-medium">
                                    {typeof value === "number" && value > 100000
                                      ? `$${(value as number / 1000000).toFixed(1)}M`
                                      : String(value)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-1 text-sm shrink-0">
                          <span className="font-semibold text-base">
                            {formatBudget(campaign.budget)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(campaign.start_date)} &mdash;{" "}
                            {formatDate(campaign.end_date)}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* Competitor Intelligence Tab */}
          {activeTab === "competitors" && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {competitors.length === 0 ? (
                <Card className="col-span-full">
                  <CardContent className="flex items-center justify-center py-12">
                    <p className="text-muted-foreground">No competitor profiles found.</p>
                  </CardContent>
                </Card>
              ) : (
                competitors.map((competitor) => (
                  <Card key={competitor.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{competitor.name}</CardTitle>
                          {competitor.website && (
                            <a
                              href={competitor.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-muted-foreground hover:text-foreground"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          )}
                        </div>
                        {competitor.is_active && (
                          <span className="inline-flex items-center rounded-full bg-green-100 text-green-700 px-2 py-0.5 text-xs font-medium">
                            Active
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground mt-1">
                        {competitor.revenue_range && (
                          <span>Revenue: {competitor.revenue_range}</span>
                        )}
                        {competitor.employee_count && (
                          <span className="flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            {competitor.employee_count.toLocaleString()}
                          </span>
                        )}
                        {competitor.cage_code && (
                          <span>CAGE: {competitor.cage_code}</span>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* Win Rate */}
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted-foreground">Win Rate</span>
                        <WinRateBar rate={competitor.win_rate} />
                      </div>

                      {/* Contract Vehicles */}
                      {competitor.contract_vehicles && competitor.contract_vehicles.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            Contract Vehicles
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {competitor.contract_vehicles.slice(0, 5).map((v, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center rounded-full bg-indigo-100 text-indigo-700 px-2 py-0.5 text-xs"
                              >
                                {v}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* NAICS Codes */}
                      {competitor.naics_codes && competitor.naics_codes.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            NAICS Codes
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {competitor.naics_codes.join(", ")}
                          </p>
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-3">
                        {/* Strengths */}
                        {competitor.strengths && competitor.strengths.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Strengths
                            </p>
                            <ul className="space-y-0.5">
                              {competitor.strengths.slice(0, 3).map((s, i) => (
                                <li
                                  key={i}
                                  className="text-xs text-green-700 flex items-start gap-1"
                                >
                                  <span className="mt-0.5">&#8226;</span>
                                  <span>{s}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Weaknesses */}
                        {competitor.weaknesses && competitor.weaknesses.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Weaknesses
                            </p>
                            <ul className="space-y-0.5">
                              {competitor.weaknesses.slice(0, 3).map((w, i) => (
                                <li
                                  key={i}
                                  className="text-xs text-red-700 flex items-start gap-1"
                                >
                                  <span className="mt-0.5">&#8226;</span>
                                  <span>{w}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Past Performance */}
                      {competitor.past_performance_summary && (
                        <div className="pt-1 border-t">
                          <p className="text-xs text-muted-foreground">
                            {truncate(competitor.past_performance_summary, 150)}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* Market Intelligence Tab */}
          {activeTab === "agencies" && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {intelligence.length === 0 ? (
                <Card className="col-span-full">
                  <CardContent className="flex items-center justify-center py-12">
                    <p className="text-muted-foreground">No market intelligence found.</p>
                  </CardContent>
                </Card>
              ) : (
                intelligence.map((item) => (
                  <Card key={item.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <CardTitle className="text-base leading-tight">
                          {item.title}
                        </CardTitle>
                        <span
                          className={`shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            CATEGORY_STYLES[item.category] || "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {item.category_display || item.category.replace(/_/g, " ")}
                        </span>
                      </div>
                      {item.published_date && (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(item.published_date)}
                        </div>
                      )}
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* Summary */}
                      <p className="text-sm text-muted-foreground">
                        {truncate(item.summary, 200)}
                      </p>

                      {/* Impact Assessment */}
                      {item.impact_assessment && (
                        <div className="rounded-md bg-amber-50 border border-amber-200 p-2.5">
                          <p className="text-xs font-medium text-amber-800 mb-0.5">
                            Impact Assessment
                          </p>
                          <p className="text-xs text-amber-700">
                            {truncate(item.impact_assessment, 180)}
                          </p>
                        </div>
                      )}

                      {/* Affected Agencies */}
                      {item.affected_agencies && item.affected_agencies.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            Affected Agencies
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {item.affected_agencies.slice(0, 5).map((agency, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center rounded-full bg-blue-100 text-blue-700 px-2 py-0.5 text-xs"
                              >
                                {agency}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Affected NAICS */}
                      {item.affected_naics && item.affected_naics.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">
                            NAICS Codes
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {item.affected_naics.join(", ")}
                          </p>
                        </div>
                      )}

                      {/* Source Link */}
                      {item.source_url && (
                        <div className="pt-1 border-t">
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                          >
                            <Globe className="h-3 w-3" />
                            View Source
                          </a>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
