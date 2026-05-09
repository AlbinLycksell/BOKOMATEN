import { BridgeBye } from "./ws";

export const VoiceTestState = {
  IDLE: "idle",
  CHECKING: "checking",
  REQUESTING_MIC: "requesting_mic",
  CONNECTING: "connecting",
  LIVE: "live",
  ENDING: "ending",
  ENDED: "ended",
} as const;
export type VoiceTestState = (typeof VoiceTestState)[keyof typeof VoiceTestState];

export const BRIDGE_BYE_MESSAGES_SV: Record<BridgeBye, string> = {
  [BridgeBye.GEMINI_AUTH_FAILED]:
    "Gemini avvisade autentiseringen. GEMINI_API_KEY är ogiltig, utgången, eller i fel projekt.",
  [BridgeBye.GEMINI_MODEL_UNAVAILABLE]:
    "Gemini-modellen är otillgänglig för det här projektet. Kontrollera SWITCHBOARD_GEMINI_MODEL.",
  [BridgeBye.GEMINI_QUOTA_EXHAUSTED]:
    "Gemini-quota är slut för det här projektet eller minuten. Vänta en stund eller höj rate-limit.",
  [BridgeBye.GEMINI_CONNECT_FAILED]:
    "Bryggan kunde inte ansluta till Gemini Live. Vanligtvis nätverk eller GEMINI_API_KEY saknas.",
  [BridgeBye.UNKNOWN_FIRMA]: "Okänd firma — bridge fick fel firma_id.",
};

export const InboxFilter = {
  ALL: "all",
  AKUT: "akut",
  NEEDS_FOLLOWUP: "needs_followup",
  HANDLED: "handled",
} as const;
export type InboxFilter = (typeof InboxFilter)[keyof typeof InboxFilter];
