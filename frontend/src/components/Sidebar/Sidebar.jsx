import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";
import StatusBar from "../StatusBar/StatusBar";
import Logo from "../Logo";

const SUGGESTION_GROUPS = [
  {
    title: "Sprint & Delivery",
    prompts: ["What's our biggest release risk this sprint?"],
  },
  {
    title: "Build & Deploy",
    prompts: ["Summarize deployment failures this week"],
  },
  {
    title: "Code Health",
    prompts: ["Are there any signs of technical debt piling up?"],
  },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { conversations, conversationId, sendMessage, startNewChat, loadConversation } = useChat();
  const [collapsed, setCollapsed] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <aside className={`sidebar ${collapsed ? "sidebar--collapsed" : ""}`}>
      <div className="sidebar__top">
        {!collapsed && (
          <div className="sidebar__brand">
            <Logo size={22} />
            <span>Command Center</span>
          </div>
        )}
        <button
          className="sidebar__toggle"
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>

      <button className="sidebar__new-chat" onClick={startNewChat} title="New chat">
        <span className="sidebar__new-chat-icon">+</span>
        {!collapsed && <span>New chat</span>}
      </button>

      {!collapsed && (
        <div className="sidebar__scroll">
          <div className="sidebar__suggestions">
            {SUGGESTION_GROUPS.map((group) => (
              <div className="sidebar__suggestion-group" key={group.title}>
                <div className="sidebar__section-title">{group.title}</div>
                {group.prompts.map((prompt) => (
                  <button key={prompt} className="sidebar__suggestion" onClick={() => sendMessage(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            ))}
          </div>

          <div className="sidebar__history">
            <div className="sidebar__section-title">Recent chats</div>
            {conversations.length === 0 && <p className="sidebar__history-empty">No conversations yet</p>}
            {conversations.map((c) => (
              <button
                key={c.id}
                className={`sidebar__history-item ${c.id === conversationId ? "sidebar__history-item--active" : ""}`}
                onClick={() => loadConversation(c.id)}
                title={c.title}
              >
                {c.title}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="sidebar__footer">
        {!collapsed && (
          <div className="sidebar__sources">
            <button
              className="sidebar__sources-toggle"
              onClick={() => setSourcesOpen((o) => !o)}
              aria-expanded={sourcesOpen}
            >
              <span>Sources</span>
              <span className="sidebar__sources-chevron">{sourcesOpen ? "▾" : "▸"}</span>
            </button>
            {sourcesOpen && (
              <div className="sidebar__sources-body">
                <StatusBar />
              </div>
            )}
          </div>
        )}
        {!collapsed && user && <span className="sidebar__user">{user.email}</span>}
        <button className="sidebar__logout" onClick={logout} title="Log out">
          {collapsed ? "⏻" : "Log out"}
        </button>
      </div>
    </aside>
  );
}
