import AddIcon from "@mui/icons-material/Add";
import {
  Button,
  List,
  ListItemButton,
  ListItemText,
  Box,
} from "@mui/material";
import type { Conversation } from "../types";

interface Props {
  conversations: Conversation[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onNew: () => void;
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNew,
}: Props) {
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
          >
            <ListItemText primary={c.title} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}
