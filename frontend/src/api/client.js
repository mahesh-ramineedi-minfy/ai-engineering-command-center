import { getAccessToken, setAccessToken, clearAccessToken, notifySessionExpired } from "./tokenStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function rawRequest(path, options = {}) {
  const token = getAccessToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  return fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers,
    ...options,
  });
}

async function parseOrThrow(response) {
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
  if (response.status === 204) return null;
  return response.json();
}

async function request(path, options = {}) {
  let response = await rawRequest(path, options);

  const isAuthEndpoint = path === "/api/auth/login" || path === "/api/auth/refresh";
  if (response.status === 401 && !isAuthEndpoint) {
    try {
      const refreshed = await refresh();
      setAccessToken(refreshed.access_token);
      response = await rawRequest(path, options);
    } catch {
      clearAccessToken();
      notifySessionExpired();
      throw new Error("Session expired — please log in again.");
    }
  }

  return parseOrThrow(response);
}

export function login(email, password) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// Refresh rotates the token server-side (old jti revoked, new one issued), so
// concurrent callers (React StrictMode's double-invoked mount effect, multiple
// browser tabs loading at once, or two 401s racing each other into a retry)
// must share one in-flight request rather than each firing their own — two
// overlapping rotations trip the server's reuse-detection and revoke the
// session that was just issued.
let refreshPromise = null;

export function refresh() {
  if (!refreshPromise) {
    refreshPromise = request("/api/auth/refresh", { method: "POST" }).finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export function logout() {
  return request("/api/auth/logout", { method: "POST" });
}

export function getMe() {
  return request("/api/auth/me");
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

export function listConversations() {
  return request("/api/chat");
}

export function getConversation(conversationId) {
  return request(`/api/chat/${conversationId}`);
}
