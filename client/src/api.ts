import type {
  Conversation,
  ConversationHistory,
  RunDetail,
  RunFilters,
  RunOutcome,
  RunsPage,
  RunStats,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let token: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setToken(t: string | null) {
  token = t;
}

export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler;
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(path, { ...options, headers });
  let body: unknown = null;
  try {
    body = await resp.json();
  } catch {
    body = null;
  }
  if (!resp.ok) {
    if (resp.status === 401 && onUnauthorized) onUnauthorized();
    const message =
      body && typeof body === "object" && "error" in body
        ? String((body as { error: unknown }).error)
        : `HTTP ${resp.status}`;
    throw new ApiError(resp.status, message);
  }
  return body as T;
}

function runQuery(filters: RunFilters, includePage: boolean): string {
  const p = new URLSearchParams();
  if (filters.status) p.set("status", filters.status);
  if (filters.conversationId) p.set("conversation_id", String(filters.conversationId));
  if (filters.dateFrom) p.set("date_from", filters.dateFrom);
  if (filters.dateTo) p.set("date_to", filters.dateTo);
  if (filters.userEmail) p.set("user_email", filters.userEmail);
  if (includePage && filters.page) p.set("page", String(filters.page));
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const api = {
  register: (email: string, password: string) =>
    apiFetch<{ id: number; email: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    apiFetch<{ token: string; email?: string; is_admin?: boolean }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  listConversations: (q?: string) =>
    apiFetch<Conversation[]>(
      q ? `/api/conversations?q=${encodeURIComponent(q)}` : "/api/conversations"
    ),

  createConversation: (title?: string) =>
    apiFetch<{ id: number; title: string }>("/api/conversations", {
      method: "POST",
      body: JSON.stringify(title ? { title } : {}),
    }),
  sendMessage: (convId: number, content: string) =>
    apiFetch<RunOutcome>(`/api/conversations/${convId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  getHistory: (convId: number) =>
    apiFetch<ConversationHistory>(`/api/conversations/${convId}/messages`),
  confirmRun: (runId: number, approved: boolean) =>
    apiFetch<RunOutcome>(`/api/runs/${runId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ approved }),
    }),
  getRun: (runId: number) => apiFetch<RunDetail>(`/api/runs/${runId}`),
  listRuns: (filters: RunFilters) =>
    apiFetch<RunsPage>(`/api/runs${runQuery(filters, true)}`),
  getRunStats: (filters: RunFilters) =>
    apiFetch<RunStats>(`/api/runs/stats${runQuery(filters, false)}`),
};
