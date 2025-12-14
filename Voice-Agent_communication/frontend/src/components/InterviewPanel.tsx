import { useEffect } from "react";
import { AvatarCanvas } from "./avatar/AvatarCanvas";
import { useSessionStore } from "../state/sessionStore";
import { useSpeechPipeline } from "../hooks/useSpeechPipeline";

export function InterviewPanel() {
  const { transcriptLog, agentDecisions } = useSessionStore();
  const { startRecording, stopRecording, isRecording } = useSpeechPipeline();

  useEffect(() => {
    void startRecording();
    return () => {
      void stopRecording();
    };
  }, [startRecording, stopRecording]);

  return (
    <div className="interview-panel">
      <div className="avatar-column">
        <AvatarCanvas />
        <button onClick={() => (isRecording ? stopRecording() : startRecording())} className="record-btn">
          {isRecording ? "Stop" : "Start"} Recording
        </button>
      </div>
      <div className="conversation-column">
        <section>
          <h2>Transcript</h2>
          <ul>
            {transcriptLog.map((entry) => (
              <li key={entry.timestamp}>
                <strong>{entry.speaker}:</strong> {entry.text}
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2>Agent Decisions</h2>
          <ul>
            {agentDecisions.map((entry) => (
              <li key={entry.timestamp}>
                <div className="agent-decision-header">
                  <span className="agent-sig">{entry.provider ?? "Unknown"} · {entry.model ?? "Unknown"}</span>
                  <span className={`agent-verdict agent-verdict-${entry.gate.verdict}`}>
                    {entry.gate.verdict.toUpperCase()}
                  </span>
                </div>
                <p className="agent-risk">{entry.riskSummary ?? "No risk summary returned"}</p>
                <p className="agent-root">Root cause: {entry.likelyRootCause ?? "Unavailable"}</p>
                {entry.recommendedAction ? (
                  <p className="agent-action">
                    Recommended action: <strong>{entry.recommendedAction.type}</strong>
                  </p>
                ) : null}
                <div className="agent-meta">
                  <span>Confidence: {entry.confidence !== null && entry.confidence !== undefined ? `${(entry.confidence * 100).toFixed(1)}%` : "n/a"}</span>
                  <span>Risk: {(entry.gate.mlRiskScore * 100).toFixed(1)}%</span>
                  <span>Gate reason: {entry.gate.reason}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
