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
  Users,
  Building,
  Phone,
  Mail,
  Calendar,
  Star,
  MessageSquare,
  UserCheck,
  ChevronDown,
  ChevronRight,
  Plus,
} from "lucide-react";

interface AgencyContact {
  id: string;
  deal: string;
  name: string;
  title: string;
  email: string;
  phone: string;
  role: string;
  influence_level: "low" | "medium" | "high" | "critical";
  relationship_strength: number; // 1-5
  notes: string;
  last_contact: string | null;
  created_at: string;
}

interface AgencyInteraction {
  id: string;
  contact: string;
  contact_name?: string;
  interaction_type: string;
  date: string;
  summary: string;
  outcome: string;
  next_steps: string;
  created_at: string;
}

interface Stakeholder {
  id: string;
  deal: string;
  name: string;
  organization: string;
  role: string;
  stance: "champion" | "supporter" | "neutral" | "skeptic" | "blocker";
  influence: "low" | "medium" | "high";
  notes: string;
  created_at: string;
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const INFLUENCE_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

const STANCE_COLORS: Record<string, string> = {
  champion: "bg-green-100 text-green-700",
  supporter: "bg-blue-100 text-blue-700",
  neutral: "bg-gray-100 text-gray-600",
  skeptic: "bg-yellow-100 text-yellow-700",
  blocker: "bg-red-100 text-red-700",
};

const INTERACTION_TYPE_LABELS: Record<string, string> = {
  meeting: "Meeting",
  call: "Phone Call",
  email: "Email",
  event: "Event",
  site_visit: "Site Visit",
  briefing: "Briefing",
};

function RelationshipStrengthBars({ strength }: { strength: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <div
          key={n}
          className={`h-3 w-4 rounded-sm ${n <= strength ? "bg-blue-500" : "bg-gray-200"}`}
        />
      ))}
    </div>
  );
}

