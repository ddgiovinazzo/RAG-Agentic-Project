import { useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Button,
  List,
  ListItemButton,
  ListItemText,
  IconButton,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number, e: React.MouseEvent) => void;
  onNew: () => void;
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onDelete,
  onNew,
}: Props) {
  const [confirmId, setConfirmId] = useState<number | null>(null);

  const handleOpenConfirm = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setConfirmId(id);
  };

  const handleConfirmDelete = (e: React.MouseEvent) => {
    if (confirmId !== null) {
      onDelete(confirmId, e);
      setConfirmId(null);
    }
  };

  const handleCloseDialog = () => {
    setConfirmId(null);
  };

  return (
    <Box sx={{ p: 1 }}>
      <Button startIcon={<AddIcon />} fullWidth variant="outlined" onClick={onNew}>
        New conversation
      </Button>
      <List dense>
        {conversations.map((c) => (
          <ListItemButton
            key={c.id}
            selected={c.id === selectedId}
            onClick={() => onSelect(c.id)}
            sx={{ pr: 5, position: "relative" }}
          >
            <ListItemText primary={c.title} sx={{ overflow: "hidden", textOverflow: "ellipsis" }} />
            <IconButton
              size="small"
              edge="end"
              aria-label="delete conversation"
              onClick={(e) => handleOpenConfirm(c.id, e)}
              sx={{
                position: "absolute",
                right: 8,
                opacity: c.id === selectedId ? 1 : 0.4,
                "&:hover": { opacity: 1, color: "error.main" },
              }}
            >
              <DeleteOutlineIcon fontSize="small" />
            </IconButton>
          </ListItemButton>
        ))}
      </List>

      <Dialog open={confirmId !== null} onClose={handleCloseDialog}>
        <DialogTitle>Delete Conversation?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this conversation? All message and step history for this run will be permanently removed.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button color="error" variant="contained" onClick={handleConfirmDelete} autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}


