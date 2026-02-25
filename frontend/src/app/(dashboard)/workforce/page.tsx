"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  getEmployees,
  getAssignments,
  getHiringRequisitions,
  getDemandForecast,
} from "@/services/workforce";
import { Employee, Assignment, HiringRequisition, DemandForecast } from "@/types/workforce";
import {
  Loader2,
  Search,
  Users,
  UserCheck,
  ShieldAlert,
  Briefcase,
  AlertTriangle,
  TrendingUp,
} from "lucide-react";

type ActiveTab = "employees" | "assignments" | "hiring" | "forecast";

const CLEARANCE_COLORS: Record<string, string> = {
  none: "bg-gray-100 text-gray-600",
  confidential: "bg-blue-100 text-blue-700",
  secret: "bg-yellow-100 text-yellow-700",
  top_secret: "bg-orange-100 text-orange-700",
  ts_sci: "bg-red-100 text-red-700",
};

const CLEARANCE_LABELS: Record<string, string> = {
  none: "None",
  confidential: "Confidential",
  secret: "Secret",
  top_secret: "Top Secret",
  ts_sci: "TS/SCI",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  pending: "bg-yellow-100 text-yellow-700",
  expired: "bg-red-100 text-red-700",
  not_required: "bg-gray-100 text-gray-600",
};

const REQ_STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-100 text-blue-700",
  sourcing: "bg-purple-100 text-purple-700",
  interviewing: "bg-yellow-100 text-yellow-700",
  offer: "bg-orange-100 text-orange-700",
  filled: "bg-green-100 text-green-700",
  cancelled: "bg-gray-100 text-gray-500",
};

const PRIORITY_COLORS: Record<number, string> = {
  1: "bg-red-100 text-red-700",
  2: "bg-orange-100 text-orange-700",
  3: "bg-blue-100 text-blue-700",
  4: "bg-gray-100 text-gray-600",
};

