import {
  AppBar,
  Box,
  Button,
  Drawer,
  Snackbar,
  Toolbar,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { ApiError, api } from "../api";
import { useAuth } from "../auth/AuthContext";
import type { Conversation } from "../types";
import ConversationList from "./ConversationList";

const DRAWER_WIDTH = 260;

export function errMsg(err: unknown): string {
  return err instanceof ApiError ? err.message : "Network error — is the backend running?";
}

export default function AppPage() {
  const { email, logout } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [snack, setSnack] = useState<string | null>(null);

  useEffect(() => {
    api
      .listConversations()
      .then(setConversations)
      .catch((err) => setSnack(errMsg(err)));
  }, []);

  const newConversation = async () => {
    try {
      const created = await api.createConversation();
      setConversations((cs) => [...cs, { ...created, created_at: "" }]);
      setSelectedId(created.id);
    } catch (err) {
      setSnack(errMsg(err));
    }
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Triage Agent
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            {email}
          </Typography>
          <Button color="inherit" onClick={logout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <ConversationList
          conversations={conversations}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onNew={newConversation}
        />
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
        <Toolbar />
        <Box sx={{ p: 3 }}>
          <Typography color="text.secondary">
            {selectedId === null
              ? "Select or create a conversation to start."
              : `Conversation #${selectedId}`}
          </Typography>
        </Box>
      </Box>
      <Snackbar
        open={snack !== null}
        autoHideDuration={5000}
        onClose={() => setSnack(null)}
        message={snack ?? ""}
      />
    </Box>
  );
}
