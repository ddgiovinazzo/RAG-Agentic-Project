import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import App from "../App";
import { AuthProvider } from "../auth/AuthContext";
import { jsonResponse, stubFetch } from "./helpers";

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

export const EMPTY_STATS = {
  total_runs: 0, by_status: {}, success_rate: null, avg_steps: null,
  avg_latency_ms: null, total_prompt_tokens: 0, total_completion_tokens: 0,
  tool_usage: {}, runs_per_day: [], latency_buckets: [],
};

export const STATS = {
  total_runs: 4,
  by_status: { completed: 2, failed: 1, declined: 1 },
  success_rate: 0.5,
  avg_steps: 2.0,
  avg_latency_ms: 6625,
  total_prompt_tokens: 600,
  total_completion_tokens: 60,
  tool_usage: { search_knowledge: 3, escalate: 1 },
  runs_per_day: [
    { date: "2026-08-01", completed: 2, failed: 0, declined: 0, needs_confirmation: 0 },
    { date: "2026-08-02", completed: 0, failed: 1, declined: 1, needs_confirmation: 0 },
  ],
  latency_buckets: [
    { label: "<2s", count: 1 }, { label: "2–5s", count: 1 },
    { label: "5–15s", count: 1 }, { label: "15s+", count: 1 },
  ],
};

export const RUNS_PAGE = {
  runs: [
    {
      id: 17, status: "completed", goal: "Escalate ticket T-1",
      conversation_id: 1, conversation_title: "VPN ticket", model: "llama3.1:8b",
      step_count: 3, total_latency_ms: 5210, prompt_tokens: 1450,
      completion_tokens: 220, created_at: "2026-08-04T10:00:00",
    },
  ],
  total: 1, page: 1, per_page: 20,
};

export function renderAudit(extraRoutes: Parameters<typeof stubFetch>[0] = {}) {
  localStorage.setItem("agent_token", "jwt-123");
  localStorage.setItem("agent_email", "me@test.com");
  stubFetch({
    "GET /api/conversations": () => jsonResponse([]),
    "GET /api/runs?page=1": () => jsonResponse(RUNS_PAGE),
    "GET /api/runs/stats": () => jsonResponse(STATS),
    ...extraRoutes,
  });
  return render(
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

test("audit tab shows stat cards from the stats endpoint", async () => {
  renderAudit();
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  expect(await screen.findByText("50%")).toBeInTheDocument(); // success rate
  expect(screen.getByText("4")).toBeInTheDocument(); // total runs
  expect(screen.getByText(/6\.6s/)).toBeInTheDocument(); // avg latency
});

test("chat tab is unaffected and switching back works", async () => {
  renderAudit();
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  await screen.findByText("50%");
  await userEvent.click(screen.getByRole("tab", { name: /chat/i }));
  expect(
    await screen.findByText(/how can i assist you today/i)
  ).toBeInTheDocument();
});


test("audit tab renders both charts when there is data", async () => {
  renderAudit();
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  expect(await screen.findByTestId("runs-per-day-chart")).toBeInTheDocument();
  expect(screen.getByTestId("latency-chart")).toBeInTheDocument();
});

test("audit tab shows chart empty state with no runs", async () => {
  renderAudit({
    "GET /api/runs?page=1": () =>
      jsonResponse({ runs: [], total: 0, page: 1, per_page: 20 }),
    "GET /api/runs/stats": () => jsonResponse(EMPTY_STATS),
  });
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  expect(await screen.findByText(/no run data yet/i)).toBeInTheDocument();
  expect(screen.queryByTestId("runs-per-day-chart")).not.toBeInTheDocument();
});

test("runs table renders rows and drives filters", async () => {
  const routes = {
    "GET /api/runs?status=failed&page=1": () =>
      jsonResponse({ runs: [], total: 0, page: 1, per_page: 20 }),
    "GET /api/runs/stats?status=failed": () => jsonResponse(EMPTY_STATS),
  };
  renderAudit(routes);
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  expect(await screen.findByText("Escalate ticket T-1")).toBeInTheDocument();
  expect(screen.getByText("5.2s")).toBeInTheDocument();

  // no admin column for regular users
  expect(screen.queryByText(/user email/i)).not.toBeInTheDocument();

  await userEvent.click(screen.getByLabelText(/status filter/i));
  await userEvent.click(await screen.findByRole("option", { name: /^failed$/i }));
  expect(await screen.findByText(/no runs match these filters/i)).toBeInTheDocument();
});

test("admin sees the user column and email filter", async () => {
  localStorage.setItem("agent_is_admin", "1");
  renderAudit({
    "GET /api/runs?page=1": () =>
      jsonResponse({
        ...RUNS_PAGE,
        runs: [{ ...RUNS_PAGE.runs[0], user_email: "someone@test.com" }],
      }),
  });
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  expect(await screen.findByText("someone@test.com")).toBeInTheDocument();
  expect(screen.getByLabelText(/user email/i)).toBeInTheDocument();
});

test("clicking a run opens the drawer with steps and JSON export", async () => {
  const createObjectURL = vi.fn(() => "blob:fake");
  vi.stubGlobal("URL", {
    ...URL,
    createObjectURL,
    revokeObjectURL: vi.fn(),
  });
  renderAudit({
    "GET /api/runs/17": () =>
      jsonResponse({
        id: 17, status: "completed", model: "llama3.1:8b",
        total_latency_ms: 5210, created_at: "2026-08-04T10:00:00",
        steps: [
          {
            seq: 1, kind: "tool_call", tool_name: "search_knowledge",
            arguments: { query: "sla" }, result: { answer: "24h" }, latency_ms: 230,
          },
        ],
      }),
  });
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  await userEvent.click(await screen.findByText("Escalate ticket T-1"));
  expect(await screen.findByText(/#1 · search_knowledge/i)).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: /download json/i }));
  expect(createObjectURL).toHaveBeenCalledOnce();
});

test("drawer shows an error when the run fails to load", async () => {
  renderAudit({
    "GET /api/runs/17": () =>
      jsonResponse({ error: "run not found" }, 404),
  });
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  await userEvent.click(await screen.findByText("Escalate ticket T-1"));
  expect(await screen.findByText(/couldn't load this run/i)).toBeInTheDocument();
});

test("drawer disables confirm buttons for a needs_confirmation run", async () => {
  renderAudit({
    "GET /api/runs/17": () =>
      jsonResponse({
        id: 17, status: "needs_confirmation", model: "llama3.1:8b",
        total_latency_ms: 5210, created_at: "2026-08-04T10:00:00",
        steps: [],
        pending_action: { id: 1, tool: "escalate", arguments: { ticket_id: "T-1" } },
      }),
  });
  await userEvent.click(await screen.findByRole("tab", { name: /audit/i }));
  await userEvent.click(await screen.findByText("Escalate ticket T-1"));
  expect(await screen.findByRole("button", { name: /approve/i })).toBeDisabled();
  expect(screen.getByRole("button", { name: /reject/i })).toBeDisabled();
});
