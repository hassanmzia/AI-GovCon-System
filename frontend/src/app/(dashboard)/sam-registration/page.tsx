"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  CheckCircle,
  Circle,
  AlertTriangle,
  Shield,
  Clock,
  User,
  Building2,
  Hash,
  FileText,
  Landmark,
  Phone,
  ClipboardCheck,
  Send,
  Eye,
  ChevronRight,
  RefreshCw,
  Plus,
  Save,
  Loader2,
  Trash2,
} from "lucide-react";
import {
  SAMRegistration,
  SAMContact,
  getSAMRegistrations,
  getSAMRegistration,
  createSAMRegistration,
  updateSAMRegistration,
  updateSAMSteps,
  updateSAMValidation,
  checkSAMExpiration,
  createSAMContact,
  updateSAMContact,
  deleteSAMContact,
} from "@/services/sam-registration";

// ── Types ───────────────────────────────────────────────────────────────────

type RegistrationStatus =
  | "not_started"
  | "in_progress"
  | "submitted"
  | "active"
  | "expired";

// ── Constants ───────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  RegistrationStatus,
  { label: string; color: string; bgColor: string }
> = {
  not_started: {
    label: "Not Started",
    color: "text-gray-700",
    bgColor: "bg-gray-100",
  },
  in_progress: {
    label: "In Progress",
    color: "text-blue-700",
    bgColor: "bg-blue-100",
  },
  submitted: {
    label: "Submitted",
    color: "text-yellow-700",
    bgColor: "bg-yellow-100",
  },
  active: {
    label: "Active",
    color: "text-green-700",
    bgColor: "bg-green-100",
  },
  expired: {
    label: "Expired",
    color: "text-red-700",
    bgColor: "bg-red-100",
  },
};

const STEP_DEFINITIONS = [
  {
    title: "Get a DUNS/UEI Number",
    description:
      "Obtain your Unique Entity Identifier (UEI) from SAM.gov. This replaced DUNS numbers as of April 2022.",
  },
  {
    title: "Register at Login.gov",
    description:
      "Create a Login.gov account with multi-factor authentication to access SAM.gov.",
  },
  {
    title: "Complete Entity Registration",
    description:
      "Begin your entity registration in SAM.gov by selecting entity type and purpose of registration.",
  },
  {
    title: "Enter Entity Information",
    description:
      "Provide legal business name, physical address, mailing address, and start date as registered with the IRS.",
  },
  {
    title: "Enter Financial Information",
    description:
      "Enter your EIN/TIN, electronic funds transfer (EFT) banking details, and CAGE code information.",
  },
  {
    title: "Add NAICS Codes",
    description:
      "Select the North American Industry Classification System codes that describe your business capabilities.",
  },
  {
    title: "Add Points of Contact",
    description:
      "Designate your Electronic Business, Government Business, and Past Performance POCs.",
  },
  {
    title: "Complete Representations & Certifications",
    description:
      "Fill out required FAR and DFARS representations and certifications for your entity.",
  },
  {
    title: "Review and Submit",
    description:
      "Review all entered information for accuracy and submit your registration for processing.",
  },
  {
    title: "Monitor Registration Status",
    description:
      "Track your registration status. Processing typically takes 7-10 business days after submission.",
  },
];

const STEP_ICONS = [
  <Hash key="1" className="h-4 w-4" />,
  <User key="2" className="h-4 w-4" />,
  <FileText key="3" className="h-4 w-4" />,
  <Building2 key="4" className="h-4 w-4" />,
  <Landmark key="5" className="h-4 w-4" />,
  <ClipboardCheck key="6" className="h-4 w-4" />,
  <Phone key="7" className="h-4 w-4" />,
  <Shield key="8" className="h-4 w-4" />,
  <Send key="9" className="h-4 w-4" />,
  <Eye key="10" className="h-4 w-4" />,
];

