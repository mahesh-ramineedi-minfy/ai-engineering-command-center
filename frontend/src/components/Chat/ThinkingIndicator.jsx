import { useEffect, useState } from "react";

const STAGES = [
  "investigating across sources",
  "correlating signals",
  "drafting summary",
];

export default function ThinkingIndicator() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStage((s) => Math.min(s + 1, STAGES.length - 1));
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="message-row">
      <div className="message-bubble message-bubble--assistant message-bubble--loading">
        <span>{STAGES[stage]}</span>
        <span className="typing-dots">
          <span className="typing-dots__dot" />
          <span className="typing-dots__dot" />
          <span className="typing-dots__dot" />
        </span>
      </div>
    </div>
  );
}
