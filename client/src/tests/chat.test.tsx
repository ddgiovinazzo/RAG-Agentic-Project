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

const CONV = [{ id: 1, title: "VPN ticket", created_at: "2026-08-03T00:00:00" }];
const TRACE = [
  {
    seq: 1,
    kind: "llm_call",
    tool_name: null,
    arguments: null,
    result: {},
    latency_ms: 900,
  },
  {
    seq: 2,
    kind: "tool_call",
    tool_name: "search_knowledge",
    arguments: { query: "vpn" },
    result: { answer: "reset it", sources: [] },
    latency_ms: 230,
  },
];

async function renderAndOpenConversation(extraRoutes: Parameters<typeof stubFetch>[0]) {
  localStorage.setItem("agent_token", "jwt-123");
  localStorage.setItem("agent_email", "me@test.com");
  stubFetch({
    "GET /api/conversations": () => jsonResponse(CONV),
    "GET /api/conversations/1/messages": () =>
      jsonResponse({ messages: [], runs: [] }),
    ...extraRoutes,
  });
  render(
    <AuthProvider>
      <App />
    </AuthProvider>
  );
  await userEvent.click(await screen.findByText("VPN ticket"));
}

test("sending a goal renders the answer with a trace chip and fills the panel", async () => {
  await renderAndOpenConversation({
    "POST /api/conversations/1/messages": () =>
      jsonResponse({
        run_id: 17,
        status: "completed",
        answer: "Reset it in Settings.",
        trace: TRACE,
      }),
  });
  await userEvent.type(
    screen.getByPlaceholderText(/give the agent a goal/i),
    "How do I reset my VPN?"
  );
  await userEvent.click(screen.getByRole("button", { name: /send/i }));

  expect(await screen.findByText("Reset it in Settings.")).toBeInTheDocument();
  expect(screen.getByTestId("trace-chip-17")).toHaveTextContent("2 steps");
  expect(screen.getByText(/run #17/i)).toBeInTheDocument();
  expect(screen.getByText(/#2 · search_knowledge/i)).toBeInTheDocument();
});

test("needs_confirmation pauses: approve resolves the placeholder", async () => {
  await renderAndOpenConversation({
    "POST /api/conversations/1/messages": () =>
      jsonResponse({
        run_id: 18,
        status: "needs_confirmation",
        pending_action: {
          id: 3,
          tool: "escalate",
          arguments: { ticket_id: "T-1", priority: "high", reason: "outage" },
        },
        trace: TRACE.slice(0, 1),
      }),
    "POST /api/runs/18/confirm": () =>
      jsonResponse({
        run_id: 18,
        status: "completed",
        answer: "Escalated to on-call.",
        trace: TRACE,
      }),
  });
  await userEvent.type(
    screen.getByPlaceholderText(/give the agent a goal/i),
    "Escalate ticket T-1"
  );
  await userEvent.click(screen.getByRole("button", { name: /send/i }));

  expect(
    await screen.findByText(/waiting for your confirmation/i)
  ).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/give the agent a goal/i)).toBeDisabled();
  expect(screen.getByText(/the agent wants to run/i)).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: /approve/i }));
  expect(await screen.findByText("Escalated to on-call.")).toBeInTheDocument();
  expect(screen.queryByText(/waiting for your confirmation/i)).not.toBeInTheDocument();
  expect(screen.getByPlaceholderText(/give the agent a goal/i)).toBeEnabled();
});

test("send failure shows a snackbar and preserves the draft", async () => {
  await renderAndOpenConversation({
    "POST /api/conversations/1/messages": () =>
      jsonResponse({ error: "boom" }, 500),
  });
  const input = screen.getByPlaceholderText(/give the agent a goal/i);
  await userEvent.type(input, "hello agent");
  await userEvent.click(screen.getByRole("button", { name: /send/i }));
  expect(await screen.findByText("boom")).toBeInTheDocument();
  expect(input).toHaveValue("hello agent");
});

test("clicking a trace chip loads the run into the panel", async () => {
  await renderAndOpenConversation({
    "POST /api/conversations/1/messages": () =>
      jsonResponse({ run_id: 17, status: "completed", answer: "Done.", trace: TRACE }),
    "GET /api/runs/17": () =>
      jsonResponse({
        id: 17,
        status: "completed",
        model: "llama3.1:8b",
        total_latency_ms: 1130,
        created_at: "2026-08-03T00:00:00",
        steps: TRACE,
      }),
  });
  await userEvent.type(
    screen.getByPlaceholderText(/give the agent a goal/i),
    "do it"
  );
  await userEvent.click(screen.getByRole("button", { name: /send/i }));
  await screen.findByText("Done.");
  await userEvent.click(screen.getByTestId("trace-chip-17"));
  expect(await screen.findByText(/1\.1s total/i)).toBeInTheDocument();
});

test("selecting a conversation restores its history with trace chips", async () => {
  await renderAndOpenConversation({
    "GET /api/conversations/1/messages": () =>
      jsonResponse({
        messages: [
          { id: 1, role: "user", content: "reset vpn?", created_at: "t1" },
          { id: 2, role: "assistant", content: "In Settings.", created_at: "t2" },
        ],
        runs: [{ id: 10, user_message_id: 1, status: "completed" }],
      }),
  });
  expect(await screen.findByText("In Settings.")).toBeInTheDocument();
  expect(screen.getByTestId("trace-chip-10")).toBeInTheDocument();
});
