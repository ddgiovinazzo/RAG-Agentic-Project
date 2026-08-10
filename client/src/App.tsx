import AuthPage from "./auth/AuthPage";
import { useAuth } from "./auth/AuthContext";
import AppPage from "./chat/AppPage";

export default function App() {
  const { authed } = useAuth();
  return authed ? <AppPage /> : <AuthPage />;
}
