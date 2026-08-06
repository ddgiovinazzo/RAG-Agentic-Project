import { useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Button,
  List,
  ListItemButton,
  ListItemText,
  IconButton,
  Box,
  TextField,
} from "@mui/material";
import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onRename: (id: number, newTitle: string) => void;
  onNew: () => void;
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onRename,
  onNew,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const startEditing = (c: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(c.id);
    setEditTitle(c.title);
  };

  const cancelEditing = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditingId(null);
    setEditTitle("");
  };

  const saveEditing = (id: number, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const trimmed = editTitle.trim();
    if (trimmed) {
      onRename(id, trimmed);
    }
    setEditingId(null);
    setEditTitle("");
  };

  return (
    <Box sx={{ p: 1 }}>
      <Button startIcon={<AddIcon />} fullWidth variant="outlined" onClick={onNew}>
        New conversation
      </Button>
      <List dense>
        {conversations.map((c) => {
          const isEditing = editingId === c.id;
          return (
            <ListItemButton
              key={c.id}
              selected={c.id === selectedId}
              onClick={() => onSelect(c.id)}
              sx={{ pr: isEditing ? 1 : 5, position: "relative" }}
            >
              {isEditing ? (
                <Box
                  sx={{ display: "flex", alignItems: "center", width: "100%", gap: 0.5 }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <TextField
                    fullWidth
                    size="small"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") saveEditing(c.id);
                      if (e.key === "Escape") cancelEditing();
                    }}
                    autoFocus
                    variant="outlined"
                    sx={{ flex: 1, minWidth: 0, "& .MuiInputBase-input": { py: 0.5, px: 1, fontSize: "0.875rem" } }}
                  />
                  <IconButton size="small" color="primary" onClick={(e) => saveEditing(c.id, e)}>
                    <CheckIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={cancelEditing}>
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </Box>
              ) : (
                <>
                  <ListItemText
                    primary={c.title}
                    sx={{ overflow: "hidden", textOverflow: "ellipsis" }}
                  />
                  <IconButton
                    size="small"
                    aria-label="rename conversation"
                    onClick={(e) => startEditing(c, e)}
                    sx={{
                      position: "absolute",
                      right: 4,
                      opacity: c.id === selectedId ? 1 : 0.4,
                      "&:hover": { opacity: 1 },
                    }}
                  >
                    <EditOutlinedIcon fontSize="small" />
                  </IconButton>
                </>
              )}
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );
}


