import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";
import SearchIcon from "@mui/icons-material/Search";

import {
  Button,
  List,
  ListItemButton,
  ListItemText,
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Typography,
} from "@mui/material";
import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  selectedId: number | null;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSelect: (id: number) => void;
  onNew: () => void;
}

export default function ConversationList({
  conversations,
  selectedId,
  searchQuery,
  onSearchChange,
  onSelect,
  onNew,
}: Props) {
  return (
    <Box sx={{ p: 1 }}>
      <Button startIcon={<AddIcon />} fullWidth variant="outlined" onClick={onNew}>
        New conversation
      </Button>
      <TextField
        size="small"
        fullWidth
        placeholder="Search titles & messages…"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        sx={{ mt: 1, mb: 0.5 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" color="action" />
            </InputAdornment>
          ),
          endAdornment: searchQuery ? (
            <InputAdornment position="end">
              <IconButton size="small" onClick={() => onSearchChange("")} aria-label="clear search">
                <CloseIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ) : null,
        }}
      />
      <List dense>
        {conversations.map((c) => (
          <ListItemButton
            key={c.id}
            selected={c.id === selectedId}
            onClick={() => onSelect(c.id)}
          >
            <ListItemText primary={c.title} sx={{ overflow: "hidden", textOverflow: "ellipsis" }} />
          </ListItemButton>
        ))}
        {conversations.length === 0 && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ p: 2, display: "block", textAlign: "center" }}
          >
            {searchQuery ? "No matching conversations" : "No conversations yet"}
          </Typography>
        )}
      </List>
    </Box>
  );
}


