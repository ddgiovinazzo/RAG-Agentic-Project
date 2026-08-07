import SendIcon from "@mui/icons-material/Send";
import {
  Box,
  IconButton,
  LinearProgress,
  Stack,
  TextField,
} from "@mui/material";
import type { UiMessage } from "../types";
import MessageBubble from "./MessageBubble";
import PromptStarters from "./PromptStarters";

interface Props {
  messages: UiMessage[];
  busy: boolean;
  disabled: boolean;
  draft: string;
  onDraftChange: (v: string) => void;
  onSend: () => void;
  onSelectPrompt?: (prompt: string) => void;
  onOpenRun: (runId: number) => void;
}

export default function ChatView({
  messages,
  busy,
  disabled,
  draft,
  onDraftChange,
  onSend,
  onSelectPrompt,
  onOpenRun,
}: Props) {
  const handleStarterSelect = (prompt: string) => {
    if (onSelectPrompt) {
      onSelectPrompt(prompt);
    } else {
      onDraftChange(prompt);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      {messages.length === 0 ? (
        <Box sx={{ flex: 1, overflowY: "auto" }}>
          <PromptStarters onSelectPrompt={handleStarterSelect} />
        </Box>
      ) : (
        <Stack spacing={1.5} sx={{ flex: 1, overflowY: "auto", p: 2 }}>
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} onOpenRun={onOpenRun} />
          ))}
        </Stack>
      )}
      {busy && <LinearProgress />}
      <Box
        component="form"
        onSubmit={(e) => {
          e.preventDefault();
          onSend();
        }}
        sx={{ display: "flex", gap: 1, p: 1.5, borderTop: 1, borderColor: "divider" }}
      >
        <TextField
          fullWidth
          size="small"
          placeholder="Give the agent a goal…"
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          disabled={disabled}
        />
        <IconButton
          type="submit"
          color="primary"
          disabled={disabled || !draft.trim()}
          aria-label="send"
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}

