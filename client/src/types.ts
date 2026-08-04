export interface Conversation {
  id: number;
  title: string;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface TraceStep {
  seq: number;
  kind: "llm_call" | "tool_call" | string;
  tool_name: string | null;
  arguments: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  latency_ms: number | null;
  llm_messages?: unknown[] | null;
}

export interface PendingAction {
  id: number;
  tool: string;
  arguments: Record<string, unknown>;
}

export interface RunOutcome {
  run_id: number;
  status: "completed" | "failed" | "declined" | "needs_confirmation" | string;
  answer?: string;
  pending_action?: PendingAction;
  trace: TraceStep[];
}

export interface RunDetail {
  id: number;
  status: string;
  model: string | null;
  total_latency_ms: number | null;
  created_at: string;
  steps: TraceStep[];
}

export interface RunSummary {
  id: number;
  user_message_id: number;
  status: string;
}

export interface ConversationHistory {
  messages: ChatMessage[];
  runs: RunSummary[];
}

export interface UiMessage {
  role: "user" | "assistant";
  content: string;
  runId?: number;
  stepCount?: number;
  totalLatencyMs?: number | null;
  awaitingConfirmation?: boolean;
}

export interface PanelState {
  runId: number;
  status: string;
  steps: TraceStep[];
  pendingAction?: PendingAction;
  totalLatencyMs?: number | null;
}
