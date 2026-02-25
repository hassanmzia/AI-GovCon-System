"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScoreBreakdown } from "@/components/opportunities/score-breakdown";
import { RecommendationBadge } from "@/components/opportunities/score-badge";
import { getOpportunity } from "@/services/opportunities";
import { Opportunity } from "@/types/opportunity";
import {
  ArrowLeft,
  Calendar,
  Building2,
  FileText,
  Paperclip,
  User,
  Mail,
  Phone,
  ExternalLink,
  Loader2,
  Plus,
} from "lucide-react";

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOpportunity() {
      if (!params.id) return;
      setLoading(true);
      setError(null);
      try {
        const data = await getOpportunity(params.id as string);
        setOpportunity(data);
      } catch (err) {
        setError("Failed to load opportunity details.");
        console.error("Error fetching opportunity:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchOpportunity();
  }, [params.id]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "--";
    return new Date(dateStr).toLocaleDateString("en-US", {
      weekday: "short",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatFileSize = (bytes: number | null) => {
    if (bytes === null || bytes === undefined) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading opportunity details...
        </span>
      </div>
    );
  }

  if (error || !opportunity) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <p className="text-red-600 mb-4">{error || "Opportunity not found."}</p>
        <Button variant="outline" onClick={() => router.push("/opportunities")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Opportunities
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => router.push("/opportunities")}
        className="mb-2"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Opportunities
      </Button>

      {/* Title and Badges */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">
          {opportunity.title}
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4" />
            {opportunity.agency}
            {opportunity.sub_agency && ` - ${opportunity.sub_agency}`}
          </span>
          {opportunity.notice_type && (
            <span className="inline-flex items-center rounded-md border bg-secondary px-2 py-0.5 text-xs font-medium">
              {opportunity.notice_type}
            </span>
          )}
          {opportunity.sol_number && (
            <span className="text-xs text-muted-foreground">
              Sol: {opportunity.sol_number}
            </span>
          )}
          {opportunity.score && (
            <RecommendationBadge
              recommendation={opportunity.score.recommendation}
              size="sm"
            />
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - 2/3 width */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Description
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {opportunity.description || "No description available."}
              </p>
              {opportunity.source_url && (
                <a
                  href={opportunity.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  View on SAM.gov
                </a>
              )}
            </CardContent>
          </Card>

          {/* Contacts */}
          {opportunity.contacts && opportunity.contacts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Contacts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  {opportunity.contacts.map((contact, index) => (
                    <div
                      key={index}
                      className="rounded-lg border p-4 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">
                          {contact.name || "Unknown"}
                        </span>
                        {contact.type && (
                          <span className="text-xs text-muted-foreground capitalize">
                            {contact.type}
                          </span>
                        )}
                      </div>
                      {contact.email && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Mail className="h-3.5 w-3.5" />
                          <a
                            href={`mailto:${contact.email}`}
                            className="hover:underline"
                          >
                            {contact.email}
                          </a>
                        </div>
                      )}
                      {contact.phone && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Phone className="h-3.5 w-3.5" />
                          {contact.phone}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Attachments */}
          {opportunity.attachments && opportunity.attachments.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Paperclip className="h-5 w-5" />
                  Attachments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {opportunity.attachments.map((attachment, index) => (
                    <a
                      key={index}
                      href={attachment.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">
                          {attachment.name}
                        </span>
                      </div>
                      {attachment.size !== null && (
                        <span className="text-xs text-muted-foreground">
                          {formatFileSize(attachment.size)}
                        </span>
                      )}
                    </a>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Key Dates */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Key Dates
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">
                    Posted Date
                  </span>
                  <p className="text-sm font-medium">
                    {formatDate(opportunity.posted_date)}
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">
                    Response Deadline
                  </span>
                  <p className="text-sm font-medium">
                    {formatDate(opportunity.response_deadline)}
                  </p>
                  {opportunity.days_until_deadline !== null && (
                    <p
                      className={`text-xs font-medium ${
                        opportunity.days_until_deadline < 0
                          ? "text-red-600"
                          : opportunity.days_until_deadline <= 7
                          ? "text-red-600"
                          : opportunity.days_until_deadline <= 30
                          ? "text-yellow-600"
                          : "text-green-600"
                      }`}
                    >
                      {opportunity.days_until_deadline < 0
                        ? "Expired"
                        : `${opportunity.days_until_deadline} days remaining`}
                    </p>
                  )}
                </div>
                <div className="space-y-1">
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">
                    Archive Date
                  </span>
                  <p className="text-sm font-medium text-muted-foreground">
                    --
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Additional Details */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Additional Details</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-3 sm:grid-cols-2 text-sm">
                <div>
                  <dt className="text-muted-foreground">NAICS Code</dt>
                  <dd className="font-medium">
                    {opportunity.naics_code || "--"}
                    {opportunity.naics_description &&
                      ` - ${opportunity.naics_description}`}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">PSC Code</dt>
                  <dd className="font-medium">
                    {opportunity.psc_code || "--"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Set-Aside</dt>
                  <dd className="font-medium">
                    {opportunity.set_aside || "Full & Open"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Estimated Value</dt>
                  <dd className="font-medium">
                    {opportunity.estimated_value
                      ? `$${opportunity.estimated_value.toLocaleString()}`
                      : "--"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">
                    Place of Performance
                  </dt>
                  <dd className="font-medium">
                    {opportunity.place_of_performance || "--"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Status</dt>
                  <dd className="font-medium">
                    {opportunity.status || "--"}
                  </dd>
                </div>
              </dl>
              {opportunity.keywords && opportunity.keywords.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <span className="text-sm text-muted-foreground">
                    Keywords
                  </span>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {opportunity.keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="inline-flex rounded-md bg-secondary px-2 py-0.5 text-xs font-medium"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - 1/3 width */}
        <div className="space-y-6">
          {/* Score Breakdown */}
          {opportunity.score ? (
            <ScoreBreakdown score={opportunity.score} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  No score data available for this opportunity. Scoring will be
                  performed during the next scan cycle.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Create Deal Button */}
          <Button
            className="w-full"
            size="lg"
            onClick={() =>
              router.push(`/deals/new?opportunity_id=${opportunity.id}`)
            }
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Deal from Opportunity
          </Button>
        </div>
      </div>
    </div>
  );
}
