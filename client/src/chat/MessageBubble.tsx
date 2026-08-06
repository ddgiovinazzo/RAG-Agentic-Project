import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import SearchIcon from "@mui/icons-material/Search";
import { Box, Chip, Paper, Typography } from "@mui/material";
import type { UiMessage } from "../types";

interface Props {
  message: UiMessage;
  onOpenRun: (runId: number) => void;
}

export default function MessageBubble({ message, onOpenRun }: Props) {
  const isUser = message.role === "user";
  return (
    <Box sx={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <Paper
        elevation={1}
        sx={{
          p: 1.5,
          maxWidth: "75%",
          bgcolor: isUser ? "primary.main" : "background.paper",
          color: isUser ? "primary.contrastText" : "text.primary",
        }}
      >
        <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
          {message.content}
        </Typography>
        {!isUser && message.awaitingConfirmation && (
          <Chip
            size="small"
            icon={<HourglassTopIcon />}
            label="waiting for your confirmation"
            sx={{ mt: 1 }}
          />
        )}
        {!isUser &&
          !message.awaitingConfirmation &&
          message.runId !== undefined &&
          message.stepCount != null &&
          message.stepCount > 0 && (
            <Chip
              size="small"
              icon={<SearchIcon />}
              data-testid={`trace-chip-${message.runId}`}
              onClick={() => onOpenRun(message.runId!)}
              label={`${message.stepCount} steps${
                message.totalLatencyMs != null
                  ? ` · ${(message.totalLatencyMs / 1000).toFixed(1)}s`
                  : ""
              }`}
              sx={{ mt: 1, cursor: "pointer" }}
            />
          )}

      </Paper>
    </Box>
  );
}