const DEFAULT_VALIDATION_ITEMS: Record<string, { label: string }> = {
  name_irs: { label: "Name matches IRS records" },
  addr_irs: { label: "Address matches IRS records" },
  ein_verified: { label: "EIN verified" },
  bank_business: { label: "Bank info is business account" },
  entity_type: { label: "Correct entity type selected" },
  naics_codes: { label: "NAICS codes added" },
  reps_certs: { label: "Reps & Certs complete" },
  pocs_added: { label: "POCs added" },
  all_sections: { label: "All sections complete" },
};

const CONTACT_ROLES = [
  { value: "admin_poc", label: "Admin POC" },
  { value: "gov_business_poc", label: "Gov Business POC" },
  { value: "electronic_business_poc", label: "Electronic Business POC" },
  { value: "past_performance_poc", label: "Past Performance POC" },
];

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function SamRegistrationPage() {
  const [registration, setRegistration] = useState<SAMRegistration | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingContact, setEditingContact] = useState<number | null>(null);
  const [editingDetails, setEditingDetails] = useState(false);
  const [addingContact, setAddingContact] = useState(false);
  const [expirationWarning, setExpirationWarning] = useState<string | null>(
    null
  );

  // Form state for entity details editing
  const [detailsForm, setDetailsForm] = useState({
    legal_business_name: "",
    uei_number: "",
    cage_code: "",
    tracking_number: "",
    ein_number: "",
    physical_address: "",
    entity_type: "",
    registration_date: "",
    expiration_date: "",
    notes: "",
  });

  // New contact form
  const [newContact, setNewContact] = useState({
    role: "admin_poc",
    name: "",
    title: "",
    email: "",
    phone: "",
  });

  // ── Data loading ────────────────────────────────────────────────

  const loadRegistration = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const listResp = await getSAMRegistrations();
      if (listResp.results && listResp.results.length > 0) {
        const detail = await getSAMRegistration(listResp.results[0].id);
        setRegistration(detail);
        syncDetailsForm(detail);
        // Check expiration
        try {
          const expResult = await checkSAMExpiration(detail.id);
          if (expResult.warning) {
            setExpirationWarning(expResult.message);
          }
        } catch {
          // Non-critical
        }
      } else {
        setRegistration(null);
      }
    } catch (err) {
      setError(
        "Failed to load registration data. The server may be unavailable."
      );
      // Fall back to local-only mode
      setRegistration(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const syncDetailsForm = (reg: SAMRegistration) => {
    setDetailsForm({
      legal_business_name: reg.legal_business_name || "",
      uei_number: reg.uei_number || "",
      cage_code: reg.cage_code || "",
      tracking_number: reg.tracking_number || "",
      ein_number: reg.ein_number || "",
      physical_address: reg.physical_address || "",
      entity_type: reg.entity_type || "",
      registration_date: reg.registration_date || "",
      expiration_date: reg.expiration_date || "",
      notes: reg.notes || "",
    });
  };

  useEffect(() => {
    loadRegistration();
  }, [loadRegistration]);

  // ── Create new registration ────────────────────────────────────

  const handleCreateRegistration = async () => {
    try {
      setSaving(true);
      const newReg = await createSAMRegistration({
        legal_business_name: "My Organization",
        status: "not_started",
      });
      const detail = await getSAMRegistration(newReg.id);
      setRegistration(detail);
      syncDetailsForm(detail);
      setEditingDetails(true);
    } catch {
      setError("Failed to create registration. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  // ── Save entity details ────────────────────────────────────────

  const handleSaveDetails = async () => {
    if (!registration) return;
    try {
      setSaving(true);
      const updated = await updateSAMRegistration(registration.id, {
        ...detailsForm,
        registration_date: detailsForm.registration_date || null,
        expiration_date: detailsForm.expiration_date || null,
      });
      setRegistration(updated);
      setEditingDetails(false);
    } catch {
      setError("Failed to save details.");
    } finally {
      setSaving(false);
    }
  };

  // ── Status change ──────────────────────────────────────────────

  const handleStatusChange = async (newStatus: RegistrationStatus) => {
    if (!registration) return;
    try {
      setSaving(true);
      const updated = await updateSAMRegistration(registration.id, {
        status: newStatus,
      });
      setRegistration(updated);
    } catch {
      setError("Failed to update status.");
    } finally {
      setSaving(false);
    }
  };

  // ── Step toggle ────────────────────────────────────────────────

  const handleToggleStep = async (stepIndex: number) => {
    if (!registration) return;
    const newSteps = [...registration.steps_completed];
    newSteps[stepIndex] = !newSteps[stepIndex];
    // Optimistic update
    setRegistration({ ...registration, steps_completed: newSteps });
    try {
      const updated = await updateSAMSteps(registration.id, newSteps);
      setRegistration(updated);
    } catch {
      // Revert on error
      setRegistration(registration);
      setError("Failed to save step progress.");
    }
  };

  // ── Validation toggle ─────────────────────────────────────────

  const handleToggleValidation = async (itemId: string) => {
    if (!registration) return;
    const newItems = {
      ...registration.validation_items,
      [itemId]: !registration.validation_items[itemId],
    };
    // Optimistic update
    setRegistration({ ...registration, validation_items: newItems });
    try {
      const updated = await updateSAMValidation(registration.id, newItems);
      setRegistration(updated);
    } catch {
      setRegistration(registration);
      setError("Failed to save validation.");
    }
  };

  // ── Contact CRUD ───────────────────────────────────────────────

  const handleSaveContact = async (contact: SAMContact) => {
    try {
      setSaving(true);
      await updateSAMContact(contact.id, {
        name: contact.name,
        title: contact.title,
        email: contact.email,
        phone: contact.phone,
      });
      setEditingContact(null);
      await loadRegistration();
    } catch {
      setError("Failed to save contact.");
    } finally {
      setSaving(false);
    }
  };

  const handleAddContact = async () => {
    if (!registration) return;
    try {
      setSaving(true);
      await createSAMContact({
        registration: registration.id,
        ...newContact,
      });
      setAddingContact(false);
      setNewContact({
        role: "admin_poc",
        name: "",
        title: "",
        email: "",
        phone: "",
      });
      await loadRegistration();
    } catch {
      setError("Failed to add contact.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteContact = async (contactId: string) => {
    try {
      setSaving(true);
      await deleteSAMContact(contactId);
      await loadRegistration();
    } catch {
      setError("Failed to delete contact.");
    } finally {
      setSaving(false);
    }
  };

  // ── Computed values ────────────────────────────────────────────

  const stepsCompleted = registration?.steps_completed || Array(10).fill(false);
  const completedCount = stepsCompleted.filter(Boolean).length;
  const stepsProgress = Math.round((completedCount / 10) * 100);

  const validationItems = registration?.validation_items || {};
  const validationKeys = Object.keys(
    Object.keys(validationItems).length > 0
      ? validationItems
      : DEFAULT_VALIDATION_ITEMS
  );
  const checkedCount = Object.values(validationItems).filter(Boolean).length;
  const totalValidation = validationKeys.length || 9;
  const validationProgress = Math.round((checkedCount / totalValidation) * 100);

  const activeStepIndex = stepsCompleted.findIndex((s: boolean) => !s);
  const currentStepNumber = activeStepIndex >= 0 ? activeStepIndex + 1 : 10;

  const status = (registration?.status || "not_started") as RegistrationStatus;
  const daysLeft = registration?.days_until_expiration;
  const isExpiringSoon =
    daysLeft !== null && daysLeft !== undefined && daysLeft >= 0 && daysLeft <= 60;

  const contacts = registration?.contacts || [];

  // ── Loading state ──────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">
          Loading registration data...
        </span>
      </div>
    );
  }

  // ── No registration yet ────────────────────────────────────────

  if (!registration) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            SAM Registration
          </h1>
          <p className="text-muted-foreground">
            Track and manage your SAM.gov registration
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
            <AlertTriangle className="mr-2 inline h-4 w-4" />
            {error}
          </div>
        )}

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Building2 className="h-16 w-16 text-muted-foreground/30 mb-4" />
            <h2 className="text-lg font-semibold mb-2">
              No SAM Registration Found
            </h2>
            <p className="text-sm text-muted-foreground mb-6 text-center max-w-md">
              Start tracking your SAM.gov registration progress. You&apos;ll be
              able to enter your UEI, CAGE code, track all 10 registration
              steps, and manage your points of contact.
            </p>
            <Button onClick={handleCreateRegistration} disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Plus className="mr-2 h-4 w-4" />
              Start Tracking Registration
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Main view ──────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            SAM Registration
          </h1>
          <p className="text-muted-foreground">
            {registration.legal_business_name || "Track and manage your SAM.gov registration"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadRegistration}
            disabled={loading}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <a href="https://sam.gov" target="_blank" rel="noopener noreferrer">
            <Button size="sm">
              <Send className="mr-2 h-4 w-4" />
              Open SAM.gov
            </Button>
          </a>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 flex items-center justify-between">
          <span>
            <AlertTriangle className="mr-2 inline h-4 w-4" />
            {error}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setError(null)}
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Expiration warning */}
      {expirationWarning && (
        <div className="rounded-md border border-orange-200 bg-orange-50 p-3 text-sm text-orange-800">
          <AlertTriangle className="mr-2 inline h-4 w-4" />
          {expirationWarning}
        </div>
      )}

      {/* Registration Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Registration Status</CardTitle>
            {!editingDetails ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingDetails(true)}
              >
                Edit Details
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setEditingDetails(false);
                    syncDetailsForm(registration);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveDetails}
                  disabled={saving}
                >
                  {saving && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  <Save className="mr-2 h-4 w-4" />
                  Save
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">
                  Status:
                </span>
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${STATUS_CONFIG[status].bgColor} ${STATUS_CONFIG[status].color}`}
                >
                  {STATUS_CONFIG[status].label}
                </span>
              </div>
              {isExpiringSoon && (
                <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-3 py-1 text-sm font-medium text-orange-700">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Expiring in {daysLeft} days
                </span>
              )}
            </div>
            <div>
              <select
                value={status}
                onChange={(e) =>
                  handleStatusChange(e.target.value as RegistrationStatus)
                }
                disabled={saving}
                className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="not_started">Not Started</option>
                <option value="in_progress">In Progress</option>
                <option value="submitted">Submitted</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
              </select>
            </div>
          </div>

          {/* Entity Details - View/Edit */}
          {editingDetails ? (
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Legal Business Name
                </label>
                <Input
                  value={detailsForm.legal_business_name}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      legal_business_name: e.target.value,
                    })
                  }
                  placeholder="Your registered business name"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  UEI Number
                </label>
                <Input
                  value={detailsForm.uei_number}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      uei_number: e.target.value,
                    })
                  }
                  placeholder="12-character UEI"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  CAGE Code
                </label>
                <Input
                  value={detailsForm.cage_code}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      cage_code: e.target.value,
                    })
                  }
                  placeholder="5-character CAGE code"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Tracking Number
                </label>
                <Input
                  value={detailsForm.tracking_number}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      tracking_number: e.target.value,
                    })
                  }
                  placeholder="SAM tracking number"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  EIN / TIN
                </label>
                <Input
                  value={detailsForm.ein_number}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      ein_number: e.target.value,
                    })
                  }
                  placeholder="XX-XXXXXXX"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Entity Type
                </label>
                <Input
                  value={detailsForm.entity_type}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      entity_type: e.target.value,
                    })
                  }
                  placeholder="e.g., LLC, Corporation"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Registration Date
                </label>
                <Input
                  type="date"
                  value={detailsForm.registration_date}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      registration_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Expiration Date
                </label>
                <Input
                  type="date"
                  value={detailsForm.expiration_date}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      expiration_date: e.target.value,
                    })
                  }
                />
              </div>
              <div className="sm:col-span-2 lg:col-span-1">
                <label className="text-xs font-medium text-muted-foreground">
                  Physical Address
                </label>
                <Input
                  value={detailsForm.physical_address}
                  onChange={(e) =>
                    setDetailsForm({
                      ...detailsForm,
                      physical_address: e.target.value,
                    })
                  }
                  placeholder="Street, City, State ZIP"
                />
              </div>
              <div className="sm:col-span-2 lg:col-span-3">
                <label className="text-xs font-medium text-muted-foreground">
                  Notes
                </label>
                <textarea
                  value={detailsForm.notes}
                  onChange={(e) =>
                    setDetailsForm({ ...detailsForm, notes: e.target.value })
                  }
                  placeholder="Additional notes about your registration..."
                  rows={2}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                />
              </div>
            </div>
          ) : (
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  UEI Number
                </p>
                <p className="mt-1 text-sm font-semibold font-mono text-foreground">
                  {registration.uei_number || "--"}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  CAGE Code
                </p>
                <p className="mt-1 text-sm font-semibold font-mono text-foreground">
                  {registration.cage_code || "--"}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  Registration Date
                </p>
                <p className="mt-1 text-sm font-semibold text-foreground">
                  {formatDate(registration.registration_date)}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  Expiration Date
                </p>
                <p
                  className={`mt-1 text-sm font-semibold ${isExpiringSoon ? "text-orange-600" : "text-foreground"}`}
                >
                  {formatDate(registration.expiration_date)}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  Tracking Number
                </p>
                <p className="mt-1 text-sm font-semibold font-mono text-foreground">
                  {registration.tracking_number || "--"}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  EIN / TIN
                </p>
                <p className="mt-1 text-sm font-semibold font-mono text-foreground">
                  {registration.ein_number || "--"}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  Entity Type
                </p>
                <p className="mt-1 text-sm font-semibold text-foreground">
                  {registration.entity_type || "--"}
                </p>
              </div>
              <div className="rounded-lg border bg-muted/30 px-4 py-3">
                <p className="text-xs font-medium text-muted-foreground">
                  Physical Address
                </p>
                <p className="mt-1 text-sm font-semibold text-foreground">
                  {registration.physical_address || "--"}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Steps Completed
                </p>
                <p className="text-2xl font-bold">
                  {completedCount} / 10
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {stepsProgress}% of registration
                </p>
              </div>
              <ClipboardCheck className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Validation Score
                </p>
                <p className="text-2xl font-bold">
                  {checkedCount} / {totalValidation}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {validationProgress}% validated
                </p>
              </div>
              <Shield className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Current Step</p>
                <p className="text-2xl font-bold">Step {currentStepNumber}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {STEP_DEFINITIONS[currentStepNumber - 1]?.title ??
                    "All complete"}
                </p>
              </div>
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* 10-Step Registration Wizard (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Registration Steps</CardTitle>
                <span className="text-sm text-muted-foreground">
                  {completedCount} of 10 complete
                </span>
              </div>
              {/* Progress bar */}
              <div className="mt-2 h-2 w-full rounded-full bg-muted">
                <div
                  className="h-2 rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${stepsProgress}%` }}
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {STEP_DEFINITIONS.map((step, index) => {
                  const isCompleted = stepsCompleted[index];
                  const isActive = index === activeStepIndex;
                  return (
                    <div
                      key={index}
                      className={`group flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                        isActive
                          ? "border-primary bg-primary/5"
                          : isCompleted
                            ? "border-transparent bg-muted/30"
                            : "border-transparent hover:bg-muted/20"
                      }`}
                    >
                      <button
                        onClick={() => handleToggleStep(index)}
                        className="mt-0.5 shrink-0 transition-colors"
                        title={
                          isCompleted
                            ? "Mark as incomplete"
                            : "Mark as complete"
                        }
                      >
                        {isCompleted ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : isActive ? (
                          <div className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-primary">
                            <div className="h-2 w-2 rounded-full bg-primary" />
                          </div>
                        ) : (
                          <Circle className="h-5 w-5 text-muted-foreground/40" />
                        )}
                      </button>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`flex h-6 w-6 items-center justify-center rounded text-xs ${
                              isCompleted
                                ? "bg-green-100 text-green-700"
                                : isActive
                                  ? "bg-primary/10 text-primary"
                                  : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {STEP_ICONS[index]}
                          </span>
                          <h4
                            className={`text-sm font-medium ${
                              isCompleted
                                ? "text-muted-foreground line-through"
                                : isActive
                                  ? "text-foreground"
                                  : "text-muted-foreground"
                            }`}
                          >
                            Step {index + 1}: {step.title}
                          </h4>
                          {isActive && (
                            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                              Current
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                          {step.description}
                        </p>
                      </div>

                      {isActive && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="shrink-0 hidden sm:flex"
                          onClick={() => handleToggleStep(index)}
                        >
                          Complete
                          <ChevronRight className="ml-1 h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Points of Contact */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Points of Contact</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAddingContact(!addingContact)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Contact
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Add contact form */}
              {addingContact && (
                <div className="rounded-lg border border-dashed border-primary/50 bg-primary/5 p-4 mb-4 space-y-3">
                  <h4 className="text-sm font-semibold">New Contact</h4>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="text-xs text-muted-foreground">
                        Role
                      </label>
                      <select
                        value={newContact.role}
                        onChange={(e) =>
                          setNewContact({
                            ...newContact,
                            role: e.target.value,
                          })
                        }
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      >
                        {CONTACT_ROLES.map((r) => (
                          <option key={r.value} value={r.value}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">
                        Name
                      </label>
                      <Input
                        value={newContact.name}
                        onChange={(e) =>
                          setNewContact({
                            ...newContact,
                            name: e.target.value,
                          })
                        }
                        placeholder="Full name"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">
                        Title
                      </label>
                      <Input
                        value={newContact.title}
                        onChange={(e) =>
                          setNewContact({
                            ...newContact,
                            title: e.target.value,
                          })
                        }
                        placeholder="Job title"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">
                        Email
                      </label>
                      <Input
                        value={newContact.email}
                        onChange={(e) =>
                          setNewContact({
                            ...newContact,
                            email: e.target.value,
                          })
                        }
                        placeholder="email@company.com"
                        type="email"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">
                        Phone
                      </label>
                      <Input
                        value={newContact.phone}
                        onChange={(e) =>
                          setNewContact({
                            ...newContact,
                            phone: e.target.value,
                          })
                        }
                        placeholder="(555) 123-4567"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      onClick={handleAddContact}
                      disabled={
                        saving || !newContact.name || !newContact.email
                      }
                    >
                      {saving && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Save Contact
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAddingContact(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {contacts.length === 0 && !addingContact ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No contacts added yet. Add your POCs to track them here.
                </p>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {contacts.map((contact, index) => (
                    <div
                      key={contact.id}
                      className="rounded-lg border p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
                          {contact.role_display}
                        </span>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (editingContact === index) {
                                handleSaveContact(contact);
                              } else {
                                setEditingContact(index);
                              }
                            }}
                          >
                            {editingContact === index ? "Save" : "Edit"}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteContact(contact.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>

                      {editingContact === index ? (
                        <div className="space-y-2">
                          <div>
                            <label className="text-xs text-muted-foreground">
                              Name
                            </label>
                            <Input
                              value={contact.name}
                              onChange={(e) => {
                                const updated = [...contacts];
                                updated[index] = {
                                  ...contact,
                                  name: e.target.value,
                                };
                                setRegistration({
                                  ...registration,
                                  contacts: updated,
                                });
                              }}
                            />
                          </div>
                          <div>
                            <label className="text-xs text-muted-foreground">
                              Title
                            </label>
                            <Input
                              value={contact.title}
                              onChange={(e) => {
                                const updated = [...contacts];
                                updated[index] = {
                                  ...contact,
                                  title: e.target.value,
                                };
                                setRegistration({
                                  ...registration,
                                  contacts: updated,
                                });
                              }}
                            />
                          </div>
                          <div>
                            <label className="text-xs text-muted-foreground">
                              Email
                            </label>
                            <Input
                              value={contact.email}
                              onChange={(e) => {
                                const updated = [...contacts];
                                updated[index] = {
                                  ...contact,
                                  email: e.target.value,
                                };
                                setRegistration({
                                  ...registration,
                                  contacts: updated,
                                });
                              }}
                            />
                          </div>
                          <div>
                            <label className="text-xs text-muted-foreground">
                              Phone
                            </label>
                            <Input
                              value={contact.phone}
                              onChange={(e) => {
                                const updated = [...contacts];
                                updated[index] = {
                                  ...contact,
                                  phone: e.target.value,
                                };
                                setRegistration({
                                  ...registration,
                                  contacts: updated,
                                });
                              }}
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-1.5">
                          <p className="text-sm font-semibold text-foreground">
                            {contact.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {contact.title}
                          </p>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <span>{contact.email}</span>
                          </div>
                          {contact.phone && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Phone className="h-3 w-3" />
                              <span>{contact.phone}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Validation Checklist (1/3 width) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Validation Checklist</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Ensure all items are verified before submission
              </p>
            </CardHeader>
            <CardContent>
              {/* Score display */}
              <div className="mb-4 flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  Completion
                </span>
                <span
                  className={`text-sm font-bold ${
                    validationProgress === 100
                      ? "text-green-600"
                      : validationProgress >= 50
                        ? "text-yellow-600"
                        : "text-red-600"
                  }`}
                >
                  {validationProgress}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="mb-5 h-2.5 w-full rounded-full bg-muted">
                <div
                  className={`h-2.5 rounded-full transition-all duration-300 ${
                    validationProgress === 100
                      ? "bg-green-500"
                      : validationProgress >= 50
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${validationProgress}%` }}
                />
              </div>

              {/* Checklist items */}
              <div className="space-y-2">
                {Object.entries(DEFAULT_VALIDATION_ITEMS).map(
                  ([id, { label }]) => {
                    const isChecked = validationItems[id] || false;
                    return (
                      <label
                        key={id}
                        className="flex items-center gap-3 rounded-md p-2 cursor-pointer transition-colors hover:bg-muted/50"
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleValidation(id)}
                          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                        />
                        <span
                          className={`text-sm ${
                            isChecked
                              ? "text-muted-foreground line-through"
                              : "text-foreground"
                          }`}
                        >
                          {label}
                        </span>
                        {isChecked && (
                          <CheckCircle className="ml-auto h-3.5 w-3.5 text-green-500" />
                        )}
                      </label>
                    );
                  }
                )}
              </div>

              {/* Status message */}
              <div className="mt-4 rounded-md border p-3">
                {validationProgress === 100 ? (
                  <div className="flex items-center gap-2 text-sm text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <span className="font-medium">
                      All validations passed. Ready to submit.
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-yellow-700">
                    <AlertTriangle className="h-4 w-4" />
                    <span>
                      {totalValidation - checkedCount} item
                      {totalValidation - checkedCount !== 1 ? "s" : ""}{" "}
                      remaining
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Quick Tips */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    SAM registration must be renewed annually before expiration
                    to avoid disruption.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Your entity name and address must exactly match IRS records
                    (Letter CP575 or 147C).
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Processing takes 7-10 business days. Government-wide CAGE
                    code validation may add 2-3 more days.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Bank account must be a business account matching your entity
                    name -- not a personal account.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Contact the Federal Service Desk at 866-606-8220 for help
                    with registration issues.
                  </span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
