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

function renderAuthed() {
  localStorage.setItem("agent_token", "jwt-123");
  localStorage.setItem("agent_email", "me@test.com");
  return render(
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

test("lists the user's conversations", async () => {
  stubFetch({
    "GET /api/conversations": () =>
      jsonResponse([
        { id: 1, title: "VPN ticket", created_at: "2026-08-03T00:00:00" },
        { id: 2, title: "Refund question", created_at: "2026-08-03T00:00:00" },
      ]),
  });
  renderAuthed();
  expect(await screen.findByText("VPN ticket")).toBeInTheDocument();
  expect(screen.getByText("Refund question")).toBeInTheDocument();
});

test("new conversation creates and selects it", async () => {
  stubFetch({
    "GET /api/conversations": () => jsonResponse([]),
    "POST /api/conversations": () => jsonResponse({ id: 5, title: "New conversation" }, 201),
    "GET /api/conversations/5/messages": () => jsonResponse({ messages: [], runs: [] }),
  });
  renderAuthed();
  await userEvent.click(
    await screen.findByRole("button", { name: /new conversation/i })
  );
  expect(
    await screen.findByPlaceholderText(/give the agent a goal/i)
  ).toBeInTheDocument();
});

test("logout returns to the auth screen", async () => {
  stubFetch({ "GET /api/conversations": () => jsonResponse([]) });
  renderAuthed();
  await userEvent.click(await screen.findByRole("button", { name: /logout/i }));
  expect(await screen.findByRole("tab", { name: /log in/i })).toBeInTheDocument();
  expect(localStorage.getItem("agent_token")).toBeNull();
});
