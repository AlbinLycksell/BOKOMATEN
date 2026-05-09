export const AudioFormat = {
  PCM_16K: "pcm_16000",
  PCM_24K: "pcm_24000",
} as const;

export const AudioRate = {
  PCM_16K: 16_000,
  PCM_24K: 24_000,
} as const;

export const AudioContextState = {
  SUSPENDED: "suspended",
  RUNNING: "running",
  CLOSED: "closed",
} as const;

export const VoiceCaptureWorklet = {
  PATH: "/voice-capture-worklet.js",
  PROCESSOR_NAME: "voice-capture",
} as const;
