import { useCallback, useRef, useState } from "react";
import { useSessionStore } from "../state/sessionStore";

const BACKEND_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function useSpeechPipeline() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [isRecording, setRecording] = useState(false);
  const { sessionId, appendTranscript, appendAgentDecision } = useSessionStore();

  const stopRecording = useCallback(async () => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return;

    return new Promise<void>((resolve) => {
      recorder.addEventListener(
        "stop",
        async () => {
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          chunksRef.current = [];

          const formData = new FormData();
          formData.append("session_id", sessionId ?? "");
          formData.append("file", blob, "capture.webm");

          try {
            const response = await fetch(`${BACKEND_URL}/api/v1/speech/transcribe?session_id=${sessionId}`, {
              method: "POST",
              body: formData
            });
            if (!response.ok) {
              throw new Error(`Transcription failed: ${response.status}`);
            }
            const payload: {
              transcript: string;
              agent_decision?: {
                provider: string;
                model: string;
                risk_summary: string;
                likely_root_cause: string;
                confidence: number;
                recommended_action: {
                  type: string;
                  parameters: Record<string, unknown>;
                };
                prompt_hash: string;
              } | null;
              gate_result?: {
                verdict: "allow" | "block";
                reason: string;
                ml_risk_score: number;
                llm_confidence: number | null;
                decision_type: string | null;
                provider: string | null;
                model: string | null;
                schema_valid: boolean;
              } | null;
            } = await response.json();
            appendTranscript({ speaker: "user", text: payload.transcript });
            if (payload.agent_decision || payload.gate_result) {
              appendAgentDecision({
                provider: payload.agent_decision?.provider ?? payload.gate_result?.provider ?? null,
                model: payload.agent_decision?.model ?? payload.gate_result?.model ?? null,
                riskSummary: payload.agent_decision?.risk_summary ?? null,
                likelyRootCause: payload.agent_decision?.likely_root_cause ?? null,
                confidence: payload.agent_decision?.confidence ?? payload.gate_result?.llm_confidence ?? null,
                recommendedAction: payload.agent_decision
                  ? {
                      type: payload.agent_decision.recommended_action.type,
                      parameters: payload.agent_decision.recommended_action.parameters
                    }
                  : null,
                promptHash: payload.agent_decision?.prompt_hash ?? payload.gate_result?.prompt_hash ?? null,
                gate: {
                  verdict: payload.gate_result?.verdict ?? "block",
                  reason: payload.gate_result?.reason ?? "missing_gate",
                  mlRiskScore: payload.gate_result?.ml_risk_score ?? 0,
                  llmConfidence: payload.gate_result?.llm_confidence ?? null,
                  decisionType: payload.gate_result?.decision_type ?? null,
                  schemaValid: payload.gate_result?.schema_valid ?? false
                }
              });
            }
          } catch (error) {
            console.error("Audio pipeline error", error);
          }
          setRecording(false);
          resolve();
        },
        { once: true }
      );
      recorder.stop();
    });
  }, [appendAgentDecision, appendTranscript, sessionId]);

  const startRecording = useCallback(async () => {
    if (isRecording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.start();
      setRecording(true);
    } catch (error) {
      console.error("Unable to start recording", error);
    }
  }, [isRecording]);

  return {
    startRecording,
    stopRecording,
    isRecording
  };
}