function ContactCard({ contact, interactions }: { contact: AgencyContact; interactions: AgencyInteraction[] }) {
  const [expanded, setExpanded] = useState(false);
  const contactInteractions = interactions.filter((i) => i.contact === contact.id);

  return (
    <Card className="overflow-hidden">
      <div
        className="flex items-start gap-4 p-4 cursor-pointer hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-sm flex-shrink-0">
          {contact.name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm">{contact.name}</span>
            <span className={`px-2 py-0.5 text-xs rounded-full ${INFLUENCE_COLORS[contact.influence_level]}`}>
              {contact.influence_level}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">{contact.title}</p>
          <div className="flex items-center gap-3 mt-1">
            <RelationshipStrengthBars strength={contact.relationship_strength} />
            <span className="text-xs text-muted-foreground">
              Last contact: {formatDate(contact.last_contact)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {contact.email && (
            <a
              href={`mailto:${contact.email}`}
              className="text-muted-foreground hover:text-blue-600"
              onClick={(e) => e.stopPropagation()}
            >
              <Mail className="h-4 w-4" />
            </a>
          )}
          {contact.phone && (
            <a
              href={`tel:${contact.phone}`}
              className="text-muted-foreground hover:text-blue-600"
              onClick={(e) => e.stopPropagation()}
            >
              <Phone className="h-4 w-4" />
            </a>
          )}
          <button className="text-muted-foreground">
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t bg-gray-50 p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Role</p>
              <p>{contact.role || "--"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Phone</p>
              <p>{contact.phone || "--"}</p>
            </div>
          </div>
          {contact.notes && (
            <div>
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Notes</p>
              <p className="text-sm">{contact.notes}</p>
            </div>
          )}

          {contactInteractions.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">
                Recent Interactions
              </p>
              <div className="space-y-2">
                {contactInteractions.slice(0, 3).map((i) => (
                  <div key={i.id} className="bg-white rounded border p-2 text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-muted-foreground">
                        {INTERACTION_TYPE_LABELS[i.interaction_type] || i.interaction_type}
                      </span>
                      <span className="text-xs text-muted-foreground">{formatDate(i.date)}</span>
                    </div>
                    <p className="text-sm">{i.summary}</p>
                    {i.next_steps && (
                      <p className="text-xs text-blue-600 mt-1">Next: {i.next_steps}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

// ── Stakeholder Map ──────────────────────────────────────────────────────────
function StakeholderMap({ stakeholders }: { stakeholders: Stakeholder[] }) {
  if (stakeholders.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
        No stakeholders mapped
      </div>
    );
  }

  const byStance: Record<string, Stakeholder[]> = {};
  stakeholders.forEach((s) => {
    if (!byStance[s.stance]) byStance[s.stance] = [];
    byStance[s.stance].push(s);
  });

  const stanceOrder = ["champion", "supporter", "neutral", "skeptic", "blocker"];

  return (
    <div className="space-y-4">
      {stanceOrder.map((stance) => {
        const group = byStance[stance];
        if (!group || group.length === 0) return null;
        return (
          <div key={stance}>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 capitalize">
              {stance}s ({group.length})
            </p>
            <div className="flex flex-wrap gap-2">
              {group.map((s) => (
                <div
                  key={s.id}
                  className={`px-3 py-2 rounded-lg border text-sm ${STANCE_COLORS[s.stance]}`}
                  title={`${s.role} at ${s.organization}\nInfluence: ${s.influence}`}
                >
                  <div className="font-medium">{s.name}</div>
                  <div className="text-xs opacity-75">{s.organization}</div>
                  <div className="text-xs mt-0.5 flex items-center gap-1">
                    <span className={`w-2 h-2 rounded-full inline-block ${
                      s.influence === "high" ? "bg-orange-400" : s.influence === "medium" ? "bg-blue-400" : "bg-gray-400"
                    }`} />
                    {s.influence} influence
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function DealRelationshipsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [deal, setDeal] = useState<Deal | null>(null);
  const [contacts, setContacts] = useState<AgencyContact[]>([]);
  const [interactions, setInteractions] = useState<AgencyInteraction[]>([]);
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"contacts" | "stakeholders">("contacts");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await getDeal(id);
      setDeal(d);

      const [cRes, iRes, sRes] = await Promise.all([
        api.get("/deals/agency-contacts/", { params: { deal: id } }),
        api.get("/deals/agency-interactions/", { params: { deal: id } }),
        api.get("/deals/stakeholders/", { params: { deal: id } }),
      ]);

      setContacts(cRes.data.results || cRes.data || []);
      setInteractions(iRes.data.results || iRes.data || []);
      setStakeholders(sRes.data.results || sRes.data || []);
    } catch {
      setError("Failed to load relationship data.");
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

  const champCount = stakeholders.filter((s) => s.stance === "champion").length;
  const blockerCount = stakeholders.filter((s) => s.stance === "blocker" || s.stance === "skeptic").length;
  const criticalContacts = contacts.filter((c) => c.influence_level === "critical" || c.influence_level === "high").length;

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
          <h1 className="text-2xl font-bold">Relationship Map</h1>
          {deal && <p className="text-muted-foreground mt-0.5">{deal.title}</p>}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Building className="h-4 w-4" />
              <span className="text-xs">Agency Contacts</span>
            </div>
            <div className="text-2xl font-bold">{contacts.length}</div>
            <p className="text-xs text-muted-foreground">{criticalContacts} high-influence</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <MessageSquare className="h-4 w-4" />
              <span className="text-xs">Interactions</span>
            </div>
            <div className="text-2xl font-bold">{interactions.length}</div>
            <p className="text-xs text-muted-foreground">total logged</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Star className="h-4 w-4 text-green-500" />
              <span className="text-xs">Champions</span>
            </div>
            <div className="text-2xl font-bold text-green-600">{champCount}</div>
            <p className="text-xs text-muted-foreground">stakeholders</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <UserCheck className="h-4 w-4 text-red-500" />
              <span className="text-xs">Risks</span>
            </div>
            <div className="text-2xl font-bold text-red-600">{blockerCount}</div>
            <p className="text-xs text-muted-foreground">skeptics/blockers</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b flex gap-6">
        <button
          onClick={() => setActiveTab("contacts")}
          className={`pb-2 text-sm font-medium border-b-2 -mb-px flex items-center gap-2 ${
            activeTab === "contacts"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Building className="h-4 w-4" /> Agency Contacts ({contacts.length})
        </button>
        <button
          onClick={() => setActiveTab("stakeholders")}
          className={`pb-2 text-sm font-medium border-b-2 -mb-px flex items-center gap-2 ${
            activeTab === "stakeholders"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Users className="h-4 w-4" /> Stakeholder Map ({stakeholders.length})
        </button>
      </div>

      {/* Content */}
      {activeTab === "contacts" ? (
        contacts.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16 gap-4">
              <Building className="h-12 w-12 text-muted-foreground" />
              <div className="text-center">
                <h3 className="font-semibold text-lg">No Agency Contacts</h3>
                <p className="text-muted-foreground text-sm mt-1">
                  Agency contacts will be discovered by the Scout Agent or added manually.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {contacts
              .sort((a, b) => {
                const order = { critical: 0, high: 1, medium: 2, low: 3 };
                return (order[a.influence_level] || 3) - (order[b.influence_level] || 3);
              })
              .map((contact) => (
                <ContactCard key={contact.id} contact={contact} interactions={interactions} />
              ))}
          </div>
        )
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4" /> Stakeholder Map
            </CardTitle>
          </CardHeader>
          <CardContent>
            <StakeholderMap stakeholders={stakeholders} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
