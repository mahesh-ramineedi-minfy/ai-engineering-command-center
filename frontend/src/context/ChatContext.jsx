import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { sendChatMessage, listConversations, getConversation } from "../api/client";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversations, setConversations] = useState([]);

  // Bumped by every action that changes which conversation is "active"
  // (new chat, loading a past conversation, sending a message). An in-flight
  // request that resolves after the user has since moved on discards its
  // result instead of writing into whatever conversation is active by then.
  const activeRequestRef = useRef(0);

  const refreshConversations = useCallback(() => {
    listConversations()
      .then(setConversations)
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  const performSend = useCallback(
    async (text) => {
      setError(null);
      setLoading(true);
      const isNewConversation = !conversationId;
      const requestToken = ++activeRequestRef.current;
      try {
        const res = await sendChatMessage(text, conversationId);
        if (activeRequestRef.current !== requestToken) return;
        setConversationId(res.conversation_id);
        setMessages((prev) => [...prev, { role: "assistant", content: res.reply, toolCalls: res.tool_calls }]);
        if (isNewConversation) refreshConversations();
      } catch (err) {
        if (activeRequestRef.current !== requestToken) return;
        setError({ message: err.message, text });
      } finally {
        if (activeRequestRef.current === requestToken) setLoading(false);
      }
    },
    [conversationId, refreshConversations]
  );

  const sendMessage = useCallback(
    (text) => {
      setMessages((prev) => [...prev, { role: "user", content: text }]);
      performSend(text);
    },
    [performSend]
  );

  const retry = useCallback(() => {
    if (error?.text) performSend(error.text);
  }, [error, performSend]);

  const startNewChat = useCallback(() => {
    activeRequestRef.current++;
    setConversationId(null);
    setMessages([]);
    setError(null);
    setLoading(false);
  }, []);

  const loadConversation = useCallback(async (id) => {
    const requestToken = ++activeRequestRef.current;
    setError(null);
    setLoading(true);
    try {
      const res = await getConversation(id);
      if (activeRequestRef.current !== requestToken) return;
      setConversationId(res.id);
      setMessages(res.messages.map((m) => ({ role: m.role, content: m.content })));
    } catch (err) {
      if (activeRequestRef.current !== requestToken) return;
      setError({ message: err.message, text: null });
    } finally {
      if (activeRequestRef.current === requestToken) setLoading(false);
    }
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        conversationId,
        loading,
        error,
        conversations,
        sendMessage,
        retry,
        startNewChat,
        loadConversation,
        refreshConversations,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
