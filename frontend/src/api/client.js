const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    let message = body;
    try {
      message = JSON.parse(body).detail || body;
    } catch {
      // not JSON, use raw body
    }
    throw new Error(message);
  }
  return response.json();
}

export function sendChatMessage(message, conversationId) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
  });
}

export function getIntegrationStatus() {
  return request("/api/integrations/status");
}
