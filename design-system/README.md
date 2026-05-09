# Switchboard Design System — Verkstad

> **Verkstad** (sv. _workshop_) is the design language of **Switchboard** — the Swedish phone-booking AI for tradespeople.
> The system is built so that a 47-year-old VVS-företagare in Bromma looks at our product and thinks: _"Det här ser ut som något jag redan använder."_

---

## What Switchboard is

Switchboard is an AI phone assistant ("svarstjänst") for Scandinavian tradespeople — VVS, el, snickeri, plattsättning. It answers calls when Magnus is on a tak, in a kryputrymme, or at lunch; it speaks calmly and competently in Swedish; it captures jobs, books in time-slots, and routes true emergencies to the on-call tech. The product exists so that **Inger's 71-year-old vattenläcka call doesn't get lost**.

### The four people the system serves

| Persona | Surface they meet | Primary design need |
|---|---|---|
| **Magnus**, 47, VVS-företagare, Bromma — _the buyer_ | Marketing site, akutnotis on phone, watch face | Trust at first glance, single-thumb readability in sun/headlamp |
| **Lena**, 44, kontorsadministratör, Magnus's sambo — _the daily driver_ | Web dashboard | Editorial calm. Twelve minutes with morning coffee. |
| **Alex**, 28, jourtekniker — _the on-call_ | Lock-screen akutnotis | High contrast, single primary action, eight-second decision |
| **Inger**, 71, calling customer — _invisible persona_ | The voice only | Every UI choice must indirectly serve her getting answered |

---

## Sources & inputs

This system was authored from a written brand brief (the **"Verkstad — Designspråk"** document). At the time of authoring there was **no attached codebase, Figma file, or production screenshots**. Every visual decision is derived from the brief plus the named reference shelf:

- **Pleo** — editorial restraint, photography-as-brand, pill buttons, warm whites (pleo.io)
- **Klarna** — grid system, type-led layouts, signal-color discipline (brand.klarna.com)
- **Hilti / Husqvarna / Stihl / Bahco / Snickers** — color-as-function, presumed-competent UI, durable industrial form
- **Linear** — calm operational dashboard, type doing heavy lifting (linear.app)
- **PagerDuty / Uber Driver** — the akutnotis pattern: single-action, can't-miss
- **Iittala** — Swedish-Nordic restraint with personality (iittala.com)

If/when a codebase or Figma is attached, this README should be revised to point to those sources directly.

---

## Index

