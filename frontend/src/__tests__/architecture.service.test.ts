/**
 * Tests for the architecture service (services/architecture.ts).
 * We mock the api module to avoid real HTTP calls.
 */

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

import api from "@/lib/api";
import {
  runSolutionArchitect,
  getTechnicalSolution,
  getArchitectureDiagrams,
  getValidationReport,
  startAgentRun,
  getAgentRunStatus,
} from "@/services/architecture";

const mockApi = api as jest.Mocked<typeof api>;

beforeEach(() => {
  jest.clearAllMocks();
});

describe("runSolutionArchitect", () => {
  it("calls POST with the correct URL and extended timeout", async () => {
    const mockResult = {
      id: "sol-1",
      deal_id: "deal-123",
      status: "completed",
      components: [],
    };
    mockApi.post.mockResolvedValueOnce({ data: mockResult });

    const result = await runSolutionArchitect("deal-123");

    expect(mockApi.post).toHaveBeenCalledWith(
      "/deals/deals/deal-123/run-solution-architect/",
      {},
      { timeout: 180_000 }
    );
    expect(result).toEqual(mockResult);
  });

  it("propagates errors from the API", async () => {
    mockApi.post.mockRejectedValueOnce(new Error("Gateway Timeout"));

    await expect(runSolutionArchitect("deal-999")).rejects.toThrow(
      "Gateway Timeout"
    );
  });
});

describe("getTechnicalSolution", () => {
  it("returns the first result when results exist", async () => {
    const solution = { id: "ts-1", deal: "deal-1", status: "completed" };
    mockApi.get.mockResolvedValueOnce({
      data: { results: [solution], count: 1 },
    });

    const result = await getTechnicalSolution("deal-1");

    expect(mockApi.get).toHaveBeenCalledWith(
      "/proposals/technical-solutions/?deal=deal-1"
    );
    expect(result).toEqual(solution);
  });

  it("returns null when no results exist", async () => {
    mockApi.get.mockResolvedValueOnce({
      data: { results: [], count: 0 },
    });

    const result = await getTechnicalSolution("deal-empty");

    expect(result).toBeNull();
  });

  it("returns null when the API call fails", async () => {
    mockApi.get.mockRejectedValueOnce(new Error("Network Error"));

    const result = await getTechnicalSolution("deal-err");

    expect(result).toBeNull();
  });

  it("handles response data without results wrapper", async () => {
    const solution = { id: "ts-2", deal: "deal-2" };
    mockApi.get.mockResolvedValueOnce({ data: [solution] });

    const result = await getTechnicalSolution("deal-2");

    expect(result).toEqual(solution);
  });
});

describe("getArchitectureDiagrams", () => {
  it("returns diagrams for a technical solution", async () => {
    const diagrams = [
      {
        id: "diag-1",
        title: "System Overview",
        diagram_type: "architecture",
        mermaid_code: "graph TD; A-->B;",
        description: "High-level system overview",
      },
    ];
    mockApi.get.mockResolvedValueOnce({ data: { results: diagrams } });

    const result = await getArchitectureDiagrams("ts-1");

    expect(mockApi.get).toHaveBeenCalledWith(
      "/proposals/architecture-diagrams/?technical_solution=ts-1"
    );
    expect(result).toEqual(diagrams);
  });
});

describe("getValidationReport", () => {
  it("returns the validation report when it exists", async () => {
    const report = {
      overall_quality: "good",
      score: 85,
      passed: true,
      issues: [],
      suggestions: ["Add caching layer"],
      compliance_gaps: [],
    };
    mockApi.get.mockResolvedValueOnce({ data: { results: [report] } });

    const result = await getValidationReport("ts-1");

    expect(result).toEqual(report);
  });

  it("returns null when no report exists", async () => {
    mockApi.get.mockResolvedValueOnce({ data: { results: [] } });

    const result = await getValidationReport("ts-none");

    expect(result).toBeNull();
  });

  it("returns null on API failure", async () => {
    mockApi.get.mockRejectedValueOnce(new Error("Server Error"));

    const result = await getValidationReport("ts-err");

    expect(result).toBeNull();
  });
});

describe("startAgentRun", () => {
  it("posts to the correct agent endpoint with params and timeout", async () => {
    const runData = { run_id: "run-abc", status: "queued" };
    mockApi.post.mockResolvedValueOnce({ data: runData });

    const params = { deal_id: "deal-1", mode: "full" };
    const result = await startAgentRun("solution-architect", params);

    expect(mockApi.post).toHaveBeenCalledWith(
      "/ai/agents/solution-architect/run",
      params,
      { timeout: 30_000 }
    );
    expect(result).toEqual(runData);
  });
});

describe("getAgentRunStatus", () => {
  it("returns run data for a given run ID", async () => {
    const runStatus = {
      run_id: "run-abc",
      status: "completed",
      result: { components: [], diagrams: [] },
    };
    mockApi.get.mockResolvedValueOnce({ data: runStatus });

    const result = await getAgentRunStatus("run-abc");

    expect(mockApi.get).toHaveBeenCalledWith("/ai/agents/runs/run-abc");
    expect(result).toEqual(runStatus);
    expect(result.status).toBe("completed");
  });

  it("returns in-progress status when agent is still running", async () => {
    const runStatus = { run_id: "run-xyz", status: "running" };
    mockApi.get.mockResolvedValueOnce({ data: runStatus });

    const result = await getAgentRunStatus("run-xyz");

    expect(result.status).toBe("running");
    expect(result.result).toBeUndefined();
  });
});
