import Typography from "@mui/material/Typography";
import AuthPage from "./auth/AuthPage";
import { useAuth } from "./auth/AuthContext";

export default function App() {
  const { authed } = useAuth();
  return authed ? <Typography>Signed in</Typography> : <AuthPage />;
}
