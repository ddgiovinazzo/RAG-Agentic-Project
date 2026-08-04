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

interface Props {
  messages: UiMessage[];
  busy: boolean;
  disabled: boolean;
  draft: string;
  onDraftChange: (v: string) => void;
  onSend: () => void;
  onOpenRun: (runId: number) => void;
}

export default function ChatView({
  messages,
  busy,
  disabled,
  draft,
  onDraftChange,
  onSend,
  onOpenRun,
}: Props) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <Stack spacing={1.5} sx={{ flex: 1, overflowY: "auto", p: 2 }}>
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} onOpenRun={onOpenRun} />
        ))}
      </Stack>
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
