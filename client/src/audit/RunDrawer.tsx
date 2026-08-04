import CloseIcon from "@mui/icons-material/Close";
import DownloadIcon from "@mui/icons-material/Download";
import { Box, Button, Drawer, IconButton, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { api } from "../api";
import TracePanel from "../trace/TracePanel";
import type { RunDetail } from "../types";

interface Props {
  runId: number | null;
  onClose: () => void;
}

export default function RunDrawer({ runId, onClose }: Props) {
  const [detail, setDetail] = useState<RunDetail | null>(null);

  useEffect(() => {
    setDetail(null);
    if (runId != null) {
      api.getRun(runId).then(setDetail).catch(() => {});
    }
  }, [runId]);

  const download = () => {
    if (!detail) return;
    const blob = new Blob([JSON.stringify(detail, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `run-${detail.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Drawer anchor="right" open={runId != null} onClose={onClose}>
      <Box sx={{ width: 460, maxWidth: "90vw" }}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ p: 2, pb: 0 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Run #{runId}
          </Typography>
          <Button
            size="small"
            startIcon={<DownloadIcon />}
            onClick={download}
            disabled={!detail}
          >
            Download JSON
          </Button>
          <IconButton onClick={onClose} aria-label="close">
            <CloseIcon />
          </IconButton>
        </Stack>
        <TracePanel
          panel={
            detail
              ? {
                  runId: detail.id,
                  status: detail.status,
                  steps: detail.steps,
                  pendingAction: detail.pending_action,
                  totalLatencyMs: detail.total_latency_ms,
                }
              : null
          }
          busy={false}
          onConfirm={() => {}}
        />
      </Box>
    </Drawer>
  );
}
