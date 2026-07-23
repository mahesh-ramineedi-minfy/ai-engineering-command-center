import { useRef, useState, useEffect } from "react";
import { sendChatMessage } from "../../api/client";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import ThinkingIndicator from "./ThinkingIndicator";

const SUGGESTIONS = [
  "What's our biggest release risk this sprint?",
  "Summarize deployment failures this week",
  "Are there any signs of technical debt piling up?",
];

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text) {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await sendChatMessage(text, conversationId);
      setConversationId(res.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, toolCalls: res.tool_calls }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask me anything about delivery health across Jira, GitHub, CI/CD, and incidents.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => handleSend(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} toolCalls={m.toolCalls} />
        ))}
        {loading && <ThinkingIndicator />}
        {error && <div className="chat-error">{error}</div>}
      </div>
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
