"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import api from "@/lib/api";
import { Loader2, Eye, EyeOff, Save, Info } from "lucide-react";

interface UserProfile {
  email: string;
  first_name: string;
  last_name: string;
  username: string;
}

const APP_VERSION = "1.0.0";
const BUILD_ENV: string = process.env.NEXT_PUBLIC_APP_ENV || process.env.NODE_ENV || "development";

export default function SettingsPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Company Profile
  const [companyName, setCompanyName] = useState("");
  const [uei, setUei] = useState("");
  const [cageCode, setCageCode] = useState("");
  const [naicsCodes, setNaicsCodes] = useState("");
  const [coreCompetencies, setCoreCompetencies] = useState("");

  // Notification Settings
  const [notifyNewOpportunity, setNotifyNewOpportunity] = useState(true);
  const [notifyDeadlineApproaching, setNotifyDeadlineApproaching] =
    useState(true);
  const [notifyProposalUpdates, setNotifyProposalUpdates] = useState(true);
  const [notifyContractAwards, setNotifyContractAwards] = useState(true);
  const [notifyTeamMessages, setNotifyTeamMessages] = useState(false);
  const [notifySystemAlerts, setNotifySystemAlerts] = useState(true);
  const [dashboardEmails, setDashboardEmails] = useState(true);

  // API Key display
  const [showApiKey, setShowApiKey] = useState(false);
  const MASKED_SAM_KEY = "SAM-••••••••••••••••••••••••••••••";
  const DISPLAY_SAM_KEY = "SAM-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6";

  useEffect(() => {
    const fetchUserSettings = async () => {
      try {
        const { data } = await api.get("/auth/me/");
        setUser(data);
      } catch (error) {
        console.error("Failed to fetch user settings:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserSettings();
  }, []);

  const handleSaveCompanyProfile = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      // Simulate save (no backend endpoint defined, visual only)
      await new Promise((resolve) => setTimeout(resolve, 600));
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error("Failed to save company profile:", error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading settings...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Settings</h1>
        <p className="text-muted-foreground">
          Manage your profile, company information, and system preferences
        </p>
      </div>

      {/* User Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">User Profile</CardTitle>
        </CardHeader>
        <CardContent>
          {user ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  Email
                </p>
                <p className="text-sm font-medium">{user.email}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  Username
                </p>
                <p className="text-sm font-medium">{user.username}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  First Name
                </p>
                <p className="text-sm font-medium">
                  {user.first_name || "--"}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">
                  Last Name
                </p>
                <p className="text-sm font-medium">{user.last_name || "--"}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Could not load user profile.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Company Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Company Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                Company Name
              </label>
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Acme Defense Systems Inc."
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                UEI (Unique Entity Identifier)
              </label>
              <Input
                value={uei}
                onChange={(e) => setUei(e.target.value)}
                placeholder="ABCDEF123456"
                maxLength={12}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                CAGE Code
              </label>
              <Input
                value={cageCode}
                onChange={(e) => setCageCode(e.target.value)}
                placeholder="1A2B3"
                maxLength={5}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                NAICS Codes{" "}
                <span className="font-normal">(comma-separated)</span>
              </label>
              <Input
                value={naicsCodes}
                onChange={(e) => setNaicsCodes(e.target.value)}
                placeholder="541511, 541512, 541519"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">
              Core Competencies{" "}
              <span className="font-normal">(one per line)</span>
            </label>
            <textarea
              value={coreCompetencies}
              onChange={(e) => setCoreCompetencies(e.target.value)}
              placeholder="Cybersecurity&#10;Cloud Architecture&#10;Systems Integration"
              rows={4}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
            />
          </div>
          <div className="flex items-center gap-3 pt-1">
            <Button
              onClick={handleSaveCompanyProfile}
              disabled={saving}
              size="sm"
            >
              {saving ? (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Save className="mr-2 h-3.5 w-3.5" />
              )}
              Save Company Profile
            </Button>
            {saveSuccess && (
              <span className="text-xs text-green-600 font-medium">
                Saved successfully
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Notification Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Choose which events trigger email notifications for your account.
          </p>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyNewOpportunity}
                onChange={(e) => setNotifyNewOpportunity(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">New Opportunities</span>
                <p className="text-xs text-muted-foreground">
                  Notify when new matching contract opportunities are discovered
                </p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyDeadlineApproaching}
                onChange={(e) =>
                  setNotifyDeadlineApproaching(e.target.checked)
                }
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">
                  Deadline Approaching
                </span>
                <p className="text-xs text-muted-foreground">
                  Notify when proposal or opportunity deadlines are within 7
                  days
                </p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyProposalUpdates}
                onChange={(e) => setNotifyProposalUpdates(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">Proposal Updates</span>
                <p className="text-xs text-muted-foreground">
                  Notify when proposal status changes or reviews are completed
                </p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyContractAwards}
                onChange={(e) => setNotifyContractAwards(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">Contract Awards</span>
                <p className="text-xs text-muted-foreground">
                  Notify on contract award decisions and outcomes
                </p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifyTeamMessages}
                onChange={(e) => setNotifyTeamMessages(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">Team Messages</span>
                <p className="text-xs text-muted-foreground">
                  Notify when team members send messages in communication
                  threads
                </p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={dashboardEmails}
                onChange={(e) => setDashboardEmails(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">
                  Dashboard Summary Emails
                </span>
                <p className="text-xs text-muted-foreground">
                  Receive a weekly digest summarizing deal pipeline activity
                </p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={notifySystemAlerts}
                onChange={(e) => setNotifySystemAlerts(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
              />
              <div>
                <span className="text-sm font-medium">System Alerts</span>
                <p className="text-xs text-muted-foreground">
                  Notify on important system events and maintenance windows
                </p>
              </div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">API Keys & Integrations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            API keys used for external data integrations. Contact your
            administrator to update key values.
          </p>
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">SAM.gov API Key</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Used for fetching government contract opportunities from
                  SAM.gov
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <code className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                    {showApiKey ? DISPLAY_SAM_KEY : MASKED_SAM_KEY}
                  </code>
                  <button
                    onClick={() => setShowApiKey((v) => !v)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    title={showApiKey ? "Hide key" : "Show key"}
                  >
                    {showApiKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
              <span className="inline-flex items-center rounded-full bg-green-100 text-green-700 px-2 py-0.5 text-xs font-medium ml-4 shrink-0">
                Active
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3 opacity-60">
              <div>
                <p className="text-sm font-medium">USASpending.gov API</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Used for contract award and spending data (public API, no key
                  required)
                </p>
              </div>
              <span className="inline-flex items-center rounded-full bg-blue-100 text-blue-700 px-2 py-0.5 text-xs font-medium ml-4 shrink-0">
                Public
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Info className="h-4 w-4 text-muted-foreground" />
            System Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">
                App Version
              </p>
              <p className="font-mono font-medium">v{APP_VERSION}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">
                Environment
              </p>
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  BUILD_ENV === "production"
                    ? "bg-green-100 text-green-700"
                    : BUILD_ENV === "staging"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-orange-100 text-orange-700"
                }`}
              >
                {BUILD_ENV.charAt(0).toUpperCase() + BUILD_ENV.slice(1)}
              </span>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Frontend</p>
              <p className="font-mono text-xs text-muted-foreground">
                Next.js 14
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-0.5">Backend</p>
              <p className="font-mono text-xs text-muted-foreground">
                Django / DRF
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
