import { Box, Snackbar, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { errMsg } from "../chat/AppPage";
import type { Conversation, RunFilters, RunsPage, RunStats } from "../types";
import ChartsRow from "./ChartsRow";
import RunsTable from "./RunsTable";
import StatsCards from "./StatsCards";

export default function AuditPage() {
  const { isAdmin } = useAuth();
  const [filters, setFilters] = useState<RunFilters>({ page: 1 });
  const [runsPage, setRunsPage] = useState<RunsPage | null>(null);
  const [stats, setStats] = useState<RunStats | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [snack, setSnack] = useState<string | null>(null);

  useEffect(() => {
    api.listConversations().then(setConversations).catch(() => {});
  }, []);

  useEffect(() => {
    api.listRuns(filters).then(setRunsPage).catch((e) => setSnack(errMsg(e)));
    api.getRunStats(filters).then(setStats).catch((e) => setSnack(errMsg(e)));
  }, [filters]);

  void selectedRunId;

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: "auto" }}>
      <Typography variant="h5" gutterBottom>
        Run audit
      </Typography>
      <StatsCards stats={stats} />
      <ChartsRow stats={stats} />
      <RunsTable
        page={runsPage}
        filters={filters}
        onFiltersChange={setFilters}
        conversations={conversations}
        isAdmin={isAdmin}
        onOpenRun={setSelectedRunId}
      />
      <Snackbar
        open={snack !== null}
        autoHideDuration={5000}
        onClose={() => setSnack(null)}
        message={snack ?? ""}
      />
    </Box>
  );
}
