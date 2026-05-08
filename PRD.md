# PRD — Svarsa AI

**Product Requirements Document**

| Field | Value |
|---|---|
| Product name (working) | Svarsa AI |
| Document version | 0.9 — Draft for review |
| Document owner | Founding team |
| Status | In review |
| Last updated | 2026-05-08 |
| Target launch (closed beta) | 2026-09 |
| Target launch (GA) | 2026-12 |

---

## 1. Executive summary

Svarsa AI is a voice-first AI receptionist purpose-built for Swedish hantverkare — VVS-firmor, elektriker, snickare, plattsättare, and adjacent service trades — in the 1–10 anställda segment. It answers inbound phone calls 24/7 in natural Swedish using Google's **Gemini 3.1 Flash Live** model, triages each call in under 30 seconds, books work directly into the firm's existing calendar and affärssystem (Fortnox, Hantverksdata Next, Visma eEkonomi), and escalates true emergencies to the owner within 15 seconds via SMS and outbound call.

The product is explicitly **additive, not replacement**: it integrates with the bokföring/CRM the firm already uses, plus a thin "call operations" web/mobile app for the owner to see what's happened, listen to recordings, and act on follow-ups. The wedge is the captured akut-jobb, the missed offert-förfrågan, and the ten-minute-per-call admin tax that the owner is paying today by stopping work to answer the phone on a job site.

Pricing target is **1 495–2 995 SEK/mån** with a setup-avgift of 2–5 kSEK and a 30-day no-questions refund — designed to be an ROI-positive impulse purchase on the strength of one captured emergency call per quarter.

## 2. Problem statement

### 2.1 What we observed

Sole proprietors and small crews in the Swedish trades have a structural conflict: the work is done with hands, often in a customer's home, often in a noisy environment, often two-handed and dirty. The phone rings while they are in the middle of a soldered koppling, a 230V-anslutning, or a takpanna. They have three bad options: stop working (loses billable time), ignore the call (loses the lead), or answer with dirty hands while distracted (loses the quality of both interactions).

Industry data and our discovery interviews (n=27 firms across Stockholm, Göteborg, Skellefteå, and Malmö, January–April 2026) converge on a few numbers:

- **24–38%** of inbound calls go unanswered during weekday working hours
- **62–80%** of calls outside 07–17 go unanswered
- The typical converted **akut-jobb is worth 4–18 kSEK** (jourutryckning + work)
- The typical converted **planned offert is worth 30–250 kSEK** (badrumsrenovering, värmepumpsinstallation, omdragning av el)
- Owners self-report **40–90 minutes/day** spent on phone admin
- When a customer doesn't reach a hantverkare, **~70%** call a competitor within 30 minutes — the lead is lost, not deferred

### 2.2 Why now

Three forces converge in 2026 that didn't exist 18 months ago. First, **Gemini 3.1 Flash Live** (released March 26, 2026) is the first real-time speech model where end-to-end Swedish conversation is fluid enough — sub-800ms first-audio latency, native acoustic nuance handling, 90+ languages including Swedish — that the average ringing customer will not realize they are talking to an AI within the first 10 seconds, and will not care after that, provided the AI actually solves their problem. Earlier voice models (cascaded STT→LLM→TTS pipelines) had Swedish but felt robotic; Gemini 2.5 Native Audio was usable but stilted; 3.1 Flash Live crosses the threshold.

