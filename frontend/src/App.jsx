import ChatWindow from "./components/Chat/ChatWindow";
import StatusBar from "./components/StatusBar/StatusBar";
import LoginPage from "./components/Auth/LoginPage";
import Logo from "./components/Logo";
import { AuthProvider, useAuth } from "./context/AuthContext";
import "./App.css";

function AppShell() {
  const { status, user, logout } = useAuth();

  if (status === "loading") return <div className="app-loading">Loading…</div>;
  if (status === "unauthenticated") return <LoginPage />;

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__brand">
          <Logo />
          <h1>AI Engineering Command Center</h1>
        </div>
        <div className="app-header__right">
          <StatusBar />
          {user && <span className="app-header__user">{user.email}</span>}
          <button className="app-header__logout" onClick={logout}>
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        <ChatWindow />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
