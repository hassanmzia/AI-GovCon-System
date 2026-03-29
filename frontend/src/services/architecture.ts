import api, { orchestratorApi } from "@/lib/api";
import { ArchitectureResult } from "@/types/architecture";

/**
 * Run the Solution Architect Agent for a deal.
 * Calls POST /api/deals/deals/{id}/run-solution-architect/
 *
 * This is a long-running operation (30-120 seconds) as it invokes an
 * AI agent pipeline. The request is made with an extended timeout.
 */
export async function runSolutionArchitect(dealId: string): Promise<ArchitectureResult> {
  const response = await api.post(
    `/deals/deals/${dealId}/run-solution-architect/`,
    {},
    { timeout: 180_000 }
  );
  return response.data;
}

/**
 * Fetch the persisted technical solution for a deal (if one exists).
 */
export async function getTechnicalSolution(dealId: string): Promise<ArchitectureResult | null> {
  try {
    const response = await api.get(`/proposals/technical-solutions/?deal=${dealId}`);
    const results = response.data?.results ?? response.data;
    return results.length > 0 ? results[0] : null;
  } catch {
    return null;
  }
}

/**
 * Fetch architecture diagrams for a deal's technical solution.
 */
export async function getArchitectureDiagrams(
  technicalSolutionId: string
): Promise<Array<{ id: string; title: string; diagram_type: string; mermaid_code: string; description: string }>> {
  const response = await api.get(
    `/proposals/architecture-diagrams/?technical_solution=${technicalSolutionId}`
  );
  return response.data?.results ?? response.data;
}

/**
 * Fetch the validation report for a technical solution.
 */
export async function getValidationReport(
  technicalSolutionId: string
): Promise<{
  overall_quality: string;
  score: number | null;
  passed: boolean;
  issues: string[];
  suggestions: string[];
  compliance_gaps: string[];
} | null> {
  try {
    const response = await api.get(
      `/proposals/validation-reports/?technical_solution=${technicalSolutionId}`
    );
    const results = response.data?.results ?? response.data;
    return results.length > 0 ? results[0] : null;
  } catch {
    return null;
  }
}

/**
 * Trigger an AI agent run via the orchestrator and return the run ID.
 * The caller can then poll or subscribe via WebSocket for completion.
 */
export async function startAgentRun(
  agentType: string,
  params: Record<string, unknown>
): Promise<{ run_id: string; status: string }> {
  // Uses orchestratorApi (baseURL: /ai) so this hits /ai/agents/{type}/run via Nginx,
  // NOT Django's /api/ai/agents/... which would 404.
  const response = await orchestratorApi.post(`/agents/${agentType}/run`, params, {
    timeout: 30_000,
  });
  return response.data;
}

/**
 * Poll the status of an AI agent run.
 */
export async function getAgentRunStatus(
  runId: string
): Promise<{ run_id: string; status: string; result?: Record<string, unknown> }> {
  // Uses orchestratorApi (baseURL: /ai) so this hits /ai/agents/runs/{id} via Nginx.
  const response = await orchestratorApi.get(`/agents/runs/${runId}`);
  return response.data;
}