Second, **function calling on audio** has reached production reliability. Gemini 3.1 Flash Live scores 90.8% on ComplexFuncBench Audio (Google's multi-step tool-use benchmark), making it competent enough to actually book calendar slots, look up customers, and trigger SMS — not just chat.

Third, the Swedish hantverker-segment has finished its **digital baseline**: ~85% of firms with 3+ employees are already on Fortnox, Hantverksdata Next, or Visma — meaning we have integration targets, not change-management projects.

### 2.3 Why this hasn't been solved already

Generic AI receptionist products (Goodcall, Rosie, Synthflow, Vapi-built tools) are English-first, do not handle Swedish ROT-avdrag mechanics, do not integrate with Hantverksdata or Fortnox, and have no domain knowledge of jourärenden, OVK-besiktning, säker vatten-certifiering, or the subcontractor structure of Swedish trades. Generic Swedish svarstjänster (Telavox, Voxbone resellers) are human-staffed, expensive (>5 kSEK/mån), and do not book — they take a message. The product gap is a Swedish-native, trade-specific, booking-capable AI receptionist at hantverkare price points.

## 3. Goals and non-goals

### 3.1 Goals (v1)

The product must, at GA, accomplish all of the following without exception:

1. Answer inbound calls in natural Swedish within 2 rings, 24/7, with end-to-end first-audio latency under 1 200 ms p50 and under 2 000 ms p95.
2. Correctly classify every call into one of five intent buckets (akut, offertförfrågan, bokning av planerat arbete, befintlig kund-fråga, övrigt) with ≥92% accuracy on a held-out test set of 500 real Swedish calls.
3. Book planned-work appointments directly into Fortnox, Hantverksdata Next, Visma eEkonomi, and Google Calendar, with bidirectional sync.
4. Escalate true emergencies to the right human within 15 seconds via SMS + outbound call, following an owner-configured eskaleringskedja.
5. Capture leads (caller name, number, address, problem description, photos via SMS link) in a structured format that lands in the firm's CRM as a new prospect/projekt.
6. Produce, after each call, a structured Swedish summary delivered to the owner via SMS and the dashboard, with full transcript and audio recording link.
7. Comply with GDPR including recording consent disclosure ("Detta samtal kan spelas in för kvalitetsändamål"), EU data residency, DPA with all sub-processors, and a documented retention policy.
8. Run reliably at a per-call cost (telephony + Gemini + infrastructure) below **2,50 SEK** at typical call lengths (90 seconds median).

### 3.2 Non-goals (v1)

The following are out of scope and will be explicitly declined to scope-creep requests:

- Outbound cold-calling or telemarketing (regulatory and brand risk for v1)
- Replacing the customer's existing affärssystem or accounting platform
- Multi-tenant call-center workflows for firms >25 anställda (different product)
- Languages other than Swedish at GA (English added in v1.1, Finnish v1.2)
- Video/visual modality (Gemini supports it, but our use case is voice-only on PSTN)
- Voice cloning of the owner's actual voice (legal and trust risk; we use synthetic voices)
- Generative responses about pricing — quotes are taken, not given, by the AI
- AI-driven dispute resolution, complaint handling, or fakturafrågor with binding answers — these always escalate

### 3.3 Explicit anti-goals

We will not, even on customer request, build features that:

- Mimic the owner's voice without explicit, written consent and a verification flow
- Collect personnummer or sensitive payment data over voice (we use SMS-link to a verified web form for anything sensitive)
- Auto-quote prices on complex work (the AI will explicitly say "Magnus återkommer med en offert efter 17:00")
- Operate without a clear "this is an AI" disclosure on customer request

## 4. Success metrics

### 4.1 North-star metric

**Captured value per firm per month** = (booked jobs originating from AI-handled calls) × (average margin per job). Target: median customer captures ≥10 kSEK/mån net of subscription cost by month 3, ≥30 kSEK/mån by month 9.

### 4.2 Product KPIs

| Metric | Target (GA) | Measurement |
|---|---|---|
| Answer rate (calls picked up by AI) | ≥99,5% | Telephony logs |
| Time to first model audio | <1 200 ms p50, <2 000 ms p95 | Internal trace |
| Triage accuracy (5-class) | ≥92% | Weekly held-out eval |
| Booking completion rate (when intent = bokning) | ≥75% | Booking events / bokning intents |
| Emergency escalation latency | <15 s p95 | Trace from triage → SMS sent |
| Hallucination rate (off-policy or factually wrong) | <1% of calls | Sampled human review |
| Caller hangup-during-AI rate | <8% | Telephony logs |
| Post-call CSAT (SMS, 1–5) | ≥4,2 | SMS survey |
| Owner monthly NPS | ≥40 | In-app prompt |
| Per-call infra cost | <2,50 SEK median, <5 SEK p95 | Cost telemetry |
| Logo retention 12-mån | ≥85% | Billing |

### 4.3 Guardrail metrics

These are not optimized for, but watched for breach:

- **False-positive emergency rate** (AI escalates when it shouldn't) — must stay <5% to avoid owner alarm fatigue
- **False-negative emergency rate** (AI fails to escalate when it should) — must stay <0,5%, hard ceiling
- **GDPR incident count** — zero tolerance
- **Outbound SMS spam complaints** — <0,1% of SMS sent

## 5. Personas

### 5.1 Magnus, 47, VVS-företagare (primary buyer, "the owner")

Magnus owns Anderssons VVS AB in Bromma. Three anställda including himself, runs Hantverksdata Next for projekthantering and Fortnox for bokföring. Drives a panelbil, on a job site 80% of his working hours, hands often wet or in a kryputrymme. Has a kontorsmänniska, his sambo Lena, who handles roughly half of incoming calls when she has time — but she also has a halvtidsjobb. Magnus loses an estimated 6–10 kSEK/vecka on missed akut-samtal and unanswered offert-förfrågningar. He's tried two svarstjänster, both 4–6 kSEK/mån, both gave him useless messages 24 hours later. He wants something that actually books work and doesn't make him look like a clown to customers. Buys software based on what other VVS-firmor in his Facebook-grupp recommend; doesn't read marketing copy.

### 5.2 Lena, 44, kontor/administration (secondary user, "the back office")

Magnus's sambo, runs the kontor 20 timmar/vecka. She's the actual user of Fortnox, Hantverksdata, and the kalender. Her relationship to Svarsa AI is: morning coffee, she opens the dashboard, sees the 11 calls handled overnight and during yesterday afternoon, triages the 3 that need follow-up, books the 2 that didn't quite resolve, and gets on with invoicing. She is not technical but is competent. If our product wastes her time or creates double-bookings, she will kill it.

### 5.3 Alex, 28, jourtekniker (tertiary user, "the on-call")

Works for Magnus, takes the jourtelefon every other week. When Svarsa escalates an emergency, Alex is the human at the other end. He gets an SMS with structured info (address, problem, customer phone, when reported) and a "ring tillbaka"-button. If our escalation is unclear or duplicative, he will refuse to use the system.

### 5.4 Inger, 71, kund (the caller)

Discovered a vattenläcka under diskbänken. Found Anderssons VVS via Google Maps. Calls at 14:32 on a Tuesday. She does not know she is talking to an AI for the first 8 seconds; when she figures it out, she is mildly skeptical but mostly relieved that someone answered. She wants three things: to be heard, to know someone is coming, and to know roughly when. She does not want to navigate a meny, repeat herself, or be told to fill in a webform.

### 5.5 Karim, 35, B2B fastighetsförvaltare (the other caller archetype)

Manages 14 properties for a BRF. Calls Anderssons VVS to book OVK-besiktningar in three buildings, wants to consolidate dates. Knows what he wants, speaks in jargon, and gets annoyed at being forced to explain basics. Needs the AI to recognize him as a returning B2B kund within the first turn and skip the small talk.

## 6. User journeys

### 6.1 Inbound emergency call (akut)

Inger calls at 14:32. The number rings 1,5 times and Svarsa AI picks up.

> **Svarsa:** "Hej, du har kommit till Anderssons VVS, jag är deras digitala assistent. Hur kan jag hjälpa dig?"
>
> **Inger:** "Hej, jag har en vattenläcka under diskbänken, det rinner ner på golvet."
>
> **Svarsa** *(recognizes "läcka" + "rinner" → potential emergency)*: "Det låter akut. Är det mycket vatten — har du behövt stänga av vattnet?"
>
> **Inger:** "Ja, jag stängde av huvudkranen. Men det är ändå vått."
>
> **Svarsa:** "Bra att du stängt av. Vad är din adress?"
>
> **Inger:** "Storgatan 14, lägenhet 3, Bromma."
>
> **Svarsa:** "Tack. Och ditt namn och telefonnummer så Magnus kan ringa upp?"
>
> **Inger:** "Inger Svensson, du har mitt nummer."
>
> **Svarsa** *(verifies CLI matches existing kund)*: "Tack Inger. Magnus är på ett jobb just nu men jag skickar honom ditt ärende direkt. Han ringer upp inom 15 minuter. Du har stängt av vattnet, det är bra. Annars — sätt en hink under och håll koll. Stämmer det att jag återkommer på 070-XXX-XXXX?"
>
> **Inger:** "Ja det stämmer. Tack."
>
> **Svarsa:** "Vi hörs snart. Hej då."

In parallel, before the call ends, Svarsa has:

- Called `triage_emergency()` → confirmed emergency, severity high
- Called `lookup_customer("+46708...")` → found Inger as existing kund from a 2024 service
- Called `escalate_to_owner({customer_id, address, problem_summary, severity: "high", customer_audio_clip_url})` — fires SMS to Magnus *and* a phone call (configurable per-firma)
- Called `create_lead_or_update_job()` in Hantverksdata as "Akut: vattenläcka, kök, Inger Svensson"
- Called `send_sms_followup(to=Inger, template="emergency_ack")` — "Tack Inger, Magnus har fått ditt ärende och ringer upp inom 15 min. /Anderssons VVS"

Total elapsed: 38 seconds. Magnus's phone buzzes 11 seconds after Inger said "läcka".

### 6.2 Inbound quote request (offertförfrågan)

Karim, the BRF-förvaltare, calls.

> **Svarsa:** "Hej, du har kommit till Anderssons VVS …"
>
> **Karim:** "Hej, det är Karim på Brf Vasaliljan. Jag behöver boka in OVK i tre fastigheter."
>
> **Svarsa** *(`lookup_customer` finds match by org-nummer/phone)*: "Hej Karim, jag har dig här. Är det samma tre adresser som senast — Vasagatan 8, 10 och 12?"
>
> **Karim:** "Plus Karlbergsvägen 22 nu också."
>
> **Svarsa** *(`check_availability` for OVK-jobb, 4 stops, 2-3 days)*: "Då lägger jag in fyra adresser. Jag har Magnus disponibel den 15:e och 16:e maj på förmiddag, eller den 22:a hela dagen — vad funkar bäst?"
>
> **Karim:** "Den 22:a."
>
> **Svarsa:** "Bokat: den 22:a maj, 08:00–16:00, fyra OVK-besiktningar. Jag skickar dig en bekräftelse på SMS och e-post. Något mer?"
>
> **Karim:** "Nej, tack."

In the background: `book_appointment()` in Hantverksdata, mirror to Google Calendar, `send_sms_followup` and `send_email_followup` with kalenderfil (.ics).

### 6.3 Out-of-scope / dunno call

Caller asks something the AI shouldn't answer.

> **Caller:** "Vad kostar det att byta en blandare?"
>
> **Svarsa:** "Det beror helt på vilken blandare och var den sitter, så jag vill inte chansa på pris. Kan jag boka in en kostnadsfri offert där Magnus tittar på det? Det tar 15 minuter på plats."

The AI is explicitly trained never to invent prices. This is a hard-coded behavior in the system prompt and verified in eval.

### 6.4 Owner morning routine

08:00, Lena opens the Svarsa dashboard on her phone. Sees: 11 calls handled since 17:00 yesterday, 2 emergencies (both resolved by Magnus on-call), 4 bookings made, 3 leads to follow up, 2 informational with no action needed. Each call has a 2-sentence Swedish summary, full transcript, audio playback, and a "ring tillbaka" or "skicka offert"-knapp. Lena spends 12 minutes processing the queue. Pre-Svarsa, this was 90 minutes of phone-tag.

## 7. Functional requirements

### 7.1 Telephony layer

**FR-T-1.** The system must accept inbound calls on a Swedish E.164 number (+46…) provisioned through 46elks (primary) or Twilio (fallback/international). Each kund-firma gets one or more dedicated numbers, or alternatively configures call-forwarding (vidarekoppling) from their existing number to the Svarsa number.

**FR-T-2.** The system must support number-portability inbound (porta in befintligt nummer) for firms that want to keep their established number on Svarsa infrastructure. 46elks supports this for Swedish numbers.

**FR-T-3.** The system must play a brief verbal disclosure ("Detta samtal kan spelas in") at call connect, configurable per-firma, in line with GDPR Art. 6 and IMY (Integritetsskyddsmyndigheten) guidance.

**FR-T-4.** The system must support seamless handoff to a human (Magnus, Lena, jourtekniker, or external svarstjänst) via SIP-bridging or warm transfer. The AI must not "trap" callers.

**FR-T-5.** The system must support ringing-pattern policies: answer-on-no-pickup-after-N-rings (typical: 4 rings, ~12s); answer-immediately (always); answer-only-outside-office-hours; per-day-of-week schedules; helgdagsschema (Sveriges röda dagar autoloaded).

**FR-T-6.** The system must support outbound calls in defined scenarios only: (a) returning a missed call to confirm a booking, (b) calling the owner to escalate an emergency, (c) sending an outbound voicemail-drop to a customer who left a message and asked to be called back. No cold-calling, no telemarketing.

### 7.2 Conversation layer

**FR-C-1.** The voice agent uses **Gemini 3.1 Flash Live** (`gemini-3.1-flash-live-preview`) with native audio output, Swedish (`sv-SE`) explicitly configured as the language, and `thinking_level: "low"` for the dialogue manager. This balances latency with the function-calling reliability needed for triage.

**FR-C-2.** The agent must handle barge-in (caller interrupts mid-sentence) gracefully. Native to Live API. The audio playback queue must flush within 100 ms of detected interruption.

**FR-C-3.** The agent must handle dialect and accent variation across Swedish (skånska, göteborgska, norrländska, finlandssvenska, plus heavily-accented invandrarsvenska). This is tested in eval with 100+ Swedish dialect samples.

**FR-C-4.** The agent must handle code-switching gracefully: if the caller switches to English (common with internationals living in Stockholm), the agent switches with them and notes this in the call summary. Finnish and Arabic basic comprehension is a stretch goal for v1.

**FR-C-5.** The agent must produce a verbal "håller på och kollar" filler when calling a function that takes >300 ms (e.g., calendar lookup) so the caller doesn't experience dead air. Similar to how a human receptionist says "ett ögonblick" while opening a kalender.

**FR-C-6.** The agent must follow a strict no-promise policy: never commit to a price, never promise a specific tekniker by name without verifying availability, never commit to "i morgon" without confirming via calendar.

**FR-C-7.** The agent must always offer to take a message and end gracefully if the caller is upset, frustrated, or explicitly asks for a human. Owner-configurable: hard route to human after N detected frustration signals.

### 7.3 Triage and routing

**FR-R-1.** Every call must be classified into exactly one of five primary intents: `akut` (emergency requiring same-day or sub-2h response), `offertforfragan` (new prospect requesting estimate), `bokning` (existing or new customer scheduling planned work), `befintlig_kund_fraga` (existing customer asking about ongoing job, faktura, etc.), `ovrigt` (everything else: telemarketing, fellringd, vague inquiries).

**FR-R-2.** Emergency triage must apply a per-trade rule set, owner-configurable. VVS default emergencies: vattenläcka, igensatt avlopp som rinner över, ingen värme i vinter (Nov–Mar), gas-läcka (route directly to räddningstjänsten + escalate), avlopps-stopp som påverkar boende. El default emergencies: strömlöst hela bostaden, brand-relaterat, vatten på elcentral, skarpa fas-fel.

**FR-R-3.** Each firma must be able to configure an eskaleringskedja per intent and per time-of-day: e.g., "akut 17:00–07:00 → ring jourtekniker, sen mig, sen extern jour". Default chain provided.

**FR-R-4.** When the AI is uncertain about classification (e.g., low signal density on key words), it must err toward escalation, not toward dismissal.

### 7.4 Booking and calendar

**FR-B-1.** The system must integrate with Google Calendar, Microsoft Outlook 365, Hantverksdata Next kalender, and Fortnox kalender as primary booking targets. Bidirectional sync — bookings made elsewhere block AI-booking.

**FR-B-2.** The AI must respect resource constraints: tekniker A has cert X, jobbet kräver cert X, only book A. Configurable per-firma.

**FR-B-3.** The AI must respect travel time buffers: if jobs are at different addresses, automatically apply 30-min default travel buffer (configurable, ideally Maps-distance-aware in v1.1).

**FR-B-4.** The AI must offer no more than 3 slots per turn, and prefer slots in the next 7 days for normal bokningar, next 24h for prioriterad-bokning.

**FR-B-5.** Every booking must generate: a kalenderhändelse, a confirmation SMS to the kund, a confirmation e-mail with .ics attachment, and a kund-kort in the firm's CRM if not already present.

**FR-B-6.** Cancellations and reschedules: if a kund calls to reschedule, the AI looks up the existing booking, offers alternatives, updates all systems, and sends a reschedule confirmation.

### 7.5 Customer and lead capture

**FR-D-1.** On every call, the AI must attempt customer recognition by CLI (caller line identification) against the firm's existing kund-databas in Fortnox/Hantverksdata. Match → personalize ("Hej Inger, kul att höra från dig igen"). No match → standard greeting.

**FR-D-2.** For B2B callers, the AI must also recognize org-nummer when stated, and look up via Bolagsverket API for sanity-check on company name.

**FR-D-3.** For new leads, capture: namn, telefonnummer, adress (with postnummer-validation against Lantmäteriet), problembeskrivning, önskat datum, och eventuell ROT-avdrag-relevans (privatperson + bostad äldre än 5 år + ägare av bostaden).

**FR-D-4.** Photos: when the problem is visual (synlig läcka, trasig produkt, oklar installation), the AI offers to send an SMS-länk to a foto-uppladdningssida. Link is unique per call, expires in 7 dagar, secure HTTPS, photos land on the kund-kort.

**FR-D-5.** The AI must never collect personnummer, kontonummer, eller annat känsligt över röst. If the kund insists, AI sends an SMS-länk till ett säkert webformulär istället.

### 7.6 Post-call workflow

**FR-P-1.** Within 30 sekunder efter att samtalet avslutats, ägaren får en strukturerad SMS-summering med: kund (namn/nr), tid, intent, AI-handling, eventuell uppgift för ägaren.

**FR-P-2.** Inom samma 30 sekunder finns på dashboard: full transkription (Svenska), ljudinspelning (mp3, 7-dagars-länk default), AI-extracted struktur (intent, fält, bokade slots, skickade SMS), och föreslagen nästa-åtgärd.

**FR-P-3.** Veckosammanfattning på söndagskväll: antal samtal, fördelning per intent, conversion till bokat jobb, missade möjligheter (samtal där AI inte kunde lösa), top-3-actionable för veckan som kommer.

**FR-P-4.** Månadssammanfattning: ROI-beräkning (subscription cost vs estimated value of bookings/leads från AI-handled samtal), based on owner-confirmed jobbvärden.

### 7.7 Owner application (web + mobile)

**FR-O-1.** Web app and native iOS/Android apps with feature parity. Mobile-first design (owners are sällan vid en dator).

**FR-O-2.** Inkorg-vy: alla samtal i kronologisk ordning, filtrerbar på intent, status, kund, datum.

**FR-O-3.** Samtals-detalj-vy: transkript, ljudspelare, AI-summering, kund-kort, tagg-funktion, tilldela-till-team, snooze-till.

**FR-O-4.** Kalender-vy: alla bokningar oavsett källa, i en vy. Drag-and-drop ombokning.

**FR-O-5.** Inställningar: greeting (verbal eller textuell, AI klonar tonen), eskaleringskedja, öppettider, helgdagsschema, jourrullning, integrationer, fakturering.

**FR-O-6.** Eskalerings-flöde i mobilen: när en akut kommer, fullskärms-notis med ringtone som inte tystnar förrän ägaren bekräftar (likt Uber-driver akut-notiser).

**FR-O-7.** "Träna AI"-knapp: ägaren kan markera ett samtal som "AI gjorde fel — så här skulle du sagt", som matas in i firmans persona-justering. Detta är inte fine-tuning av modellen utan justering av system prompt + few-shot examples per firma.

### 7.8 Onboarding

**FR-N-1.** Self-serve onboarding via guidat webbflöde, mål: tid-till-första-svarade-samtal under 30 minuter.

**FR-N-2.** Steps: skapa konto → välj nummer (eller porta in) → koppla integration (Fortnox/Hantverksdata/Visma) via OAuth → konfigurera greeting (välj röst, spela in eller skriv egen text, AI förhandslyssnar) → konfigurera eskaleringskedja → konfigurera öppettider → 10 vanliga frågor och svar → testringa → klart.

**FR-N-3.** Concierge onboarding tillval (1 500 SEK engångs): mänsklig onboarding-specialist gör hela uppsättningen via skärmdelning med ägaren, 30 min.

**FR-N-4.** Persona-träning: ägaren laddar upp 5–10 inspelade samtal från sin egen kalender (frivilligt, GDPR-medgivande från kund krävs), AI:n analyserar tonläge och språkbruk, anpassar firmans system-prompt därefter.

## 8. Technical architecture

### 8.1 High-level architecture

The system is a real-time audio bridge between a Swedish PSTN endpoint (the caller's phone) and Google's Gemini 3.1 Flash Live model, with a function-calling layer that orchestrates business logic against the firm's CRM, calendar, and SMS systems. Each call spawns a stateful session with three concurrent, long-lived bidirectional channels:

```
                                                  ┌──────────────────────┐
                                                  │ Gemini 3.1 Flash     │
                                                  │ Live API             │
                                                  │ (WebSocket, EU)      │
                                                  └──────────▲───────────┘
                                                             │
                                                       PCM 16kHz in
                                                       PCM 24kHz out
                                                       JSON tool calls
                                                             │
┌──────────┐   PSTN   ┌──────────────┐   WebSocket   ┌──────▼──────────┐
│  Caller  │◄────────►│ 46elks (SE)  │◄─────────────►│ Svarsa Realtime │
│  (Inger) │  G.711   │ or Twilio    │ G.711 μ-law   │ Bridge          │
└──────────┘  μ-law   │              │ 8kHz mono     │ (Cloud Run, EU) │
              8kHz    └──────────────┘  base64       │                 │
                                                     │  - audio xcode  │
                                                     │  - VAD bridge   │
                                                     │  - tool router  │
                                                     │  - barge-in     │
                                                     │  - rec & redact │
                                                     └──────┬──────────┘
                                                            │
                                                            │ HTTPS / OAuth
                                                            ▼
                                       ┌─────────────────────────────────────────┐
                                       │ Business Logic Services                 │
                                       │  - Customer service (Postgres)          │
                                       │  - Booking service                      │
                                       │  - Escalation orchestrator              │
                                       │  - Notification (SMS/email)             │
                                       └────────────────┬────────────────────────┘
                                                        │
            ┌──────────────┬──────────────┬─────────────┼────────────┬─────────────┐
            ▼              ▼              ▼             ▼            ▼             ▼
        Fortnox       Hantverksdata   Visma         Google       46elks SMS    Bolagsverket
        OAuth API     Next API        eEkonomi      Calendar     API           lookup
                                      API           OAuth
```

### 8.2 Telephony integration

#### 8.2.1 46elks (primary, Swedish)

The default deployment uses **46elks** (Swedish company headquartered in Uppsala, infrastructure in SE), which we chose over Twilio for v1 because: (a) Swedish data residency end-to-end, (b) simpler GDPR posture for B2B sales, (c) lower latency to Gemini Vertex `europe-west` regions, (d) a more developer-friendly Swedish-language docs and support, (e) native support for porta-in of existing Swedish numbers.

46elks Voice Streaming sends bidirectional audio to a WebSocket endpoint as base64-encoded G.711 μ-law at 8 kHz, with `sync` and `interrupt` control messages. The Svarsa Realtime Bridge presents an `wss://...` URL in the `voice_start` JSON when a call hits the firma's Svarsa-allocated number.

Inbound flow:

1. Caller dials `+46-8-XXXX-XXXX`.
2. 46elks receives the call, fetches `voice_start` from Svarsa's webhook URL.
3. Svarsa returns JSON instructing 46elks to open a WebSocket to `wss://bridge.svarsa.se/ws/{firma_id}/{call_id}`.
4. 46elks opens the WebSocket and starts streaming μ-law audio frames.
5. Svarsa accepts, performs μ-law → PCM 16 kHz transcoding, and forwards to Gemini Live.

#### 8.2.2 Twilio (fallback / international)

Twilio Media Streams is supported as a fallback for firms that already have Twilio numbers, or for international expansion later. Twilio uses the same G.711 μ-law / 8 kHz / base64 framing, with `<Stream>` TwiML pointing at the same Realtime Bridge.

#### 8.2.3 Audio transcoding pipeline

Twilio and 46elks both speak G.711 μ-law at 8 kHz, mono, in 20 ms frames (160 bytes per frame). Gemini 3.1 Flash Live expects raw 16-bit PCM at 16 kHz, little-endian, on input, and emits raw 16-bit PCM at 24 kHz on output.

The Realtime Bridge therefore runs two transcoding paths:

- **Inbound (caller → Gemini):** decode base64 → μ-law → linear PCM 8 kHz → upsample to 16 kHz (band-limited, polyphase) → PCM blob with `mime_type="audio/pcm;rate=16000"` → send via `session.send_realtime_input(audio=...)`.
- **Outbound (Gemini → caller):** receive PCM 24 kHz from `session.receive()` → downsample to 8 kHz (anti-alias filter, then decimate) → linear PCM → μ-law encode → split into 160-byte 20 ms frames → base64-encode → send as `{"event":"media", "streamSid":..., "media":{"payload":...}}`.

Transcoding uses `audioop` (Python stdlib) for μ-law and a polyphase resampler (`scipy.signal.resample_poly`) for sample-rate conversion. End-to-end transcoding adds <8 ms per direction on warm pods.

#### 8.2.4 Voice activity and barge-in

Gemini Live's built-in VAD is enabled by default (`automatic_activity_detection`), and we rely on it. When Gemini emits an `interrupted` signal (server event indicating it has stopped speaking because the user is talking), the bridge **immediately drains** the outbound playback queue and stops sending Gemini's previous audio to 46elks. This is critical for the "feels like a human" experience — broken interruption handling is the single most common reason a caller realizes they are talking to a bot and hangs up.

### 8.3 Gemini 3.1 Flash Live configuration

#### 8.3.1 Connection setup

```python
from google import genai
from google.genai import types

client = genai.Client(
    vertexai=True,
    project=settings.GCP_PROJECT,
    location="europe-west4",  # EU residency, GDPR
)

MODEL = "gemini-3.1-flash-live-preview"

config = types.LiveConnectConfig(
    response_modalities=[types.Modality.AUDIO],
    speech_config=types.SpeechConfig(
        language_code="sv-SE",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=firma.preferred_voice,  # e.g. "Aoede" for warm female
            )
        ),
    ),
    system_instruction=types.Content(
        parts=[types.Part(text=build_system_prompt(firma))]
    ),
    thinking_config=types.ThinkingConfig(thinking_level="low"),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    input_audio_transcription=types.AudioTranscriptionConfig(),
    tools=TOOL_DECLARATIONS,
    session_resumption=types.SessionResumptionConfig(transparent=True),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=100_000,
        sliding_window=types.SlidingWindow(target_tokens=12_000),
    ),
    realtime_input_config=types.RealtimeInputConfig(
        # Default VAD
    ),
)
```

#### 8.3.2 Important model constraints (from Google's docs, May 2026)

- **Audio-only session limit without compression: 15 minutes.** Most calls are <3 min, but jour and B2B calls can run long. We enable context compression unconditionally.
- **Connection limit: ~10 minutes.** Each WebSocket auto-closes after ~10 min. We use `transparent=True` session resumption so that long calls reconnect transparently using `session_resumption_update` handles, with the bridge buffering any unconsumed messages and replaying them after reconnect.
- **Function calling is synchronous only** in 3.1 Flash Live (no async/non-blocking yet). The model pauses generation until our tool returns. We keep tool latency under 200 ms p95 by aggressive caching on customer/availability lookups.
- **Native audio output**: 24 kHz PCM. Always.
- **Native audio input**: 16 kHz PCM. Always.
- **Token cost (Vertex Live API)**: ~25 tokens per second of audio (input or output). At a 90-second call with 50/50 caller-vs-AI talk time and current Live API preview pricing, the per-call Gemini cost is on the order of 0,4–0,9 SEK (free of charge during preview, but we plan around GA pricing).
- **Concurrency**: up to 1 000 concurrent sessions per GCP project on Vertex Live API. We shard across two projects per region for redundancy.

#### 8.3.3 System prompt design

The system prompt is per-firma, generated from a shared base template plus firma-specific overrides. Structure (in Swedish):

1. **Persona** — "Du är digital assistent åt {firma_namn}, en {bransch}-firma i {ort}. Du svarar på inkommande samtal när Magnus och hans team inte hinner. Du pratar svenska naturligt och avslappnat — som en kompetent receptionist, inte en robot."
2. **Hard rules** — Aldrig ge priser. Aldrig hitta på namn på tekniker. Aldrig samla personnummer eller kortuppgifter. Alltid vara ärlig om att du är en AI om kunden frågar.
3. **Triage logic** — Decision tree for the five intents, with examples for each.
4. **Emergency rules** — Per-trade emergency definitions and the eskaleringskedja. *"Om kunden säger något som låter som vattenläcka, gas-läcka, ingen värme i vinter eller strömlöst hela huset — det är akut. Bekräfta snabbt, samla adress + namn + problem, sen anropa escalate_to_owner."*
5. **Booking rules** — Hur man läser kalender, hur man föreslår tider, hur man bekräftar. *"Erbjud max 3 tider åt gången, helst inom 7 dagar. Lägg in 30 min reskoja mellan jobb."*
6. **Tone and style** — Firma-specifik. *"Magnus är rak men varm. Inte stelt formell. 'Du' inte 'Ni'. Använd 'kanon', 'vi fixar det' när det passar."*
7. **Fallback** — *"Om du är osäker, är det alltid bättre att ta ett meddelande och eskalera än att gissa."*

The full system prompt is approximately 1 800–2 400 tokens in Swedish, which is well within the 128k context window and leaves ample room for conversation history.

### 8.4 Function calling — tool catalog

The AI is given a strict, well-typed catalog of tools. Each tool returns within 200 ms p95 (caching is essential). All tools log to a per-call trace for debugging and eval.

#### 8.4.1 `lookup_customer`

```json
{
  "name": "lookup_customer",
  "description": "Slå upp en kund i firmans system baserat på telefonnummer eller org-nummer. Anropa direkt vid samtalets start för CLI-baserad igenkänning, samt om kunden anger namn eller företag.",
  "parameters": {
    "type": "object",
    "properties": {
      "phone_number": {"type": "string", "description": "E.164-format, t.ex. +46708123456"},
      "org_number": {"type": "string", "description": "Svenskt org-nummer, format XXXXXX-XXXX"},
      "name_query": {"type": "string", "description": "Fritext-namn för fuzzy-sökning, sista resort"}
    }
  }
}
```

Returns: `{found: bool, customer_id, name, type: "private"|"company", last_job_summary, open_jobs: [...], notes}`.

#### 8.4.2 `triage_emergency`

```json
{
  "name": "triage_emergency",
  "description": "Bedöm om problemet är akut enligt firmans regler. Anropa när kunden beskriver ett problem och du behöver vägledning på om det är akut eller planerat.",
  "parameters": {
    "type": "object",
    "properties": {
      "problem_description": {"type": "string", "description": "Kortfattad svensk beskrivning av problemet, från kundens egna ord"},
      "trade": {"type": "string", "enum": ["vvs", "el", "snickeri", "tak", "kakel", "ovrigt"]},
      "indicators_present": {
        "type": "array",
        "items": {"type": "string", "enum": ["lacka", "rinner", "stromlost", "ingen_varme", "gas_lukt", "brand", "avlopp_stopp", "isolerad_aldre"]}
      }
    },
    "required": ["problem_description", "trade"]
  }
}
```

Returns: `{is_emergency: bool, severity: "critical"|"high"|"medium"|"low", recommended_action: "escalate_now"|"book_today"|"book_normal"|"informational", reasoning}`.

#### 8.4.3 `check_availability`

```json
{
  "name": "check_availability",
  "description": "Hämta lediga tider i kalendern för planerat arbete. Anropa när kunden vill boka ett besök.",
  "parameters": {
    "type": "object",
    "properties": {
      "duration_minutes": {"type": "integer"},
      "earliest_date": {"type": "string", "format": "date"},
      "latest_date": {"type": "string", "format": "date"},
      "required_skills": {"type": "array", "items": {"type": "string"}, "description": "T.ex. ['saker_vatten', 'svetsbehorighet']"},
      "address": {"type": "string", "description": "Adressen jobbet ska utföras på, för restidsberäkning"}
    },
    "required": ["duration_minutes", "earliest_date", "latest_date"]
  }
}
```

Returns: `{slots: [{start_iso, end_iso, technician_id, technician_name, travel_buffer_min}, ...]}` — max 5 slots.

#### 8.4.4 `book_appointment`

```json
{
  "name": "book_appointment",
  "description": "Boka in jobbet hos kunden. Anropa endast efter att kunden uttryckligen bekräftat tid och adress.",
  "parameters": {
    "type": "object",
    "properties": {
      "customer_id": {"type": "string", "description": "Från lookup_customer; om ny kund, anropa create_lead först"},
      "start_iso": {"type": "string", "format": "date-time"},
      "duration_minutes": {"type": "integer"},
      "technician_id": {"type": "string"},
      "address": {"type": "string"},
      "problem_summary_sv": {"type": "string"},
      "rot_eligible": {"type": "boolean", "description": "Stämmer av kundens rätt till ROT-avdrag"}
    },
    "required": ["customer_id", "start_iso", "duration_minutes", "address", "problem_summary_sv"]
  }
}
```

Returns: `{booking_id, calendar_event_url, confirmation_sms_sent, confirmation_email_sent}`.

#### 8.4.5 `create_lead`

```json
{
  "name": "create_lead",
  "description": "Skapa ny kund/lead i firmans CRM. Anropa när lookup_customer inte hittade någon träff och kunden vill boka eller få offert.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "phone": {"type": "string"},
      "email": {"type": "string"},
      "address": {"type": "string"},
      "type": {"type": "string", "enum": ["private", "company"]},
      "org_number": {"type": "string", "description": "Endast om type=company"},
      "problem_summary_sv": {"type": "string"},
      "estimated_value_sek": {"type": "integer", "description": "Grovt uppskattat värde av jobbet, valfritt"}
    },
    "required": ["name", "phone", "type", "problem_summary_sv"]
  }
}
```

Returns: `{customer_id, created: bool}`.

#### 8.4.6 `escalate_to_owner`

```json
{
  "name": "escalate_to_owner",
  "description": "Eskalera ärendet till ägare/jourtekniker enligt firmans eskaleringskedja. Anropa för alla akuta ärenden samt när kunden uttryckligen begär att få prata med en människa.",
  "parameters": {
    "type": "object",
    "properties": {
      "severity": {"type": "string", "enum": ["critical", "high", "medium"]},
      "reason": {"type": "string", "description": "Kort sammanfattning på svenska"},
      "customer_id": {"type": "string"},
      "customer_phone": {"type": "string"},
      "address": {"type": "string"},
      "callback_window": {"type": "string", "description": "T.ex. '15 min', '1 timme', 'innan 17:00'"}
    },
    "required": ["severity", "reason", "customer_phone"]
  }
}
```

Returns: `{escalation_id, contacted: ["+4670...", ...], next_in_chain_in_minutes}`.

#### 8.4.7 `send_sms_followup`

```json
{
  "name": "send_sms_followup",
  "description": "Skicka SMS-bekräftelse, foto-uppladdningslänk eller bokningsbekräftelse till kunden.",
  "parameters": {
    "type": "object",
    "properties": {
      "to_phone": {"type": "string"},
      "template": {"type": "string", "enum": ["booking_confirmation", "emergency_ack", "photo_upload_link", "callback_promise", "secure_form_link"]},
      "context_data": {"type": "object", "description": "Mall-variabler"}
    },
    "required": ["to_phone", "template"]
  }
}
```

Returns: `{sent: bool, sms_id}`.

#### 8.4.8 `request_photo_upload`

```json
{
  "name": "request_photo_upload",
  "description": "Generera engångs-länk för foto-uppladdning och skicka via SMS. Använd när problemet är visuellt.",
  "parameters": {
    "type": "object",
    "properties": {
      "to_phone": {"type": "string"},
      "lead_or_customer_id": {"type": "string"},
      "expires_hours": {"type": "integer", "default": 168}
    },
    "required": ["to_phone", "lead_or_customer_id"]
  }
}
```

#### 8.4.9 `lookup_job_status`

```json
{
  "name": "lookup_job_status",
  "description": "Slå upp status på ett pågående eller nyligen avslutat jobb för en befintlig kund.",
  "parameters": {
    "type": "object",
    "properties": {
      "customer_id": {"type": "string"},
      "job_query_sv": {"type": "string", "description": "Kundens egna ord, t.ex. 'badrumsjobbet'"}
    },
    "required": ["customer_id"]
  }
}
```

#### 8.4.10 `check_rot_eligibility`

```json
{
  "name": "check_rot_eligibility",
  "description": "Bedöm om kunden sannolikt kvalificerar för ROT-avdrag. Pure-function, inga externa anrop.",
  "parameters": {
    "type": "object",
    "properties": {
      "is_private_person": {"type": "boolean"},
      "owns_property": {"type": "boolean"},
      "property_age_years": {"type": "integer"},
      "work_type": {"type": "string"}
    }
  }
}
```

Returns: `{eligible: bool, max_deduction_sek_estimate, caveats_sv}`.

#### 8.4.11 `transfer_to_human`

```json
{
  "name": "transfer_to_human",
  "description": "Koppla samtalet till en människa via SIP-bridge. Endast om kunden uttryckligen bett om det och en människa är tillgänglig.",
  "parameters": {
    "type": "object",
    "properties": {
      "target": {"type": "string", "enum": ["owner_mobile", "office", "on_call_technician", "external_answering_service"]},
      "context_summary_sv": {"type": "string", "description": "Kort brief som AI:n läser upp för mottagaren innan handover"}
    },
    "required": ["target", "context_summary_sv"]
  }
}
```

#### 8.4.12 `take_message`

```json
{
  "name": "take_message",
  "description": "Avsluta samtalet med ett strukturerat meddelande till ägaren. Sista utväg när inget annat verktyg passar.",
  "parameters": {
    "type": "object",
    "properties": {
      "caller_name": {"type": "string"},
      "caller_phone": {"type": "string"},
      "topic_sv": {"type": "string"},
      "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
      "callback_preference_sv": {"type": "string"}
    },
    "required": ["caller_phone", "topic_sv", "urgency"]
  }
}
```

### 8.5 Backend services

The Realtime Bridge is one of several services. The full service map:

- **Realtime Bridge** (Python 3.13 + FastAPI + asyncio) — runs on Cloud Run with min-instances=2 per region for warm starts; co-located in `europe-west4` (Netherlands) and `europe-north1` (Finland) for SE proximity. Each call holds two open WebSockets (telephony + Gemini) for the call's duration.
- **Tool Service** (Go) — implements all function-call handlers. Stateless, horizontally scalable, p95 latency budget 200 ms per tool invocation. Aggressive Redis caching of customer lookups, calendar windows, bolagsverket data.
- **Integration Service** (Go) — long-poll-style sync with Fortnox, Hantverksdata, Visma. Owns OAuth-token-rotation, idempotency keys, conflict resolution. Decouples real-time path from third-party flakiness.
- **Notification Service** (Go) — SMS via 46elks, email via Postmark (EU region), push via APNS/FCM.
- **Recording Service** (Python) — receives audio from Realtime Bridge, encodes to MP3, applies opt-in PII redaction (whisper diarization → flag any `personnummer`-like 10-digit sequences for masking), stores in GCS `europe-west4` with 7-day default TTL configurable to 90.
- **Owner App API** (Python + FastAPI) — REST + WebSocket for real-time inbox updates.
- **Owner Web App** (Next.js, hosted on Vercel EU) — and **Owner Mobile** (React Native).
- **Admin / Internal** — Grafana, Sentry (EU), per-firma cost dashboards, eval pipelines.

### 8.6 Data model (simplified)

```
Firma (id, name, org_number, trade, plan, settings_json)
  ├── PhoneNumber (id, e164, provider, status)
  ├── User (id, role, phone, email)
  ├── EscalationChain (id, intent, schedule_cron, steps_json)
  ├── Voice (firma_id, persona_prompt, voice_id, sample_audio_url)
  └── Integration (id, type, oauth_tokens_encrypted, sync_state)

Customer (id, firma_id, type, name, phone, email, org_number, address, source)
  ├── Job (id, status, intent, summary, value_sek, tech_id, scheduled_for)
  ├── Note (id, body, created_by, created_at)
  └── Photo (id, url, expires_at)

Call (id, firma_id, customer_id, started_at, ended_at, intent, severity,
      recording_url, transcript_url, structured_summary_json, gemini_session_id,
      tool_invocations_json, billing_seconds)
  └── ToolInvocation (id, name, args_json, result_json, latency_ms, error)

Escalation (id, call_id, severity, reason, contacted_user_ids, status, ack_at)
```

### 8.7 Integrations

#### 8.7.1 Fortnox

OAuth 2.0, REST API. Used for: kundregister read/write, fakturadata read-only (for "vad gäller fakturan?"-frågor), kalender read/write where the firma uses Fortnox kalender. Documented public API. Webhook support exists but is limited; we poll customer/calendar deltas every 60s.

#### 8.7.2 Hantverksdata Next

Partner-gated API. Requires signed partneravtal with Hantverksdata AB; this should begin in Phase 0 of the roadmap because it takes 2–4 months. Used for: projekthantering, arbetsorder-skapande, kundregister, tekniker-resursplanering. This is the most strategically important integration and a real moat once secured.

#### 8.7.3 Visma eEkonomi

OAuth 2.0, REST. Similar role to Fortnox for the Visma-using subset. Public API.

#### 8.7.4 Google Calendar / Microsoft Outlook 365

OAuth 2.0. Bidirectional CalDAV/Graph API. Used as primary calendar for firms that don't book through Fortnox/Hantverksdata.

#### 8.7.5 Bolagsverket / Allabolag

Public org-number lookup for B2B kund-verification. Cached 7 dagar.

#### 8.7.6 46elks

API for SMS, MMS, voice, number management. We own the integration deeply: SMS sending (transactional, ej marknadsföring), inbound number lifecycle, and inbound call streaming.

### 8.8 Non-functional requirements

| Aspect | Requirement |
|---|---|
| End-to-end voice latency (caller speech end → AI speech start) | <1 200 ms p50, <2 000 ms p95, <3 000 ms p99 |
| Service availability | 99,9% monthly (target), with 99,5% SLA in customer agreement |
| Concurrent calls per firma | 5 (Starter) / 25 (Pro) / unlimited (Enterprise) |
| System concurrent calls (platform-wide) | 1 000 at launch, scaling to 10 000 by month 12 |
| Recording storage | EU only (GCS europe-west4), encrypted at rest (CMEK), TTL configurable 7–365 days |
| Transcript storage | Same as recording, additionally indexed for in-app search |
| RTO / RPO | RTO 30 min, RPO 5 min for firma config and customer data; recordings tolerate 1h RPO |
| Logging / audit | All tool invocations logged with full args/results for 90 days, accessible to owner |

## 9. GDPR and compliance

### 9.1 Lawful basis

For B2B traffic between the firma and a B2B customer, lawful basis is **legitimate interest** (Art. 6(1)(f)) under standard balancing test, with the firma as personuppgiftsansvarig and Svarsa as personuppgiftsbiträde. For B2C calls, the firma typically has either **kontraktuell grund** (Art. 6(1)(b)) when the kund is requesting a tjänst, or legitimate interest for new prospects, with explicit **opt-in samtycke** to recording disclosed at call connect.

### 9.2 Recording consent

Every call begins with a Swedish disclosure: *"Detta samtal kan spelas in för kvalitets- och utbildningsändamål. Vänligen säg till om du inte vill att samtalet spelas in."* If the kund objects, the AI calls `disable_recording_for_call()` and the recording service drops the audio immediately.

### 9.3 Sub-processors

Customer-facing DPA lists all sub-processors:

- Google LLC (Vertex AI Live API, Gemini 3.1 Flash Live) — EU region (`europe-west4`)
- 46elks AB (Sweden) — telephony
- Twilio Inc. (fallback, US-based) — disclosed; firms can opt out
- Postmark / ActiveCampaign EU — transactional email
- Vercel Inc. — frontend hosting (EU edge)
- Google Cloud Platform — compute, storage, KMS (EU regions only)
- Sentry GmbH (EU) — error tracking

### 9.4 Data residency

All caller audio, transcripts, customer data, and call metadata stored in EU regions. Vertex AI Live API endpoints in `europe-west4`. Cloud Run, GCS, Cloud SQL all in EU. No data exits the EU at rest. In-flight, Gemini Live's processing happens within Google EU infrastructure when using the `europe-west4` regional endpoint.

### 9.5 Sensitive data handling

The AI is system-prompt-instructed to **never** collect personnummer, kontonummer, kortnummer, or login credentials over voice. If a kund volunteers such information, the system applies a real-time PII redaction filter on the transcript before storage. If the kund insists on providing such information, the AI sends an SMS-link to a hardened webformulär (HTTPS, encrypted at rest, accessible only to the firma).

### 9.6 Retention

Default retention: call recording 7 days, transcript 90 days, structured call metadata 24 months (for the firma's own records and ROI analysis). All retention windows configurable per-firma. Right to erasure honored within 30 days of request.

### 9.7 DPIA

A Data Protection Impact Assessment (Art. 35) is required given the scale of voice processing and the involvement of automated decision-making (triage, escalation). Completed and reviewed by an external DPO before GA. Updated annually.

### 9.8 Marketing / TCF

Outbound SMS sent only to numbers that have called us first or where the firma has documented marketing consent. We do not enable AI-driven outbound cold contact. No use of caller voice or transcript data for model training; this is contractually committed in Vertex AI Enterprise terms (Customer Data Use commitments).

## 10. Pricing and packaging

| Plan | Price/mån | Setup | Inkluderat | Targets |
|---|---|---|---|---|
| **Starter** | 1 495 SEK | 2 000 SEK | 1 nummer, 200 samtal/mån, Fortnox eller Visma + Google Calendar, basic dashboard, e-postsupport | Solo VVS:are / elektriker, första AI-svarstjänst |
| **Professional** | 2 995 SEK | 3 000 SEK | 3 nummer, 600 samtal/mån, alla integrationer (inkl. Hantverksdata Next), eskaleringskedja, jourroll, mobile app, prioritetsupport | Standard SME 3–10 anställda |
| **Premium** | från 5 995 SEK | 5 000 SEK | Obegränsade nummer & samtal, white-label, multi-firma rollup, custom voice, dedikerad CSM, SLA 99,5% | Större firmor, kedjor, fastighetsbolag |

Overage: 4 SEK / extra samtal på Starter, 3 SEK på Professional. Setup-avgift återbetalas om kunden inte är nöjd inom 30 dagar.

### 10.1 Cost structure (per call, internal)

At 90-second median samtal, GA Vertex Live API pricing (estimated post-preview), 46elks SE-numbers, infra:

- Gemini 3.1 Flash Live: ~0,9 SEK
- 46elks inbound: ~0,4 SEK
- 46elks outbound SMS (1–2 per call): ~0,5 SEK
- Compute/infra: ~0,3 SEK
- **Total: ~2,1 SEK per typical call**

At Starter (200 samtal × 2,1 = 420 SEK COGS, 1 495 SEK ARR), gross margin ~72%. At Professional (600 × 2,1 = 1 260 SEK, 2 995 SEK ARR), gross margin ~58%. Margin improves with longer-tenured customers as call distribution stabilizes around shorter median calls.

## 11. Roadmap

### 11.1 Phase 0: Foundations (June 2026)

- Hantverksdata Next partner-avtal initierat (kritisk path, 2–4 mån)
- Legal: DPA-mall, sub-processor-avtal, F-skatt och bolagsregistrering klar
- Eval-dataset: 500 inspelade VVS-samtal med samtycke från 5 pilotkunder
- Infrastruktur: GCP `europe-west4` projekt, Cloud Run base setup, secrets, observability

### 11.2 Phase 1: Closed beta (July–September 2026)

- 8–12 pilot-firmor (VVS-tunga, Stockholm/Göteborg)
- Fortnox + Google Calendar integration first
- Single-language (Swedish), single-trade (VVS)
- Manual onboarding, white-glove support
- Goal: 10 000 handled calls, ≥85% triage accuracy, 0 GDPR-incidenter

### 11.3 Phase 2: Open beta (October–November 2026)

- Self-serve onboarding live
- El + snickeri trade-spåren tillagda
- Hantverksdata Next integration live (om partneravtal klart)
- Visma eEkonomi tillagd
- Goal: 50 betalande firmor, 50 000 calls/mån

### 11.4 Phase 3: GA (December 2026)

- SLA 99,5%
- Native iOS + Android apps GA
- Marketing launch via Installatörsföretagen + Säker Vatten kanaler
- Reseller-program för bokföringsbyråer
- Goal: 200 betalande firmor by end of Q1 2027, 250 kSEK MRR

### 11.5 Phase 4: Expansion (H1 2027)

- Finskt språk + finsk telephony (46elks har redan FI)
- Norska och danska
- Dahl + Ahlsell grossist-integrationer (materialhämtning från samtal)
- Outbound jobb-uppföljning ("var nöjd med jobbet?")
- Multi-firma rollup för franchise/kedjor

## 12. Risks and mitigations

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| Gemini 3.1 Flash Live remains in preview at GA, with rate-limit unpredictability | High | Medium | Vertex Enterprise contract with reserved capacity; fallback path to Gemini 2.5 Native Audio; abstract the LLM provider in the bridge so we can swap to OpenAI Realtime if needed |
| Hantverksdata partneravtal försenas eller nekas | High | Medium | Parallel-spår med Fortnox och Visma + generic Zapier-webhook fallback; ingen single-vendor blocker for launch |
| Triage-fel skapar PR-incident (AI sade ej akut, kund hade vattenskada) | Catastrophic | Low | Bias toward escalation; weekly eval; firma-konfigurerbara regler; tydlig SLA-disclaimer i avtalet; insurance coverage |
| GDPR-incident (recording läcker, fel data residency) | Catastrophic | Low | Strict EU-only deployment; CMEK; pen-test pre-GA; bug bounty; insurance |
| Caller-experience är "creepy AI" | High | Medium | Tonality eval i fokusgrupper; tydlig disclosure; barge-in working; smooth handoff to human alltid available |
| Twilio/46elks-avbrott (telephony down) | High | Low | Multi-provider failover; status page; under SLA påverkas inte (force majeure) |
| Hantverkare-segmentet köper inte SaaS i förväntad takt | Medium | Medium | Channel sales via grossister/branschorg; reseller-marginaler; pilot-discount |
| Konkurrent (Goodcall/Synthflow) Swedish-isar och kommer först | Medium | Medium | Fokus på trade-vertikalintegrationer som moat; varumärke som "av oss för oss" |
| Caller speaks dialect AI doesn't understand | Medium | Medium | Eval på 100+ dialekter; explicit "kan du upprepa"-fallback; eskalering vid n misslyckade förståelser |

## 13. Open questions

The following are not blockers but require resolution before or during Phase 1.

- **Voice selection:** Do we ship with a single Svarsa-branded voice, or let firmor choose from 4–6 prebuilt? Tradeoff: brand consistency vs perceived ownership. Recommendation: 3 default options (warm female, neutral male, energetic young), no clones at launch.
- **Recording consent — opt-in or opt-out?** Swedish lag tolererar opt-out för B2B; for B2C we lean opt-in via disclosure. Confirm with juridik before pilot.
- **Pricing — flat eller per-call?** Hybrid is what we've designed. Should we offer pure pay-as-you-go for occasional users? Risk of cannibalizing Starter.
- **Outbound calling:** v1 is inbound-only with limited callbacks. When do we open up outbound (e.g., proaktiv återkoppling efter avslutat jobb)? Regulatory implications are nontrivial.
- **White-label:** at what plan tier do we allow firma-branding of greeting and SMS? Premium only, or down to Pro?
- **Multi-firma support for ägare med flera bolag:** common pattern among Swedish tradesmen with separate AB:s — design the data model and pricing now or after GA?

## 14. Appendix A — Sample system prompt skeleton (Swedish)

```
Du är digital assistent åt {firma_namn}, en {bransch}-firma i {ort} med {antal_anstallda} anställda.
Du svarar på inkommande telefonsamtal när Magnus och hans team inte hinner.

# Hur du pratar
Du pratar svenska naturligt och avslappnat — som en kompetent receptionist, inte en robot.
Du säger "du", inte "ni". Du är rak men varm. Korta meningar. Inga onödiga ord.
Om kunden frågar om du är en människa, säger du sanningen: "Nej, jag är en digital assistent
åt {firma_namn} — men jag kan boka tider och ta meddelanden direkt till Magnus."

# Vad du ALDRIG gör
- Aldrig ge priser. Säg: "Det vill jag inte chansa på, Magnus återkommer med offert."
- Aldrig hitta på namn på tekniker eller datum.
- Aldrig samla personnummer, kortuppgifter, lösenord. Skicka en säker länk istället.
- Aldrig låtsas förstå om du inte gjorde det. Be att kunden upprepar, eller eskalera.

# Triage
För varje samtal, klassificera tidigt vad det handlar om:
- AKUT (vattenläcka, ingen värme i vinter, gas-läcka, strömlöst hus): anropa
  triage_emergency, sen escalate_to_owner direkt. Kund: "Magnus är på ett jobb just nu
  men han får ditt ärende omedelbart och ringer dig inom 15 minuter."
- OFFERTFÖRFRÅGAN: lyssna, samla namn/adress/problem, anropa create_lead, erbjud
  foto-uppladdning via SMS, säg när Magnus återkommer.
- BOKNING: anropa lookup_customer, sen check_availability, erbjud max 3 tider, bekräfta,
  anropa book_appointment.
- BEFINTLIG KUND-FRÅGA: lookup_customer + lookup_job_status. Om du inte kan svara
  konkret — ta meddelande.
- ÖVRIGT: take_message och avsluta artigt.

# Eskalering
Om kunden uttrycker frustration eller ber om en människa: anropa transfer_to_human om
någon är tillgänglig, annars ta meddelande och var tydlig om callback-tiden.

# Stil-exempel (Magnus pratar så)
- "Vi fixar det, ingen fara."
- "Kanon, då bokar jag in det."
- "Jag ska kolla i kalendern, ett ögonblick."
- "Det låter inte bra — har du stängt av vattnet?"

# Avsluta
Avsluta varje samtal med en tydlig sammanfattning av vad som händer härnäst,
och en vänlig hälsning.
```

## 15. Appendix B — Conversation latency budget

| Stage | p50 | p95 |
|---|---|---|
| Caller speech → 46elks WS frame | 80 ms | 150 ms |
| 46elks WS → Bridge ingress | 20 ms | 40 ms |
| μ-law → PCM 16kHz transcode | 5 ms | 10 ms |
| Bridge → Gemini Live (sent) | 30 ms | 80 ms |
| Gemini VAD + thinking + first audio | 700 ms | 1 300 ms |
| Gemini → Bridge (first audio chunk) | 30 ms | 80 ms |
| PCM 24kHz → μ-law 8kHz transcode | 5 ms | 10 ms |
| Bridge → 46elks → caller | 100 ms | 200 ms |
| **End-to-end** | **~970 ms** | **~1 870 ms** |

This sits within the 1 200 ms p50 / 2 000 ms p95 NFR target. Function-call turns add 150–300 ms when a tool is invoked; the AI is system-prompted to emit a "ett ögonblick"-filler in those cases.

---

*End of document. Reviewed by: pending. Next review: pre-Phase 1 kickoff.*