import api from "@/lib/api";
import { ArchitectureResult } from "@/types/architecture";

/**
 * Run the Solution Architect Agent for a deal.
 * Calls POST /api/deals/{id}/run-solution-architect/
 *
 * This is a long-running operation (30-120 seconds) as it invokes an
 * AI agent pipeline. The request is made with an extended timeout.
 */
export async function runSolutionArchitect(dealId: string): Promise<ArchitectureResult> {
  const response = await api.post(
    `/deals/deals/${dealId}/run-solution-architect/`,
    {},
    { timeout: 180_000 }   // 3-minute timeout for the full agent pipeline
  );
  return response.data;
}
