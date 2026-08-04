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

function renderApp() {
  return render(
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

test("logging in stores the token and shows the app", async () => {
  localStorage.clear();
  stubFetch({
    "POST /api/auth/login": () => jsonResponse({ token: "jwt-123" }),
    "GET /api/conversations": () => jsonResponse([]),
  });
  renderApp();
  await userEvent.type(screen.getByLabelText(/email/i), "a@b.com");
  await userEvent.type(screen.getByLabelText(/password/i), "password123");
  await userEvent.click(screen.getByRole("button", { name: /log in/i }));
  expect(await screen.findByRole("button", { name: /logout/i })).toBeInTheDocument();
  expect(localStorage.getItem("agent_token")).toBe("jwt-123");
  expect(localStorage.getItem("agent_email")).toBe("a@b.com");
});

test("register auto-logs-in", async () => {
  localStorage.clear();
  stubFetch({
    "POST /api/auth/register": () => jsonResponse({ id: 1, email: "a@b.com" }, 201),
    "POST /api/auth/login": () => jsonResponse({ token: "jwt-456" }),
    "GET /api/conversations": () => jsonResponse([]),
  });
  renderApp();
  await userEvent.click(screen.getByRole("tab", { name: /register/i }));
  await userEvent.type(screen.getByLabelText(/email/i), "a@b.com");
  await userEvent.type(screen.getByLabelText(/password/i), "password123");
  await userEvent.click(screen.getByRole("button", { name: /create account/i }));
  expect(await screen.findByRole("button", { name: /logout/i })).toBeInTheDocument();
  expect(localStorage.getItem("agent_token")).toBe("jwt-456");
});

test("failed login shows the server error", async () => {
  localStorage.clear();
  stubFetch({
    "POST /api/auth/login": () =>
      jsonResponse({ error: "invalid email or password" }, 401),
  });
  renderApp();
  await userEvent.type(screen.getByLabelText(/email/i), "a@b.com");
  await userEvent.type(screen.getByLabelText(/password/i), "wrongwrong");
  await userEvent.click(screen.getByRole("button", { name: /log in/i }));
  expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
});

test("a stored token skips the auth screen", async () => {
  localStorage.setItem("agent_token", "jwt-789");
  localStorage.setItem("agent_email", "a@b.com");
  stubFetch({ "GET /api/conversations": () => jsonResponse([]) });
  renderApp();
  expect(await screen.findByRole("button", { name: /logout/i })).toBeInTheDocument();
});
