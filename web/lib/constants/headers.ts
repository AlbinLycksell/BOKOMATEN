export const HttpHeader = {
  FIRMA_ID: "X-Firma-Id",
  INTERNAL_TOKEN: "X-Internal-Token",
  CONTENT_TYPE: "Content-Type",
  AUTHORIZATION: "Authorization",
} as const;

export const ContentType = {
  JSON: "application/json",
} as const;

export const FetchCache = {
  NO_STORE: "no-store",
} as const;
