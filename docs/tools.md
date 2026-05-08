# Tool catalog

The 12 functions Gemini Live can invoke during a call. Source of truth: `backend/src/svarsa/tools/schemas.py`.

Each tool has typed args + result Pydantic models, a Swedish description visible to the model, and a handler in `tools/handlers.py` that routes to a `services/*` function.

## When to add or change a tool

1. Update `schemas.py` (Args + Result models).
2. Update the entry in `TOOL_DESCRIPTIONS` in `declarations.py` — the description is the AI's only hint about *when* to call.
3. Update the handler in `handlers.py` — keep it thin; offload logic to a service.
4. Update tests in `tests/test_tools_handlers.py`.
5. Run `uv run dump-openapi && cd ../web && pnpm gen:api` if the args/result shape is also exposed via REST.

## Catalog

### `lookup_customer`

Slå upp en kund i firmans system baserat på telefonnummer eller org-nummer.

- **When:** First turn (CLI lookup), or when caller volunteers a name/org.
- **Args:** `phone_number?` (E.164 +46), `org_number?` (`XXXXXX-XXXX`), `name_query?` (last resort).
- **Returns:** `{found, customer_id?, name?, type?, last_job_summary?, open_jobs[], notes?}`.

### `triage_emergency`

Bedöm om problemet är akut.

- **When:** Caller describes a problem and you need a routing decision.
- **Args:** `problem_description: str`, `trade: Trade`, `indicators_present: EmergencyIndicator[]`.
- **Returns:** `{is_emergency, severity (critical|high|medium|low), recommended_action, reasoning_sv}`.
- **Backed by** `services.triage_service` — rule-based classifier; see PRD §7.3.

### `check_availability`

Hämta lediga tider i kalendern.

- **When:** Customer wants to book planned work.
- **Args:** `duration_minutes`, `earliest_date`, `latest_date`, `required_skills[]`, `address?`.
- **Returns:** Up to 5 `{start_iso, end_iso, technician_id, technician_name, travel_buffer_min}`.

### `book_appointment`

Boka in jobbet.

- **When:** Only after the customer has explicitly confirmed time + address.
- **Args:** `customer_id`, `start_iso`, `duration_minutes`, `technician_id?`, `address`, `problem_summary_sv`, `rot_eligible`.
- **Returns:** `{booking_id, calendar_event_url, confirmation_sms_sent, confirmation_email_sent}`.

### `create_lead`

Skapa ny kund/lead.

- **When:** `lookup_customer` came back empty and the caller wants to book or get an offer.
- **Args:** `name`, `phone`, `type (private|company)`, optional email, address, org_number, problem_summary_sv, estimated_value_sek.
- **Returns:** `{customer_id, created}`.

### `escalate_to_owner`

Eskalera ärendet enligt firmans eskaleringskedja.

- **When:** Acute emergencies, or when the caller insists on a human.
- **Args:** `severity`, `reason_sv`, `customer_phone`, optional `customer_id`, `address`, `callback_window_sv`.
- **Returns:** `{escalation_id, contacted: phone[], next_in_chain_minutes}`.

### `send_sms_followup`

Skicka SMS.

- **Templates:** `booking_confirmation`, `emergency_ack`, `photo_upload_link`, `callback_promise`, `secure_form_link`.
- **Returns:** `{sent, sms_id}`.

### `request_photo_upload`

Generera foto-uppladdningslänk och skicka via SMS.

- **Args:** `to_phone`, `lead_or_customer_id`, `expires_hours` (default 168 = 7 days).
- **Returns:** `{upload_url, sms_sent}`.

### `lookup_job_status`

Slå upp status på pågående jobb.

- **When:** Existing customer asks about an open arbete.
- **Returns:** `{found, job_id?, status_sv?, summary_sv?}`.

### `check_rot_eligibility`

ROT-avdrag eligibility — pure function.

- **Rule:** `is_private_person ∧ owns_property ∧ property_age_years ≥ 5 ∧ work_type ∈ ROT_OK_LIST`.
- **Returns:** `{eligible, max_deduction_sek_estimate, caveats_sv}`.

### `transfer_to_human`

Koppla samtalet till en människa.

- **When:** Caller explicitly requests, AI determines a human is available.
- **Args:** `target ∈ {owner_mobile, office, on_call_technician, external_answering_service}`, `context_summary_sv`.

### `take_message`

Sista utvägen.

- **Args:** `caller_phone`, `topic_sv`, `urgency`, optional name and callback preference.
- **Returns:** `{message_id, forwarded_to_user_id?}`.

## Hard rules from PRD §7.2 / §7.3

The tool catalog is paired with the system prompt (`bridge/system_prompt.py`). Even if the AI has a tool available, the prompt forbids:

- Inventing prices (booking always defers to a quote).
- Collecting personnummer or kortnummer over voice.
- Inventing technician names.
- Scheduling without a `check_availability` confirmation.

Eval (Phase 1) gates these behaviors on a held-out test set.
