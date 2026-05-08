/**
 * Flat aliases over the generated openapi-typescript schemas.
 * Components import from here so refactors of the generator
 * don't ripple through every file.
 */

import type { components } from "./api-types";

type S = components["schemas"];

export type CallRead = S["CallRead"];
export type CallDetailRead = S["CallDetailRead"];
export type CallSummary = S["CallSummary"];
export type CallStatus = S["CallStatus"];
export type Intent = S["Intent"];
export type Severity = S["Severity"];
export type TranscriptSegmentRead = S["TranscriptSegmentRead"];
export type TranscriptRole = TranscriptSegmentRead["role"];
export type ToolInvocationRead = S["ToolInvocationRead"];
export type CustomerRead = S["CustomerRead"];
export type CustomerType = S["CustomerType"];
export type Address = S["Address"];
export type FirmaRead = S["FirmaRead"];
export type FirmaSettings = S["FirmaSettings"];
export type FirmaSettingsUpdate = S["FirmaSettingsUpdate"];
export type Trade = S["Trade"];
export type Plan = S["Plan"];
