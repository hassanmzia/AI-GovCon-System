/**
 * Tests for the analytics service pure functions.
 * These functions compute derived KPI metrics from raw API data.
 */
import {
  computeKpis,
  computePipelineDistribution,
  getRecentActivity,
  getUpcomingDeadlines,
} from "@/services/analytics";
import type { Deal } from "@/types/deal";
import type { PendingApproval } from "@/services/analytics";
import type { Proposal } from "@/types/proposal";

// ── Fixtures ─────────────────────────────────────────────────────────────────

function makeDeal(overrides: Partial<Deal> = {}): Deal {
  return {
    id: "d1",
    title: "Test Deal",
    stage: "intake",
    priority: 3,
    estimated_value: "500000",
    win_probability: 0.5,
    fit_score: 0.7,
    strategic_score: 0.6,
    composite_score: 0.6,
    ai_recommendation: "",
    notes: "",
    due_date: null,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-10T00:00:00Z",
    opportunity: "opp-1",
    owner: null,
    ...overrides,
  } as Deal;
}

function makeApproval(overrides: Partial<PendingApproval> = {}): PendingApproval {
  return {
    id: "a1",
    deal: "d1",
    deal_title: "Test Deal",
    approval_type: "bid_decision",
    status: "pending",
    requested_by_detail: null,
    requested_from_detail: null,
    ai_recommendation: "",
    ai_confidence: null,
    decision_rationale: "",
    decided_at: null,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

function makeProposal(overrides: Partial<Proposal> = {}): Proposal {
  return {
    id: "p1",
    deal: "d1",
    status: "in_progress",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  } as Proposal;
}

// ── computeKpis ───────────────────────────────────────────────────────────────

describe("computeKpis", () => {
  it("counts active deals (non-closed stages)", () => {
    const deals = [
      makeDeal({ stage: "intake" }),
      makeDeal({ id: "d2", stage: "qualify" }),
      makeDeal({ id: "d3", stage: "closed_won" }),
      makeDeal({ id: "d4", stage: "closed_lost" }),
      makeDeal({ id: "d5", stage: "no_bid" }),
    ];
    const { activeDeals } = computeKpis(deals, [], []);
    expect(activeDeals).toBe(2);
  });

  it("sums pipeline value for active deals only", () => {
    const deals = [
      makeDeal({ stage: "intake", estimated_value: "300000" }),
      makeDeal({ id: "d2", stage: "qualify", estimated_value: "200000" }),
      makeDeal({ id: "d3", stage: "closed_won", estimated_value: "1000000" }),
    ];
    const { pipelineValue } = computeKpis(deals, [], []);
    expect(pipelineValue).toBe(500000);
  });

  it("skips null estimated_value", () => {
    const deals = [
      makeDeal({ stage: "intake", estimated_value: null as unknown as string }),
      makeDeal({ id: "d2", stage: "qualify", estimated_value: "100000" }),
    ];
    const { pipelineValue } = computeKpis(deals, [], []);
    expect(pipelineValue).toBe(100000);
  });

  it("computes win rate correctly", () => {
    const deals = [
      makeDeal({ id: "d1", stage: "closed_won" }),
      makeDeal({ id: "d2", stage: "closed_won" }),
      makeDeal({ id: "d3", stage: "closed_lost" }),
    ];
    const { winRate } = computeKpis(deals, [], []);
    expect(winRate).toBeCloseTo(66.67, 1);
  });

  it("returns null win rate when no closed deals", () => {
    const deals = [makeDeal({ stage: "intake" })];
    const { winRate } = computeKpis(deals, [], []);
    expect(winRate).toBeNull();
  });

  it("counts pending approvals", () => {
    const approvals = [makeApproval(), makeApproval({ id: "a2" })];
    const { pendingApprovals } = computeKpis([], approvals, []);
    expect(pendingApprovals).toBe(2);
  });

  it("counts open proposals (non-submitted)", () => {
    const proposals = [
      makeProposal({ status: "in_progress" }),
      makeProposal({ id: "p2", status: "submitted" }),
      makeProposal({ id: "p3", status: "draft" }),
    ];
    const { openProposals } = computeKpis([], [], proposals);
    expect(openProposals).toBe(2);
  });

  it("computes avgFitScore from active deals with non-zero scores", () => {
    const deals = [
      makeDeal({ stage: "intake", composite_score: 0.8 }),
      makeDeal({ id: "d2", stage: "qualify", composite_score: 0.6 }),
      makeDeal({ id: "d3", stage: "intake", composite_score: 0 }), // excluded
      makeDeal({ id: "d4", stage: "closed_won", composite_score: 0.9 }), // excluded (closed)
    ];
    const { avgFitScore } = computeKpis(deals, [], []);
    expect(avgFitScore).toBeCloseTo(0.7, 5);
  });

  it("returns null avgFitScore when no active deals have scores", () => {
    const deals = [makeDeal({ stage: "intake", composite_score: 0 })];
    const { avgFitScore } = computeKpis(deals, [], []);
    expect(avgFitScore).toBeNull();
  });
});

// ── computePipelineDistribution ───────────────────────────────────────────────

describe("computePipelineDistribution", () => {
  it("returns all 8 pipeline stages", () => {
    const dist = computePipelineDistribution([]);
    expect(dist).toHaveLength(8);
  });

  it("counts deals per stage correctly", () => {
    const deals = [
      makeDeal({ stage: "intake" }),
      makeDeal({ id: "d2", stage: "intake" }),
      makeDeal({ id: "d3", stage: "qualify" }),
    ];
    const dist = computePipelineDistribution(deals);
    const intake = dist.find((d) => d.stage === "intake");
    const qualify = dist.find((d) => d.stage === "qualify");
    expect(intake?.count).toBe(2);
    expect(qualify?.count).toBe(1);
  });

  it("gives count 0 for stages with no deals", () => {
    const dist = computePipelineDistribution([]);
    dist.forEach((d) => expect(d.count).toBe(0));
  });
});

// ── getRecentActivity ─────────────────────────────────────────────────────────

describe("getRecentActivity", () => {
  it("returns deals sorted by updated_at descending", () => {
    const deals = [
      makeDeal({ id: "old", updated_at: "2025-01-01T00:00:00Z" }),
      makeDeal({ id: "new", updated_at: "2025-01-10T00:00:00Z" }),
      makeDeal({ id: "mid", updated_at: "2025-01-05T00:00:00Z" }),
    ];
    const result = getRecentActivity(deals);
    expect(result[0].id).toBe("new");
    expect(result[1].id).toBe("mid");
    expect(result[2].id).toBe("old");
  });

  it("limits results to the specified count", () => {
    const deals = Array.from({ length: 10 }, (_, i) =>
      makeDeal({ id: `d${i}`, updated_at: `2025-01-${String(i + 1).padStart(2, "0")}T00:00:00Z` })
    );
    const result = getRecentActivity(deals, 3);
    expect(result).toHaveLength(3);
  });

  it("does not mutate the original array", () => {
    const deals = [
      makeDeal({ id: "a", updated_at: "2025-01-01T00:00:00Z" }),
      makeDeal({ id: "b", updated_at: "2025-01-10T00:00:00Z" }),
    ];
    const original = [...deals];
    getRecentActivity(deals);
    expect(deals[0].id).toBe(original[0].id);
  });
});

// ── getUpcomingDeadlines ───────────────────────────────────────────────────────

describe("getUpcomingDeadlines", () => {
  it("returns only deals with due_date within the window", () => {
    const now = new Date();
    const inWindow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const pastDue = new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000).toISOString();
    const farFuture = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000).toISOString();

    const deals = [
      makeDeal({ id: "in-window", due_date: inWindow }),
      makeDeal({ id: "past", due_date: pastDue }),
      makeDeal({ id: "far", due_date: farFuture }),
      makeDeal({ id: "no-date", due_date: null }),
    ];

    const result = getUpcomingDeadlines(deals, 30);
    expect(result.map((d) => d.id)).toContain("in-window");
    expect(result.map((d) => d.id)).not.toContain("past");
    expect(result.map((d) => d.id)).not.toContain("far");
    expect(result.map((d) => d.id)).not.toContain("no-date");
  });

  it("sorts results by due_date ascending", () => {
    const now = new Date();
    const sooner = new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000).toISOString();
    const later = new Date(now.getTime() + 10 * 24 * 60 * 60 * 1000).toISOString();

    const deals = [
      makeDeal({ id: "later", due_date: later }),
      makeDeal({ id: "sooner", due_date: sooner }),
    ];

    const result = getUpcomingDeadlines(deals, 30);
    expect(result[0].id).toBe("sooner");
    expect(result[1].id).toBe("later");
  });
});
