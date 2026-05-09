export const GEMINI_VOICES = ["Aoede", "Charon", "Leda", "Zephyr", "Kore", "Puck"] as const;
export type GeminiVoice = (typeof GEMINI_VOICES)[number];

export const DEFAULT_GEMINI_VOICE: GeminiVoice = "Aoede";
