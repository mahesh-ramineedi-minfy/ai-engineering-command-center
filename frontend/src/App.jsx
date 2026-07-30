import { useEffect, useState } from "react";
import ChatWindow from "./components/Chat/ChatWindow";
import Sidebar from "./components/Sidebar/Sidebar";
import LoginPage from "./components/Auth/LoginPage";
import LandingPage from "./components/Landing/LandingPage";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ChatProvider } from "./context/ChatContext";
import "./App.css";

function AppShell() {
  const { status } = useAuth();
  const [view, setView] = useState("landing");

  useEffect(() => {
    if (status === "unauthenticated") setView("landing");
  }, [status]);

  if (status === "loading") return <div className="app-loading">Loading…</div>;
  if (status === "unauthenticated") {
    return view === "login" ? (
      <LoginPage onBack={() => setView("landing")} />
    ) : (
      <LandingPage onLogin={() => setView("login")} />
    );
  }

  return (
    <ChatProvider>
      <div className="app-shell">
        <Sidebar />
        <main className="app-main">
          <ChatWindow />
        </main>
      </div>
    </ChatProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
