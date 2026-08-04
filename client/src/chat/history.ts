import type { ConversationHistory, RunSummary, UiMessage } from "../types";

export function pairHistory(history: ConversationHistory): UiMessage[] {
  const runByUserMessage = new Map<number, RunSummary>(
    history.runs.map((r) => [r.user_message_id, r])
  );
  const out: UiMessage[] = [];
  let pendingRun: RunSummary | undefined;
  for (const m of history.messages) {
    if (m.role === "user") {
      pendingRun = runByUserMessage.get(m.id);
      out.push({ role: "user", content: m.content });
    } else {
      out.push({ role: "assistant", content: m.content, runId: pendingRun?.id });
      pendingRun = undefined;
    }
  }
  return out;
}
