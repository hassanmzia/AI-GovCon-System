import api from "@/lib/api";
import {
  Proposal,
  ProposalSection,
  ReviewCycle,
  ProposalTemplate,
} from "@/types/proposal";

export async function getProposals(
  params?: Record<string, string>
): Promise<{ results: Proposal[]; count: number }> {
  const response = await api.get("/proposals/proposals/", { params });
  return response.data;
}

export async function getProposal(id: string): Promise<Proposal> {
  const response = await api.get(`/proposals/proposals/${id}/`);
  return response.data;
}

export async function createProposal(data: {
  deal: string;
  title: string;
  template?: string;
}): Promise<Proposal> {
  const response = await api.post("/proposals/proposals/", data);
  return response.data;
}

export async function updateProposal(
  id: string,
  data: Partial<Proposal>
): Promise<Proposal> {
  const response = await api.patch(`/proposals/proposals/${id}/`, data);
  return response.data;
}

export async function getProposalSections(
  proposalId: string
): Promise<{ results: ProposalSection[]; count: number }> {
  const response = await api.get("/proposals/proposal-sections/", {
    params: { proposal: proposalId },
  });
  return response.data;
}

export async function getReviewCycles(
  proposalId: string
): Promise<{ results: ReviewCycle[]; count: number }> {
  const response = await api.get("/proposals/review-cycles/", {
    params: { proposal: proposalId },
  });
  return response.data;
}

export async function getProposalTemplates(): Promise<{
  results: ProposalTemplate[];
  count: number;
}> {
  const response = await api.get("/proposals/proposal-templates/");
  return response.data;
}
