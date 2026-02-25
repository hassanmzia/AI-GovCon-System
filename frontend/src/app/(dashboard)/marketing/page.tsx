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
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Building2,
  BarChart3,
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

function GrowthTrendIcon({ trend }: { trend: string }) {
  if (trend === "up" || trend === "growing" || trend === "increasing") {
    return <TrendingUp className="h-4 w-4 text-green-600" />;
  }
  if (trend === "down" || trend === "declining" || trend === "decreasing") {
    return <TrendingDown className="h-4 w-4 text-red-600" />;
  }
  return <Minus className="h-4 w-4 text-gray-400" />;
}

export default function MarketingPage() {
  const [activeTab, setActiveTab] = useState<TabId>("campaigns");
  const [campaigns, setCampaigns] = useState<MarketingCampaign[]>([]);
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [agencies, setAgencies] = useState<MarketIntelligence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [campaignsData, competitorsData, agenciesData] = await Promise.all([
        getCampaigns().catch(() => ({ results: [], count: 0 })),
        getCompetitorProfiles().catch(() => ({ results: [], count: 0 })),
        getMarketIntelligence().catch(() => ({ results: [], count: 0 })),
      ]);
      setCampaigns(campaignsData.results || []);
      setCompetitors(competitorsData.results || []);
      setAgencies(agenciesData.results || []);
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

  const tabs: { id: TabId; label: string }[] = [
    { id: "campaigns", label: "Campaigns" },
    { id: "competitors", label: "Competitor Intelligence" },
    { id: "agencies", label: "Agency Intelligence" },
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
            Manage campaigns, track competitors, and analyze agency intelligence
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
              <p className="text-sm text-muted-foreground">Agencies Profiled</p>
              <p className="text-2xl font-bold">{agencies.length}</p>
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
                    <p className="text-muted-foreground">
                      No campaigns found.
                    </p>
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
                              {CHANNEL_LABELS[campaign.channel] ||
                                campaign.channel}
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
                              <p className="text-xs text-muted-foreground">
                                {truncate(campaign.goals.join(", "), 120)}
                              </p>
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
                    <p className="text-muted-foreground">
                      No competitor profiles found.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                competitors.map((competitor) => (
                  <Card key={competitor.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          {competitor.name}
                        </CardTitle>
                        <div className="flex items-center gap-1">
                          <GrowthTrendIcon
                            trend={competitor.growth_trend || ""}
                          />
                          <span className="text-xs text-muted-foreground capitalize">
                            {competitor.growth_trend || "Unknown"}
                          </span>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* Core Competencies */}
                      {competitor.core_competencies &&
                        competitor.core_competencies.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Core Competencies
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {competitor.core_competencies
                                .slice(0, 5)
                                .map((comp, i) => (
                                  <span
                                    key={i}
                                    className="inline-flex items-center rounded-full bg-slate-100 text-slate-700 px-2 py-0.5 text-xs"
                                  >
                                    {comp}
                                  </span>
                                ))}
                            </div>
                          </div>
                        )}

                      <div className="grid grid-cols-2 gap-3">
                        {/* Strengths */}
                        {competitor.strengths &&
                          competitor.strengths.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Strengths
                              </p>
                              <ul className="space-y-0.5">
                                {competitor.strengths
                                  .slice(0, 3)
                                  .map((s, i) => (
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
                        {competitor.weaknesses &&
                          competitor.weaknesses.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Weaknesses
                              </p>
                              <ul className="space-y-0.5">
                                {competitor.weaknesses
                                  .slice(0, 3)
                                  .map((w, i) => (
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

                      <div className="flex items-center justify-between pt-1 border-t">
                        {competitor.pricing_tendency && (
                          <span className="inline-flex items-center rounded-full bg-orange-100 text-orange-700 px-2 py-0.5 text-xs font-medium capitalize">
                            {competitor.pricing_tendency}
                          </span>
                        )}
                        {competitor.head_to_head_record && (
                          <span className="text-xs text-muted-foreground">
                            H2H:{" "}
                            <span className="font-medium">
                              {typeof competitor.head_to_head_record ===
                              "string"
                                ? competitor.head_to_head_record
                                : `W:${
                                    (
                                      competitor.head_to_head_record as Record<
                                        string,
                                        unknown
                                      >
                                    ).wins ?? 0
                                  } / L:${
                                    (
                                      competitor.head_to_head_record as Record<
                                        string,
                                        unknown
                                      >
                                    ).losses ?? 0
                                  }`}
                            </span>
                          </span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* Agency Intelligence Tab */}
          {activeTab === "agencies" && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {agencies.length === 0 ? (
                <Card className="col-span-full">
                  <CardContent className="flex items-center justify-center py-12">
                    <p className="text-muted-foreground">
                      No agency intelligence found.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                agencies.map((agency) => (
                  <Card key={agency.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          {agency.agency}
                        </CardTitle>
                        <span className="text-xs text-muted-foreground">
                          Last contact:{" "}
                          {agency.last_interaction
                            ? formatDate(agency.last_interaction)
                            : "Never"}
                        </span>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {/* Relationship Score */}
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-medium text-muted-foreground">
                            Relationship Score
                          </p>
                          <span className="text-xs font-semibold">
                            {agency.relationship_score ?? 0}/100
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-100">
                          <div
                            className={`h-2 rounded-full transition-all ${
                              (agency.relationship_score ?? 0) >= 70
                                ? "bg-green-500"
                                : (agency.relationship_score ?? 0) >= 40
                                ? "bg-yellow-500"
                                : "bg-red-400"
                            }`}
                            style={{
                              width: `${Math.min(
                                100,
                                Math.max(0, agency.relationship_score ?? 0)
                              )}%`,
                            }}
                          />
                        </div>
                      </div>

                      {/* Mission */}
                      {agency.mission && (
                        <p className="text-xs text-muted-foreground">
                          {truncate(agency.mission, 120)}
                        </p>
                      )}

                      {/* Strategic Priorities */}
                      {agency.strategic_priorities &&
                        agency.strategic_priorities.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Strategic Priorities
                            </p>
                            <ul className="space-y-0.5">
                              {agency.strategic_priorities
                                .slice(0, 3)
                                .map((priority, i) => (
                                  <li
                                    key={i}
                                    className="text-xs text-foreground flex items-start gap-1"
                                  >
                                    <span className="mt-0.5 text-muted-foreground">
                                      &#8226;
                                    </span>
                                    <span>{priority}</span>
                                  </li>
                                ))}
                            </ul>
                          </div>
                        )}

                      {/* Technology Initiatives */}
                      {agency.technology_initiatives &&
                        agency.technology_initiatives.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              Tech Initiatives
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {agency.technology_initiatives
                                .slice(0, 5)
                                .map((initiative, i) => (
                                  <span
                                    key={i}
                                    className="inline-flex items-center rounded-full bg-blue-100 text-blue-700 px-2 py-0.5 text-xs"
                                  >
                                    {initiative}
                                  </span>
                                ))}
                            </div>
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
