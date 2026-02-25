import api from "@/lib/api";
import {
  SecurityFramework,
  SecurityControl,
  SecurityControlMapping,
  SecurityComplianceReport,
  ComplianceRequirement,
} from "@/types/security";

export async function getSecurityFrameworks(
  params?: Record<string, string>
): Promise<{ results: SecurityFramework[]; count: number }> {
  const response = await api.get("/security-compliance/frameworks/", { params });
  return response.data;
}

export async function getSecurityControls(
  params?: Record<string, string>
): Promise<{ results: SecurityControl[]; count: number }> {
  const response = await api.get("/security-compliance/controls/", { params });
  return response.data;
}

export async function getControlMappings(
  params?: Record<string, string>
): Promise<{ results: SecurityControlMapping[]; count: number }> {
  const response = await api.get("/security-compliance/control-mappings/", { params });
  return response.data;
}

export async function getComplianceReports(
  params?: Record<string, string>
): Promise<{ results: SecurityComplianceReport[]; count: number }> {
  const response = await api.get("/security-compliance/reports/", { params });
  return response.data;
}

export async function getComplianceRequirements(
  params?: Record<string, string>
): Promise<{ results: ComplianceRequirement[]; count: number }> {
  const response = await api.get("/security-compliance/requirements/", { params });
  return response.data;
}
