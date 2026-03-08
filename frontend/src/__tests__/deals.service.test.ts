/**
 * Tests for the deals service (services/deals.ts).
 * We mock the api module to avoid real HTTP calls.
 */

jest.mock("@/lib/api", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
  },
}));

import api from "@/lib/api";
import {
  getDeals,
  getDeal,
  createDeal,
  updateDeal,
  transitionDealStage,
  getDealStageHistory,
  getDealPipelineSummary,
  requestApproval,
  getTasks,
  completeTask,
  getApprovals,
  decideApproval,
} from "@/services/deals";

const mockApi = api as jest.Mocked<typeof api>;

beforeEach(() => {
  jest.clearAllMocks();
});

describe("getDeals", () => {
  it("calls the correct endpoint without params", async () => {
    const dealsData = { results: [], count: 0 };
    mockApi.get.mockResolvedValueOnce({ data: dealsData });

    const result = await getDeals();

    expect(mockApi.get).toHaveBeenCalledWith("/deals/deals/", {
      params: undefined,
    });
    expect(result).toEqual(dealsData);
  });

  it("passes query params to the API", async () => {
    const dealsData = {
      results: [{ id: "d-1", title: "Test Deal", stage: "qualification" }],
      count: 1,
    };
    mockApi.get.mockResolvedValueOnce({ data: dealsData });

    const params = { stage: "qualification", ordering: "-created_at" };
    const result = await getDeals(params);

    expect(mockApi.get).toHaveBeenCalledWith("/deals/deals/", { params });
    expect(result.results).toHaveLength(1);
  });
});

describe("getDeal", () => {
  it("fetches a single deal by ID", async () => {
    const deal = {
      id: "deal-123",
      title: "Cloud Migration",
      stage: "proposal",
      value: 500000,
    };
    mockApi.get.mockResolvedValueOnce({ data: deal });

    const result = await getDeal("deal-123");

    expect(mockApi.get).toHaveBeenCalledWith("/deals/deals/deal-123/");
    expect(result).toEqual(deal);
  });

  it("propagates errors for non-existent deals", async () => {
    mockApi.get.mockRejectedValueOnce(new Error("Not Found"));

    await expect(getDeal("bad-id")).rejects.toThrow("Not Found");
  });
});

describe("createDeal", () => {
  it("posts a new deal to the correct endpoint", async () => {
    const payload = {
      title: "New Deal",
      opportunity_id: "opp-456",
      value: 250000,
    };
    const created = { id: "deal-new", ...payload, stage: "identification" };
    mockApi.post.mockResolvedValueOnce({ data: created });

    const result = await createDeal(payload as any);

    expect(mockApi.post).toHaveBeenCalledWith("/deals/deals/", payload);
    expect(result.id).toBe("deal-new");
    expect(result.title).toBe("New Deal");
  });
});

describe("updateDeal", () => {
  it("patches an existing deal with partial data", async () => {
    const payload = { title: "Updated Deal Title" };
    const updated = {
      id: "deal-123",
      title: "Updated Deal Title",
      stage: "proposal",
    };
    mockApi.patch.mockResolvedValueOnce({ data: updated });

    const result = await updateDeal("deal-123", payload as any);

    expect(mockApi.patch).toHaveBeenCalledWith(
      "/deals/deals/deal-123/",
      payload
    );
    expect(result.title).toBe("Updated Deal Title");
  });
});

describe("transitionDealStage", () => {
  it("posts with target_stage to the transition endpoint", async () => {
    const payload = { target_stage: "proposal" };
    const transitioned = {
      id: "deal-123",
      title: "Deal",
      stage: "proposal",
    };
    mockApi.post.mockResolvedValueOnce({ data: transitioned });

    const result = await transitionDealStage("deal-123", payload as any);

    expect(mockApi.post).toHaveBeenCalledWith(
      "/deals/deals/deal-123/transition/",
      payload
    );
    expect(result.stage).toBe("proposal");
  });

  it("includes optional notes in the transition payload", async () => {
    const payload = {
      target_stage: "review",
      notes: "Ready for review",
    };
    mockApi.post.mockResolvedValueOnce({
      data: { id: "deal-123", stage: "review" },
    });

    await transitionDealStage("deal-123", payload as any);

    expect(mockApi.post).toHaveBeenCalledWith(
      "/deals/deals/deal-123/transition/",
      payload
    );
  });
});

