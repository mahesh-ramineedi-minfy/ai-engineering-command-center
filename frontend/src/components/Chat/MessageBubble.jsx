export default function MessageBubble({ role, content, toolCalls }) {
  const isUser = role === "user";
  return (
    <div className={`message-row ${isUser ? "message-row--user" : ""}`}>
      <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
        <p>{content}</p>
        {toolCalls && toolCalls.length > 0 && (
          <div className="tool-trace">
            {toolCalls.map((call, i) => (
              <span key={i} className="tool-trace__chip" title={call.summary}>
                {call.tool}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
