import { useEffect, useState } from "react";
import { getIntegrationStatus } from "../../api/client";

export default function StatusBar() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    getIntegrationStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  if (!status) return null;

  return (
    <div className="status-bar">
      {status.mock_mode && <span className="status-bar__mock-badge">MOCK DATA</span>}
      {status.sources.map((s) => (
        <span key={s.key} className={`status-pill ${s.configured ? "status-pill--live" : "status-pill--mock"}`}>
          {s.name}
        </span>
      ))}
    </div>
  );
}