describe("getDealStageHistory", () => {
  it("returns stage transition history for a deal", async () => {
    const history = [
      {
        id: "h-1",
        from_stage: "identification",
        to_stage: "qualification",
        transitioned_at: "2025-01-15T10:00:00Z",
      },
      {
        id: "h-2",
        from_stage: "qualification",
        to_stage: "proposal",
        transitioned_at: "2025-02-01T14:00:00Z",
      },
    ];
    mockApi.get.mockResolvedValueOnce({ data: history });

    const result = await getDealStageHistory("deal-123");

    expect(mockApi.get).toHaveBeenCalledWith(
      "/deals/deals/deal-123/stage-history/"
    );
    expect(result).toHaveLength(2);
    expect(result[0].to_stage).toBe("qualification");
  });
});

describe("getDealPipelineSummary", () => {
  it("returns pipeline summary data", async () => {
    const summary = {
      total_deals: 15,
      total_value: 3000000,
      stages: { identification: 5, qualification: 4, proposal: 6 },
    };
    mockApi.get.mockResolvedValueOnce({ data: summary });

    const result = await getDealPipelineSummary("deal-123");

    expect(mockApi.get).toHaveBeenCalledWith(
      "/deals/deals/deal-123/pipeline-summary/"
    );
    expect(result).toEqual(summary);
  });
});

describe("requestApproval", () => {
  it("posts an approval request for a deal", async () => {
    const approval = {
      id: "apr-1",
      deal: "deal-123",
      status: "pending",
    };
    mockApi.post.mockResolvedValueOnce({ data: approval });

    const result = await requestApproval("deal-123");

    expect(mockApi.post).toHaveBeenCalledWith(
      "/deals/deals/deal-123/request-approval/"
    );
    expect(result.status).toBe("pending");
  });
});

describe("getTasks", () => {
  it("fetches tasks with optional filters", async () => {
    const tasksData = {
      results: [
        { id: "t-1", title: "Review proposal", completed: false },
        { id: "t-2", title: "Update pricing", completed: true },
      ],
      count: 2,
    };
    mockApi.get.mockResolvedValueOnce({ data: tasksData });

    const result = await getTasks({ deal: "deal-123" });

    expect(mockApi.get).toHaveBeenCalledWith("/deals/tasks/", {
      params: { deal: "deal-123" },
    });
    expect(result.results).toHaveLength(2);
    expect(result.count).toBe(2);
  });
});

describe("completeTask", () => {
  it("marks a task as completed", async () => {
    const completedTask = {
      id: "t-1",
      title: "Review proposal",
      completed: true,
    };
    mockApi.post.mockResolvedValueOnce({ data: completedTask });

    const result = await completeTask("t-1");

    expect(mockApi.post).toHaveBeenCalledWith("/deals/tasks/t-1/complete/");
    expect(result.completed).toBe(true);
  });
});

describe("getApprovals", () => {
  it("fetches approvals with optional filters", async () => {
    const approvalsData = {
      results: [{ id: "apr-1", status: "pending" }],
      count: 1,
    };
    mockApi.get.mockResolvedValueOnce({ data: approvalsData });

    const result = await getApprovals({ status: "pending" });

    expect(mockApi.get).toHaveBeenCalledWith("/deals/approvals/", {
      params: { status: "pending" },
    });
    expect(result.results).toHaveLength(1);
  });
});

describe("decideApproval", () => {
  it("posts an approval decision", async () => {
    const payload = { decision: "approved", comments: "Looks good" };
    const decided = {
      id: "apr-1",
      status: "approved",
      comments: "Looks good",
    };
    mockApi.post.mockResolvedValueOnce({ data: decided });

    const result = await decideApproval("apr-1", payload as any);

    expect(mockApi.post).toHaveBeenCalledWith(
      "/deals/approvals/apr-1/decide/",
      payload
    );
    expect(result.status).toBe("approved");
  });

  it("handles rejection decisions", async () => {
    const payload = {
      decision: "rejected",
      comments: "Needs more detail",
    };
    const decided = {
      id: "apr-2",
      status: "rejected",
      comments: "Needs more detail",
    };
    mockApi.post.mockResolvedValueOnce({ data: decided });

    const result = await decideApproval("apr-2", payload as any);

    expect(result.status).toBe("rejected");
  });
});
