import { create } from "zustand";

interface SessionPayload {
  mode: string;
  user_profile: {
    user_id: string;
    language_level: string;
    target_role: string;
  };
}

interface TranscriptEntry {
  speaker: string;
  text: string;
  timestamp: number;
}

interface AgentDecisionEntry {
  provider: string | null;
  model: string | null;
  riskSummary: string | null;
  likelyRootCause: string | null;
  confidence: number | null;
  recommendedAction: {
    type: string;
    parameters: Record<string, unknown>;
  } | null;
  promptHash: string | null;
  gate: {
    verdict: "allow" | "block";
    reason: string;
    mlRiskScore: number;
    llmConfidence: number | null;
    decisionType: string | null;
    schemaValid: boolean;
  };
  timestamp: number;
}

interface SessionState {
  sessionId: string | null;
  mode: string | null;
  transcriptLog: TranscriptEntry[];
  agentDecisions: AgentDecisionEntry[];
  createSession: (payload: SessionPayload) => Promise<void>;
  appendTranscript: (entry: Omit<TranscriptEntry, "timestamp">) => void;
  appendAgentDecision: (entry: Omit<AgentDecisionEntry, "timestamp">) => void;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null,
  mode: null,
  transcriptLog: [],
  agentDecisions: [],
  createSession: async (payload: SessionPayload) => {
    const response = await fetch(`${API_URL}/api/v1/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.status}`);
    }
    const data = await response.json();
    set({ sessionId: data.session_id, mode: data.mode });
  },
  appendTranscript: (entry) =>
    set((state) => ({
      transcriptLog: [...state.transcriptLog, { ...entry, timestamp: Date.now() }]
    })),
  appendAgentDecision: (entry) =>
    set((state) => ({
      agentDecisions: [...state.agentDecisions, { ...entry, timestamp: Date.now() }]
    }))
}));
