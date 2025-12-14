import { useEffect, useState } from "react";
import { InterviewPanel } from "./components/InterviewPanel";
import { SessionHeader } from "./components/SessionHeader";
import { useSessionStore } from "./state/sessionStore";

export default function App() {
  const { sessionId, createSession } = useSessionStore();
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      if (sessionId) return;
      setLoading(true);
      setError(null);
      try {
        await createSession({
          mode: "mock_interview",
          user_profile: {
            user_id: "demo-user",
            language_level: "intermediate",
            target_role: "software_engineer"
          }
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create session");
      } finally {
        setLoading(false);
      }
    }

    bootstrap();
  }, [createSession, sessionId]);

  if (isLoading) {
    return <div className="app-shell">Bootstrapping session...</div>;
  }

  if (error) {
    return <div className="app-shell error">{error}</div>;
  }

  return (
    <div className="app-shell">
      <SessionHeader />
      <InterviewPanel />
    </div>
  );
}
