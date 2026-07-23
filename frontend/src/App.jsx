import ChatWindow from "./components/Chat/ChatWindow";
import StatusBar from "./components/StatusBar/StatusBar";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Engineering Command Center</h1>
        <StatusBar />
      </header>
      <main className="app-main">
        <ChatWindow />
      </main>
    </div>
  );
}
