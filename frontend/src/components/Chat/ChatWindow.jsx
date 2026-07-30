import { useRef, useEffect } from "react";
import { useChat } from "../../context/ChatContext";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import ThinkingIndicator from "./ThinkingIndicator";

export default function ChatWindow() {
  const { messages, loading, error, sendMessage, retry } = useChat();
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="chat-window">
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask me anything about delivery health across Jira, GitHub, CI/CD, and incidents.</p>
            <p className="chat-empty__hint">Pick a prompt from the sidebar to get started.</p>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} toolCalls={m.toolCalls} />
        ))}
        {loading && <ThinkingIndicator />}
        {error && (
          <div className="chat-error">
            {error.message}
            <button className="chat-error__retry" onClick={retry} disabled={loading}>
              Retry
            </button>
          </div>
        )}
      </div>
      <ChatInput onSend={sendMessage} disabled={loading} />
    </div>
  );
}