| File | Purpose |
|---|---|
| `README.md` | This document — context, content & visual fundamentals, iconography |
| `colors_and_type.css` | All design tokens — color, type, spacing, radii |
| `fonts/` | Webfonts (currently Geist Sans/Mono — flagged substitution for Söhne) |
| `assets/` | Wordmark SVG, photo-frame placeholders, signal-orange dot |
| `preview/` | Design-system cards (Type, Colors, Spacing, Components, Brand) |
| `ui_kits/marketing/` | Marketing site UI kit (home + pricing + product story) |
| `ui_kits/dashboard/` | Web dashboard UI kit (Lena's morning briefing + samtalsdetalj) |
| `ui_kits/akutnotis/` | Mobile akutnotis UI kit (lock screen + alert + watch) |
| `SKILL.md` | Cross-compatible Skill manifest for use in Claude Code |

### UI kits

- **`ui_kits/marketing/`** — home page (hero, briefing, quote, pricing, footer). Pleo-editorial + Klarna-grid + type-led.
- **`ui_kits/dashboard/`** — Lena's morning briefing (sidenav, stats, calls list, slide-in detail sheet with transcript).
- **`ui_kits/akutnotis/`** — Alex's lock-screen akutnotis + Magnus's Apple Watch face. The sacred surface — single pulse, then stillness.

### Preview cards (Design System tab)

Cards are grouped into Type, Colors, Spacing, Components, Brand. Twenty-two cards in total, each one a single concept (e.g. "tabular numerals" gets its own card, separate from "type hierarchy"). Edit any single card without touching the others.

---

## Font substitution flag

**Söhne** is a paid Klim Type Foundry license and is not redistributable. We have substituted **Geist Sans + Geist Mono** (open license, similar grotesque proportions, modern, not yet visually overused). Geist holds the Verkstad type intent — confident, geometric without being cold, tabular numerals available — but it is not Söhne. **Action for the user**: please ship the Söhne `.woff2` files to `fonts/` and update `colors_and_type.css` `--font-display` / `--font-body` so production uses the licensed face.

---

## CONTENT FUNDAMENTALS

The brand's tone of voice is inseparable from the visual system. If the copy is wrong, no amount of type and color fixes it.

### Three rules, no exceptions

1. **Du, never ni.** Swedish second-person familiar. Magnus uses it; the AI uses it with customers; we use it with everyone. _Ni_ reads as 1980s-banking and is wrong for this brand.
2. **Concrete over abstract.** _"Boka tid med Magnus"_ beats _"Schedule a service appointment."_ _"Vattenläcka kl 14:32"_ beats _"New incident detected."_ The product handles concrete jobs; the language stays concrete.
3. **Magnus's voice, not the corporation's voice.** When the brand has to say something — a confirmation toast, an empty state, an error — it speaks the way Magnus speaks: rakt, varmt, kort.

### Casing and form

- **Sentence case always.** Buttons, headings, labels: _"Boka in tid"_ not _"Boka In Tid"._ This is Swedish convention and matches Klarna and Pleo. The wordmark is the only exception.
- **Lowercase months.** _"22 maj"_ never _"May 22"_ or _"22 Maj."_
- **24-hour time.** _"14:32"_ never _"2:32 PM."_
- **Currency**: non-breaking space, SEK postfix. _"1 495 SEK"_ never _"kr1,495"_ or _"$152."_
- **Diacritics typeset correctly.** å ä ö, never æ or accidentally ae. Geist and Söhne both ship them; never substitute.

### Voice examples

| Verkstad ✓ | Anti-Verkstad ✗ |
|---|---|
| _"Det funkade. Bokningen ligger i kalendern."_ | _"Your appointment has been successfully scheduled."_ |
| _"Du fångade tre akutjobb i natt — kosta dig själv en till kopp kaffe på det."_ | _"🎉 Great job! You handled 3 emergency jobs."_ |
| _"Vattenläcka hos Inger Lindqvist · 14:32"_ | _"New incident · High priority · 5 minutes ago"_ |
| _"Ta jobbet"_ / _"Skicka till Alex"_ | _"Accept assignment"_ / _"Delegate to on-call technician"_ |
| _"Boka demo"_ | _"Get started — it takes 30 seconds!"_ |

### Emoji

**No.** Not in product, not in marketing, not in error states, not in onboarding. The brand has humor — it lives in voice and copy, not in pictograms. Magnus does not get a 🎉 when he closes a job. The single visual exception is the orange wordmark dot, which functions as identity, not decoration.

### Empty states and errors

Empty states are written like a calm aside, not a tutorial. Errors are honest about what happened. _"Vi nådde inte din kund. Försök igen, eller ring själv."_ — not _"Oops! Something went wrong. Please try again."_

---

## VISUAL FOUNDATIONS

### Color philosophy

Seven colors, narrowly scoped. Anyone designing in Verkstad who wants to add an eighth must defend why.

| Token | Hex | Role |
|---|---|---|
| **havsblå** | `#0A1F33` | Primary brand. Wordmark, navigation, body type on light surfaces. Dark enough to feel substantial; not pure black. |
| **linne** | `#FBF8F2` | Primary surface. Warm off-white (linen) — lightened May 2026 to give body copy clear AA contrast. The dashboard background, marketing surfaces. |
| **linne-cool** | `#FFFFFE` | Cooler product variant where contrast against photography is needed. |
| **signaloranje** | `#E25822` | The one signal color. Reserved: primary CTA, akutnotis state, wordmark dot, 1–2 marketing moments per year. **Never** for hover states, link underlines, or feature-update highlights. |
| **tallgrön** | `#2F5233` | Confirmed bookings, positive states. Swedish pine, not bank-app success-toast green. |
| **larmröd** | `#A82E2E` | Genuinely critical only — gas leak, AI failure, payment failure. Never used in marketing. |
| **warm grays** | 5 steps + ink | Tuned with a hint of yellow, never blue. Dashboard secondary text, dividers, disabled. |

### Type

Two type families do all the work. Söhne for everything (display + body), Söhne Mono / Geist Mono for tabular contexts. **No third family for "personality."**

- **Two weights only in product UI**: Regular 400 and Medium 500. Bold is reserved for the wordmark and large marketing display.
- **Sentence case always.**
- **Tabular numerals on by default** for time, currency, phone numbers, org.nr.
- **Scale aggressively on marketing** (Klarna principle). When you can go to 96px, go to 96px. Display headlines may offset a word for tension — _"Magnus missar inga **akutsamtal**"_ with the last word in signaloranje, used very sparingly.

### Spacing & grid

- **4px base spacing scale** — `s-1 (4)` through `s-32 (128)`.
- **Klarna-derived layout grid**: 6% margin of the shortest side (single-margin), 12% (double-margin), gutter = ½ margin, trademark width = ⅓ of the shortest side. This is not a suggestion — it is the rule that lets a junior designer in 2027 sit comfortably next to a senior designer's 2026 work.

### Backgrounds

- **No gradients on UI.** Period. The bluish-purple gradient is Silicon Valley; the warm-cream gradient is wedding invitation; neither is Verkstad.
- **Photography is the brand**, not illustration. See the photography section below.
- **No repeating patterns or textures** in product UI. The dashboard is a piece of paper, not a quilt.
- The single permitted "background event" is the **akutnotis halo** — the soft orange box-shadow around an active emergency card.

### Borders, fills, hierarchy

- **Hairline borders are the only structural cue.** A 1px warm-gray border (`--border`) on `#fff` is the default container. Sunken regions use `--linne-deep` with no border.
- **Verkstad uses no drop shadows.** Cards do not float, menus do not cast, modals do not lift. Hierarchy comes from type weight, surface fill, and 1–2px borders — never depth.
- The single permitted "shadow event" is **`--shadow-signal`** — a 4px orange ring + soft halo, reserved for the akutnotis card. Read it as identity, not elevation. Do not borrow it for "look at this new feature" moments.
- **Focus rings are not shadows** for the purposes of this rule. The 3px navy focus ring on inputs is an accessibility affordance and stays.
- **No glassmorphism, no gradients, no textures.** Magnus is not impressed and Lena finds it harder to read.

### Corner radii

- `--r-pill` (∞) — buttons, tags. **The pill button is signature** (Pleo-derived).
- `--r-card` (14) — cards, panels.
- `--r-input` (10) — inputs, selects.
- `--r-tight` (6) — chips, code.
- `--r-none` (0) — photography frames. Photographs are honest rectangles.

### Cards

White or sunken-linen background, hairline border, 14px radius, **no drop shadow**. Cards sit on the page, they don't float above it. If a card needs more emphasis, change its fill or its border weight — never lift it.e it. The inverse variant (havsblå) is used for editorial moments — pull-quotes, briefings — not as a default container.

### Hover, press, focus

- **Hover**: darken backgrounds (primary CTA → signaloranje-press; navy → havsbla-85). Outline buttons fill on hover (transparent → havsblå). Never use opacity-fade for hover; it reads as "broken" in cold light.
- **Press**: same color as hover state, no scale transform. Industrial tools don't shrink when you push them.
- **Focus**: 3px outer halo at 12% of the brand color. `havsblå` halo for inputs, never orange — orange means akut, not "you're typing here."

### Motion

Restrained. The product is used in stressful contexts — bouncy animations read as unserious.

- **Functional only.** Modal fades 120ms. Drawer slides 320ms. Page tab cross-fades 200ms.
- **No confetti, no spring physics, no delight micro-interactions.** A booked appointment slides into the calendar — that's it.
- **Loading**: skeleton states that show the structure of arriving content. Never indeterminate spinners on screens longer than ½ second.
- **Active call**: a slow, calm heartbeat pulse on the call card (the call is alive, not loading).
- **Akutnotis motion is unique**: a single attention-claiming pulse, then stillness. Not a continuous wobble. The first pulse signals; the stillness signals "this is now waiting on you."
- **Easing**: `cubic-bezier(0.2, 0, 0, 1)` standard. No overshoot easings, no `cubic-bezier(0.68, -0.55, …)` consumer-app curves.

### Transparency & blur

Avoid both. Product UI is opaque. The single permitted use is the **focus-ring halo at 12% of brand color** and the **status pill backgrounds** (12–16% tint of the foreground color, used for chip fill). No backdrop-filter blur anywhere.

### Imagery vibe

- **Daylight, not stage lighting.** Cold blue-grey of a January Bromma morning; amber of a Skellefteå summer afternoon; headlamp-yellow of a källare in november. If the photo could have been shot in California, reshoot it.
- **Subjects**: real Swedish hantverkare in real Swedish working environments. Never models, never staged "diverse young professional team" group shots, never stock.
- **Objects are protagonists** (Pleo still-life sensibility): a Bahco wrench on a faktura, an iPhone in a magnetic dashboard holder, an iPad propped against a coffee cup at 06:30. Honest, used, scuffed.
- **Composition**: arranged but accidental-looking. Generous negative space. Product screenshot integrated into the physical scene, never floating against a gradient.
- **Aspect**: 3:2 dominant. Portrait 4:5 for hero portraits.
- **Forbidden**: stock photography, isometric 3D illustrations, cartoon plumbers, sunsets, "freedom" imagery, group brainstorm scenes with sticky notes.

### Layout rules

- **Type-led OR image-led** — never both fighting for attention (Klarna).
- **Editorial composition over feature-list density** on marketing pages. Density is permitted, even encouraged, deep in the product (samtalsdetalj, audit logs, integration pages).
- **Left-aligned by default.** Centered text is allowed only on standalone marketing display moments. The rest of the system is left-aligned.
- **Fixed elements**: sticky top nav (havsblå), no sticky footers, no chat-widget bubbles.

---

## ICONOGRAPHY

Verkstad is **icon-light**. The brand brief does not specify an icon system; the inspiration shelf (Pleo, Klarna, Linear) all use minimal, consistent line iconography.

### What we use

- **Lucide** (loaded from CDN) — modern grotesque-friendly stroke icons, 1.75px stroke at 20px size. Lucide is the closest open-source match to Söhne's geometry, and its restraint suits the brand. We pin to a tagged release. Substitution flagged: Lucide is a **stand-in until the user provides the canonical icon set** if one exists in their codebase.

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<script>lucide.createIcons();</script>
```

- **The orange dot** (`.v-dot`) — the wordmark accent. Functions as the brand's only true pictogram. It earns its place by appearing exactly once per surface.
- **Status dots** — small filled circles (8px) inside status pills. Color-coded to the meaning (green/red/orange/grey).

### What we do not use

- **No emoji**, anywhere. The bullet list above already said it; saying it again because it matters.
- **No bespoke illustration system.** No cartoon plumbers, no isometric vans, no aspirational illustrated people. If we need to depict something, we photograph it.
- **No icon font.** Vector SVG only.
- **No multi-color or filled-glyph icons.** Lucide-style line is the rule.

### Sizing & color

- **20×20** is the default product UI icon size. **24×24** on touch surfaces.
- **Stroke width** 1.75–2px. Match Lucide's defaults.
- **Color**: icons inherit `currentColor` from the surrounding text. Never the signaloranje, ever, except inside an akutnotis where the entire surface is orange.

### When iconography earns its place

Inside the dashboard, an icon may stand alone in front of a label only when the icon is genuinely faster to read than the label (calendar, phone, paperclip, search). Otherwise, **label-only buttons win**. Magnus is presumed competent; he does not need a tooltip explaining what "Inställningar" means.

### Logo & wordmark assets

| File | Use |
|---|---|
| `assets/wordmark.svg` | Light surfaces (linne backgrounds) |
| `assets/wordmark-on-dark.svg` | Dark surfaces (havsblå backgrounds) |
| `assets/mark.svg` | App icons, favicons large, tight square contexts |
| `assets/favicon.svg` | Browser tab |
| `assets/photo-placeholder-3x2.svg` | Stand-in for production photography (3:2) |
| `assets/photo-placeholder-portrait.svg` | Stand-in for portrait photography (4:5) |

### Forbidden moves

- Don't drop the orange dot from the wordmark "to be safe." It is the brand.
- Don't tilt, italicize, or animate the wordmark.
- Don't put the wordmark at less than 80px wide. Below that, use the mark.

---
