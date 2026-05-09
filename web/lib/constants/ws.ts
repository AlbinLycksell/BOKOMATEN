export const InboxEvent = {
  CALL_CREATED: "inbox.call.created",
  CALL_UPDATED: "inbox.call.updated",
} as const;
export type InboxEvent = (typeof InboxEvent)[keyof typeof InboxEvent];

export const BridgeWSEvent = {
  HELLO: "hello",
  AUDIO: "audio",
  SYNC: "sync",
  BYE: "bye",
  STOP: "stop",
  SENDING: "sending",
  LISTENING: "listening",
  INTERRUPT: "interrupt",
  TRANSCRIPT: "transcript",
} as const;
export type BridgeWSEvent = (typeof BridgeWSEvent)[keyof typeof BridgeWSEvent];

export const BridgeFrameField = {
  TYPE: "t",
  DATA: "data",
  REASON: "reason",
  ROLE: "role",
  TEXT: "text",
  FORMAT: "format",
  CALLID: "callid",
  FROM: "from",
  TO: "to",
} as const;

export const BridgeBye = {
  UNKNOWN_FIRMA: "unknown_firma",
  GEMINI_AUTH_FAILED: "gemini_auth_failed",
  GEMINI_MODEL_UNAVAILABLE: "gemini_model_unavailable",
  GEMINI_QUOTA_EXHAUSTED: "gemini_quota_exhausted",
  GEMINI_CONNECT_FAILED: "gemini_connect_failed",
} as const;
export type BridgeBye = (typeof BridgeBye)[keyof typeof BridgeBye];

export const BridgeQueryParam = {
  SOURCE: "source",
} as const;
