import api from "@/lib/api";
import {
  Contract,
  ContractTemplate,
  ContractClause,
  ContractVersion,
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