const PRIORITY_LABELS: Record<number, string> = {
  1: "Critical",
  2: "High",
  3: "Medium",
  4: "Low",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function WorkforcePage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("employees");

  // Data
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [requisitions, setRequisitions] = useState<HiringRequisition[]>([]);
  const [forecast, setForecast] = useState<DemandForecast | null>(null);

  // UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [clearanceFilter, setClearanceFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (clearanceFilter) params.clearance_type = clearanceFilter;
      if (departmentFilter) params.department = departmentFilter;
      const data = await getEmployees(params);
      setEmployees(data.results || []);
    } catch {
      setError("Failed to load employees.");
    } finally {
      setLoading(false);
    }
  }, [search, clearanceFilter, departmentFilter]);

  const fetchAssignments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAssignments({ is_active: "true" });
      setAssignments(data.results || []);
    } catch {
      setError("Failed to load assignments.");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRequisitions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getHiringRequisitions();
      setRequisitions(data.results || []);
    } catch {
      setError("Failed to load hiring requisitions.");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchForecast = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDemandForecast();
      setForecast(data);
    } catch {
      setError("Failed to load demand forecast.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "employees") fetchEmployees();
    else if (activeTab === "assignments") fetchAssignments();
    else if (activeTab === "hiring") fetchRequisitions();
    else if (activeTab === "forecast") fetchForecast();
  }, [activeTab, fetchEmployees, fetchAssignments, fetchRequisitions, fetchForecast]);

  // Summary stats
  const activeEmployees = employees.filter((e) => e.is_active);
  const clearedCount = employees.filter(
    (e) => e.clearance_status === "active" && e.clearance_type !== "none"
  ).length;
  const expiringClearances = employees.filter((e) => {
    if (!e.clearance_expiry || e.clearance_type === "none") return false;
    const days = (new Date(e.clearance_expiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    return days >= 0 && days <= 90;
  }).length;

  const departments = Array.from(new Set(employees.map((e) => e.department).filter(Boolean))).sort();

  const tabs: { key: ActiveTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { key: "employees", label: "Employees", icon: Users },
    { key: "assignments", label: "Assignments", icon: Briefcase },
    { key: "hiring", label: "Hiring", icon: UserCheck },
    { key: "forecast", label: "Demand Forecast", icon: TrendingUp },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Workforce & HR Intelligence
        </h1>
        <p className="text-muted-foreground">
          Manage employees, clearances, assignments, and hiring pipeline
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Employees</p>
                <p className="text-2xl font-bold">{activeEmployees.length}</p>
              </div>
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cleared Personnel</p>
                <p className="text-2xl font-bold">{clearedCount}</p>
              </div>
              <ShieldAlert className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Clearances Expiring</p>
                <p className={`text-2xl font-bold ${expiringClearances > 0 ? "text-yellow-600" : ""}`}>
                  {expiringClearances}
                </p>
                <p className="text-xs text-muted-foreground">Within 90 days</p>
              </div>
              <AlertTriangle className={`h-8 w-8 ${expiringClearances > 0 ? "text-yellow-500" : "text-muted-foreground"}`} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Open Requisitions</p>
                <p className="text-2xl font-bold">
                  {requisitions.filter((r) => !["filled", "cancelled"].includes(r.status)).length}
                </p>
              </div>
              <UserCheck className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:border-muted-foreground hover:text-foreground"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Employees Tab */}
      {activeTab === "employees" && (
        <>
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by name, email, or title..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <select
                  value={clearanceFilter}
                  onChange={(e) => setClearanceFilter(e.target.value)}
                  className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">All Clearances</option>
                  {Object.entries(CLEARANCE_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
                <select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">All Departments</option>
                  {departments.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Employees
                {!loading && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({employees.length} results)
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  <span className="ml-3 text-muted-foreground">Loading employees...</span>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <p className="text-red-600 mb-4">{error}</p>
                  <Button variant="outline" onClick={fetchEmployees}>Retry</Button>
                </div>
              ) : employees.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Users className="h-10 w-10 text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">No employees found.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Name</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Title</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Department</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Clearance</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Status</th>
                        <th className="pb-3 pr-4 font-medium text-muted-foreground">Labor Category</th>
                        <th className="pb-3 font-medium text-muted-foreground">Skills</th>
                      </tr>
                    </thead>
                    <tbody>
                      {employees.map((emp) => (
                        <tr key={emp.id} className="border-b transition-colors hover:bg-muted/50">
                          <td className="py-3 pr-4">
                            <div>
                              <span className="font-medium">{emp.name}</span>
                              <span className="text-xs text-muted-foreground block">{emp.email}</span>
                            </div>
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground">{emp.title || "--"}</td>
                          <td className="py-3 pr-4 text-muted-foreground">{emp.department || "--"}</td>
                          <td className="py-3 pr-4">
                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${CLEARANCE_COLORS[emp.clearance_type] || "bg-gray-100 text-gray-600"}`}>
                              {CLEARANCE_LABELS[emp.clearance_type] || emp.clearance_type}
                            </span>
                          </td>
                          <td className="py-3 pr-4">
                            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[emp.clearance_status] || "bg-gray-100 text-gray-600"}`}>
                              {emp.clearance_status_display || emp.clearance_status}
                            </span>
                            {emp.clearance_expiry && (
                              <span className="text-xs text-muted-foreground block mt-0.5">
                                Exp: {formatDate(emp.clearance_expiry)}
                              </span>
                            )}
                          </td>
                          <td className="py-3 pr-4 text-muted-foreground text-xs">{emp.labor_category || "--"}</td>
                          <td className="py-3">
                            <div className="flex flex-wrap gap-1 max-w-[200px]">
                              {(emp.skills || []).slice(0, 3).map((skill) => (
                                <span key={skill} className="inline-flex items-center rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">
                                  {skill}
                                </span>
                              ))}
                              {(emp.skills || []).length > 3 && (
                                <span className="text-xs text-muted-foreground">+{emp.skills.length - 3}</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Assignments Tab */}
      {activeTab === "assignments" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Active Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : assignments.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Briefcase className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No active assignments.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Employee</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Role</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Allocation</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Start Date</th>
                      <th className="pb-3 font-medium text-muted-foreground">End Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((a) => (
                      <tr key={a.id} className="border-b transition-colors hover:bg-muted/50">
                        <td className="py-3 pr-4 font-medium">{a.employee_name || a.employee}</td>
                        <td className="py-3 pr-4 text-muted-foreground">{a.role || "--"}</td>
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 rounded-full bg-muted overflow-hidden">
                              <div
                                className={`h-full rounded-full ${a.allocation_percentage > 90 ? "bg-red-400" : a.allocation_percentage > 70 ? "bg-yellow-400" : "bg-green-400"}`}
                                style={{ width: `${Math.min(a.allocation_percentage, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground">{a.allocation_percentage}%</span>
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground text-xs">{formatDate(a.start_date)}</td>
                        <td className="py-3 text-muted-foreground text-xs">{formatDate(a.end_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Hiring Tab */}
      {activeTab === "hiring" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Hiring Requisitions
              {!loading && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  ({requisitions.length} total)
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : requisitions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <UserCheck className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No hiring requisitions.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Title</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Department</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Clearance Req.</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Priority</th>
                      <th className="pb-3 pr-4 font-medium text-muted-foreground">Status</th>
                      <th className="pb-3 font-medium text-muted-foreground">Target Start</th>
                    </tr>
                  </thead>
                  <tbody>
                    {requisitions.map((req) => (
                      <tr key={req.id} className="border-b transition-colors hover:bg-muted/50">
                        <td className="py-3 pr-4">
                          <div>
                            <span className="font-medium">{req.title}</span>
                            <span className="text-xs text-muted-foreground block">{req.labor_category}</span>
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-muted-foreground">{req.department || "--"}</td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${CLEARANCE_COLORS[req.clearance_required] || "bg-gray-100 text-gray-600"}`}>
                            {CLEARANCE_LABELS[req.clearance_required] || req.clearance_required}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${PRIORITY_COLORS[req.priority] || "bg-gray-100 text-gray-600"}`}>
                            {PRIORITY_LABELS[req.priority] || `P${req.priority}`}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${REQ_STATUS_COLORS[req.status] || "bg-gray-100 text-gray-600"}`}>
                            {req.status_display || req.status}
                          </span>
                        </td>
                        <td className="py-3 text-muted-foreground text-xs">{formatDate(req.target_start_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Demand Forecast Tab */}
      {activeTab === "forecast" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Labor Demand Forecast</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : !forecast ? (
              <div className="flex flex-col items-center justify-center py-12">
                <TrendingUp className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No forecast data available.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Pipeline Deals Analyzed</p>
                    <p className="text-2xl font-bold">{forecast.pipeline_deals}</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Labor Categories Forecasted</p>
                    <p className="text-2xl font-bold">{Object.keys(forecast.forecast || {}).length}</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">Staffing Gaps</p>
                    <p className={`text-2xl font-bold ${Object.values(forecast.gaps || {}).some((v) => v > 0) ? "text-red-600" : "text-green-600"}`}>
                      {Object.values(forecast.gaps || {}).filter((v) => v > 0).length}
                    </p>
                  </div>
                </div>

                {Object.keys(forecast.gaps || {}).length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold mb-3">Demand vs Capacity by Labor Category</h3>
                    <div className="space-y-3">
                      {Object.entries(forecast.forecast || {}).map(([category, demand]) => {
                        const capacity = (forecast.current_capacity || {})[category] || 0;
                        const gap = (forecast.gaps || {})[category] || 0;
                        const maxVal = Math.max(Number(demand), capacity, 1);
                        return (
                          <div key={category} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-medium">{category}</span>
                              <span className={gap > 0 ? "text-red-600 font-semibold" : "text-green-600"}>
                                {gap > 0 ? `Gap: ${gap.toFixed(1)} FTE` : "Covered"}
                              </span>
                            </div>
                            <div className="flex gap-1 h-3">
                              <div className="flex-1 rounded-full bg-muted overflow-hidden" title={`Demand: ${Number(demand).toFixed(1)}`}>
                                <div
                                  className="h-full rounded-full bg-blue-400"
                                  style={{ width: `${(Number(demand) / maxVal) * 100}%` }}
                                />
                              </div>
                              <div className="flex-1 rounded-full bg-muted overflow-hidden" title={`Capacity: ${capacity}`}>
                                <div
                                  className="h-full rounded-full bg-green-400"
                                  style={{ width: `${(capacity / maxVal) * 100}%` }}
                                />
                              </div>
                            </div>
                            <div className="flex gap-4 text-xs text-muted-foreground">
                              <span>Demand: {Number(demand).toFixed(1)} FTE</span>
                              <span>Capacity: {capacity} FTE</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-blue-400 inline-block" /> Demand</span>
                      <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-400 inline-block" /> Capacity</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
