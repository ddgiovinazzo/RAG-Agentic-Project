import { afterEach, expect, test, vi } from "vitest";
import { ApiError, api, setOnUnauthorized, setToken } from "../api";
import { jsonResponse, stubFetch } from "./helpers";

afterEach(() => {
  vi.unstubAllGlobals();
  setToken(null);
  setOnUnauthorized(null);
});

test("login posts credentials and returns the token", async () => {
  const fetchMock = stubFetch({
    "POST /api/auth/login": () => jsonResponse({ token: "jwt-123" }),
  });
  const result = await api.login("a@b.com", "password123");
  expect(result).toEqual({ token: "jwt-123" });
  const init = fetchMock.mock.calls[0][1]!;
  expect(JSON.parse(init.body as string)).toEqual({
    email: "a@b.com",
    password: "password123",
  });
});

test("requests carry the bearer token once set", async () => {
  const fetchMock = stubFetch({
    "GET /api/conversations": () => jsonResponse([]),
  });
  setToken("jwt-123");
  await api.listConversations();
  const headers = fetchMock.mock.calls[0][1]!.headers as Record<string, string>;
  expect(headers["Authorization"]).toBe("Bearer jwt-123");
});

test("error responses throw ApiError with the server message", async () => {
  stubFetch({
    "POST /api/auth/login": () => jsonResponse({ error: "invalid email or password" }, 401),
  });
  await expect(api.login("a@b.com", "wrong")).rejects.toThrowError(
    "invalid email or password"
  );
  await api.login("a@b.com", "wrong").catch((e: ApiError) => {
    expect(e.status).toBe(401);
  });
});

test("401 triggers the onUnauthorized handler", async () => {
  stubFetch({
    "GET /api/conversations": () => jsonResponse({ error: "invalid or expired token" }, 401),
  });
  const handler = vi.fn();
  setOnUnauthorized(handler);
  await expect(api.listConversations()).rejects.toThrow();
  expect(handler).toHaveBeenCalledOnce();
});

test("confirmRun posts the approved boolean", async () => {
  const fetchMock = stubFetch({
    "POST /api/runs/7/confirm": () =>
      jsonResponse({ run_id: 7, status: "completed", answer: "done", trace: [] }),
  });
  await api.confirmRun(7, false);
  expect(JSON.parse(fetchMock.mock.calls[0][1]!.body as string)).toEqual({
    approved: false,
  });
});
