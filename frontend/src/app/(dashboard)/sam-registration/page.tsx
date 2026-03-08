"use client";

import { useState } from "react";
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
} from "lucide-react";

// ── Types ───────────────────────────────────────────────────────────────────

type RegistrationStatus =
  | "not_started"
  | "in_progress"
  | "submitted"
  | "active"
  | "expired";

interface RegistrationStep {
  id: number;
  title: string;
  description: string;
  completed: boolean;
  icon: React.ReactNode;
}

interface ValidationItem {
  id: string;
  label: string;
  checked: boolean;
}

interface PointOfContact {
  role: string;
  name: string;
  title: string;
  email: string;
  phone: string;
}

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

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const target = new Date(dateStr);
  const now = new Date();
  const diffMs = target.getTime() - now.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function SamRegistrationPage() {
  // Registration status state
  const [status, setStatus] = useState<RegistrationStatus>("in_progress");
  const [registrationDate] = useState<string>("2025-03-15");
  const [expirationDate] = useState<string>("2026-03-15");
  const [trackingNumber] = useState<string>("SAM-2025-0315-78421");

  // 10-step wizard state
  const [steps, setSteps] = useState<RegistrationStep[]>([
    {
      id: 1,
      title: "Get a DUNS/UEI Number",
      description:
        "Obtain your Unique Entity Identifier (UEI) from SAM.gov. This replaced DUNS numbers as of April 2022.",
      completed: true,
      icon: STEP_ICONS[0],
    },
    {
      id: 2,
      title: "Register at Login.gov",
      description:
        "Create a Login.gov account with multi-factor authentication to access SAM.gov.",
      completed: true,
      icon: STEP_ICONS[1],
    },
    {
      id: 3,
      title: "Complete Entity Registration",
      description:
        "Begin your entity registration in SAM.gov by selecting entity type and purpose of registration.",
      completed: true,
      icon: STEP_ICONS[2],
    },
    {
      id: 4,
      title: "Enter Entity Information",
      description:
        "Provide legal business name, physical address, mailing address, and start date as registered with the IRS.",
      completed: true,
      icon: STEP_ICONS[3],
    },
    {
      id: 5,
      title: "Enter Financial Information",
      description:
        "Enter your EIN/TIN, electronic funds transfer (EFT) banking details, and CAGE code information.",
      completed: true,
      icon: STEP_ICONS[4],
    },
    {
      id: 6,
      title: "Add NAICS Codes",
      description:
        "Select the North American Industry Classification System codes that describe your business capabilities.",
      completed: false,
      icon: STEP_ICONS[5],
    },
    {
      id: 7,
      title: "Add Points of Contact",
      description:
        "Designate your Electronic Business, Government Business, and Past Performance POCs.",
      completed: false,
      icon: STEP_ICONS[6],
    },
    {
      id: 8,
      title: "Complete Representations & Certifications",
      description:
        "Fill out required FAR and DFARS representations and certifications for your entity.",
      completed: false,
      icon: STEP_ICONS[7],
    },
    {
      id: 9,
      title: "Review and Submit",
      description:
        "Review all entered information for accuracy and submit your registration for processing.",
      completed: false,
      icon: STEP_ICONS[8],
    },
    {
      id: 10,
      title: "Monitor Registration Status",
      description:
        "Track your registration status. Processing typically takes 7-10 business days after submission.",
      completed: false,
      icon: STEP_ICONS[9],
    },
  ]);

  // Validation checklist state
  const [validationItems, setValidationItems] = useState<ValidationItem[]>([
    { id: "name_irs", label: "Name matches IRS records", checked: true },
    { id: "addr_irs", label: "Address matches IRS records", checked: true },
    { id: "ein_verified", label: "EIN verified", checked: true },
    {
      id: "bank_business",
      label: "Bank info is business account",
      checked: true,
    },
    {
      id: "entity_type",
      label: "Correct entity type selected",
      checked: false,
    },
    { id: "naics_codes", label: "NAICS codes added", checked: false },
    { id: "reps_certs", label: "Reps & Certs complete", checked: false },
    { id: "pocs_added", label: "POCs added", checked: false },
    { id: "all_sections", label: "All sections complete", checked: false },
  ]);

  // Points of Contact state
  const [contacts, setContacts] = useState<PointOfContact[]>([
    {
      role: "Admin POC",
      name: "Jane Smith",
      title: "Director of Operations",
      email: "jane.smith@company.com",
      phone: "(555) 123-4567",
    },
    {
      role: "Gov Business POC",
      name: "John Davis",
      title: "BD Manager",
      email: "john.davis@company.com",
      phone: "(555) 987-6543",
    },
  ]);

  const [editingContact, setEditingContact] = useState<number | null>(null);

  // Active step (first incomplete or last if all done)
  const activeStepIndex = steps.findIndex((s) => !s.completed);
  const currentStepNumber =
    activeStepIndex >= 0 ? activeStepIndex + 1 : steps.length;

  // Computed values
  const completedSteps = steps.filter((s) => s.completed).length;
  const stepsProgress = Math.round((completedSteps / steps.length) * 100);

  const checkedCount = validationItems.filter((v) => v.checked).length;
  const validationProgress = Math.round(
    (checkedCount / validationItems.length) * 100
  );

  const expirationDays = daysUntil(expirationDate);
  const isExpiringSoon =
    expirationDays !== null && expirationDays >= 0 && expirationDays <= 30;

  // Handlers
  const toggleStep = (stepId: number) => {
    setSteps((prev) =>
      prev.map((s) =>
        s.id === stepId ? { ...s, completed: !s.completed } : s
      )
    );
  };

  const toggleValidation = (itemId: string) => {
    setValidationItems((prev) =>
      prev.map((v) =>
        v.id === itemId ? { ...v, checked: !v.checked } : v
      )
    );
  };

  const updateContact = (
    index: number,
    field: keyof PointOfContact,
    value: string
  ) => {
    setContacts((prev) =>
      prev.map((c, i) => (i === index ? { ...c, [field]: value } : c))
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            SAM Registration
          </h1>
          <p className="text-muted-foreground">
            Track and manage your SAM.gov registration per the 10-step process
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Sync Status
          </Button>
          <a href="https://sam.gov" target="_blank" rel="noopener noreferrer">
            <Button size="sm">
              <Send className="mr-2 h-4 w-4" />
              Open SAM.gov
            </Button>
          </a>
        </div>
      </div>

      {/* Registration Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registration Status</CardTitle>
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
                  Expiring Soon ({expirationDays} days)
                </span>
              )}
            </div>
            <div>
              <select
                value={status}
                onChange={(e) =>
                  setStatus(e.target.value as RegistrationStatus)
                }
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

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg border bg-muted/30 px-4 py-3">
              <p className="text-xs font-medium text-muted-foreground">
                Registration Date
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {formatDate(registrationDate)}
              </p>
            </div>
            <div className="rounded-lg border bg-muted/30 px-4 py-3">
              <p className="text-xs font-medium text-muted-foreground">
                Expiration Date
              </p>
              <p
                className={`mt-1 text-sm font-semibold ${isExpiringSoon ? "text-orange-600" : "text-foreground"}`}
              >
                {formatDate(expirationDate)}
              </p>
            </div>
            <div className="rounded-lg border bg-muted/30 px-4 py-3">
              <p className="text-xs font-medium text-muted-foreground">
                Tracking Number
              </p>
              <p className="mt-1 text-sm font-semibold font-mono text-foreground">
                {trackingNumber}
              </p>
            </div>
          </div>
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
                  {completedSteps} / {steps.length}
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
                  {checkedCount} / {validationItems.length}
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
                <p className="text-2xl font-bold">
                  Step {currentStepNumber}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {steps[currentStepNumber - 1]?.title ?? "All complete"}
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
                <CardTitle className="text-lg">
                  Registration Steps
                </CardTitle>
                <span className="text-sm text-muted-foreground">
                  {completedSteps} of {steps.length} complete
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
                {steps.map((step, index) => {
                  const isActive = index === activeStepIndex;
                  return (
                    <div
                      key={step.id}
                      className={`group flex items-start gap-3 rounded-lg border p-3 transition-colors ${
                        isActive
                          ? "border-primary bg-primary/5"
                          : step.completed
                            ? "border-transparent bg-muted/30"
                            : "border-transparent hover:bg-muted/20"
                      }`}
                    >
                      {/* Step indicator */}
                      <button
                        onClick={() => toggleStep(step.id)}
                        className="mt-0.5 shrink-0 transition-colors"
                        title={
                          step.completed
                            ? "Mark as incomplete"
                            : "Mark as complete"
                        }
                      >
                        {step.completed ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : isActive ? (
                          <div className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-primary">
                            <div className="h-2 w-2 rounded-full bg-primary" />
                          </div>
                        ) : (
                          <Circle className="h-5 w-5 text-muted-foreground/40" />
                        )}
                      </button>

                      {/* Connecting line (visual only via border) */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`flex h-6 w-6 items-center justify-center rounded text-xs ${
                              step.completed
                                ? "bg-green-100 text-green-700"
                                : isActive
                                  ? "bg-primary/10 text-primary"
                                  : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {step.icon}
                          </span>
                          <h4
                            className={`text-sm font-medium ${
                              step.completed
                                ? "text-muted-foreground line-through"
                                : isActive
                                  ? "text-foreground"
                                  : "text-muted-foreground"
                            }`}
                          >
                            Step {step.id}: {step.title}
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

                      {/* Action */}
                      {isActive && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="shrink-0 hidden sm:flex"
                          onClick={() => toggleStep(step.id)}
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
              <CardTitle className="text-lg">Points of Contact</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {contacts.map((contact, index) => (
                  <div
                    key={contact.role}
                    className="rounded-lg border p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
                        {contact.role}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setEditingContact(
                            editingContact === index ? null : index
                          )
                        }
                      >
                        {editingContact === index ? "Done" : "Edit"}
                      </Button>
                    </div>

                    {editingContact === index ? (
                      <div className="space-y-2">
                        <div>
                          <label className="text-xs text-muted-foreground">
                            Name
                          </label>
                          <Input
                            value={contact.name}
                            onChange={(e) =>
                              updateContact(index, "name", e.target.value)
                            }
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">
                            Title
                          </label>
                          <Input
                            value={contact.title}
                            onChange={(e) =>
                              updateContact(index, "title", e.target.value)
                            }
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">
                            Email
                          </label>
                          <Input
                            value={contact.email}
                            onChange={(e) =>
                              updateContact(index, "email", e.target.value)
                            }
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">
                            Phone
                          </label>
                          <Input
                            value={contact.phone}
                            onChange={(e) =>
                              updateContact(index, "phone", e.target.value)
                            }
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
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Phone className="h-3 w-3" />
                          <span>{contact.phone}</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
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
                {validationItems.map((item) => (
                  <label
                    key={item.id}
                    className="flex items-center gap-3 rounded-md p-2 cursor-pointer transition-colors hover:bg-muted/50"
                  >
                    <input
                      type="checkbox"
                      checked={item.checked}
                      onChange={() => toggleValidation(item.id)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <span
                      className={`text-sm ${
                        item.checked
                          ? "text-muted-foreground line-through"
                          : "text-foreground"
                      }`}
                    >
                      {item.label}
                    </span>
                    {item.checked && (
                      <CheckCircle className="ml-auto h-3.5 w-3.5 text-green-500" />
                    )}
                  </label>
                ))}
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
                      {validationItems.length - checkedCount} item
                      {validationItems.length - checkedCount !== 1
                        ? "s"
                        : ""}{" "}
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
                    SAM registration must be renewed annually before
                    expiration to avoid disruption.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Your entity name and address must exactly match IRS
                    records (Letter CP575 or 147C).
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Processing takes 7-10 business days. Government-wide
                    CAGE code validation may add 2-3 more days.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Bank account must be a business account matching your
                    entity name -- not a personal account.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                  <span>
                    Contact the Federal Service Desk at 866-606-8220 for
                    help with registration issues.
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
