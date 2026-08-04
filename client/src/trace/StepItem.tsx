import BuildIcon from "@mui/icons-material/Build";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PsychologyIcon from "@mui/icons-material/Psychology";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Stack,
  Typography,
} from "@mui/material";
import type { TraceStep } from "../types";

function Section({ label, value }: { label: string; value: unknown }) {
  return (
    <Box sx={{ mb: 1 }}>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ textTransform: "uppercase" }}
      >
        {label}
      </Typography>
      <Box
        component="pre"
        sx={{
          m: 0,
          p: 1,
          fontSize: 12,
          overflowX: "auto",
          bgcolor: "action.hover",
          borderRadius: 1,
        }}
      >
        {JSON.stringify(value, null, 2)}
      </Box>
    </Box>
  );
}

export default function StepItem({ step }: { step: TraceStep }) {
  const isLlm = step.kind === "llm_call";
  const title = isLlm ? "model call" : (step.tool_name ?? step.kind);
  return (
    <Accordion disableGutters>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} alignItems="center">
          {isLlm ? (
            <PsychologyIcon fontSize="small" color="secondary" />
          ) : (
            <BuildIcon fontSize="small" color="primary" />
          )}
          <Typography variant="body2">
            #{step.seq} · {title}
          </Typography>
          {step.latency_ms != null && (
            <Typography variant="caption" color="text.secondary">
              {step.latency_ms} ms
            </Typography>
          )}
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        {step.arguments != null && <Section label="arguments" value={step.arguments} />}
        {step.result != null && <Section label="result" value={step.result} />}
        {step.llm_messages != null && (
          <Section label="model input" value={step.llm_messages} />
        )}
      </AccordionDetails>
    </Accordion>
  );
}
