import { useSessionStore } from "../state/sessionStore";

export function SessionHeader() {
  const { sessionId, mode } = useSessionStore();

  return (
    <header className="session-header">
      <div>
        <h1>VocaVerse Interview Studio</h1>
        <p>Mode: {mode}</p>
      </div>
      <div className="session-meta">
        <span>Session ID</span>
        <code>{sessionId}</code>
      </div>
    </header>
  );
}
