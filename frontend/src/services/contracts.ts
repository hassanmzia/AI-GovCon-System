import api from "@/lib/api";
import {
  Contract,
  ContractTemplate,
  ContractClause,
  ContractVersion,
  ContractMilestone,
  ContractModification,
  OptionYear,
} from "@/types/contract";

export async function getContracts(
  params?: Record<string, string>
): Promise<{ results: Contract[]; count: number }> {
  const response = await api.get("/contracts/contracts/", { params });
  return response.data;
}

export async function getContract(id: string): Promise<Contract> {
  const response = await api.get(`/contracts/contracts/${id}/`);
  return response.data;
}

export async function createContract(
  data: Partial<Contract>
): Promise<Contract> {
  const response = await api.post("/contracts/contracts/", data);
  return response.data;
}

export async function updateContract(
  id: string,
  data: Partial<Contract>
): Promise<Contract> {
  const response = await api.patch(`/contracts/contracts/${id}/`, data);
  return response.data;
}

export async function getContractTemplates(
  params?: Record<string, string>
): Promise<{ results: ContractTemplate[]; count: number }> {
  const response = await api.get("/contracts/templates/", { params });
  return response.data;
}

export async function getContractClauses(
  params?: Record<string, string>
): Promise<{ results: ContractClause[]; count: number }> {
  const response = await api.get("/contracts/clauses/", { params });
  return response.data;
}

export async function getContractVersions(
  contractId: string
): Promise<{ results: ContractVersion[]; count: number }> {
  const response = await api.get("/contracts/versions/", {
    params: { contract: contractId },
  });
  return response.data;
}

// ── Milestones ──────────────────────────────────────────

export async function getContractMilestones(
  contractId: string
): Promise<ContractMilestone[]> {
  const response = await api.get("/contracts/milestones/", {
    params: { contract: contractId },
  });
  return response.data.results || response.data;
}

export async function createMilestone(
  data: Partial<ContractMilestone>
): Promise<ContractMilestone> {
  const response = await api.post("/contracts/milestones/", data);
  return response.data;
}

export async function updateMilestone(
  id: string,
  data: Partial<ContractMilestone>
): Promise<ContractMilestone> {
  const response = await api.patch(`/contracts/milestones/${id}/`, data);
  return response.data;
}

export async function deleteMilestone(id: string): Promise<void> {
  await api.delete(`/contracts/milestones/${id}/`);
}

// ── Modifications ───────────────────────────────────────

export async function getContractModifications(
  contractId: string
): Promise<ContractModification[]> {
  const response = await api.get("/contracts/modifications/", {
    params: { contract: contractId },
  });
  return response.data.results || response.data;
}

export async function createModification(
  data: Partial<ContractModification>
): Promise<ContractModification> {
  const response = await api.post("/contracts/modifications/", data);
  return response.data;
}

export async function updateModification(
  id: string,
  data: Partial<ContractModification>
): Promise<ContractModification> {
  const response = await api.patch(`/contracts/modifications/${id}/`, data);
  return response.data;
}

// ── Option Years ────────────────────────────────────────

export async function getOptionYears(
  contractId: string
): Promise<OptionYear[]> {
  const response = await api.get("/contracts/option-years/", {
    params: { contract: contractId },
  });
  return response.data.results || response.data;
}

export async function createOptionYear(
  data: Partial<OptionYear>
): Promise<OptionYear> {
  const response = await api.post("/contracts/option-years/", data);
  return response.data;
}

export async function updateOptionYear(
  id: string,
  data: Partial<OptionYear>
): Promise<OptionYear> {
  const response = await api.patch(`/contracts/option-years/${id}/`, data);
  return response.data;
}
